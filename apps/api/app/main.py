"""ASTRA-GUARD FastAPI Application Entrypoint."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.routers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION} [{settings.ENVIRONMENT}]")
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

    # Health check router mounted at root and under /api/v1
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")

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
