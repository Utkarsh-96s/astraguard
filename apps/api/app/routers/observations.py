"""Observation Tasking Optimizer Router.

Implements F12: Observation Tasking Optimizer.
Provides endpoints for scheduling ground-based radar and optical observation passes,
estimating covariance shrinkage to avoid false-alarm collision avoidance maneuvers.
"""
from typing import Any

from fastapi import APIRouter, Query

from app.services.observation_service import observation_service

router = APIRouter(prefix="/api/v1/debris/observations", tags=["Observation Tasking"])


@router.get("", summary="Get optimized sensor tasking windows")
async def get_observation_tasking_plan(
    conjunction_id: str = Query("CONJ-29834", description="Conjunction event ID"),
    secondary_name: str = Query("FENGYUN-1C-DEB-29834", description="Secondary object name/ID"),
    hours_to_tca: float = Query(14.2, ge=0.5, le=168.0, description="Hours remaining until TCA"),
    sigma_y_m: float = Query(250.0, ge=1.0, le=5000.0, description="Initial in-track uncertainty sigma (m)"),
    sigma_x_m: float = Query(50.0, ge=1.0, le=1000.0, description="Initial normal uncertainty sigma (m)"),
) -> dict[str, Any]:
    """Calculate optimal sensor pass windows across TIRA, Teide, AMOS, and Learmonth."""
    return observation_service.optimize_tasking(
        conjunction_id=conjunction_id,
        secondary_name=secondary_name,
        hours_to_tca=hours_to_tca,
        initial_sigma_y_m=sigma_y_m,
        initial_sigma_x_m=sigma_x_m,
    )
