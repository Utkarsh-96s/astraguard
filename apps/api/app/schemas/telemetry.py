"""Schemas for telemetry ingestion and querying."""
from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryItem(BaseModel):
    """Single telemetry reading."""
    asset_id: str = Field(..., description="Target asset identifier")
    ts: datetime = Field(..., description="Timestamp of telemetry reading")
    channel: str = Field(..., description="Telemetry channel identifier")
    value: float = Field(..., description="Numerical sensor measurement")
    quality: float = Field(1.0, ge=0.0, le=1.0, description="Quality indicator (1.0 = nominal)")
    synthetic: bool = Field(False, description="Flag indicating synthetic / simulated data")


class TelemetryBatchRequest(BaseModel):
    """Batch of telemetry readings for ingestion."""
    readings: list[TelemetryItem] = Field(..., description="Array of telemetry points")


class TelemetryIngestResponse(BaseModel):
    """Response after ingesting telemetry."""
    ingested_count: int = Field(..., description="Number of telemetry points persisted")
    asset_id: str = Field(..., description="Asset ID")
    synthetic: bool = Field(..., description="Whether batch was synthetic")


class TelemetryQueryResponse(BaseModel):
    """Telemetry query results."""
    asset_id: str
    channel: str | None = None
    count: int
    data: list[TelemetryItem]
