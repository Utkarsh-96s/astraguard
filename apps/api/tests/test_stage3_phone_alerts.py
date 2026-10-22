"""Test suite for Stage 3: Phone Alerts (Web Push PWA & ntfy.sh)."""
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from pywebpush import WebPushException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Alert, NotificationChannel, Subscription
from app.services.adapters.ntfy import NtfyAdapter
from app.services.adapters.webpush import WebPushAdapter, generate_vapid_keypair
from app.services.tokens import generate_action_token


@pytest.mark.asyncio
async def test_vapid_keypair_generation():
    """Verify cryptographic P-256 VAPID keypair generation."""
    pub, priv = generate_vapid_keypair()
    assert isinstance(pub, str) and len(pub) > 40
    assert isinstance(priv, str) and ("-----BEGIN PRIVATE KEY-----" in priv or "-----BEGIN EC PRIVATE KEY-----" in priv)


@pytest.mark.asyncio
async def test_vapid_public_key_and_keygen_endpoints(client: AsyncClient):
    """Verify GET /push/vapid-public-key and POST /push/generate-vapid-keys."""
    # Test with empty VAPID key
    orig_pub = settings.VAPID_PUBLIC_KEY
    settings.VAPID_PUBLIC_KEY = ""
    try:
        res = await client.get("/api/v1/notifications/push/vapid-public-key")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "NOT CONFIGURED"
        assert data["public_key"] is None

        # Generate keys endpoint
        gen_res = await client.post("/api/v1/notifications/push/generate-vapid-keys")
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "VAPID_PUBLIC_KEY" in gen_data
        assert "VAPID_PRIVATE_KEY" in gen_data

        # Test with configured public key
        settings.VAPID_PUBLIC_KEY = gen_data["VAPID_PUBLIC_KEY"]
        res2 = await client.get("/api/v1/notifications/push/vapid-public-key")
        assert res2.status_code == 200
        assert res2.json()["status"] == "READY"
        assert res2.json()["public_key"] == gen_data["VAPID_PUBLIC_KEY"]
    finally:
        settings.VAPID_PUBLIC_KEY = orig_pub


@pytest.mark.asyncio
async def test_webpush_subscription_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """Verify subscribing and unsubscribing a browser device via Web Push endpoints."""
    endpoint = f"https://fcm.googleapis.com/fcm/send/test_{uuid.uuid4().hex[:12]}"
    payload = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9t0Ppk6CmJedHYg2m0MwQ3mg5DI2eh7HHGEG_gBiT1xD24",
            "auth": "tBHItJI5svbpez7KI4CCXg",
        },
        "user_id": "FlightDirector_Sarah",
        "user_agent": "Mozilla/5.0 Test PWA Browser",
    }

    # Subscribe
    res = await client.post("/api/v1/notifications/push/subscribe", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "subscribed"
    channel_id = data["channel_id"]

    # Verify channel in DB
    ch = await db_session.get(NotificationChannel, channel_id)
    assert ch is not None
    assert ch.type == "webpush"
    assert ch.status == "CONNECTED"
    assert ch.prefs["endpoint"] == endpoint

    # Verify default subscription was created
    stmt = select(Subscription).where(Subscription.channel_id == channel_id)
    subs = list((await db_session.execute(stmt)).scalars().all())
    assert len(subs) == 1
    assert subs[0].min_level == "WATCH"

    # Unsubscribe
    unsub_res = await client.post("/api/v1/notifications/push/unsubscribe", json={"endpoint": endpoint})
    assert unsub_res.status_code == 200
    assert unsub_res.json()["status"] == "unsubscribed"

    await db_session.refresh(ch)
    assert ch.status == "UNSUBSCRIBED"


@pytest.mark.asyncio
async def test_webpush_adapter_send_payload_and_mock(db_session: AsyncSession):
    """Verify WebPushAdapter formatting and mock delivery."""
    adapter = WebPushAdapter()

    alert = Alert(
        id="ALT-WP-001",
        snapshot_id="RSN-1",
        level="CRITICAL",
        title="ISS Conjunction Risk",
        rationale="Close approach with orbital debris within 450m.",
        recommendation="Execute prograde orbital adjustment maneuver.",
        status="ACTIVE",
        synthetic=True,
        dedup_key="iss_wp_001",
        created_at=datetime.now(UTC),
    )

    channel = NotificationChannel(
        id="chan_wp_test",
        user_id="Operator",
        type="webpush",
        name="Test Browser",
        encrypted_address="https://updates.push.services.mozilla.com/wpush/v2/test_token",
        prefs={
            "endpoint": "https://updates.push.services.mozilla.com/wpush/v2/test_token",
            "keys": {"p256dh": "test_p256", "auth": "test_auth"},
        },
        status="CONNECTED",
    )

    action_tokens = {
        "approve_url": "http://test/api/v1/alerts/ALT-WP-001/action-token/tok_approve",
        "snooze_url": "http://test/api/v1/alerts/ALT-WP-001/action-token/tok_snooze",
    }

    # Temporarily supply mock VAPID credentials
    orig_pub = settings.VAPID_PUBLIC_KEY
    orig_priv = settings.VAPID_PRIVATE_KEY
    settings.VAPID_PUBLIC_KEY = "test_pub_key"
    settings.VAPID_PRIVATE_KEY = "-----BEGIN EC PRIVATE KEY-----\nMOCK_KEY\n-----END EC PRIVATE KEY-----"

    captured_payload = None

    def fake_webpush(subscription_info, data, vapid_private_key, vapid_claims, ttl):
        nonlocal captured_payload
        captured_payload = json.loads(data)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        return mock_resp

    try:
        with patch("app.services.adapters.webpush.webpush", side_effect=fake_webpush):
            res = await adapter.send(alert, channel, test=False, action_tokens=action_tokens)
            assert res.success is True
            assert res.provider_message_id is not None
            assert res.provider_message_id.startswith("wp_")

            assert captured_payload is not None
            assert "[SIMULATED]" in captured_payload["title"]
            assert "ISS Conjunction Risk" in captured_payload["title"]
            assert captured_payload["tag"] == "alert-ALT-WP-001"
            assert captured_payload["data"]["actions"][0]["action"] == "approve"
            assert captured_payload["data"]["actions"][0]["url"] == action_tokens["approve_url"]
    finally:
        settings.VAPID_PUBLIC_KEY = orig_pub
        settings.VAPID_PRIVATE_KEY = orig_priv


@pytest.mark.asyncio
async def test_webpush_adapter_410_expired_handling(db_session: AsyncSession):
    """Verify WebPushAdapter handles 410 Gone by deactivating the channel without retries."""
    adapter = WebPushAdapter()

    alert = Alert(
        id="ALT-WP-410",
        snapshot_id="RSN-410",
        level="WARNING",
        title="Telemetry Drift Warning",
        rationale="Battery temperature drift.",
        recommendation="Switch to secondary bus.",
        status="ACTIVE",
        synthetic=True,
        dedup_key="wp_410",
        created_at=datetime.now(UTC),
    )

    channel = NotificationChannel(
        id="chan_wp_410",
        user_id="Operator",
        type="webpush",
        name="Expired Browser",
        encrypted_address="https://fcm.googleapis.com/fcm/send/expired_token",
        prefs={
            "endpoint": "https://fcm.googleapis.com/fcm/send/expired_token",
            "keys": {"p256dh": "k", "auth": "a"},
        },
        status="CONNECTED",
    )

    orig_pub = settings.VAPID_PUBLIC_KEY
    orig_priv = settings.VAPID_PRIVATE_KEY
    settings.VAPID_PUBLIC_KEY = "test_pub"
    settings.VAPID_PRIVATE_KEY = "test_priv"

    mock_resp = MagicMock()
    mock_resp.status_code = 410
    exc = WebPushException("Subscription has expired or is invalid.", response=mock_resp)

    try:
        with patch("app.services.adapters.webpush.webpush", side_effect=exc):
            res = await adapter.send(alert, channel, test=False)
            assert res.success is False
            assert res.retryable is False  # Never retry expired subscriptions
            assert "410" in res.error
            assert channel.status == "ERROR"
            assert "expired" in channel.last_error.lower()
    finally:
        settings.VAPID_PUBLIC_KEY = orig_pub
        settings.VAPID_PRIVATE_KEY = orig_priv


@pytest.mark.asyncio
async def test_ntfy_adapter_payload_and_priorities():
    """Verify NtfyAdapter formats priorities and HTTP action buttons."""
    adapter = NtfyAdapter()

    alert_critical = Alert(
        id="ALT-NTFY-01",
        snapshot_id="RSN-1",
        level="CRITICAL",
        title="Immediate Debris Collision",
        rationale="TCA < 2 hours with Pc > 1e-4.",
        recommendation="Confirm collision avoidance maneuver.",
        status="ACTIVE",
        synthetic=True,
        dedup_key="ntfy_01",
        created_at=datetime.now(UTC),
    )

    channel = NotificationChannel(
        id="chan_ntfy_01",
        user_id="Operator",
        type="ntfy",
        name="Mission Team ntfy",
        encrypted_address="astraguard_mission_ops",
        prefs={"topic": "astraguard_mission_ops", "server_url": "https://ntfy.sh"},
        status="CONNECTED",
    )

    action_tokens = {
        "approve_url": "http://api/action-token/approve123",
        "snooze_url": "http://api/action-token/snooze123",
    }

    captured_post = None

    class MockHttpxClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, url, json=None, headers=None):
            nonlocal captured_post
            captured_post = {"url": url, "json": json, "headers": headers}
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.text = '{"id":"ntfy_msg_7788"}'
            mock_res.json.return_value = {"id": "ntfy_msg_7788"}
            return mock_res

    with patch("httpx.AsyncClient", return_value=MockHttpxClient()):
        res = await adapter.send(alert_critical, channel, test=False, action_tokens=action_tokens)
        assert res.success is True
        assert res.provider_message_id == "ntfy_msg_7788"

        assert captured_post is not None
        payload = captured_post["json"]
        assert payload["topic"] == "astraguard_mission_ops"
        assert payload["priority"] == 5  # Critical = 5 (urgent)
        assert "satellite" in payload["tags"]
        assert "rotating_light" in payload["tags"]

        # Verify action buttons
        actions = payload["actions"]
        assert len(actions) == 3
        assert actions[0]["action"] == "view"
        assert actions[1]["action"] == "http"
        assert actions[1]["label"] == "Approve"
        assert actions[1]["url"] == action_tokens["approve_url"]
        assert actions[2]["action"] == "http"
        assert actions[2]["label"] == "Snooze 30m"
        assert actions[2]["url"] == action_tokens["snooze_url"]


@pytest.mark.asyncio
async def test_ntfy_test_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verify POST /api/v1/notifications/ntfy/test executes mock publish cleanly."""
    class MockHttpxClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def post(self, url, json=None, headers=None):
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.text = '{"id":"ntfy_test_999"}'
            mock_res.json.return_value = {"id": "ntfy_test_999"}
            return mock_res

    with patch("httpx.AsyncClient", return_value=MockHttpxClient()):
        res = await client.post(
            "/api/v1/notifications/ntfy/test",
            json={"topic": "astraguard_test_topic", "server_url": "https://ntfy.sh"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "delivered"
        assert data["topic"] == "astraguard_test_topic"
        assert data["provider_message_id"] == "ntfy_test_999"


@pytest.mark.asyncio
async def test_signed_token_action_execution_from_phone(client: AsyncClient, db_session: AsyncSession):
    """Verify that an HTTP action executed from phone notification acknowledges alert in DB."""
    alert = Alert(
        id="ALT-PHONE-HITL-01",
        snapshot_id="RSN-HITL",
        level="CRITICAL",
        title="Severe Conjunction Alert",
        rationale="Collision probability exceeds safety threshold.",
        recommendation="Acknowledge and proceed with avoidance.",
        status="ACTIVE",
        synthetic=True,
        dedup_key="hitl_phone_01",
        created_at=datetime.now(UTC),
    )
    db_session.add(alert)
    await db_session.commit()

    # Generate single-use signed token for "approve" action
    token, _ = await generate_action_token(
        db=db_session,
        alert_id=alert.id,
        channel_id="chan_phone",
        action="approve",
        user_id="MobileOperator_Alex",
        expiry_seconds=3600,
    )
    await db_session.commit()

    # Simulate mobile action click (POST to signed token endpoint)
    res = await client.post(f"/api/v1/alerts/{alert.id}/action-token/{token}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["action_executed"] == "approve"
    assert data["alert_status"] == "ACKNOWLEDGED"

    # Confirm in DB
    await db_session.refresh(alert)
    assert alert.status == "ACKNOWLEDGED"

    # Confirm token is consumed and cannot be replayed
    res_replay = await client.post(f"/api/v1/alerts/{alert.id}/action-token/{token}")
    assert res_replay.status_code == 400
    assert "already been used" in res_replay.json()["detail"].lower()
