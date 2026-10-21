from typing import Any

import numpy as np
import torch
from captum.attr import IntegratedGradients
from torch import nn

from ml.common.schemas import Attribution
from ml.debris.baselines import CDM_FEATURE_NAMES


class ModelLogitWrapper(nn.Module):
    """Wrapper ensuring scalar or single batch element output for Captum attribution."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        if out.ndim > 1:
            return out[:, 0]
        return out


def compute_debris_integrated_gradients(
    model: nn.Module,
    input_seq: torch.Tensor | np.ndarray,
    feature_names: list[str] | None = None,
    time_to_tca_hours: list[float] | None = None,
    baseline: torch.Tensor | None = None,
    n_steps: int = 25,
) -> dict[str, Any]:
    """Compute step-level and feature-level Integrated Gradients attributions.

    Args:
        model: Trained PyTorch sequence model (GRU, LSTM, or 1D-CNN).
        input_seq: Sequence tensor or array shaped (1, seq_len, num_features) or (seq_len, num_features).
        feature_names: List of CDM feature names (defaults to CDM_FEATURE_NAMES).
        time_to_tca_hours: Optional array of hours before TCA for each CDM update step.
        baseline: Reference baseline sequence (defaults to zeros).
        n_steps: Number of integration steps for Captum.

    Returns:
        Dictionary containing:
        - feature_attributions: List of Attribution objects sorted descending.
        - temporal_attributions: List of dicts with step index, time_to_tca, and importance.
        - attribution_matrix: 2D numpy array (num_features, seq_len) with signed attributions.
    """
    model.eval()
    feat_names = feature_names or CDM_FEATURE_NAMES

    if isinstance(input_seq, np.ndarray):
        tensor_in = torch.tensor(input_seq, dtype=torch.float32)
    else:
        tensor_in = input_seq.clone().detach().float()

    if tensor_in.dim() == 2:
        tensor_in = tensor_in.unsqueeze(0)

    if baseline is None:
        baseline = torch.zeros_like(tensor_in)
    elif baseline.dim() == 2:
        baseline = baseline.unsqueeze(0)

    wrapper = ModelLogitWrapper(model)
    ig = IntegratedGradients(wrapper)

    attributions_tensor = ig.attribute(tensor_in, baselines=baseline, n_steps=n_steps)
    # attributions_tensor: (1, seq_len, num_features)
    attr_np = attributions_tensor.detach().cpu().numpy()[0]  # (seq_len, num_features)

    seq_len, _num_features = attr_np.shape

    # 1. Feature attributions: sum absolute values across time dimension
    feat_mags = np.sum(np.abs(attr_np), axis=0)
    total_feat_mag = float(np.sum(feat_mags)) + 1e-8
    norm_feat_mags = feat_mags / total_feat_mag

    feature_attributions: list[Attribution] = []
    for idx, fname in enumerate(feat_names):
        feature_attributions.append(
            Attribution(
                driver=fname,
                module="debris_captum_ig",
                contribution=round(float(norm_feat_mags[idx]), 4),
                direction="increase",
            )
        )
    feature_attributions.sort(key=lambda a: a.contribution, reverse=True)

    # 2. Temporal step attributions: sum absolute values across feature dimension
    step_mags = np.sum(np.abs(attr_np), axis=1)
    total_step_mag = float(np.sum(step_mags)) + 1e-8
    norm_step_mags = step_mags / total_step_mag

    temporal_attributions: list[dict[str, Any]] = []
    for step_idx in range(seq_len):
        h_tca = float(time_to_tca_hours[step_idx]) if time_to_tca_hours and step_idx < len(time_to_tca_hours) else None
        temporal_attributions.append(
            {
                "step": step_idx + 1,
                "time_to_tca_hours": h_tca,
                "importance": round(float(norm_step_mags[step_idx]), 4),
            }
        )

    # 3. Attribution matrix: transpose to (num_features, seq_len)
    attribution_matrix = attr_np.T

    return {
        "feature_attributions": feature_attributions,
        "temporal_attributions": temporal_attributions,
        "attribution_matrix": attribution_matrix,
    }


__all__ = ["compute_debris_integrated_gradients"]
