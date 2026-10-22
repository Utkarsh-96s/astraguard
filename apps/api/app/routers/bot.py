"""Phone Alert Bot Router (Telegram Webhook & Polling integration)."""
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Alert, InboundEvent, NotificationChannel, RiskSnapshot
from app.db.session import get_db
from app.services.alert_service import alert_service
from app.services.telegram_service import (
    build_alert_inline_keyboard,
    format_telegram_alert_html,
    telegram_service,
)

router = APIRouter(prefix="/bot", tags=["Phone Alert Bot"])


class BotActionRequest(BaseModel):
    """Payload for executing an operator action via the bot."""
    alert_id: str = Field(..., description="ID of the alert to act on")
    action: Literal["approve", "dismiss", "snooze"] = Field(
        ..., description="Action: approve, dismiss, or snooze"
    )
    operator: str = Field(
        "MobileOperator_Sarah", description="Operator identifier"
    )
    note: str = Field(
        "Executed via Mobile Telegram Bot inline button",
        description="Audit note for action",
    )


class SetupWebhookRequest(BaseModel):
    """Payload for configuring live Telegram webhook."""
    webhook_url: str = Field(..., description="Public HTTPS endpoint URL for webhook")
    secret_token: str | None = Field(None, description="Optional secret token for request verification")


@router.get("/preview/{alert_id}", summary="Get Telegram alert dispatch preview")
async def get_bot_preview(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate real HTML Telegram alert preview and inline keyboard."""
    stmt = (
        select(Alert, RiskSnapshot.asset_id, RiskSnapshot.score, RiskSnapshot.drivers)
        .join(RiskSnapshot, Alert.snapshot_id == RiskSnapshot.id, isouter=True)
        .where(Alert.id == alert_id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")

    alert, asset_id, score, drivers = row
    asset_name = asset_id or "SENTINEL-2A"
    score_val = float(score) if score is not None else 0.0
    drivers_list = []
    if isinstance(drivers, dict):
        drivers_list = drivers.get("drivers", [])

    formatted_html = format_telegram_alert_html(
        alert=alert,
        asset_id=asset_name,
        score=score_val,
        drivers=drivers_list,
        test=alert.synthetic,
    )
    keyboard = build_alert_inline_keyboard(alert.id)

    # Check live configuration
    is_live = bool(settings.TELEGRAM_BOT_TOKEN)

    return {
        "alert_id": alert.id,
        "asset_id": asset_name,
        "level": alert.level,
        "status": alert.status,
        "telegram_payload": {
            "chat_id": "@astraguard_alerts_channel",
            "text": formatted_html,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
        },
        "dispatched_at": datetime.now(UTC).isoformat(),
        "channel": f"Telegram Bot (@{settings.TELEGRAM_BOT_USERNAME})",
        "is_live_configured": is_live,
    }


@router.post("/dispatch/{alert_id}", summary="Dispatch alert to Telegram bot")
async def dispatch_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dispatch alert to connected Telegram channel or return honest status."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")

    if not settings.TELEGRAM_BOT_TOKEN:
        return {
            "status": "simulated",
            "dispatch_status": "simulated",
            "alert_id": alert.id,
            "recipient": "FlightDirector_Mobile",
            "message": "[SIMULATED] Telegram bot token not configured in environment. Recorded in simulation mode.",
        }

    # Find connected Telegram channels
    stmt = select(NotificationChannel).where(
        NotificationChannel.type == "telegram",
        NotificationChannel.status == "CONNECTED",
    )
    channels = list((await db.execute(stmt)).scalars().all())

    if not channels:
        return {
            "status": "pending_channel",
            "dispatch_status": "pending_channel",
            "alert_id": alert.id,
            "recipient": "FlightDirector_Mobile",
            "message": "Telegram bot token configured, but no connected Telegram channels found. Link a chat via /start <code>.",
        }

    from app.services.adapters.telegram import TelegramBotAdapter
    adapter = TelegramBotAdapter()
    results = []
    for ch in channels:
        res = await adapter.send(alert, ch, test=alert.synthetic)
        results.append({
            "channel_id": ch.id,
            "chat_id": ch.encrypted_address,
            "success": res.success,
            "provider_message_id": res.provider_message_id,
            "error": res.error,
        })

    return {
        "status": "dispatched",
        "dispatch_status": "dispatched",
        "alert_id": alert.id,
        "deliveries": results,
    }


@router.post("/action", summary="Handle mobile callback action from bot")
async def bot_action(
    req: BotActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute operator action (Approve / Dismiss / Snooze) originating from bot."""
    try:
        op_action = await alert_service.record_operator_action(
            db=db,
            alert_id=req.alert_id,
            user=req.operator,
            action=req.action,
            note=req.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    alert = await db.get(Alert, req.alert_id)
    return {
        "status": alert.status if alert else "ACKNOWLEDGED",
        "action": req.action.upper(),
        "alert_id": req.alert_id,
        "new_status": alert.status if alert else "UPDATED",
        "operator": req.operator,
        "timestamp": op_action.ts.isoformat(),
    }


@router.post("/webhook", summary="Receive incoming updates from Telegram Webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, Any]:
    """Verify secret token and process incoming Telegram update."""
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Telegram webhook received with invalid secret token.")
            raise HTTPException(status_code=403, detail="Invalid secret token.")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from e

    # Record redacted incoming event in inbound_events table
    event_id = f"EVT-TG-{uuid.uuid4().hex[:10].upper()}"
    redacted = {
        "update_id": body.get("update_id"),
        "has_message": "message" in body,
        "has_callback_query": "callback_query" in body,
    }
    inbound = InboundEvent(
        id=event_id,
        channel_type="telegram",
        raw_payload_redacted=redacted,
        received_at=datetime.now(UTC),
    )
    db.add(inbound)
    await db.commit()

    # Process update
    result = await telegram_service.process_update(body, db)
    return {"ok": True, "result": result}


@router.post("/setup-webhook", summary="Register webhook with Telegram API")
async def setup_webhook(
    req: SetupWebhookRequest,
) -> dict[str, Any]:
    """Helper endpoint to register webhook endpoint with Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_BOT_TOKEN is not configured in environment.",
        )

    res = await telegram_service.set_webhook(
        webhook_url=req.webhook_url,
        secret_token=req.secret_token or settings.TELEGRAM_WEBHOOK_SECRET or None,
    )
    return res
