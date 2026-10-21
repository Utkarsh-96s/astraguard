"""Explainability utilities for Spacecraft Health AI: Residual heatmaps and Captum Integrated Gradients."""

import numpy as np
import torch
from captum.attr import IntegratedGradients
from torch import nn

from ml.common.schemas import Attribution


def compute_residual_matrix(
    actual: np.ndarray | torch.Tensor,
    reconstructed: np.ndarray | torch.Tensor,
) -> np.ndarray:
    """Compute per-channel per-timestep squared error residual matrix.

    Returns:
        Array shaped (channels, time_steps) with non-negative squared residuals.
    """
    if isinstance(actual, torch.Tensor):
        actual_np = actual.detach().cpu().numpy()
    else:
        actual_np = np.asarray(actual)

    if isinstance(reconstructed, torch.Tensor):
        rec_np = reconstructed.detach().cpu().numpy()
    else:
        rec_np = np.asarray(reconstructed)

    # Ensure shape is (timesteps, channels)
    if actual_np.ndim == 3:
        actual_np = actual_np[0]
    if rec_np.ndim == 3:
        rec_np = rec_np[0]

    # Squared error: (timesteps, channels) -> transpose to (channels, timesteps)
    sq_err = (actual_np - rec_np) ** 2
    return sq_err.T


class ReconstructionLossWrapper(nn.Module):
    """Wrapper that outputs scalar mean reconstruction error for Captum gradient attribution."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, W, C)
        reconstructed = self.model(x)
        # Sum of squared errors per batch element
        loss_per_sample = torch.sum((x - reconstructed) ** 2, dim=(1, 2))
        return loss_per_sample


def compute_integrated_gradients_attributions(
    model: nn.Module,
    input_tensor: torch.Tensor,
    channel_names: list[str],
    baseline: torch.Tensor | None = None,
    n_steps: int = 25,
) -> list[Attribution]:
    """Calculate channel-level attribution using Captum Integrated Gradients.

    Evaluates the path integral of gradients of the reconstruction loss function
    with respect to input telemetry features over n_steps interpolations.

    Args:
        model: Trained autoencoder (LSTM, TCN, or Transformer).
        input_tensor: Input sequence shaped (1, W, C) or (W, C).
        channel_names: List of telemetry channel identifiers.
        baseline: Baseline sequence (zeros if None).
        n_steps: Number of Gauss-Legendre quadrature steps.

    Returns:
        Sorted list of Attribution objects labeled with 'largest contributor' semantics.
    """
    model.eval()
    if input_tensor.dim() == 2:
        input_tensor = input_tensor.unsqueeze(0)

    if baseline is None:
        baseline = torch.zeros_like(input_tensor)
    elif baseline.dim() == 2:
        baseline = baseline.unsqueeze(0)

    wrapper = ReconstructionLossWrapper(model)
    ig = IntegratedGradients(wrapper)

    # Attribute reconstruction loss to inputs
    attributions_tensor = ig.attribute(input_tensor, baselines=baseline, n_steps=n_steps)
    # attributions_tensor shape: (1, W, C)
    attr_np = attributions_tensor.detach().cpu().numpy()[0]

    # Aggregate absolute attribution across the time dimension
    channel_mags = np.sum(np.abs(attr_np), axis=0)  # (C,)
    total_mag = float(np.sum(channel_mags)) + 1e-8
    normalized_rel = channel_mags / total_mag

    results: list[Attribution] = []
    for idx, ch in enumerate(channel_names):
        rel_val = float(normalized_rel[idx])
        results.append(
            Attribution(
                driver=ch,
                module="health_captum_ig",
                contribution=round(rel_val, 4),
                direction="increase",
            )
        )

    # Sort descending by contribution magnitude
    results.sort(key=lambda a: a.contribution, reverse=True)
    return results
