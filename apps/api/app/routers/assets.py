"""Router for satellite assets and health history."""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, Asset, RiskSnapshot, TelemetryWindow
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])


@router.get("", summary="List monitored satellite assets")
async def list_assets(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve all monitored primary assets with live risk summary."""
    stmt = select(Asset).offset(skip).limit(limit)
    res = await db.execute(stmt)
    assets = list(res.scalars().all())

    # If database not yet seeded, provide Sentinel-2A default per PRD §4
    if not assets:
        default_asset = Asset(
            id="SENTINEL-2A",
            name="Sentinel-2A Earth Observation Satellite",
            norad_id=40697,
            type="satellite",
            tle_epoch=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        db.add(default_asset)
        await db.commit()
        await db.refresh(default_asset)
        assets = [default_asset]

    enriched_assets = []
    for a in assets:
        # Latest snapshot
        snap_stmt = select(RiskSnapshot).where(RiskSnapshot.asset_id == a.id).order_by(RiskSnapshot.ts.desc()).limit(1)
        snap_res = await db.execute(snap_stmt)
        latest_snap = snap_res.scalar_one_or_none()

        # Count active alerts
        alert_stmt = (
            select(func.count(Alert.id))
            .join(RiskSnapshot, Alert.snapshot_id == RiskSnapshot.id)
            .where(RiskSnapshot.asset_id == a.id, Alert.status == "ACTIVE")
        )
        alert_res = await db.execute(alert_stmt)
        active_alerts_count = alert_res.scalar() or 0

        enriched_assets.append({
            "id": a.id,
            "name": a.name,
            "norad_id": a.norad_id,
            "type": a.type,
            "tle_epoch": a.tle_epoch.isoformat() if a.tle_epoch else None,
            "created_at": a.created_at.isoformat(),
            "latest_score": round(latest_snap.score, 2) if latest_snap else 10.0,
            "latest_level": latest_snap.level if latest_snap else "NOMINAL",
            "active_alerts_count": active_alerts_count,
            "last_updated": latest_snap.ts.isoformat() if latest_snap else a.created_at.isoformat(),
        })

    return enriched_assets


@router.get("/{asset_id}", summary="Get asset details by ID")
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve details for a specific spacecraft asset with live risk summary."""
    asset = await db.get(Asset, asset_id)
    if not asset:
        # Check fallback
        if asset_id.upper() == "SENTINEL-2A":
            asset = Asset(
                id="SENTINEL-2A",
                name="Sentinel-2A Earth Observation Satellite",
                norad_id=40697,
                type="satellite",
                tle_epoch=datetime.now(UTC),
                created_at=datetime.now(UTC),
            )
            db.add(asset)
            await db.commit()
            await db.refresh(asset)
        else:
            raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found.")

    snap_stmt = select(RiskSnapshot).where(RiskSnapshot.asset_id == asset.id).order_by(RiskSnapshot.ts.desc()).limit(1)
    snap_res = await db.execute(snap_stmt)
    latest_snap = snap_res.scalar_one_or_none()

    alert_stmt = (
        select(func.count(Alert.id))
        .join(RiskSnapshot, Alert.snapshot_id == RiskSnapshot.id)
        .where(RiskSnapshot.asset_id == asset.id, Alert.status == "ACTIVE")
    )
    alert_res = await db.execute(alert_stmt)
    active_alerts_count = alert_res.scalar() or 0

    return {
        "id": asset.id,
        "name": asset.name,
        "norad_id": asset.norad_id,
        "type": asset.type,
        "tle_epoch": asset.tle_epoch.isoformat() if asset.tle_epoch else None,
        "created_at": asset.created_at.isoformat(),
        "latest_score": round(latest_snap.score, 2) if latest_snap else 10.0,
        "latest_level": latest_snap.level if latest_snap else "NOMINAL",
        "active_alerts_count": active_alerts_count,
        "last_updated": latest_snap.ts.isoformat() if latest_snap else asset.created_at.isoformat(),
    }


@router.get("/{asset_id}/health", summary="Get asset health history")
async def get_asset_health(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    from_ts: datetime | None = Query(None, alias="from"),
    to_ts: datetime | None = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Retrieve evaluated telemetry health windows for an asset."""
    stmt = (
        select(TelemetryWindow)
        .where(TelemetryWindow.asset_id == asset_id)
        .order_by(TelemetryWindow.created_at.desc())
        .limit(limit)
    )
    if from_ts:
        stmt = stmt.where(TelemetryWindow.t_start >= from_ts)
    if to_ts:
        stmt = stmt.where(TelemetryWindow.t_end <= to_ts)

    res = await db.execute(stmt)
    windows = list(res.scalars().all())
    return [
        {
            "id": w.id,
            "asset_id": w.asset_id,
            "t_start": w.t_start.isoformat(),
            "t_end": w.t_end.isoformat(),
            "score": w.score,
            "model_ver": w.model_ver,
            "created_at": w.created_at.isoformat(),
        }
        for w in windows
    ]
