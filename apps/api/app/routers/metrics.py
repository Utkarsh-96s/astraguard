"""Router for pipeline observability and telemetry metrics."""
from typing import Any

from fastapi import APIRouter

from app.services.observability_service import observability_service

router = APIRouter(prefix="/metrics", tags=["Observability"])


@router.get("/pipeline", summary="Get pipeline telemetry and performance observability metrics")
async def get_pipeline_metrics() -> dict[str, Any]:
    """Retrieve live latency percentiles (p50, p90, p95, p99), throughput, and queue depth."""
    return observability_service.get_pipeline_metrics()
