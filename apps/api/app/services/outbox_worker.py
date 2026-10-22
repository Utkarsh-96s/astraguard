"""Outbox background worker claiming items, dispatching to adapters, handling backoff & DLQ."""
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import Alert, NotificationChannel, NotificationOutbox
from app.services.adapters.registry import adapter_registry
from app.services.tokens import generate_action_token


def mask_contact_info(info: str) -> str:
    """Mask email, phone, or token for secure logging."""
    if not info:
        return ""
    if "@" in info:
        user, domain = info.split("@", 1)
        return f"{user[:1]}***@{domain}"
    if info.startswith("+"):
        return f"{info[:2]}***{info[-4:]}"
    if len(info) > 10:
        return f"{info[:4]}***{info[-4:]}"
    return "***"


class OutboxWorker:
    """Background outbox processor delivering notifications with exponential backoff & DLQ."""

    def __init__(self, base_delay_sec: float = 2.0, max_jitter_sec: float = 1.0) -> None:
        self.base_delay_sec = base_delay_sec
        self.max_jitter_sec = max_jitter_sec
        self._last_send_by_channel: dict[str, datetime] = {}
        self._running: bool = False

    async def claim_and_process_batch(
        self,
        db: AsyncSession,
        batch_size: int = 10,
    ) -> int:
        """Claim a batch of queued/failed items due for delivery and process them."""
        now = datetime.now(UTC)

        # Select items due for delivery
        # SQLite doesn't support SKIP LOCKED, so we handle both PostgreSQL and SQLite gracefully
        stmt = (
            select(NotificationOutbox)
            .where(
                NotificationOutbox.status.in_(["queued", "failed"]),
                NotificationOutbox.next_attempt_at <= now,
                NotificationOutbox.attempts < NotificationOutbox.max_attempts,
            )
            .order_by(NotificationOutbox.created_at.asc())
            .limit(batch_size)
        )

        try:
            # Try PostgreSQL SKIP LOCKED if supported
            stmt = stmt.with_for_update(skip_locked=True)
            res = await db.execute(stmt)
        except Exception:
            # Fallback for SQLite in tests
            stmt_plain = (
                select(NotificationOutbox)
                .where(
                    NotificationOutbox.status.in_(["queued", "failed"]),
                    NotificationOutbox.next_attempt_at <= now,
                    NotificationOutbox.attempts < NotificationOutbox.max_attempts,
                )
                .order_by(NotificationOutbox.created_at.asc())
                .limit(batch_size)
            )
            res = await db.execute(stmt_plain)

        items = list(res.scalars().all())
        if not items:
            return 0

        # Mark claimed items as sending
        for item in items:
            item.status = "sending"
        await db.commit()

        processed_count = 0
        for item in items:
            await self._process_single_item(db, item)
            processed_count += 1

        await db.commit()
        return processed_count

    async def _process_single_item(
        self,
        db: AsyncSession,
        item: NotificationOutbox,
    ) -> None:
        """Deliver one outbox item through its channel's registered provider adapter."""
        now = datetime.now(UTC)

        alert = await db.get(Alert, item.alert_id)
        channel = await db.get(NotificationChannel, item.channel_id)

        if not alert or not channel:
            item.status = "dead"
            item.last_error = "Associated alert or notification channel was not found in DB."
            return

        # Check per-chat rate limit (at least 1.0 second between messages to the same channel)
        last_sent = self._last_send_by_channel.get(channel.id)
        if last_sent and (now - last_sent).total_seconds() < 1.0:
            delay = 1.0 - (now - last_sent).total_seconds()
            item.status = "queued"
            item.next_attempt_at = now + timedelta(seconds=delay + 0.1)
            return

        adapter = adapter_registry.get(channel.type)

        # Generate HMAC-signed single-use action tokens for one-click approval / snooze
        action_tokens: dict[str, str] = {}
        try:
            _, approve_url = await generate_action_token(db, alert.id, channel.id, "approve", expiry_seconds=86400)
            _, dismiss_url = await generate_action_token(db, alert.id, channel.id, "dismiss", expiry_seconds=86400)
            _, snooze_url = await generate_action_token(db, alert.id, channel.id, "snooze", expiry_seconds=86400)
            action_tokens = {
                "approve_url": approve_url,
                "dismiss_url": dismiss_url,
                "snooze_url": snooze_url,
            }
        except Exception as e:
            logger.warning(f"Could not generate signed action tokens for alert {alert.id}: {e}")

        # Dispatch via Provider Adapter
        masked_addr = mask_contact_info(channel.encrypted_address)
        logger.info(
            f"Dispatching notification: outbox_id={item.id}, channel_type={channel.type}, "
            f"target={masked_addr}, attempt={item.attempts + 1}/{item.max_attempts}"
        )

        try:
            res = await adapter.send(
                alert=alert,
                channel=channel,
                test=item.test or alert.synthetic,
                action_tokens=action_tokens,
            )
        except Exception as e:
            logger.error(f"Provider adapter raised unhandled exception: {e}")
            res = type("Result", (), {
                "success": False,
                "error": str(e),
                "retryable": True,
                "provider_message_id": None,
                "delivered_at": None,
            })()

        item.attempts += 1
        self._last_send_by_channel[channel.id] = now

        if res.success:
            item.status = "delivered"
            item.sent_at = now
            item.delivered_at = getattr(res, "delivered_at", now) or now
            item.provider_message_id = getattr(res, "provider_message_id", None)
            item.last_error = None

            # Mark channel status as CONNECTED upon successful verified transmission
            if channel.status != "CONNECTED":
                channel.status = "CONNECTED"
                channel.verified_at = now
                channel.last_error = None

            logger.info(f"Notification delivered successfully: outbox_id={item.id}, msg_id={item.provider_message_id}")
        else:
            item.last_error = getattr(res, "error", "Delivery failed without error details")
            is_retryable = getattr(res, "retryable", True)

            if is_retryable and item.attempts < item.max_attempts:
                # Exponential backoff with jitter: 2^attempt * base_delay + uniform(0, jitter)
                backoff_sec = (2 ** item.attempts) * self.base_delay_sec + random.uniform(0, self.max_jitter_sec)
                item.status = "failed"
                item.next_attempt_at = now + timedelta(seconds=backoff_sec)
                logger.warning(
                    f"Notification failed (retryable): outbox_id={item.id}, "
                    f"next_attempt_in={backoff_sec:.1f}s, error='{item.last_error}'"
                )
            else:
                # Dead letter queue
                item.status = "dead"
                item.next_attempt_at = None
                logger.error(
                    f"Notification moved to DEAD LETTER queue: outbox_id={item.id}, "
                    f"attempts={item.attempts}, error='{item.last_error}'"
                )

    async def edit_message_after_ack(
        self,
        db: AsyncSession,
        alert_id: str,
        operator: str,
        action: str,
    ) -> int:
        """Update delivered messages across external channels to show acknowledgment."""
        stmt = (
            select(NotificationOutbox, NotificationChannel)
            .join(NotificationChannel, NotificationOutbox.channel_id == NotificationChannel.id)
            .where(
                NotificationOutbox.alert_id == alert_id,
                NotificationOutbox.status == "delivered",
                NotificationOutbox.provider_message_id.is_not(None),
            )
        )
        res = await db.execute(stmt)
        rows = list(res.all())
        now = datetime.now(UTC)
        edited_count = 0

        alert = await db.get(Alert, alert_id)
        if not alert:
            return 0

        for outbox_item, channel in rows:
            adapter = adapter_registry.get(channel.type)
            try:
                ok = await adapter.edit_after_ack(
                    alert=alert,
                    channel=channel,
                    provider_message_id=outbox_item.provider_message_id or "",
                    operator=operator,
                    action=action,
                    timestamp=now,
                )
                if ok:
                    edited_count += 1
            except Exception as e:
                logger.warning(f"Failed to edit message in channel {channel.id}: {e}")

        return edited_count


outbox_worker = OutboxWorker()
