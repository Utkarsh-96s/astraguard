"""Service coordinating telemetry, conjunctions, and disaster AI into persisted RiskSnapshots."""
import uuid
from datetime import UTC, datetime
from typing import Any

from ml.risk_engine.engine import MissionRiskEngine
from ml.risk_engine.schemas import RiskSnapshot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.websocket import ws_manager
from app.db.models import Conjunction, DisasterEvent, TelemetryWindow
from app.db.models import RiskSnapshot as DBRiskSnapshot
from app.services.alert_service import alert_service


class RiskService:
    """Evaluates, persists, and broadcasts fused mission risk snapshots."""

    def __init__(self) -> None:
        self.engine = MissionRiskEngine()

    async def evaluate_and_persist(
        self,
        db: AsyncSession,
        asset_id: str = "SENTINEL-2A",
        override_rh: float | None = None,
        override_rd: float | None = None,
        override_re: float | None = None,
        override_pc: float | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> DBRiskSnapshot:
        """Compute latest fused risk, persist to database, evaluate alerts, and return DB model."""
        # 1. Fetch latest health score from TelemetryWindow or fallback
        if override_rh is not None:
            r_h = override_rh
        else:
            w_stmt = (
                select(TelemetryWindow)
                .where(TelemetryWindow.asset_id == asset_id)
                .order_by(TelemetryWindow.created_at.desc())
                .limit(1)
            )
            w_res = await db.execute(w_stmt)
            latest_window = w_res.scalars().first()
            r_h = latest_window.score if latest_window else 0.05

        # 2. Fetch latest conjunction for asset
        if override_rd is not None:
            r_d = override_rd
            pc = override_pc
        else:
            c_stmt = (
                select(Conjunction)
                .where(Conjunction.primary_id == asset_id)
                .order_by(Conjunction.pc.desc())
                .limit(1)
            )
            c_res = await db.execute(c_stmt)
            top_conj = c_res.scalars().first()
            if top_conj:
                pc = top_conj.pc
                r_d = 0.95 if (pc is not None and pc >= 1.0e-4) else min(1.0, max(0.0, float(top_conj.pc * 1000.0)))
            else:
                pc = 1.0e-7
                r_d = 0.02

        # 3. Fetch latest active disaster event
        if override_re is not None:
            r_e = override_re
        else:
            d_stmt = (
                select(DisasterEvent)
                .order_by(DisasterEvent.priority.desc())
                .limit(1)
            )
            d_res = await db.execute(d_stmt)
            top_disaster = d_res.scalars().first()
            r_e = top_disaster.priority if top_disaster else 0.10

        # 4. Evaluate using ML MissionRiskEngine
        snapshot_dto: RiskSnapshot = self.engine.evaluate(
            asset_id=asset_id,
            health_input=r_h,
            debris_input=r_d,
            disaster_input=r_e,
            pc=pc,
            evidence=evidence,
        )

        # 5. Persist to DB
        snapshot_id = f"RSN-{uuid.uuid4().hex[:12].upper()}"
        drivers_dict = [d.model_dump() for d in snapshot_dto.drivers]
        recs_dict = [r.model_dump(mode="json") for r in snapshot_dto.recommendations]

        db_snapshot = DBRiskSnapshot(
            id=snapshot_id,
            asset_id=asset_id,
            ts=datetime.now(UTC),
            r_h=snapshot_dto.r_h,
            r_d=snapshot_dto.r_d,
            r_e=snapshot_dto.r_e,
            score=snapshot_dto.score,
            level=snapshot_dto.level.value,
            drivers={
                "drivers": drivers_dict,
                "rationale": snapshot_dto.rationale,
                "recommendations": recs_dict,
                "defer_eo_payloads": snapshot_dto.defer_eo_payloads,
                "critical_override_applied": snapshot_dto.critical_override_applied,
            },
            synthetic=True,
            created_at=datetime.now(UTC),
        )
        db.add(db_snapshot)
        await db.commit()
        await db.refresh(db_snapshot)

        # 6. Check Alert Lifecycle
        alert = await alert_service.process_risk_snapshot(db, db_snapshot)
        if alert:
            logger.info(f"Triggered alert {alert.id} from risk snapshot {db_snapshot.id}")

        # 7. Broadcast live risk update
        await self.broadcast_snapshot(db_snapshot)

        return db_snapshot

    async def broadcast_snapshot(self, db_snapshot: DBRiskSnapshot) -> None:
        """Broadcast live risk snapshot update over WebSocket."""
        payload: dict[str, Any] = {
            "event": "RISK_UPDATE",
            "snapshot": {
                "id": db_snapshot.id,
                "asset_id": db_snapshot.asset_id,
                "ts": db_snapshot.ts.isoformat(),
                "score": db_snapshot.score,
                "level": db_snapshot.level,
                "r_h": db_snapshot.r_h,
                "r_d": db_snapshot.r_d,
                "r_e": db_snapshot.r_e,
                "drivers": db_snapshot.drivers.get("drivers", []),
                "rationale": db_snapshot.drivers.get("rationale", ""),
                "recommendations": db_snapshot.drivers.get("recommendations", []),
                "defer_eo_payloads": db_snapshot.drivers.get("defer_eo_payloads", False),
            },
        }
        await ws_manager.broadcast_risk(db_snapshot.asset_id, payload)


risk_service = RiskService()
