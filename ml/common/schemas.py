"""Common Pydantic DTOs for ML modules and risk engine."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Attribution(BaseModel):
    """Channel or factor-level attribution for explainability."""
    driver: str = Field(..., description="Feature or channel name driving the risk score")
    module: str = Field(..., description="Source module (health, debris, disaster, fusion)")
    contribution: float = Field(..., description="Signed or relative contribution magnitude")
    direction: Literal["increase", "decrease"] = Field("increase", description="Direction of risk impact")


class ModuleResult(BaseModel):
    """Standardized output contract for any RiskModule."""
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized risk score from 0.0 to 1.0")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the score from 0.0 to 1.0")
    evidence: dict[str, Any] = Field(default_factory=dict, description="Module-specific diagnostic details")
    ts: datetime = Field(..., description="Timestamp of evaluation")
    asset_id: str = Field(..., description="Identifier of the target asset")
    synthetic: bool = Field(default=False, description="Whether this result derived from synthetic data")
