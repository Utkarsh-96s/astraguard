"""Data Ingestion Router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.conjunction import ConjunctionItem
from app.schemas.disaster import DisasterIngestRequest
from app.schemas.objects import SpaceObjectBatchRequest
from app.schemas.telemetry import TelemetryBatchRequest, TelemetryIngestResponse
from app.services.ingest import (
    ingest_conjunction_event,
    ingest_disaster_event,
    ingest_space_objects,
    ingest_telemetry_batch,
)

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


@router.post(
    "/telemetry",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry batch",
    description="Bulk ingest multi-channel telemetry points for a spacecraft asset.",
)
async def ingest_telemetry_endpoint(
    payload: TelemetryBatchRequest,
    db: AsyncSession = Depends(get_db),
) -> TelemetryIngestResponse:
    """Ingest a batch of time-series telemetry."""
    if not payload.readings:
        raise HTTPException(status_code=400, detail="Readings batch cannot be empty")

    asset_id = payload.readings[0].asset_id
    is_synthetic = any(r.synthetic for r in payload.readings)
    count = await ingest_telemetry_batch(db, payload.readings)

    return TelemetryIngestResponse(
        ingested_count=count,
        asset_id=asset_id,
        synthetic=is_synthetic,
    )


@router.post(
    "/tle",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest space objects and TLEs",
    description="Ingest or update space objects in the catalog with orbital element sets.",
)
async def ingest_tle_endpoint(
    payload: SpaceObjectBatchRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Ingest a batch of Two-Line Element (TLE) sets."""
    count = await ingest_space_objects(db, payload.objects)
    return {"ingested_count": count}


@router.post(
    "/imagery",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest imagery and disaster event",
    description="Ingest satellite imagery product and its associated disaster detection.",
)
async def ingest_imagery_endpoint(
    payload: DisasterIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Ingest an imagery product metadata and disaster event."""
    prod_id, ev_id = await ingest_disaster_event(db, payload.product, payload.event)
    return {"product_id": prod_id, "event_id": ev_id, "status": "persisted"}


@router.post(
    "/conjunction",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest conjunction screening result",
    description="Ingest a close approach event between primary asset and debris.",
)
async def ingest_conjunction_endpoint(
    payload: ConjunctionItem,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Ingest a single conjunction screening event."""
    conj_id = await ingest_conjunction_event(db, payload)
    return {"conjunction_id": conj_id, "status": "persisted"}
