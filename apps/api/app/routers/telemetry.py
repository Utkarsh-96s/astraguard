"""Telemetry Query Router."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Telemetry
from app.db.session import get_db
from app.schemas.telemetry import TelemetryItem, TelemetryQueryResponse

router = APIRouter(prefix="/api/v1/assets", tags=["Telemetry"])


@router.get(
    "/{asset_id}/telemetry",
    response_model=TelemetryQueryResponse,
    summary="Query asset telemetry",
    description="Retrieve historical or real-time time-series telemetry points for a spacecraft asset.",
)
async def get_asset_telemetry(
    asset_id: str,
    channel: str | None = Query(None, description="Filter by telemetry channel"),
    from_ts: datetime | None = Query(None, description="Start timestamp filter"),
    to_ts: datetime | None = Query(None, description="End timestamp filter"),
    limit: int = Query(200, ge=1, le=5000, description="Maximum number of points to return"),
    db: AsyncSession = Depends(get_db),
) -> TelemetryQueryResponse:
    """Query telemetry points with optional channel and time-range filtering."""
    stmt = select(Telemetry).where(Telemetry.asset_id == asset_id)

    if channel:
        stmt = stmt.where(Telemetry.channel == channel)
    if from_ts:
        stmt = stmt.where(Telemetry.ts >= from_ts)
    if to_ts:
        stmt = stmt.where(Telemetry.ts <= to_ts)

    stmt = stmt.order_by(Telemetry.ts.asc()).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    items = [
        TelemetryItem(
            asset_id=r.asset_id,
            ts=r.ts,
            channel=r.channel,
            value=r.value,
            quality=r.quality,
            synthetic=r.synthetic,
        )
        for r in rows
    ]

    return TelemetryQueryResponse(
        asset_id=asset_id,
        channel=channel,
        count=len(items),
        data=items,
    )
