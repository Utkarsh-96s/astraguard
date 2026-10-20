"""API Routers package."""
from app.routers.alerts import router as alerts_router
from app.routers.assets import router as assets_router
from app.routers.conjunctions import router as conjunctions_router
from app.routers.disaster import router as disaster_router
from app.routers.health import router as health_router
from app.routers.ingest import router as ingest_router
from app.routers.models import router as models_router
from app.routers.objects import router as objects_router
from app.routers.risk import router as risk_router
from app.routers.telemetry import router as telemetry_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "alerts_router",
    "assets_router",
    "conjunctions_router",
    "disaster_router",
    "health_router",
    "ingest_router",
    "models_router",
    "objects_router",
    "risk_router",
    "telemetry_router",
    "websocket_router",
]
