"""Constellation Fleet Mode & Multi-Asset Conjunction Router."""
from typing import Any

from fastapi import APIRouter, Query

from app.services.constellation_service import ConstellationService

router = APIRouter(prefix="/api/v1/assets", tags=["Constellation Fleet & Telemetry"])


@router.get(
    "/constellation-matrix",
    summary="Get Constellation Multi-Asset Fleet Health & Conjunction Matrix",
    description="Retrieve fleet-wide subsystem telemetry and cross-asset conjunction collision screening matrix.",
)
async def get_constellation_matrix() -> dict[str, Any]:
    """Retrieve constellation fleet health and cross-conjunction matrix."""
    service = ConstellationService()
    return service.get_fleet_matrix()


@router.get(
    "/{asset_id}/telemetry/live-stream",
    summary="Stream live spacecraft telemetry packet",
    description="Retrieve real-time synthetic spacecraft telemetry reading with orbital variation physics.",
)
async def get_live_telemetry_stream(
    asset_id: str = "SENTINEL-2A",
    step: int = Query(0, ge=0, description="Step counter for stream propagation"),
) -> dict[str, Any]:
    """Retrieve next streaming telemetry packet for flight controller display."""
    service = ConstellationService()
    return service.generate_live_telemetry_packet(asset_id=asset_id, step=step)
