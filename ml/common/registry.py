"""Model Registry metadata management and tracking for deep learning models."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torchinfo
from pydantic import BaseModel, Field
from torch import nn

REGISTRY_DIR = Path(__file__).resolve().parent.parent / "registry"
REGISTRY_FILE = REGISTRY_DIR / "models_manifest.json"


class ModelRegistryEntry(BaseModel):
    """Metadata specification for a registered ML/DL model in ASTRA-GUARD."""
    model_id: str = Field(..., description="Unique model identifier, e.g. MOD-HEALTH-LSTM-001")
    name: str = Field(..., description="Human-readable model name")
    version: str = Field(..., description="Semantic version string")
    architecture: str = Field(..., description="Architecture class name or family")
    subsystem: str = Field(..., description="Target aerospace domain: health, debris, disaster, or foundation")
    data_hash: str = Field(..., description="SHA-256 hash of training/evaluation dataset")
    params_count: dict[str, int] = Field(
        ...,
        description="Parameter counts: total_params, trainable_params, non_trainable_params, model_size_bytes",
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Training hyperparameter config dict")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Evaluated performance metrics")
    latency_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Measured inference latency percentiles: p50, p95, p99",
    )
    onnx_path: str | None = Field(None, description="Relative path to exported ONNX artifact")
    checkpoint_path: str | None = Field(None, description="Relative path to PyTorch weights checkpoint")
    training_log_path: str | None = Field(None, description="Path to CSV/JSON training loss curves")
    limitations: list[str] = Field(default_factory=list, description="Honest operational constraints and failure boundaries")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def compute_data_hash(data_source: bytes | str | Path) -> str:
    """Compute SHA-256 fingerprint from bytes, string, or file content."""
    sha = hashlib.sha256()
    if isinstance(data_source, (str, Path)) and Path(data_source).is_file():
        with open(data_source, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
    elif isinstance(data_source, bytes):
        sha.update(data_source)
    else:
        sha.update(str(data_source).encode("utf-8"))
    return sha.hexdigest()


def extract_param_counts(
    model: nn.Module,
    input_size: tuple[int, ...] | None = None,
    input_data: Any | None = None,
) -> dict[str, int]:
    """Calculate model parameter counts and footprint using torchinfo."""
    try:
        if input_size is not None:
            summary = torchinfo.summary(model, input_size=input_size, verbose=0)
        elif input_data is not None:
            summary = torchinfo.summary(model, input_data=input_data, verbose=0)
        else:
            total = sum(p.numel() for p in model.parameters())
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            return {
                "total_params": total,
                "trainable_params": trainable,
                "non_trainable_params": total - trainable,
                "model_size_bytes": sum(p.numel() * p.element_size() for p in model.parameters()),
            }

        return {
            "total_params": int(summary.total_params),
            "trainable_params": int(summary.trainable_params),
            "non_trainable_params": int(summary.total_params - summary.trainable_params),
            "model_size_bytes": int(summary.total_param_bytes),
        }
    except (RuntimeError, ValueError, TypeError):
        total = sum(p.numel() for p in model.parameters())
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        return {
            "total_params": total,
            "trainable_params": trainable,
            "non_trainable_params": total - trainable,
            "model_size_bytes": sum(p.numel() * p.element_size() for p in model.parameters()),
        }


def load_model_registry() -> dict[str, Any]:
    """Load model registry manifest."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "registry_version": "1.0.0",
        "last_updated": datetime.now(UTC).isoformat(),
        "models": {},
    }


def register_model(entry: ModelRegistryEntry) -> dict[str, Any]:
    """Register or update a model card entry in models_manifest.json."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_model_registry()
    entry_dict = entry.model_dump()
    manifest["models"][entry.model_id] = entry_dict
    manifest["last_updated"] = datetime.now(UTC).isoformat()

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return entry_dict
