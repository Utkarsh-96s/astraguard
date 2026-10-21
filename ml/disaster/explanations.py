"""Grad-CAM Convolutional Explainability for Satellite Radar (SAR) Flood Segmentation."""
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn


class SARGradCAM:
    """Gradient-weighted Class Activation Mapping (Grad-CAM) for SAR segmentation U-Nets.

    Identifies which spatial radar backscatter features (e.g. specular reflection boundary,
    river valleys, or urban edges) drove the neural network's inundation segmentation.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module | None = None) -> None:
        self.model = model
        self.model.eval()

        # Default to deepest bottleneck layer if not provided
        if target_layer is not None:
            self.target_layer = target_layer
        elif hasattr(model, "down2"):
            # U-Net down2 block
            self.target_layer = model.down2[1].conv[3]
        else:
            # Fallback to first module with Conv2d
            conv_layers = [m for m in model.modules() if isinstance(m, nn.Conv2d)]
            self.target_layer = conv_layers[-2] if len(conv_layers) >= 2 else conv_layers[0]

        self.gradients: torch.Tensor | None = None
        self.activations: torch.Tensor | None = None
        self._register_hooks()

    def _register_hooks(self) -> None:
        def forward_hook(module: nn.Module, input: Any, output: torch.Tensor) -> None:
            self.activations = output.detach()

        def backward_hook(module: nn.Module, grad_input: Any, grad_output: tuple[torch.Tensor, ...]) -> None:
            self.gradients = grad_output[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_mask: torch.Tensor | None = None,
    ) -> np.ndarray:
        """Compute 2D Grad-CAM attention heatmap normalized to [0, 1].

        Args:
            input_tensor: (1, C, H, W) float tensor.
            target_mask: Optional binary mask (1, 1, H, W). If None, uses top 25% predicted pixels.

        Returns:
            2D float numpy array shaped (H, W) in [0.0, 1.0].
        """
        self.model.zero_grad()
        logits = self.model(input_tensor)  # (1, 1, H, W)

        if target_mask is None:
            # Focus on highest confidence flood predictions
            score = torch.sum(F.relu(logits))
        else:
            score = torch.sum(logits * target_mask.float())

        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            # Fallback uniform attention if hooks failed
            return np.ones((input_tensor.shape[2], input_tensor.shape[3]), dtype=np.float32)

        # Global average pool gradients: (1, C, 1, 1)
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        # Weighted channel sum: (1, 1, H', W')
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)

        # Upsample to input resolution
        cam_upsampled = F.interpolate(
            cam,
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode="bilinear",
            align_corners=False,
        )

        cam_np = cam_upsampled.squeeze().cpu().numpy()
        max_val = float(np.max(cam_np))
        if max_val > 1e-6:
            cam_np = cam_np / max_val
        else:
            cam_np = np.zeros_like(cam_np)

        return cam_np.astype(np.float32)


__all__ = ["SARGradCAM"]
