"""Space Objects Catalog Query Router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SpaceObject
from app.db.session import get_db
from app.schemas.objects import SpaceObjectQueryResponse, SpaceObjectResponse

router = APIRouter(prefix="/api/v1/objects", tags=["Space Objects"])


@router.get(
    "",
    response_model=SpaceObjectQueryResponse,
    summary="Query space objects catalog",
    description="Retrieve space debris and satellite catalog entries with orbital element sets (TLE).",
)
async def get_space_objects(
    object_type: str | None = Query(None, alias="type", description="Filter by type (payload, debris, r/b)"),
    limit: int = Query(100, ge=1, le=1000, description="Max objects to return"),
    db: AsyncSession = Depends(get_db),
) -> SpaceObjectQueryResponse:
    """List space objects in catalog."""
    stmt = select(SpaceObject)
    if object_type:
        stmt = stmt.where(SpaceObject.type == object_type)

    stmt = stmt.order_by(SpaceObject.norad_id.asc()).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    items = [
        SpaceObjectResponse(
            norad_id=r.norad_id,
            name=r.name,
            type=r.type,
            tle_line1=r.tle_line1,
            tle_line2=r.tle_line2,
            epoch=r.epoch,
            updated_at=r.updated_at,
        )
        for r in rows
    ]

    return SpaceObjectQueryResponse(
        count=len(items),
        data=items,
    )
