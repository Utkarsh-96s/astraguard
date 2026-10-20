"""Router for alert provenance and reproducibility verification."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.provenance_service import provenance_service

router = APIRouter(prefix="/api/v1/alerts", tags=["Provenance"])


@router.get("/{alert_id}/provenance", summary="Get alert provenance and cryptographic audit record")
async def get_alert_provenance(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve complete data window hash, config hash, git commit, and model versions for an alert."""
    try:
        return await provenance_service.get_provenance(db=db, alert_id=alert_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{alert_id}/reproduce", summary="Reproduce risk evaluation and verify bit-for-bit equivalence")
async def reproduce_alert_evaluation(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Recompute the mission risk score from recorded inputs and assert numerical identity."""
    try:
        return await provenance_service.reproduce_evaluation(db=db, alert_id=alert_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
