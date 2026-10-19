"""API Routers package."""
from app.routers.conjunctions import router as conjunctions_router
from app.routers.disaster import router as disaster_router
from app.routers.health import router as health_router
from app.routers.ingest import router as ingest_router
from app.routers.objects import router as objects_router
from app.routers.telemetry import router as telemetry_router

__all__ = [
    "health_router",
    "ingest_router",
    "telemetry_router",
    "objects_router",
    "disaster_router",
    "conjunctions_router",
]
