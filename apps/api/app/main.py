"""ASTRA-GUARD FastAPI Application Entrypoint."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.routers.alerts import router as alerts_router
from app.routers.assets import router as assets_router
from app.routers.bot import integrations_router
from app.routers.bot import router as bot_router
from app.routers.conjunctions import router as conjunctions_router
from app.routers.constellation import router as constellation_router
from app.routers.demo import router as demo_router
from app.routers.disaster import router as disaster_router
from app.routers.dl_inference import router as dl_inference_router
from app.routers.features import router as features_router
from app.routers.figures import router as figures_router
from app.routers.health import router as health_router
from app.routers.health_lab import router as health_lab_router
from app.routers.ingest import router as ingest_router
from app.routers.maneuver import router as maneuver_router
from app.routers.metrics import router as metrics_router
from app.routers.models import router as models_router
from app.routers.notifications import router as notifications_router
from app.routers.objects import router as objects_router
from app.routers.observations import router as observations_router
from app.routers.provenance import router as provenance_router
from app.routers.risk import router as risk_router
from app.routers.telemetry import router as telemetry_router
from app.routers.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        from app.db.models import Base
        from app.db.session import async_engine
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified on startup.")
    except Exception as e:
        logger.warning(f"Could not verify database schema on startup: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="ASTRA-GUARD: AI-Powered Integrated Space Mission Safety & Intelligence Platform API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(ingest_router)
    app.include_router(telemetry_router)
    app.include_router(objects_router)
    app.include_router(disaster_router)
    app.include_router(conjunctions_router)
    app.include_router(constellation_router)
    app.include_router(assets_router)
    app.include_router(risk_router)
    app.include_router(alerts_router)
    app.include_router(notifications_router)
    app.include_router(provenance_router)
    app.include_router(models_router)
    app.include_router(figures_router)
    app.include_router(dl_inference_router)
    app.include_router(observations_router)
    app.include_router(websocket_router)
    app.include_router(demo_router)
    app.include_router(health_lab_router, prefix="/api/v1")
    app.include_router(bot_router, prefix="/api/v1")
    app.include_router(integrations_router, prefix="/api/v1")
    app.include_router(maneuver_router, prefix="/api/v1")
    app.include_router(features_router, prefix="/api/v1")
    app.include_router(metrics_router)
    app.include_router(metrics_router, prefix="/api/v1")

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        """Root API summary."""
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "operational",
            "docs": "/docs",
            "health": "/healthz",
        }

    return app


app = create_app()
