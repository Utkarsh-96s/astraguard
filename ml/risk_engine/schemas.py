"""Schemas and Data Transfer Objects for the Mission Risk Engine and XAI."""
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Operational Mission Risk Levels per architecture.md §5.4."""

    NOMINAL = "NOMINAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class OperatorActionType(str, Enum):
    """Required operator action type for recommendations (architecture.md §5.5)."""

    APPROVE = "approve"
    DISMISS = "dismiss"
    SNOOZE = "snooze"


class Recommendation(BaseModel):
    """Actionable, human-in-the-loop recommendation requiring operator sign-off."""

    action_code: str = Field(..., description="Machine-readable action identifier (e.g. CAM_ASSESSMENT)")
    title: str = Field(..., description="Short summary title of the recommendation")
    description: str = Field(..., description="Detailed explanation of the required operator action")
    priority: Literal["low", "medium", "high", "critical"] = Field("medium", description="Urgency priority")
    required_operator_action: OperatorActionType = Field(
        OperatorActionType.APPROVE,
        description="Action required from operator: approve, dismiss, snooze",
    )
    rationale: str = Field(..., description="Underlying cause or condition prompting this recommendation")
    subsystem_or_target: str | None = Field(None, description="Affected subsystem, debris ID, or target region")
    created_at: datetime = Field(..., description="Timestamp of generation")


class DriverContribution(BaseModel):
    """Aggregated risk driver with percentage contribution and directional impact."""

    driver: str = Field(..., description="Identifier of the driving feature or module")
    module: str = Field(..., description="Source module (health, debris, disaster, fusion)")
    magnitude: float = Field(..., description="Raw contribution magnitude")
    percent_of_risk: float = Field(..., ge=0.0, le=100.0, description="Normalized percentage of total explained risk")
    direction: Literal["increase", "decrease"] = Field("increase", description="Directional impact on risk")
    summary: str = Field(..., description="Human-readable summary of the driver's role")


class RiskSnapshot(BaseModel):
    """Comprehensive snapshot of the integrated mission risk state at time t."""

    asset_id: str = Field(..., description="Target satellite identifier (e.g. SENTINEL-2A)")
    ts: datetime = Field(..., description="Evaluation timestamp")
    score: float = Field(..., ge=0.0, le=100.0, description="Fused Mission Risk Score from 0.0 to 100.0")
    level: RiskLevel = Field(..., description="Categorical risk level (NOMINAL, WATCH, WARNING, CRITICAL)")
    r_h: float = Field(..., ge=0.0, le=1.0, description="Spacecraft health risk score [0, 1]")
    r_d: float = Field(..., ge=0.0, le=1.0, description="Debris collision risk score [0, 1]")
    r_e: float = Field(..., ge=0.0, le=1.0, description="Earth observation / disaster priority score [0, 1]")
    r_safety: float = Field(..., ge=0.0, le=1.0, description="Probabilistic Noisy-OR physical safety hazard [0, 1]")
    critical_override_applied: bool = Field(False, description="Whether Pc >= 1e-4 forced CRITICAL level")
    warning_override_applied: bool = Field(False, description="Whether persistent r_h >= 0.90 forced WARNING level")
    defer_eo_payloads: bool = Field(False, description="Whether r_h >= 0.50 triggered payload deferral cross-effect")
    drivers: list[DriverContribution] = Field(default_factory=list, description="Top factor-level risk drivers")
    rationale: str = Field(..., description="Deterministic natural language explanation of the score and level")
    recommendations: list[Recommendation] = Field(default_factory=list, description="Actionable operator recommendations")
    raw_evidence: dict[str, Any] = Field(default_factory=dict, description="Raw evidence payload from upstream modules")
    synthetic: bool = Field(True, description="Whether this evaluation contains synthetic data")
