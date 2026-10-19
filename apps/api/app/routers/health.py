"""Health check router."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns API service health, version, timestamp, and database connectivity status.",
)
async def get_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Perform health checks on service and database connectivity."""
    db_connected = False
    msg = None
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        msg = "Database connection unavailable"

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(UTC),
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        message=msg,
    )
