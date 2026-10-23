"""Tests for Stage 1: Notification Core, Outbox Pattern, Escalation Engine, and Signed Tokens."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import (
    Alert,
    NotificationChannel,
    NotificationOutbox,
    Subscription,
)
from app.services.adapters.fake import FakeProviderAdapter
from app.services.adapters.registry import adapter_registry
from app.services.escalation_engine import escalation_engine
from app.services.outbox_worker import outbox_worker
from app.services.tokens import (
    generate_action_token,
)


@pytest.fixture
def fake_adapter() -> FakeProviderAdapter:
    """Fixture to provide and register a clean FakeProviderAdapter."""
    adapter = FakeProviderAdapter("fake")
    adapter_registry.register("fake", adapter)
    return adapter


@pytest.mark.asyncio
async def test_honest_health_status(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Rule verification: Honest status reporting; missing credentials report exact env var."""
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    res = await client.get("/api/v1/notifications/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"

    # Telegram adapter should honestly report NOT CONFIGURED when TELEGRAM_BOT_TOKEN is unset
    providers = {p["type"]: p for p in data["providers"]}
    assert "telegram" in providers
    assert providers["telegram"]["status"] == "NOT CONFIGURED"
    assert "TELEGRAM_BOT_TOKEN" in providers["telegram"]["missing_env"]

    # Fake adapter reports operational
    assert "fake" in providers
    assert providers["fake"]["status"] == "CONNECTED"


@pytest.mark.asyncio
async def test_channels_crud(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test creating, listing, and deleting notification channels."""
    create_res = await client.post(
        "/api/v1/notifications/channels",
        json={
            "name": "Mission Safety Ops",
            "type": "fake",
            "address": "ops_test_queue",
            "user_id": "FlightDirector_Sarah",
            "prefs": {"quiet_hours": {"start": "22:00", "end": "06:00"}},
        },
    )
    assert create_res.status_code == 200
    ch_data = create_res.json()["channel"]
    channel_id = ch_data["id"]

    # List channels
    list_res = await client.get("/api/v1/notifications/channels")
    assert list_res.status_code == 200
    channels = list_res.json()
    assert any(c["id"] == channel_id for c in channels)

    # Delete channel
    del_res = await client.delete(f"/api/v1/notifications/channels/{channel_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_outbox_creation_on_test_alert(client: AsyncClient, db_session: AsyncSession, fake_adapter: FakeProviderAdapter) -> None:
    """Test that firing a test alert creates L1 outbox records flagged test=true."""
    # Create channel and subscription
    channel = NotificationChannel(
        id=f"CHN-{uuid.uuid4().hex[:8].upper()}",
        user_id="Operator",
        type="fake",
        name="Test Channel",
        encrypted_address="test_addr",
        status="CONNECTED",
        created_at=datetime.now(UTC),
    )
    db_session.add(channel)
    sub = Subscription(
        id=f"SUB-{uuid.uuid4().hex[:8].upper()}",
        channel_id=channel.id,
        min_level="WATCH",
        enabled=True,
        created_at=datetime.now(UTC),
    )
    db_session.add(sub)
    await db_session.commit()

    # Fire test alert
    res = await client.post(
        "/api/v1/alerts/test",
        json={"level": "CRITICAL", "asset_id": "SENTINEL-2A"},
    )
    assert res.status_code == 200
    data = res.json()
    alert_id = data["alert"]["id"]
    assert alert_id.startswith("ALT-TEST-")
    assert data["test"] is True

    # Check that outbox row exists in DB
    outbox_stmt = select(NotificationOutbox).where(NotificationOutbox.alert_id == alert_id)
    outbox_res = await db_session.execute(outbox_stmt)
    outbox_items = list(outbox_res.scalars().all())
    assert len(outbox_items) >= 1
    item = outbox_items[0]
    assert item.status == "queued"
    assert item.test is True
    assert item.escalation_level == 1


@pytest.mark.asyncio
async def test_outbox_processing_retry_and_backoff(
    db_session: AsyncSession,
    fake_adapter: FakeProviderAdapter,
) -> None:
    """Exit Gate Verification: Outbox rows retried on injected failure, delivered on next attempt."""
    now = datetime.now(UTC)

    # Create channel
    channel = NotificationChannel(
        id=f"CHN-{uuid.uuid4().hex[:8].upper()}",
        user_id="Operator",
        type="fake",
        name="Retry Channel",
        encrypted_address="retry_addr",
        status="CONNECTED",
        created_at=now,
    )
    db_session.add(channel)

    # Create test alert
    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] Critical Debris Risk",
        rationale="High Pc conjunction",
        recommendation="Maneuver",
        status="ACTIVE",
        dedup_key="test_retry_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)

    # Create outbox item
    outbox_item = NotificationOutbox(
        id=f"NOB-{uuid.uuid4().hex[:8].upper()}",
        alert_id=alert.id,
        channel_id=channel.id,
        escalation_level=1,
        idempotency_key="idemp_retry_001",
        status="queued",
        attempts=0,
        max_attempts=3,
        next_attempt_at=now,
        test=True,
        created_at=now,
    )
    db_session.add(outbox_item)
    await db_session.commit()

    # 1. Inject failure for the first attempt
    fake_adapter.inject_failure(times=1)
    processed = await outbox_worker.claim_and_process_batch(db_session)
    assert processed == 1

    await db_session.refresh(outbox_item)
    assert outbox_item.status == "failed"
    assert outbox_item.attempts == 1
    assert "Injected temporary network glitch" in (outbox_item.last_error or "")
    next_at = outbox_item.next_attempt_at
    if next_at.tzinfo is None:
        next_at = next_at.replace(tzinfo=UTC)
    assert next_at > now

    # 2. Fast-forward next_attempt_at and process again (now succeeds)
    outbox_item.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)
    outbox_worker._last_send_by_channel.clear()
    await db_session.commit()

    processed_2 = await outbox_worker.claim_and_process_batch(db_session)
    assert processed_2 == 1

    await db_session.refresh(outbox_item)
    assert outbox_item.status == "delivered"
    assert outbox_item.attempts == 2
    assert outbox_item.provider_message_id is not None
    assert len(fake_adapter.sent_deliveries) == 1


@pytest.mark.asyncio
async def test_dead_letter_queue_after_max_attempts(
    db_session: AsyncSession,
    fake_adapter: FakeProviderAdapter,
    client: AsyncClient,
) -> None:
    """Exit Gate Verification: Delivery moves to dead-letter queue after max attempts."""
    now = datetime.now(UTC)

    channel = NotificationChannel(
        id=f"CHN-{uuid.uuid4().hex[:8].upper()}",
        user_id="Operator",
        type="fake",
        name="Dead Letter Channel",
        encrypted_address="dlq_addr",
        status="CONNECTED",
        created_at=now,
    )
    db_session.add(channel)

    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] DLQ Alert",
        rationale="Conjunction",
        recommendation="Maneuver",
        status="ACTIVE",
        dedup_key="test_dlq_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)

    outbox_item = NotificationOutbox(
        id=f"NOB-{uuid.uuid4().hex[:8].upper()}",
        alert_id=alert.id,
        channel_id=channel.id,
        escalation_level=1,
        idempotency_key="idemp_dlq_001",
        status="queued",
        attempts=2,  # Already attempted twice
        max_attempts=3,
        next_attempt_at=now,
        test=True,
        created_at=now,
    )
    db_session.add(outbox_item)
    await db_session.commit()

    # Fail permanently on the 3rd attempt
    fake_adapter.set_permanent_failure(True)
    await outbox_worker.claim_and_process_batch(db_session)

    await db_session.refresh(outbox_item)
    assert outbox_item.status == "dead"
    assert outbox_item.attempts == 3

    # Verify DLQ API returns this dead item
    dlq_res = await client.get("/api/v1/notifications/outbox/dead-letter")
    assert dlq_res.status_code == 200
    dlq_items = dlq_res.json()
    assert any(i["outbox_id"] == outbox_item.id for i in dlq_items)

    # Verify Retry endpoint resets it
    retry_res = await client.post(f"/api/v1/notifications/outbox/{outbox_item.id}/retry")
    assert retry_res.status_code == 200
    await db_session.refresh(outbox_item)
    assert outbox_item.status == "queued"
    assert outbox_item.attempts == 0


@pytest.mark.asyncio
async def test_escalation_engine_and_ack_cancellation(
    db_session: AsyncSession,
    fake_adapter: FakeProviderAdapter,
    client: AsyncClient,
) -> None:
    """Exit Gate Verification: Acknowledge from one channel stops escalation and edits delivered messages."""
    now = datetime.now(UTC)

    # Create fake channel
    channel = NotificationChannel(
        id=f"CHN-{uuid.uuid4().hex[:8].upper()}",
        user_id="Operator",
        type="fake",
        name="Escalation Channel",
        encrypted_address="esc_addr",
        status="CONNECTED",
        created_at=now,
    )
    db_session.add(channel)

    sub = Subscription(
        id=f"SUB-{uuid.uuid4().hex[:8].upper()}",
        channel_id=channel.id,
        min_level="WATCH",
        enabled=True,
        created_at=now,
    )
    db_session.add(sub)

    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] Critical Alert with Escalation",
        rationale="Conjunction danger",
        recommendation="Maneuver",
        status="ACTIVE",
        dedup_key="test_esc_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)
    await db_session.commit()

    # Initialize escalation
    esc_state = await escalation_engine.initialize_alert_escalation(db_session, alert, test=True)
    assert esc_state.current_level == 1
    assert esc_state.halted_at is None

    # Deliver L1 outbox item
    await outbox_worker.claim_and_process_batch(db_session)
    assert len(fake_adapter.sent_deliveries) == 1

    # Acknowledge alert via API
    ack_res = await client.post(
        f"/api/v1/alerts/{alert.id}/action",
        json={"user": "FlightDirector_Sarah", "action": "approve", "note": "Burn authorized."},
    )
    assert ack_res.status_code == 200

    # Verify escalation is halted
    await db_session.refresh(esc_state)
    assert esc_state.halted_at is not None
    assert esc_state.halted_reason == "acknowledged"

    # Verify message edit_after_ack was called on fake adapter
    assert len(fake_adapter.edited_messages) == 1
    assert fake_adapter.edited_messages[0]["action"] == "ACKNOWLEDGED"
    assert fake_adapter.edited_messages[0]["operator"] == "FlightDirector_Sarah"

    # Advance escalations should not escalate halted alerts
    advanced = await escalation_engine.advance_escalations(db_session)
    assert advanced == 0


@pytest.mark.asyncio
async def test_hmac_signed_action_tokens(
    db_session: AsyncSession,
    client: AsyncClient,
) -> None:
    """Test HMAC action token generation, verification, execution, and single-use enforcement."""
    now = datetime.now(UTC)

    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] Token Alert",
        rationale="Conjunction",
        recommendation="Maneuver",
        status="ACTIVE",
        dedup_key="test_token_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)
    await db_session.commit()

    # Generate token
    token_str, action_url = await generate_action_token(
        db_session,
        alert_id=alert.id,
        channel_id=None,
        action="approve",
        user_id="TokenOperator_Alex",
    )
    assert "." in token_str

    # GET confirmation page (should display HTML form, NOT execute action)
    get_res = await client.get(f"/api/v1/alerts/{alert.id}/action-token/{token_str}")
    assert get_res.status_code == 200
    assert "text/html" in get_res.headers["content-type"]
    await db_session.refresh(alert)
    assert alert.status == "ACTIVE"  # Unchanged by GET

    # POST execution (executes action)
    post_res = await client.post(f"/api/v1/alerts/{alert.id}/action-token/{token_str}")
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "success"
    assert data["action_executed"] == "approve"
    assert data["operator"] == "TokenOperator_Alex"

    await db_session.refresh(alert)
    assert alert.status == "ACKNOWLEDGED"

    # Replay attack / duplicate use should fail (single-use enforced)
    replay_res = await client.post(f"/api/v1/alerts/{alert.id}/action-token/{token_str}")
    assert replay_res.status_code == 400
    assert "already been used" in replay_res.json()["detail"]


@pytest.mark.asyncio
async def test_server_side_alerts_filtering_and_cursor(
    db_session: AsyncSession,
    client: AsyncClient,
) -> None:
    """Test server-side search, status filter, and since cursor in GET /api/v1/alerts."""
    t0 = datetime.now(UTC) - timedelta(minutes=5)
    t1 = datetime.now(UTC)

    alert_1 = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="WATCH",
        title="ADCS Gyroscope Drift",
        rationale="Thermal gradient caused slight rate sensor offset.",
        recommendation="Recalibrate sensors.",
        status="ACTIVE",
        dedup_key="gyro_drift_01",
        synthetic=True,
        created_at=t0,
    )
    alert_2 = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="Orbital Conjunction Cosmos Fragment",
        rationale="Severe collision probability exceeding 1e-4 threshold.",
        recommendation="CAM burn.",
        status="ACTIVE",
        dedup_key="cosmos_frag_02",
        synthetic=True,
        created_at=t1,
    )
    db_session.add_all([alert_1, alert_2])
    await db_session.commit()

    # Search filter 'Gyroscope'
    res_search = await client.get("/api/v1/alerts?q=gyroscope")
    assert res_search.status_code == 200
    items = res_search.json()
    assert len(items) == 1
    assert items[0]["id"] == alert_1.id

    # Severity filter 'CRITICAL'
    res_crit = await client.get("/api/v1/alerts?level=CRITICAL")
    assert res_crit.status_code == 200
    crit_items = res_crit.json()
    assert all(i["level"] == "CRITICAL" for i in crit_items)

    # 'since' cursor: only alert_2 created after t0 + 1s
    cursor = (t0 + timedelta(seconds=1)).isoformat()
    res_since = await client.get(f"/api/v1/alerts?since={cursor}")
    assert res_since.status_code == 200
    since_items = res_since.json()
    assert any(i["id"] == alert_2.id for i in since_items)
    assert not any(i["id"] == alert_1.id for i in since_items)
