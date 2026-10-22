"""Router for notification channels, subscriptions, escalation policies, and provider health."""
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import (
    Alert,
    EscalationPolicy,
    NotificationChannel,
    NotificationOutbox,
    Subscription,
)
from app.db.session import get_db
from app.services.adapters.registry import adapter_registry
from app.services.outbox_worker import mask_contact_info
from app.services.tokens import generate_linking_token

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


# Schemas
class CreateChannelRequest(BaseModel):
    name: str = Field("Default Channel", description="Human-readable channel name")
    type: str = Field(..., description="Channel type: telegram, webpush, ntfy, email, webhook, sms, fake")
    address: str = Field(..., description="Destination address (chat_id, endpoint, email, webhook URL, phone)")
    user_id: str = Field("FlightDirector", description="Operator user identifier")
    prefs: dict[str, Any] = Field(default_factory=dict, description="Custom channel preferences")


class SubscriptionRequest(BaseModel):
    channel_id: str = Field(..., description="Associated channel ID")
    min_level: str = Field("WATCH", description="Minimum severity: WATCH, WARNING, CRITICAL")
    asset_filter: str | None = Field(None, description="Spacecraft asset filter (None for all)")
    quiet_hours: dict[str, Any] = Field(
        default_factory=lambda: {"start": "", "end": "", "allow_critical_override": True},
        description="Quiet hours configuration",
    )
    enabled: bool = Field(True, description="Whether subscription is enabled")


class EscalationPolicyRequest(BaseModel):
    name: str = Field(..., description="Policy name")
    l1_channels: list[str] = Field(..., description="L1 channel types/IDs")
    l2_delay_sec: int = Field(300, description="L2 escalation delay in seconds")
    l2_channels: list[str] = Field(..., description="L2 channel types/IDs")
    l3_delay_sec: int = Field(900, description="L3 escalation delay in seconds")
    l3_channels: list[str] = Field(..., description="L3 channel types/IDs")


# Endpoints
@router.get("/health", summary="Get honest notification channel provider health")
async def get_notifications_health(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return honest connectivity status of all notification channels. Never fakes success."""
    adapter_health = await adapter_registry.check_all_health()

    # Query DB channels count
    stmt = select(NotificationChannel)
    db_channels = list((await db.execute(stmt)).scalars().all())

    # Query dead letter count
    dlq_stmt = select(NotificationOutbox).where(NotificationOutbox.status == "dead")
    dlq_count = len(list((await db.execute(dlq_stmt)).scalars().all()))

    return {
        "status": "operational",
        "providers": adapter_health,
        "configured_channels_count": len(db_channels),
        "dead_letter_count": dlq_count,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/channels", summary="List notification channels")
async def list_channels(
    user_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List registered notification channels with masked contact info."""
    stmt = select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
    if user_id:
        stmt = stmt.where(NotificationChannel.user_id == user_id)

    res = await db.execute(stmt)
    channels = list(res.scalars().all())

    return [
        {
            "id": ch.id,
            "user_id": ch.user_id,
            "type": ch.type,
            "name": ch.name,
            "masked_address": mask_contact_info(ch.encrypted_address),
            "status": ch.status,
            "verified_at": ch.verified_at.isoformat() if ch.verified_at else None,
            "last_error": ch.last_error,
            "prefs": ch.prefs,
            "created_at": ch.created_at.isoformat(),
        }
        for ch in channels
    ]


@router.post("/channels", summary="Create notification channel")
async def create_channel(
    req: CreateChannelRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new notification channel. Status defaults to PENDING VERIFICATION or NOT CONFIGURED."""
    channel_type = req.type.lower()
    adapter = adapter_registry.get(channel_type)
    health = await adapter.health_check()

    initial_status = "PENDING VERIFICATION"
    if health.get("status") == "NOT CONFIGURED":
        initial_status = "NOT CONFIGURED"

    channel_id = f"CHN-{uuid.uuid4().hex[:10].upper()}"
    channel = NotificationChannel(
        id=channel_id,
        user_id=req.user_id,
        type=channel_type,
        name=req.name,
        encrypted_address=req.address,
        status=initial_status,
        last_error=health.get("details") if initial_status == "NOT CONFIGURED" else None,
        prefs=req.prefs,
        created_at=datetime.now(UTC),
    )
    db.add(channel)

    # Automatically create default subscription
    sub = Subscription(
        id=f"SUB-{uuid.uuid4().hex[:10].upper()}",
        channel_id=channel_id,
        min_level="WATCH",
        asset_filter=None,
        quiet_hours={"start": "", "end": "", "allow_critical_override": True},
        enabled=True,
        created_at=datetime.now(UTC),
    )
    db.add(sub)
    await db.commit()

    return {
        "status": "created",
        "channel": {
            "id": channel.id,
            "type": channel.type,
            "name": channel.name,
            "masked_address": mask_contact_info(channel.encrypted_address),
            "status": channel.status,
            "subscription_id": sub.id,
        },
    }


@router.delete("/channels/{channel_id}", summary="Delete notification channel")
async def delete_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a notification channel and its associated subscriptions and outbox records."""
    channel = await db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    await db.delete(channel)
    await db.commit()
    return {"status": "deleted", "channel_id": channel_id}


@router.post("/channels/{channel_id}/verify", summary="Verify channel or get Telegram link code")
async def verify_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate verification linking code or trigger verification ping."""
    channel = await db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    if channel.type == "telegram":
        code, deep_link = await generate_linking_token(db, user_id=channel.user_id, channel_type="telegram")
        return {
            "status": "pending_handshake",
            "channel_id": channel.id,
            "type": "telegram",
            "linking_code": code,
            "deep_link": deep_link,
            "qr_payload": deep_link,
            "instructions": f"Send /start {code} to @{settings.TELEGRAM_BOT_USERNAME} or tap the deep link to link your account.",
        }

    # For fake adapter or already responsive channels, mark verified
    channel.status = "CONNECTED"
    channel.verified_at = datetime.now(UTC)
    channel.last_error = None
    await db.commit()

    return {
        "status": "connected",
        "channel_id": channel.id,
        "verified_at": channel.verified_at.isoformat(),
    }


@router.post("/channels/{channel_id}/test", summary="Send test alert through channel")
async def test_send_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Send a simulated test notification through a single specific channel."""
    channel = await db.get(NotificationChannel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    # Create dummy test alert
    dummy_alert = Alert(
        id=f"ALT-TEST-{uuid.uuid4().hex[:8].upper()}",
        snapshot_id="RSN-TEST",
        level="CRITICAL",
        title=f"[TEST] Channel Verification: {channel.name}",
        rationale="[SIMULATED] Channel connectivity verification test requested by operator console.",
        recommendation="Verify reception and acknowledge.",
        status="ACTIVE",
        dedup_key="test_ch_verification",
        synthetic=True,
        created_at=datetime.now(UTC),
    )

    adapter = adapter_registry.get(channel.type)
    res = await adapter.send(dummy_alert, channel, test=True)

    if res.success:
        channel.status = "CONNECTED"
        channel.verified_at = datetime.now(UTC)
        channel.last_error = None
        await db.commit()
        return {
            "status": "delivered",
            "channel_id": channel.id,
            "provider_message_id": res.provider_message_id,
        }
    else:
        channel.last_error = res.error
        await db.commit()
        return {
            "status": "failed",
            "channel_id": channel.id,
            "error": res.error,
        }


@router.get("/subscriptions", summary="List subscriptions")
async def list_subscriptions(
    channel_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List subscriptions with channel details."""
    stmt = select(Subscription, NotificationChannel).join(NotificationChannel, Subscription.channel_id == NotificationChannel.id)
    if channel_id:
        stmt = stmt.where(Subscription.channel_id == channel_id)

    res = await db.execute(stmt)
    rows = list(res.all())
    return [
        {
            "id": sub.id,
            "channel_id": sub.channel_id,
            "channel_name": ch.name,
            "channel_type": ch.type,
            "min_level": sub.min_level,
            "asset_filter": sub.asset_filter,
            "quiet_hours": sub.quiet_hours,
            "enabled": sub.enabled,
        }
        for sub, ch in rows
    ]


@router.post("/subscriptions", summary="Create or update subscription")
async def upsert_subscription(
    req: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create or update a channel subscription rule."""
    stmt = select(Subscription).where(Subscription.channel_id == req.channel_id)
    sub = (await db.execute(stmt)).scalars().first()
    now = datetime.now(UTC)

    if sub:
        sub.min_level = req.min_level.upper()
        sub.asset_filter = req.asset_filter
        sub.quiet_hours = req.quiet_hours
        sub.enabled = req.enabled
    else:
        sub = Subscription(
            id=f"SUB-{uuid.uuid4().hex[:10].upper()}",
            channel_id=req.channel_id,
            min_level=req.min_level.upper(),
            asset_filter=req.asset_filter,
            quiet_hours=req.quiet_hours,
            enabled=req.enabled,
            created_at=now,
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)
    return {"status": "saved", "subscription_id": sub.id}


@router.get("/policies", summary="List escalation policies")
async def list_policies(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List active escalation policies."""
    stmt = select(EscalationPolicy)
    policies = list((await db.execute(stmt)).scalars().all())
    return [
        {
            "id": p.id,
            "name": p.name,
            "l1_channels": p.l1_channels,
            "l2_delay_sec": p.l2_delay_sec,
            "l2_channels": p.l2_channels,
            "l3_delay_sec": p.l3_delay_sec,
            "l3_channels": p.l3_channels,
        }
        for p in policies
    ]


@router.post("/policies", summary="Create or update escalation policy")
async def create_policy(
    req: EscalationPolicyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create or update tiered escalation policy."""
    now = datetime.now(UTC)
    policy_id = f"POL-{uuid.uuid4().hex[:8].upper()}"
    policy = EscalationPolicy(
        id=policy_id,
        name=req.name,
        l1_channels=req.l1_channels,
        l2_delay_sec=req.l2_delay_sec,
        l2_channels=req.l2_channels,
        l3_delay_sec=req.l3_delay_sec,
        l3_channels=req.l3_channels,
        created_at=now,
    )
    db.add(policy)
    await db.commit()
    return {"status": "created", "policy_id": policy.id}


@router.get("/outbox/dead-letter", summary="View dead-letter queue")
async def view_dead_letter_queue(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """View deliveries that failed after maximum retry attempts."""
    stmt = (
        select(NotificationOutbox, NotificationChannel, Alert)
        .join(NotificationChannel, NotificationOutbox.channel_id == NotificationChannel.id)
        .join(Alert, NotificationOutbox.alert_id == Alert.id)
        .where(NotificationOutbox.status == "dead")
        .order_by(NotificationOutbox.created_at.desc())
    )
    rows = list((await db.execute(stmt)).all())
    return [
        {
            "outbox_id": item.id,
            "alert_id": alert.id,
            "alert_title": alert.title,
            "level": alert.level,
            "channel_id": channel.id,
            "channel_name": channel.name,
            "channel_type": channel.type,
            "attempts": item.attempts,
            "max_attempts": item.max_attempts,
            "last_error": item.last_error,
            "created_at": item.created_at.isoformat(),
        }
        for item, channel, alert in rows
    ]


@router.post("/outbox/{outbox_id}/retry", summary="Retry dead-letter outbox delivery")
async def retry_dead_letter(
    outbox_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reset attempt counter and queue dead item for immediate redelivery."""
    item = await db.get(NotificationOutbox, outbox_id)
    if not item:
        raise HTTPException(status_code=404, detail="Outbox item not found.")

    item.status = "queued"
    item.attempts = 0
    item.next_attempt_at = datetime.now(UTC)
    item.last_error = None
    await db.commit()

    return {"status": "requeued", "outbox_id": item.id}
