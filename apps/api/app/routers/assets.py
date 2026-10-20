"""Router for satellite assets and health history."""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Asset, TelemetryWindow
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])


@router.get("", summary="List monitored satellite assets")
async def list_assets(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve all monitored primary assets (e.g., SENTINEL-2A)."""
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

    return [
        {
            "id": a.id,
            "name": a.name,
            "norad_id": a.norad_id,
            "type": a.type,
            "tle_epoch": a.tle_epoch.isoformat() if a.tle_epoch else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in assets
    ]


@router.get("/{asset_id}", summary="Get asset details by ID")
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve details for a specific spacecraft asset."""
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

    return {
        "id": asset.id,
        "name": asset.name,
        "norad_id": asset.norad_id,
        "type": asset.type,
        "tle_epoch": asset.tle_epoch.isoformat() if asset.tle_epoch else None,
        "created_at": asset.created_at.isoformat(),
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
