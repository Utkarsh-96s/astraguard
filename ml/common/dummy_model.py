"""Lightweight dummy model used for Stage A training foundation verification."""
import torch
from torch import nn


class DummySequenceModel(nn.Module):
    """Simple 1D Conv/Linear autoencoder for foundation verification."""

    def __init__(self, in_channels: int = 4, seq_len: int = 32, hidden_dim: int = 16) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.seq_len = seq_len
        self.encoder = nn.Sequential(
            nn.Conv1d(in_channels, hidden_dim, kernel_size=3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Conv1d(hidden_dim, hidden_dim // 2, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(hidden_dim // 2, hidden_dim, kernel_size=3, padding=1),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.ConvTranspose1d(hidden_dim, in_channels, kernel_size=3, padding=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch_size, seq_len, in_channels)
        x_t = x.transpose(1, 2)
        latent = self.encoder(x_t)
        out_t = self.decoder(latent)
        return out_t.transpose(1, 2)
