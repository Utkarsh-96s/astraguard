"""Router for real-time deep learning inference across Spacecraft Health, Debris, and Disaster EO."""
from fastapi import APIRouter, HTTPException, Path

from app.schemas.dl_inference import (
    DebrisInferenceRequest,
    DebrisInferenceResponse,
    DisasterInferenceRequest,
    DisasterInferenceResponse,
    HealthInferenceRequest,
    HealthInferenceResponse,
    SamplePreset,
)
from app.services.dl_inference_service import dl_inference_service

router = APIRouter(prefix="/api/v1/infer", tags=["Deep Learning Inference & Explorer"])


@router.post("/health", summary="Run Spacecraft Health Anomaly Detection (TCN / LSTM / Transformer)", response_model=HealthInferenceResponse)
async def infer_spacecraft_health(request: HealthInferenceRequest) -> HealthInferenceResponse:
    """Execute real-time ONNX autoencoder reconstruction on 64-step x 7-channel telemetry window.
    
    Returns overall reconstruction anomaly score, calibrated threshold comparison,
    and relative percentage attributions across telemetry subsystems.
    """
    try:
        return dl_inference_service.infer_health(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/debris", summary="Run Orbital Debris Sequence Classifier (1D-CNN / GRU / LSTM)", response_model=DebrisInferenceResponse)
async def infer_orbital_debris(request: DebrisInferenceRequest) -> DebrisInferenceResponse:
    """Execute real-time ONNX sequence classifier on 10-step CDM evolution trajectory.
    
    Returns raw logit, Platt-calibrated collision probability, operational risk level,
    and temporal attributions from t=-72h to TCA.
    """
    try:
        return dl_inference_service.infer_debris(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/disaster", summary="Run SAR Flood Segmentation (Dual-Temporal Siamese U-Net / UNet)", response_model=DisasterInferenceResponse)
async def infer_disaster_flood(request: DisasterInferenceRequest) -> DisasterInferenceResponse:
    """Execute real-time ONNX SAR segmentation on 128x128 backscatter radar chips.
    
    Returns flooded pixel count, inundated area in km^2, verification of specular runway
    false positive rejection, and 16x16 spatial attention grid.
    """
    try:
        return dl_inference_service.infer_disaster(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/samples/{subsystem}", summary="Get interactive mission scenario presets", response_model=list[SamplePreset])
async def get_mission_scenario_presets(
    subsystem: str = Path(..., description="Target domain: health, debris, or disaster"),
) -> list[SamplePreset]:
    """Retrieve pre-packaged mission scenarios with injected anomalies and ground truth conditions for interactive browser testing."""
    valid_subsystems = ["health", "debris", "disaster"]
    if subsystem.lower() not in valid_subsystems:
        raise HTTPException(status_code=400, detail=f"Invalid subsystem '{subsystem}'. Expected one of {valid_subsystems}")
    return dl_inference_service.get_sample_presets(subsystem.lower())
