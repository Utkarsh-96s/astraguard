"""Schemas for conjunction screening events."""
from datetime import datetime

from pydantic import BaseModel, Field


class ConjunctionItem(BaseModel):
    """Conjunction assessment record."""
    id: str = Field(..., description="Unique conjunction identifier")
    primary_id: str = Field(..., description="Asset identifier")
    secondary_id: int = Field(..., description="NORAD ID of secondary object")
    tca: datetime = Field(..., description="Time of closest approach")
    miss_km: float = Field(..., ge=0.0, description="Total miss distance in km")
    rel_vel_kms: float = Field(..., ge=0.0, description="Relative velocity in km/s")
    pc: float = Field(..., ge=0.0, le=1.0, description="Probability of collision")
    pc_method: str = Field("foster_2d_screening", description="Method used for Pc calculation")
    risk_class: str = Field("LOW", description="Risk classification (LOW, MEDIUM, HIGH, CRITICAL)")
    synthetic: bool = Field(False, description="Flag indicating simulated conjunction")
    created_at: datetime = Field(..., description="Detection timestamp")


class ConjunctionQueryResponse(BaseModel):
    """Conjunction query results."""
    primary_id: str
    count: int
    data: list[ConjunctionItem]
