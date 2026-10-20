"""Health Lab Router - Telemetry Fault Injection, Detector Arena, and Counterfactuals."""
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from ml.health.preprocessor import CORE_CHANNELS
from pydantic import BaseModel, Field

from app.services.feature_service import feature_service
from app.services.health_lab_service import health_lab_service

router = APIRouter(prefix="/health", tags=["Health AI Lab"])


class FaultInjectionRequest(BaseModel):
    """Request payload for telemetry fault injection."""

    asset_id: str = Field("SENTINEL-2A", description="Spacecraft asset ID")
    fault_type: Literal["drift", "spike", "stuck"] = Field(
        "drift", description="Type of fault: drift, spike, or stuck"
    )
    channel: str = Field(
        "wheel_temp", description="Telemetry channel to inject fault into"
    )
    magnitude: float = Field(
        1.0, ge=0.1, le=5.0, description="Fault magnitude scaling factor"
    )
    duration_steps: int = Field(
        20, ge=5, le=50, description="Duration of fault in 10-second steps"
    )
    window_size: int = Field(
        64, ge=32, le=128, description="Sliding window length in steps"
    )


class CounterfactualRequest(BaseModel):
    """Request payload for counterfactual sensitivity analysis."""

    asset_id: str = Field("SENTINEL-2A", description="Spacecraft asset ID")
    channel: str = Field("wheel_temp", description="Target telemetry channel")
    target_reduction_pct: float = Field(
        30.0, ge=0.0, le=100.0, description="Hypothetical reduction percentage"
    )


@router.get("/channels", summary="Get supported telemetry channels for fault injection")
async def get_channels() -> dict[str, Any]:
    """Return available core telemetry channels."""
    return {
        "channels": CORE_CHANNELS,
        "descriptions": {
            "wheel_temp": "Reaction Wheel Motor Temperature (°C)",
            "bus_current": "Primary Power Bus Current (A)",
            "battery_v": "Regulated Battery Voltage (V)",
            "gyro_rate_x": "Inertial Gyro Angular Rate X (°/s)",
            "gyro_rate_y": "Inertial Gyro Angular Rate Y (°/s)",
            "gyro_rate_z": "Inertial Gyro Angular Rate Z (°/s)",
            "sun_sensor": "Solar Aspect Sensor Flux (W/m²)",
        },
    }


@router.post("/inject-fault", summary="Inject telemetry fault and run Detector Arena")
async def inject_fault(req: FaultInjectionRequest) -> dict[str, Any]:
    """Inject a telemetry fault and compare Isolation Forest vs LSTM Autoencoder side-by-side."""
    if not feature_service.is_enabled("fault_injection_lab"):
        raise HTTPException(
            status_code=403,
            detail="Fault Injection Lab feature is currently disabled via feature flags.",
        )

    try:
        result = health_lab_service.inject_and_evaluate(
            asset_id=req.asset_id,
            fault_type=req.fault_type,
            channel=req.channel,
            magnitude=req.magnitude,
            duration_steps=req.duration_steps,
            window_size=req.window_size,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fault injection simulation failed: {e!s}",
        ) from e


@router.post("/counterfactual", summary="Compute counterfactual minimal safe perturbation")
async def compute_counterfactual(req: CounterfactualRequest) -> dict[str, Any]:
    """Compute what change in telemetry restores nominal safety level."""
    if not feature_service.is_enabled("counterfactual_explainer"):
        raise HTTPException(
            status_code=403,
            detail="Counterfactual Explainer feature is currently disabled via feature flags.",
        )

    try:
        # Run a drift scenario to evaluate counterfactual response
        eval_res = health_lab_service.inject_and_evaluate(
            asset_id=req.asset_id,
            fault_type="drift",
            channel=req.channel,
            magnitude=1.2,
        )
        return {
            "asset_id": req.asset_id,
            "channel": req.channel,
            "target_reduction_pct": req.target_reduction_pct,
            "counterfactual": eval_res["counterfactual"],
            "temporal_heatmap": eval_res["temporal_heatmap"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Counterfactual computation failed: {e!s}",
        ) from e
