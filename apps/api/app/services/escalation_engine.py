"""Escalation Engine: manages L1/L2/L3 escalation policies, quiet hours, and cancellation."""
import hashlib
import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import (
    Alert,
    EscalationPolicy,
    EscalationState,
    NotificationChannel,
    NotificationOutbox,
    Subscription,
)


def is_in_quiet_hours(quiet_hours: dict[str, Any], current_dt: datetime) -> bool:
    """Check if current time falls within configured quiet hours window."""
    start_str = quiet_hours.get("start")
    end_str = quiet_hours.get("end")
    if not start_str or not end_str:
        return False

    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        st = time(sh, sm)
        et = time(eh, em)
        ct = current_dt.time()

        if st <= et:
            return st <= ct <= et
        else:  # Crosses midnight (e.g. 22:00 to 07:00)
            return ct >= st or ct <= et
    except Exception as e:
        logger.warning(f"Failed to parse quiet hours {quiet_hours}: {e}")
        return False


def generate_idempotency_key(alert_id: str, channel_id: str, level: int, version: int = 1) -> str:
    """Generate unique deterministic idempotency key for outbox delivery."""
    raw = f"{alert_id}:{channel_id}:{level}:v{version}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class EscalationEngine:
    """Manages alert outbox queuing, multi-tier escalation, and quiet hours."""

    async def get_or_create_default_policy(self, db: AsyncSession) -> EscalationPolicy:
        """Fetch active escalation policy or seed default L1->L2->L3 policy."""
        stmt = select(EscalationPolicy).limit(1)
        res = await db.execute(stmt)
        policy = res.scalars().first()
        if not policy:
            policy = EscalationPolicy(
                id="POL-DEFAULT-001",
                name="Mission Safety Default Tiered Policy",
                l1_channels=["telegram", "webpush", "fake"],
                l2_delay_sec=300,  # 5 minutes
                l2_channels=["ntfy", "email"],
                l3_delay_sec=900,  # 15 minutes
                l3_channels=["sms", "webhook"],
                created_at=datetime.now(UTC),
            )
            db.add(policy)
            await db.commit()
            await db.refresh(policy)
        return policy

    async def initialize_alert_escalation(
        self,
        db: AsyncSession,
        alert: Alert,
        test: bool = False,
    ) -> EscalationState:
        """Create initial L1 outbox deliveries and schedule L2 escalation."""
        now = datetime.now(UTC)
        policy = await self.get_or_create_default_policy(db)

        # Check existing escalation state
        stmt = select(EscalationState).where(EscalationState.alert_id == alert.id)
        res = await db.execute(stmt)
        state = res.scalars().first()
        if not state:
            state = EscalationState(
                id=f"ESC-{uuid.uuid4().hex[:12].upper()}",
                alert_id=alert.id,
                policy_id=policy.id,
                current_level=1,
                next_escalation_at=now + timedelta(seconds=policy.l2_delay_sec),
                created_at=now,
            )
            db.add(state)

        # Queue L1 Outbox Items
        await self._queue_outbox_for_level(db, alert, policy.l1_channels, level=1, test=test)
        await db.commit()
        return state

    async def _queue_outbox_for_level(
        self,
        db: AsyncSession,
        alert: Alert,
        channel_types: list[str],
        level: int,
        test: bool = False,
    ) -> list[NotificationOutbox]:
        """Find matching subscribed channels and insert outbox records."""
        now = datetime.now(UTC)

        # Query all enabled channels matching requested types
        stmt = (
            select(NotificationChannel, Subscription)
            .join(Subscription, Subscription.channel_id == NotificationChannel.id)
            .where(
                NotificationChannel.type.in_([t.lower() for t in channel_types]),
                Subscription.enabled == True,  # noqa: E712
            )
        )
        res = await db.execute(stmt)
        rows = list(res.all())

        queued_items: list[NotificationOutbox] = []
        severity_map = {"NOMINAL": 0, "WATCH": 1, "WARNING": 2, "CRITICAL": 3}
        alert_sev = severity_map.get(alert.level, 1)

        for channel, sub in rows:
            # Check min level
            sub_min_sev = severity_map.get(sub.min_level, 1)
            if alert_sev < sub_min_sev:
                continue

            # Check asset filter
            if sub.asset_filter:
                # If alert has asset_id in snapshot, verify
                if hasattr(alert, "asset_id") and alert.asset_id and alert.asset_id != sub.asset_filter:
                    continue

            # Check Quiet Hours
            quiet = sub.quiet_hours or {}
            in_quiet = is_in_quiet_hours(quiet, now)
            if in_quiet:
                allow_override = quiet.get("allow_critical_override", True)
                if not (alert.level == "CRITICAL" and allow_override):
                    logger.info(f"Notification suppressed by quiet hours for channel {channel.id} (alert {alert.id})")
                    continue

            idempotency_key = generate_idempotency_key(alert.id, channel.id, level)

            # Check if outbox item already exists (deduplication)
            check_stmt = select(NotificationOutbox).where(NotificationOutbox.idempotency_key == idempotency_key)
            existing = (await db.execute(check_stmt)).scalars().first()
            if existing:
                continue

            outbox_item = NotificationOutbox(
                id=f"NOB-{uuid.uuid4().hex[:12].upper()}",
                alert_id=alert.id,
                channel_id=channel.id,
                escalation_level=level,
                idempotency_key=idempotency_key,
                status="queued",
                attempts=0,
                max_attempts=3,
                next_attempt_at=now,
                test=test,
                created_at=now,
            )
            db.add(outbox_item)
            queued_items.append(outbox_item)

        return queued_items

    async def advance_escalations(self, db: AsyncSession) -> int:
        """Scan active unacknowledged alerts due for escalation and trigger next tier."""
        now = datetime.now(UTC)
        stmt = (
            select(EscalationState, Alert, EscalationPolicy)
            .join(Alert, EscalationState.alert_id == Alert.id)
            .join(EscalationPolicy, EscalationState.policy_id == EscalationPolicy.id)
            .where(
                EscalationState.halted_at.is_(None),
                EscalationState.next_escalation_at <= now,
                Alert.status == "ACTIVE",
            )
        )
        res = await db.execute(stmt)
        candidates = list(res.all())
        escalated_count = 0

        for state, alert, policy in candidates:
            if state.current_level == 1:
                state.current_level = 2
                state.next_escalation_at = now + timedelta(seconds=policy.l3_delay_sec)
                await self._queue_outbox_for_level(db, alert, policy.l2_channels, level=2, test=alert.synthetic)
                escalated_count += 1
                logger.warning(f"Escalated Alert {alert.id} to Level 2 (Policy: {policy.name})")
            elif state.current_level == 2:
                state.current_level = 3
                state.next_escalation_at = None  # Reached max level
                await self._queue_outbox_for_level(db, alert, policy.l3_channels, level=3, test=alert.synthetic)
                escalated_count += 1
                logger.warning(f"Escalated Alert {alert.id} to Level 3 (Policy: {policy.name})")

        if escalated_count > 0:
            await db.commit()
        return escalated_count

    async def halt_escalation(
        self,
        db: AsyncSession,
        alert_id: str,
        reason: str = "acknowledged",
    ) -> bool:
        """Halt escalation timer when alert is acknowledged or dismissed by ANY channel."""
        now = datetime.now(UTC)
        stmt = select(EscalationState).where(
            EscalationState.alert_id == alert_id,
            EscalationState.halted_at.is_(None),
        )
        res = await db.execute(stmt)
        states = list(res.scalars().all())

        if not states:
            return False

        for state in states:
            state.halted_at = now
            state.halted_reason = reason
            state.next_escalation_at = None

        # Mark all sent outbox records as acked_at
        outbox_stmt = select(NotificationOutbox).where(
            NotificationOutbox.alert_id == alert_id,
            NotificationOutbox.acked_at.is_(None),
        )
        outbox_res = await db.execute(outbox_stmt)
        outbox_items = list(outbox_res.scalars().all())
        for item in outbox_items:
            item.acked_at = now

        await db.commit()
        logger.info(f"Escalation halted for alert {alert_id} (reason: {reason})")
        return True


escalation_engine = EscalationEngine()
