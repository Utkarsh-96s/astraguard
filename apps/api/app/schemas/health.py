"""Health check schema."""
from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response payload."""
    status: str = Field("ok", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current system timestamp")
    environment: str = Field(..., description="Runtime environment")
    database_connected: bool = Field(..., description="Whether database check passed")
    message: str | None = Field(None, description="Optional diagnostic message")
