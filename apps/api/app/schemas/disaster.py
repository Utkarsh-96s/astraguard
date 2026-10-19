"""Schemas for Earth Observation imagery products and disaster events."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ImageryProductItem(BaseModel):
    """Satellite imagery product metadata."""
    id: str = Field(..., description="Unique product ID")
    source: str = Field("Sentinel-2", description="Data source instrument / mission")
    bbox: dict[str, Any] = Field(..., description="Bounding box GeoJSON dictionary")
    acquired_at: datetime = Field(..., description="Timestamp of acquisition")
    cloud_pct: float = Field(0.0, ge=0.0, le=100.0, description="Cloud cover percentage")
    uri: str = Field(..., description="Asset storage URI")


class DisasterEventItem(BaseModel):
    """Detected disaster event record."""
    id: str = Field(..., description="Unique disaster event ID")
    product_id: str | None = Field(None, description="Source imagery product ID")
    type: str = Field(..., description="Disaster category (flood, wildfire, damage)")
    area_km2: float = Field(0.0, ge=0.0, description="Estimated affected area in km²")
    mask_uri: str | None = Field(None, description="Segmentation mask URI")
    priority: float = Field(0.0, ge=0.0, le=1.0, description="Computed observation priority score")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Model inference confidence")
    synthetic: bool = Field(False, description="Whether event is simulated")
    created_at: datetime = Field(..., description="Event generation timestamp")


class DisasterIngestRequest(BaseModel):
    """Disaster event ingestion payload."""
    product: ImageryProductItem
    event: DisasterEventItem


class DisasterQueryResponse(BaseModel):
    """Disaster events query results."""
    count: int
    data: list[DisasterEventItem]
