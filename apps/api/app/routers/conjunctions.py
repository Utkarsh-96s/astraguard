"""Conjunction Screening Events Router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conjunction
from app.db.session import get_db
from app.schemas.conjunction import ConjunctionItem, ConjunctionQueryResponse

router = APIRouter(prefix="/api/v1/assets", tags=["Conjunctions"])


@router.get(
    "/{asset_id}/conjunctions",
    response_model=ConjunctionQueryResponse,
    summary="Query asset conjunction events",
    description="Retrieve close approach conjunction screening events and Pc trends for a spacecraft asset.",
)
async def get_asset_conjunctions(
    asset_id: str,
    min_pc: float = Query(0.0, ge=0.0, le=1.0, description="Minimum collision probability filter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum conjunctions to return"),
    db: AsyncSession = Depends(get_db),
) -> ConjunctionQueryResponse:
    """List close approaches for asset ordered by TCA ascending."""
    stmt = (
        select(Conjunction)
        .where(Conjunction.primary_id == asset_id)
        .where(Conjunction.pc >= min_pc)
        .order_by(Conjunction.tca.asc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    items = [
        ConjunctionItem(
            id=r.id,
            primary_id=r.primary_id,
            secondary_id=r.secondary_id,
            tca=r.tca,
            miss_km=r.miss_km,
            rel_vel_kms=r.rel_vel_kms,
            pc=r.pc,
            pc_method=r.pc_method,
            risk_class=r.risk_class,
            synthetic=r.synthetic,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return ConjunctionQueryResponse(
        primary_id=asset_id,
        count=len(items),
        data=items,
    )
