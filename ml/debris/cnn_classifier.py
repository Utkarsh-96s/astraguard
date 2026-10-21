"""Multi-Scale 1D Temporal Convolutional Network (CNN) for CDM Sequence Classification."""
import torch
from torch import nn


class Conv1dBranch(nn.Module):
    """1D Convolution branch with causal padding and batch normalization."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int) -> None:
        super().__init__()
        self.padding = kernel_size - 1
        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            padding=self.padding,
        )
        self.bn = nn.BatchNorm1d(out_channels)
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, W)
        out = self.conv(x)
        if self.padding > 0:
            out = out[:, :, : -self.padding]
        return self.act(self.bn(out))


class Debris1DCNNClassifierNet(nn.Module):
    """Multi-Scale 1D-CNN Sequence Classifier for Conjunction Data Messages.

    Processes CDM sequences with multiple kernel receptive fields (short-term jitter,
    multi-step trajectory trends, and whole-sequence horizon).
    """

    def __init__(
        self,
        input_dim: int = 7,
        branch_channels: int = 16,
        hidden_dim: int = 32,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim

        # Parallel multi-scale 1D convolutional branches
        self.branch_k2 = Conv1dBranch(input_dim, branch_channels, kernel_size=2)
        self.branch_k3 = Conv1dBranch(input_dim, branch_channels, kernel_size=3)
        self.branch_k5 = Conv1dBranch(input_dim, branch_channels, kernel_size=5)

        total_branch_channels = branch_channels * 3

        # Fusion residual conv block
        self.fusion_conv = nn.Conv1d(total_branch_channels, hidden_dim, kernel_size=1)
        self.fusion_bn = nn.BatchNorm1d(hidden_dim)
        self.fusion_act = nn.ReLU()

        # Global temporal pooling & classifier
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.max_pool = nn.AdaptiveMaxPool1d(1)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: (B, seq_len, input_dim)
        Returns: logits of shape (B, 1)
        """
        # Permute to (B, C, W) for Conv1D
        x_perm = x.permute(0, 2, 1)

        b2 = self.branch_k2(x_perm)
        b3 = self.branch_k3(x_perm)
        b5 = self.branch_k5(x_perm)

        # Concatenate across channels: (B, 3 * branch_channels, W)
        multi_scale = torch.cat([b2, b3, b5], dim=1)
        fused = self.fusion_act(self.fusion_bn(self.fusion_conv(multi_scale)))

        # Dual pooling (mean + max across time dimension): (B, hidden_dim, 1)
        avg_p = self.pool(fused).squeeze(-1)
        max_p = self.max_pool(fused).squeeze(-1)
        combined = torch.cat([avg_p, max_p], dim=-1)

        logits = self.classifier(combined)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return torch.sigmoid(self.forward(x))


__all__ = ["Debris1DCNNClassifierNet"]
