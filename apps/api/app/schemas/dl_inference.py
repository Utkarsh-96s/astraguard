"""Pydantic schemas for Deep Learning model registry, figures, and real-time inference."""
from typing import Any

from pydantic import BaseModel, Field


class DLModelRegistryEntry(BaseModel):
    """Deep learning model registry catalog entry."""
    model_id: str
    name: str
    version: str
    architecture: str
    subsystem: str
    total_params: int
    trainable_params: int
    model_size_bytes: int
    data_hash: str
    dataset: str | None = None
    onnx_path: str | None = None
    latency_ms: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    status: str = "DEPLOYED"


class FigureEntry(BaseModel):
    """SpaceX monochrome figure entry from figures_manifest.json."""
    figure_id: str
    title: str
    description: str
    filename_png: str
    filename_svg: str
    url_png: str
    url_svg: str
    model_version: str
    dataset: str
    data_hash: str
    commit: str
    timestamp: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthInferenceRequest(BaseModel):
    """Spacecraft telemetry health anomaly detection inference request."""
    model_id: str = Field(default="MOD-HEALTH-TCN-001", description="Model ID: MOD-HEALTH-TCN-001, MOD-HEALTH-LSTM-001, or MOD-HEALTH-TRANSFORMER-001")
    telemetry_sequence: list[list[float]] | None = Field(default=None, description="64 timesteps x 7 channels telemetry window")
    sample_id: str | None = Field(default=None, description="Preset identifier: nominal, battery_thermal_runaway, solar_panel_degradation, reaction_wheel_friction")


class HealthInferenceResponse(BaseModel):
    """Spacecraft telemetry health anomaly detection inference response."""
    model_id: str
    subsystem: str = "health"
    is_anomaly: bool
    anomaly_score: float
    threshold: float
    channel_residuals: dict[str, float]
    channel_attributions: dict[str, float]
    sample_id: str | None = None
    latency_ms: float


class DebrisInferenceRequest(BaseModel):
    """Orbital debris sequence classification inference request."""
    model_id: str = Field(default="MOD-DEBRIS-CNN-001", description="Model ID: MOD-DEBRIS-CNN-001, MOD-DEBRIS-GRU-001, or MOD-DEBRIS-LSTM-001")
    cdm_sequence: list[list[float]] | None = Field(default=None, description="10 CDM updates x 7 features sequence")
    sample_id: str | None = Field(default=None, description="Preset identifier: critical_collision_decay, nominal_flyby, late_divergence")


class DebrisInferenceResponse(BaseModel):
    """Orbital debris sequence classification inference response."""
    model_id: str
    subsystem: str = "debris"
    raw_logit: float
    calibrated_risk_probability: float
    risk_level: str
    temporal_attributions: list[float]
    operational_recommendation: str
    lead_time_gain_hours: float
    sample_id: str | None = None
    latency_ms: float


class DisasterInferenceRequest(BaseModel):
    """Earth observation SAR flood segmentation inference request."""
    model_id: str = Field(default="MOD-DISASTER-SIAMESE-001", description="Model ID: MOD-DISASTER-SIAMESE-001 or MOD-DISASTER-UNET-001")
    pre_chip: list[list[float]] | None = Field(default=None, description="128x128 pre-disaster SAR backscatter grid")
    post_chip: list[list[float]] | None = Field(default=None, description="128x128 post-disaster SAR backscatter grid")
    sample_id: str | None = Field(default=None, description="Preset identifier: monsoon_flood_runway_present, nominal_dry_season, dense_canopy_flooding")
    decision_threshold: float = Field(default=0.5, description="Binary classification threshold for water inundation")


class DisasterInferenceResponse(BaseModel):
    """Earth observation SAR flood segmentation inference response."""
    model_id: str
    subsystem: str = "disaster"
    flood_fraction: float
    inundated_pixels: int
    total_pixels: int
    inundated_area_km2: float
    specular_runway_rejected: bool
    spatial_attention_grid: list[list[float]]
    sample_id: str | None = None
    latency_ms: float


class SamplePreset(BaseModel):
    """Interactive explorer preset scenario definition."""
    id: str
    name: str
    subsystem: str
    description: str
    injected_condition: str
    expected_verdict: str
