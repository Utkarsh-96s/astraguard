"""Router for Mission Risk snapshots, evaluations, and history."""
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskSnapshot as DBRiskSnapshot
from app.db.session import get_db
from app.services.risk_service import risk_service

router = APIRouter(prefix="/api/v1/risk", tags=["Mission Risk Engine"])


class RiskEvaluateRequest(BaseModel):
    """Payload to trigger an on-demand mission risk evaluation."""

    asset_id: str = Field("SENTINEL-2A", description="Primary asset identifier")
    r_h: float | None = Field(None, ge=0.0, le=1.0, description="Optional override for spacecraft health risk")
    r_d: float | None = Field(None, ge=0.0, le=1.0, description="Optional override for debris collision risk")
    r_e: float | None = Field(None, ge=0.0, le=1.0, description="Optional override for disaster observation priority")
    pc: float | None = Field(None, ge=0.0, le=1.0, description="Optional collision probability override")
    evidence: dict[str, Any] | None = Field(default=None, description="Operational diagnostic details")


@router.get("/{asset_id}/latest", summary="Get latest fused risk snapshot")
async def get_latest_risk(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve the latest Mission Risk Snapshot for an asset, or evaluate one on demand."""
    stmt = (
        select(DBRiskSnapshot)
        .where(DBRiskSnapshot.asset_id == asset_id)
        .order_by(DBRiskSnapshot.created_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    snapshot = res.scalars().first()

    if not snapshot:
        # Trigger an initial baseline evaluation
        snapshot = await risk_service.evaluate_and_persist(db, asset_id=asset_id)

    return {
        "id": snapshot.id,
        "asset_id": snapshot.asset_id,
        "ts": snapshot.ts.isoformat(),
        "score": snapshot.score,
        "level": snapshot.level,
        "r_h": snapshot.r_h,
        "r_d": snapshot.r_d,
        "r_e": snapshot.r_e,
        "drivers": [
            {
                "driver": d.get("driver", "Unknown"),
                "module": d.get("module", "health"),
                "contribution": d.get("magnitude", d.get("contribution", 0.0)),
                "magnitude": d.get("magnitude", d.get("contribution", 0.0)),
                "share_pct": d.get("percent_of_risk", d.get("share_pct", 0.0)),
                "percent_of_risk": d.get("percent_of_risk", d.get("share_pct", 0.0)),
                "evidence": d.get("evidence", {}),
            }
            for d in snapshot.drivers.get("drivers", [])
        ],
        "rationale": snapshot.drivers.get("rationale", ""),
        "recommendations": snapshot.drivers.get("recommendations", []),
        "defer_eo_payloads": snapshot.drivers.get("defer_eo_payloads", False),
        "critical_override_applied": snapshot.drivers.get("critical_override_applied", False),
        "synthetic": snapshot.synthetic,
        "created_at": snapshot.created_at.isoformat(),
    }


@router.get("/{asset_id}/history", summary="Get historical risk snapshots")
async def get_risk_history(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Retrieve historical Mission Risk Snapshots for timeseries trend analysis."""
    stmt = (
        select(DBRiskSnapshot)
        .where(DBRiskSnapshot.asset_id == asset_id)
        .order_by(DBRiskSnapshot.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    snapshots = list(res.scalars().all())

    if not snapshots:
        initial = await risk_service.evaluate_and_persist(db, asset_id=asset_id)
        snapshots = [initial]

    return [
        {
            "id": s.id,
            "asset_id": s.asset_id,
            "ts": s.ts.isoformat(),
            "score": s.score,
            "level": s.level,
            "r_h": s.r_h,
            "r_d": s.r_d,
            "r_e": s.r_e,
            "defer_eo_payloads": s.drivers.get("defer_eo_payloads", False),
            "created_at": s.created_at.isoformat(),
        }
        for s in snapshots
    ]


@router.post("/evaluate", summary="Evaluate and persist mission risk snapshot")
async def evaluate_risk(
    request: RiskEvaluateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute risk evaluation with optional overrides, persist snapshot, and trigger alerts."""
    snapshot = await risk_service.evaluate_and_persist(
        db=db,
        asset_id=request.asset_id,
        override_rh=request.r_h,
        override_rd=request.r_d,
        override_re=request.r_e,
        override_pc=request.pc,
        evidence=request.evidence,
    )

    return {
        "id": snapshot.id,
        "asset_id": snapshot.asset_id,
        "ts": snapshot.ts.isoformat(),
        "score": snapshot.score,
        "level": snapshot.level,
        "r_h": snapshot.r_h,
        "r_d": snapshot.r_d,
        "r_e": snapshot.r_e,
        "drivers": snapshot.drivers.get("drivers", []),
        "rationale": snapshot.drivers.get("rationale", ""),
        "recommendations": snapshot.drivers.get("recommendations", []),
        "defer_eo_payloads": snapshot.drivers.get("defer_eo_payloads", False),
        "critical_override_applied": snapshot.drivers.get("critical_override_applied", False),
        "synthetic": snapshot.synthetic,
        "created_at": snapshot.created_at.isoformat(),
    }
