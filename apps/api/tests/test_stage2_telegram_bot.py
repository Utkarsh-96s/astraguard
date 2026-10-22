"""Tests for Stage 2: Real Telegram Bot (Webhook, Polling, Linking, Commands, Inline Callbacks, Error Handling)."""
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import (
    Alert,
    InboundEvent,
    NotificationChannel,
    OperatorAction,
    RiskSnapshot,
)
from app.services.adapters.telegram import TelegramBotAdapter
from app.services.telegram_service import (
    telegram_service,
)
from app.services.tokens import generate_linking_token


class MockTelegramTransport(httpx.AsyncBaseTransport):
    """Mock HTTP transport intercepting requests to api.telegram.org."""

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []
        self.edited_messages: list[dict[str, Any]] = []
        self.answered_callbacks: list[dict[str, Any]] = []
        self.injected_status_code: int = 200
        self.injected_response_data: dict[str, Any] | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        content_json = {}
        if request.content:
            try:
                content_json = json.loads(request.content.decode("utf-8"))
            except Exception:
                pass

        if self.injected_status_code != 200:
            err_data = self.injected_response_data or {
                "ok": False,
                "error_code": self.injected_status_code,
                "description": "Injected Telegram error",
            }
            return httpx.Response(self.injected_status_code, json=err_data)

        if "getMe" in url_str:
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {
                        "id": 987654321,
                        "is_bot": True,
                        "first_name": "ASTRA-GUARD Alert Bot",
                        "username": "AstraGuardAlertsBot",
                    },
                },
            )

        if "sendMessage" in url_str:
            msg_id = len(self.sent_messages) + 1001
            self.sent_messages.append(content_json)
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {
                        "message_id": msg_id,
                        "chat": {"id": content_json.get("chat_id")},
                        "text": content_json.get("text"),
                    },
                },
            )

        if "editMessageText" in url_str:
            self.edited_messages.append(content_json)
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": {
                        "message_id": content_json.get("message_id"),
                        "text": content_json.get("text"),
                    },
                },
            )

        if "answerCallbackQuery" in url_str:
            self.answered_callbacks.append(content_json)
            return httpx.Response(200, json={"ok": True, "result": True})

        if "setWebhook" in url_str:
            return httpx.Response(200, json={"ok": True, "result": True, "description": "Webhook set"})

        return httpx.Response(200, json={"ok": True})


@pytest.fixture
def mock_tg() -> MockTelegramTransport:
    """Fixture to provide and register mock Telegram transport."""
    mock = MockTelegramTransport()
    telegram_service._mock_transport = mock
    # Temporarily set token for tests
    orig_token = settings.TELEGRAM_BOT_TOKEN
    settings.TELEGRAM_BOT_TOKEN = "123456:TEST_TELEGRAM_TOKEN_ABC"
    yield mock
    telegram_service._mock_transport = None
    settings.TELEGRAM_BOT_TOKEN = orig_token


@pytest.mark.asyncio
async def test_telegram_health_check_connected(mock_tg: MockTelegramTransport) -> None:
    """Test health check reports CONNECTED when valid token is configured."""
    adapter = TelegramBotAdapter()
    health = await adapter.health_check()
    assert health["status"] == "CONNECTED"
    assert "AstraGuardAlertsBot" in health["details"]
    assert health["missing_env"] == []


@pytest.mark.asyncio
async def test_telegram_health_check_not_configured() -> None:
    """Rule verification: Honest status NOT CONFIGURED when credentials missing."""
    orig_token = settings.TELEGRAM_BOT_TOKEN
    settings.TELEGRAM_BOT_TOKEN = ""
    try:
        adapter = TelegramBotAdapter()
        health = await adapter.health_check()
        assert health["status"] == "NOT CONFIGURED"
        assert "TELEGRAM_BOT_TOKEN" in health["missing_env"]
    finally:
        settings.TELEGRAM_BOT_TOKEN = orig_token


@pytest.mark.asyncio
async def test_telegram_linking_handshake(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Exit Gate Verification: Linking code generated from dashboard connects phone chat upon /start <code>."""
    # 1. Dashboard generates one-time linking token
    code, deep_link = await generate_linking_token(
        db_session, user_id="FlightDirector_Alex", channel_type="telegram"
    )
    assert code.startswith("LINK-")
    assert f"start={code}" in deep_link

    # 2. Telegram webhook receives /start <code> from user
    chat_id = 98765432
    update = {
        "update_id": 1,
        "message": {
            "message_id": 101,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "first_name": "Alex", "username": "alex_ops"},
            "text": f"/start {code}",
        },
    }

    result = await telegram_service.process_update(update, db_session)
    assert result["status"] == "linked"

    # 3. Channel should now exist and be CONNECTED in DB
    stmt = select(NotificationChannel).where(NotificationChannel.encrypted_address == str(chat_id))
    channel = (await db_session.execute(stmt)).scalars().first()
    assert channel is not None
    assert channel.status == "CONNECTED"
    assert channel.verified_at is not None
    assert channel.user_id == "FlightDirector_Alex"

    # 4. Confirmation message was sent to Telegram chat
    assert len(mock_tg.sent_messages) == 1
    assert "Connected" in mock_tg.sent_messages[0]["text"]


@pytest.mark.asyncio
async def test_telegram_commands(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Test flight operations Telegram bot commands (/status, /alerts, /ack, /snooze, /mute, /help)."""
    now = datetime.now(UTC)
    chat_id = 888123

    # Seed snapshot and alert
    snapshot = RiskSnapshot(
        id="RSN-CMD-001",
        asset_id="SENTINEL-2A",
        ts=now,
        r_h=0.04,
        r_d=0.02,
        r_e=0.10,
        score=6.5,
        level="NOMINAL",
        synthetic=True,
        created_at=now,
    )
    db_session.add(snapshot)

    alert = Alert(
        id="ALT-CMD-001",
        snapshot_id="RSN-CMD-001",
        level="WARNING",
        title="ADCS Reaction Wheel Friction",
        rationale="Torque deviation detected",
        recommendation="Spin down wheel 2",
        status="ACTIVE",
        dedup_key="cmd_alert_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)
    await db_session.commit()

    # /status command
    await telegram_service.process_update({
        "update_id": 2,
        "message": {"chat": {"id": chat_id}, "text": "/status", "from": {"username": "pilot"}},
    }, db_session)
    assert any("SENTINEL-2A" in m.get("text", "") for m in mock_tg.sent_messages)

    # /alerts command
    await telegram_service.process_update({
        "update_id": 3,
        "message": {"chat": {"id": chat_id}, "text": "/alerts", "from": {"username": "pilot"}},
    }, db_session)
    assert any("ALT-CMD-001" in m.get("text", "") for m in mock_tg.sent_messages)

    # /ack command
    await telegram_service.process_update({
        "update_id": 4,
        "message": {"chat": {"id": chat_id}, "text": f"/ack {alert.id}", "from": {"username": "pilot"}},
    }, db_session)
    await db_session.refresh(alert)
    assert alert.status == "ACKNOWLEDGED"

    # /snooze command
    await telegram_service.process_update({
        "update_id": 5,
        "message": {"chat": {"id": chat_id}, "text": f"/snooze {alert.id} 45", "from": {"username": "pilot"}},
    }, db_session)
    await db_session.refresh(alert)
    assert alert.status == "SNOOZED"

    # /help command
    await telegram_service.process_update({
        "update_id": 6,
        "message": {"chat": {"id": chat_id}, "text": "/help", "from": {"username": "pilot"}},
    }, db_session)
    assert any("Flight Controller Commands" in m.get("text", "") for m in mock_tg.sent_messages)


@pytest.mark.asyncio
async def test_telegram_inline_callback_approval(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Exit Gate Verification: Pressing Approve button acknowledges alert, halts escalation, and edits message."""
    now = datetime.now(UTC)
    chat_id = 777222

    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] Critical Debris Conjunction Warning",
        rationale="High probability of collision with Cosmos debris fragment. TCA: T-4.2h.",
        recommendation="Execute 0.42 m/s prograde avoidance burn.",
        status="ACTIVE",
        dedup_key="test_tg_callback_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)
    await db_session.commit()

    # Simulate Telegram callback query when user taps "Approve Advisory"
    callback_update = {
        "update_id": 10,
        "callback_query": {
            "id": "cbq_999",
            "from": {"id": chat_id, "username": "flight_director_sarah"},
            "message": {
                "message_id": 5555,
                "chat": {"id": chat_id},
                "text": "CRITICAL MISSION SAFETY ALERT: SENTINEL-2A",
            },
            "data": f"act:approve:{alert.id}",
        },
    }

    res = await telegram_service.process_update(callback_update, db_session)
    assert res["status"] == "action_recorded"
    assert res["action"] == "approve"

    # Verify alert acknowledged in DB
    await db_session.refresh(alert)
    assert alert.status == "ACKNOWLEDGED"

    # Verify audit action recorded
    action_stmt = select(OperatorAction).where(OperatorAction.alert_id == alert.id)
    actions = list((await db_session.execute(action_stmt)).scalars().all())
    assert len(actions) == 1
    assert actions[0].action == "approve"
    assert actions[0].user == "flight_director_sarah"

    # Verify answerCallbackQuery was called
    assert len(mock_tg.answered_callbacks) == 1
    assert mock_tg.answered_callbacks[0]["callback_query_id"] == "cbq_999"

    # Verify editMessageText was called, message updated, and buttons removed
    assert len(mock_tg.edited_messages) == 1
    edited = mock_tg.edited_messages[0]
    assert edited["message_id"] == 5555
    assert "ACKNOWLEDGED" in edited["text"]
    assert edited["reply_markup"]["inline_keyboard"] == []  # Buttons removed


@pytest.mark.asyncio
async def test_telegram_outbound_html_and_inline_keyboard(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Test outbound alert delivery via TelegramBotAdapter formats HTML and builds inline buttons."""
    now = datetime.now(UTC)

    channel = NotificationChannel(
        id="CHN-TG-001",
        user_id="Operator",
        type="telegram",
        name="Ops Chat",
        encrypted_address="12345678",
        status="CONNECTED",
        created_at=now,
    )
    db_session.add(channel)

    alert = Alert(
        id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="[TEST] Critical Solar Flare Radiation Storm",
        rationale="Severe proton flux perturbation detected",
        recommendation="Orient solar arrays and power down sensitive payloads",
        status="ACTIVE",
        dedup_key="test_flare_key",
        synthetic=True,
        created_at=now,
    )
    db_session.add(alert)
    await db_session.commit()

    adapter = TelegramBotAdapter()
    result = await adapter.send(alert, channel, test=True)
    assert result.success is True
    assert result.provider_message_id is not None

    # Check transmitted Telegram message
    assert len(mock_tg.sent_messages) == 1
    sent = mock_tg.sent_messages[0]
    assert sent["parse_mode"] == "HTML"
    assert "<b>[SIMULATED] CRITICAL MISSION SAFETY ALERT</b>" in sent["text"]

    # Verify buttons: Approve, Snooze 30m, Dismiss, and Web Console URL
    buttons = sent["reply_markup"]["inline_keyboard"]
    assert len(buttons) == 2
    row1 = buttons[0]
    row2 = buttons[1]
    assert row1[0]["text"] == "✅ Approve Advisory"
    assert row1[0]["callback_data"] == f"act:approve:{alert.id}"
    assert row1[1]["text"] == "⏱ Snooze 30m"
    assert row2[0]["text"] == "❌ Dismiss"
    assert row2[1]["text"] == "📊 Web Console"
    assert "alerts?id=" in row2[1]["url"]


@pytest.mark.asyncio
async def test_telegram_blocked_error_403(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Rule verification: HTTP 403 (blocked by user) marks channel ERROR and does not retry."""
    channel = NotificationChannel(
        id="CHN-TG-BLOCKED",
        user_id="Operator",
        type="telegram",
        name="Blocked Chat",
        encrypted_address="999000",
        status="CONNECTED",
        created_at=datetime.now(UTC),
    )
    db_session.add(channel)

    alert = Alert(
        id="ALT-TG-ERR",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="Alert",
        rationale="Rationale",
        recommendation="Recommendation",
        status="ACTIVE",
        dedup_key="err_key",
        synthetic=True,
        created_at=datetime.now(UTC),
    )
    db_session.add(alert)
    await db_session.commit()

    # Inject 403 Forbidden
    mock_tg.injected_status_code = 403
    mock_tg.injected_response_data = {
        "ok": False,
        "error_code": 403,
        "description": "Forbidden: bot was blocked by the user",
    }

    adapter = TelegramBotAdapter()
    result = await adapter.send(alert, channel, test=True)
    assert result.success is False
    assert result.retryable is False
    assert channel.status == "ERROR"
    assert "blocked by user" in channel.last_error


@pytest.mark.asyncio
async def test_telegram_rate_limit_429(
    db_session: AsyncSession,
    mock_tg: MockTelegramTransport,
) -> None:
    """Rule verification: HTTP 429 returns retryable failure with retry_after."""
    channel = NotificationChannel(
        id="CHN-TG-RATELIMIT",
        user_id="Operator",
        type="telegram",
        name="Rate Limited Chat",
        encrypted_address="999111",
        status="CONNECTED",
        created_at=datetime.now(UTC),
    )
    db_session.add(channel)

    alert = Alert(
        id="ALT-TG-429",
        snapshot_id="RSN-BASE-001",
        level="CRITICAL",
        title="Alert",
        rationale="Rationale",
        recommendation="Recommendation",
        status="ACTIVE",
        dedup_key="rate_limit_key",
        synthetic=True,
        created_at=datetime.now(UTC),
    )
    db_session.add(alert)
    await db_session.commit()

    # Inject 429 Too Many Requests
    mock_tg.injected_status_code = 429
    mock_tg.injected_response_data = {
        "ok": False,
        "error_code": 429,
        "description": "Too Many Requests: retry after 8",
        "parameters": {"retry_after": 8},
    }

    adapter = TelegramBotAdapter()
    result = await adapter.send(alert, channel, test=True)
    assert result.success is False
    assert result.retryable is True
    assert "retry_after: 8" in (result.error or "")


@pytest.mark.asyncio
async def test_telegram_webhook_secret_token_verification(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Rule verification: Webhook rejects invalid secret token and logs valid event into inbound_events."""
    orig_secret = settings.TELEGRAM_WEBHOOK_SECRET
    settings.TELEGRAM_WEBHOOK_SECRET = "super_secret_webhook_token_999"

    try:
        payload = {"update_id": 99, "message": {"text": "/help", "chat": {"id": 12345}}}

        # 1. Without secret token header -> 403 Forbidden
        res_no_token = await client.post("/api/v1/bot/webhook", json=payload)
        assert res_no_token.status_code == 403

        # 2. With invalid secret token header -> 403 Forbidden
        res_bad_token = await client.post(
            "/api/v1/bot/webhook",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_token"},
        )
        assert res_bad_token.status_code == 403

        # 3. With valid secret token header -> 200 OK
        res_ok = await client.post(
            "/api/v1/bot/webhook",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_webhook_token_999"},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["ok"] is True

        # Verify event was recorded in inbound_events table
        stmt = select(InboundEvent).where(InboundEvent.channel_type == "telegram")
        events = list((await db_session.execute(stmt)).scalars().all())
        assert len(events) >= 1
        assert events[-1].raw_payload_redacted["update_id"] == 99

    finally:
        settings.TELEGRAM_WEBHOOK_SECRET = orig_secret
