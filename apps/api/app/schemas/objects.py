"""Schemas for space objects and orbital TLEs."""
from datetime import datetime

from pydantic import BaseModel, Field


class SpaceObjectItem(BaseModel):
    """Space object / TLE record."""
    norad_id: int = Field(..., description="NORAD catalog identifier")
    name: str = Field(..., description="Common object name")
    type: str = Field("debris", description="Object type (payload, debris, rocket body)")
    tle_line1: str = Field(..., description="First line of Two-Line Element set")
    tle_line2: str = Field(..., description="Second line of Two-Line Element set")
    epoch: datetime = Field(..., description="Epoch timestamp of TLE")


class SpaceObjectBatchRequest(BaseModel):
    """Batch of space objects for ingestion."""
    objects: list[SpaceObjectItem] = Field(..., description="Array of space objects")


class SpaceObjectResponse(BaseModel):
    """Space object query response."""
    norad_id: int
    name: str
    type: str
    tle_line1: str
    tle_line2: str
    epoch: datetime
    updated_at: datetime


class SpaceObjectQueryResponse(BaseModel):
    """Paginated or filtered list of space objects."""
    count: int
    data: list[SpaceObjectResponse]
