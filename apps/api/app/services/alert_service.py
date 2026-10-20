"""Alert lifecycle management: deduplication, cooldown, escalation, and operator auditing."""
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from ml.risk_engine.fusion import load_risk_config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.websocket import ws_manager
from app.db.models import Alert, OperatorAction, RiskSnapshot

LEVEL_SEVERITY: dict[str, int] = {
    "NOMINAL": 0,
    "WATCH": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


class AlertService:
    """Manages alert generation, deduplication, cooldown, and operator actions."""

    def __init__(self) -> None:
        cfg = load_risk_config()
        self.cooldown_seconds = int(cfg.get("cooldown_seconds", 300))

    def compute_dedup_key(self, asset_id: str, driver: str, level: str) -> str:
        """Generate deterministic deduplication key: hash(asset:driver:level)."""
        raw = f"{asset_id}:{driver}:{level}".lower()
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    async def process_risk_snapshot(
        self,
        db: AsyncSession,
        snapshot: RiskSnapshot,
    ) -> Alert | None:
        """Evaluate a newly persisted RiskSnapshot and generate an Alert if warranted."""
        # Alerts are generated for WATCH, WARNING, or CRITICAL levels
        if snapshot.level == "NOMINAL":
            return None

        primary_driver = "general"
        if snapshot.drivers and isinstance(snapshot.drivers, dict):
            drivers_list = snapshot.drivers.get("drivers", [])
            if drivers_list and isinstance(drivers_list, list):
                first = drivers_list[0]
                if isinstance(first, dict):
                    primary_driver = first.get("driver", "general")
                elif hasattr(first, "driver"):
                    primary_driver = first.driver
        elif snapshot.drivers and isinstance(snapshot.drivers, list) and len(snapshot.drivers) > 0:
            first = snapshot.drivers[0]
            if isinstance(first, dict):
                primary_driver = first.get("driver", "general")
            elif hasattr(first, "driver"):
                primary_driver = first.driver

        dedup_key = self.compute_dedup_key(snapshot.asset_id, primary_driver, snapshot.level)
        cutoff_time = datetime.now(UTC) - timedelta(seconds=self.cooldown_seconds)

        # Check existing alerts for this asset
        stmt = (
            select(Alert)
            .join(RiskSnapshot, Alert.snapshot_id == RiskSnapshot.id)
            .where(
                RiskSnapshot.asset_id == snapshot.asset_id,
                Alert.created_at >= cutoff_time,
                Alert.status.in_(["ACTIVE", "SNOOZED"]),
            )
            .order_by(Alert.created_at.desc())
        )
        res = await db.execute(stmt)
        recent_alerts = list(res.scalars().all())

        if recent_alerts:
            last_alert = recent_alerts[0]
            last_sev = LEVEL_SEVERITY.get(last_alert.level, 0)
            curr_sev = LEVEL_SEVERITY.get(snapshot.level, 0)

            # Re-alert only if level escalated to higher severity
            if curr_sev <= last_sev:
                logger.info(
                    f"Alert suppressed by cooldown: asset={snapshot.asset_id}, "
                    f"level={snapshot.level}, driver={primary_driver} (cooldown: {self.cooldown_seconds}s)"
                )
                return None

            logger.warning(
                f"Alert escalated during cooldown: asset={snapshot.asset_id}, "
                f"from {last_alert.level} -> {snapshot.level}"
            )

        recommendation_text = "Review subsystem telemetry and flight status."
        if snapshot.drivers and isinstance(snapshot.drivers, dict):
            recs = snapshot.drivers.get("recommendations", [])
            if recs and isinstance(recs, list):
                first_rec = recs[0]
                if isinstance(first_rec, dict):
                    recommendation_text = first_rec.get("action", recommendation_text)

        alert_id = f"ALT-{uuid.uuid4().hex[:12].upper()}"
        alert_title = f"{snapshot.level} Risk: {snapshot.asset_id} ({primary_driver})"

        alert = Alert(
            id=alert_id,
            snapshot_id=snapshot.id,
            level=snapshot.level,
            title=alert_title,
            rationale=f"Mission Risk Score elevated to {snapshot.score:.1f} ({snapshot.level}). Primary driver: {primary_driver}.",
            recommendation=recommendation_text,
            status="ACTIVE",
            dedup_key=dedup_key,
            synthetic=snapshot.synthetic,
            created_at=datetime.now(UTC),
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info(f"Generated new Alert: id={alert.id}, level={alert.level}, asset={snapshot.asset_id}")
        await self.broadcast_alert_event(alert, "CREATED")
        return alert

    async def broadcast_alert_event(self, alert: Alert, action_event: str = "CREATED") -> None:
        """Broadcast alert lifecycle event over WebSocket."""
        payload: dict[str, Any] = {
            "event": action_event,
            "alert": {
                "id": alert.id,
                "snapshot_id": alert.snapshot_id,
                "level": alert.level,
                "title": alert.title,
                "rationale": alert.rationale,
                "recommendation": alert.recommendation,
                "status": alert.status,
                "created_at": alert.created_at.isoformat(),
            },
        }
        await ws_manager.broadcast_alert(payload)

    async def record_operator_action(
        self,
        db: AsyncSession,
        alert_id: str,
        user: str,
        action: str,
        note: str | None = None,
    ) -> OperatorAction:
        """Record an operator action (approve, dismiss, snooze) and update alert status."""
        alert = await db.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert with id '{alert_id}' not found.")

        valid_actions = {"approve", "dismiss", "snooze"}
        clean_action = action.lower()
        if clean_action not in valid_actions:
            raise ValueError(f"Invalid operator action '{action}'. Must be one of {valid_actions}.")

        # State transition
        if clean_action == "approve":
            alert.status = "ACKNOWLEDGED"
        elif clean_action == "dismiss":
            alert.status = "DISMISSED"
        elif clean_action == "snooze":
            alert.status = "SNOOZED"

        action_id = f"ACT-{uuid.uuid4().hex[:12].upper()}"
        op_action = OperatorAction(
            id=action_id,
            alert_id=alert_id,
            user=user,
            action=clean_action,
            note=note,
            ts=datetime.now(UTC),
        )
        db.add(op_action)
        await db.commit()
        await db.refresh(op_action)
        await db.refresh(alert)

        logger.info(f"Operator action recorded: id={action_id}, alert={alert_id}, user={user}, action={clean_action}")
        await self.broadcast_alert_event(alert, f"OPERATOR_{clean_action.upper()}")
        return op_action


alert_service = AlertService()
