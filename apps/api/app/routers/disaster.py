"""Disaster Intelligence Events Query Router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DisasterEvent
from app.db.session import get_db
from app.schemas.disaster import DisasterEventItem, DisasterQueryResponse

router = APIRouter(prefix="/api/v1/events", tags=["Disaster Intelligence"])


@router.get(
    "/disasters",
    response_model=DisasterQueryResponse,
    summary="Query disaster events",
    description="Retrieve ranked Earth Observation disaster events (floods, fires, damage) with priority scores.",
)
async def get_disaster_events(
    disaster_type: str | None = Query(None, alias="type", description="Filter by event type"),
    min_priority: float = Query(0.0, ge=0.0, le=1.0, description="Minimum observation priority score"),
    limit: int = Query(50, ge=1, le=500, description="Max events to return"),
    db: AsyncSession = Depends(get_db),
) -> DisasterQueryResponse:
    """List detected disaster events ordered by priority descending."""
    stmt = select(DisasterEvent).where(DisasterEvent.priority >= min_priority)
    if disaster_type:
        stmt = stmt.where(DisasterEvent.type == disaster_type)

    stmt = stmt.order_by(DisasterEvent.priority.desc()).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    items = [
        DisasterEventItem(
            id=r.id,
            product_id=r.product_id,
            type=r.type,
            area_km2=r.area_km2,
            mask_uri=r.mask_uri,
            priority=r.priority,
            confidence=r.confidence,
            synthetic=r.synthetic,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return DisasterQueryResponse(
        count=len(items),
        data=items,
    )
