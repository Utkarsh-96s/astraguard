"""PyTorch LSTM Autoencoder for multivariate spacecraft telemetry anomaly detection."""
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from ml.common.schemas import Attribution
from ml.health.calibrator import HealthScoreCalibrator


class LSTMAutoencoderNet(nn.Module):
    """Sequence-to-sequence LSTM Autoencoder architecture.

    Compresses input telemetry window (W, C) into a latent representation and reconstructs it.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 32,
        latent_dim: int = 16,
        num_layers: int = 1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder: (B, W, C) -> (B, W, H)
        self.encoder_lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.to_latent = nn.Linear(hidden_dim, latent_dim)

        # Decoder: (B, W, latent) -> (B, W, H) -> (B, W, C)
        self.from_latent = nn.Linear(latent_dim, hidden_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.output_proj = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder
        enc_out, _ = self.encoder_lstm(x)
        # Latent bottleneck from final step or pooled representations
        latent = torch.relu(self.to_latent(enc_out))

        # Decoder
        dec_in = torch.relu(self.from_latent(latent))
        dec_out, _ = self.decoder_lstm(dec_in)
        reconstruction = self.output_proj(dec_out)
        return reconstruction


class LSTMAutoencoder:
    """High-level LSTM Autoencoder estimator with calibration and channel attributions."""

    def __init__(
        self,
        hidden_dim: int = 32,
        latent_dim: int = 16,
        lr: float = 0.003,
        batch_size: int = 32,
        epochs: int = 25,
        seed: int = 42,
    ) -> None:
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.lr = lr
        self.batch_size = batch_size
        self.epochs = epochs
        self.seed = seed

        self.net: LSTMAutoencoderNet | None = None
        self.calibrator = HealthScoreCalibrator()
        self.channel_names: list[str] = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_fitted: bool = False

    def fit(self, windows: np.ndarray, channel_names: list[str]) -> "LSTMAutoencoder":
        """Train autoencoder on nominal 3D telemetry windows of shape (N, W, C)."""
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        self.channel_names = list(channel_names)
        _num_windows, _win_len, num_channels = windows.shape

        self.net = LSTMAutoencoderNet(
            input_dim=num_channels,
            hidden_dim=self.hidden_dim,
            latent_dim=self.latent_dim,
        ).to(self.device)

        dataset = TensorDataset(torch.from_numpy(windows).float())
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        self.net.train()
        for epoch in range(self.epochs):
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                optimizer.zero_grad()
                recon = self.net(batch_x)
                loss = criterion(recon, batch_x)
                loss.backward()
                optimizer.step()

        # Compute nominal reconstruction residuals for calibration
        self.net.eval()
        with torch.no_grad():
            tensor_windows = torch.from_numpy(windows).float().to(self.device)
            recons = self.net(tensor_windows).cpu().numpy()

        # Channel-wise squared error across window time dimension: (N, C)
        channel_errors = np.mean((windows - recons) ** 2, axis=1)
        # Total window residual: mean across channels (N,)
        nominal_residuals = np.mean(channel_errors, axis=1)

        self.calibrator.fit(nominal_residuals)
        self.is_fitted = True
        return self

    def predict_window(self, window: np.ndarray) -> tuple[float, float, dict[str, Any]]:
        """Evaluate single window (W, C) or (1, W, C) and return calibrated score and evidence."""
        if not self.is_fitted or self.net is None:
            raise RuntimeError("LSTMAutoencoder is not fitted yet.")

        if window.ndim == 2:
            window = window[None, :, :]

        self.net.eval()
        with torch.no_grad():
            tensor_win = torch.from_numpy(window).float().to(self.device)
            recon = self.net(tensor_win).cpu().numpy()

        # Reconstruction error per channel: shape (C,)
        channel_errors = np.mean((window[0] - recon[0]) ** 2, axis=0)
        raw_residual = float(np.mean(channel_errors))
        calibrated_score = float(self.calibrator.calibrate(raw_residual))

        # Channel-wise breakdown
        channel_residuals = {
            ch: round(float(channel_errors[idx]), 6)
            for idx, ch in enumerate(self.channel_names)
        }

        evidence = {
            "model_type": "lstm_autoencoder",
            "raw_reconstruction_mse": round(raw_residual, 6),
            "calibrated_score": round(calibrated_score, 4),
            "channel_residuals": channel_residuals,
            "p95_threshold": round(self.calibrator.p95, 6),
            "p99_threshold": round(self.calibrator.p99, 6),
        }
        return calibrated_score, raw_residual, evidence

    def explain_window(
        self,
        window: np.ndarray,
        top_k: int = 5,
    ) -> list[Attribution]:
        """Produce channel-level attributions directly from reconstruction residuals."""
        if not self.is_fitted or self.net is None:
            raise RuntimeError("LSTMAutoencoder is not fitted yet.")

        if window.ndim == 2:
            window = window[None, :, :]

        self.net.eval()
        with torch.no_grad():
            tensor_win = torch.from_numpy(window).float().to(self.device)
            recon = self.net(tensor_win).cpu().numpy()

        channel_errors = np.mean((window[0] - recon[0]) ** 2, axis=0)
        total_error = float(np.sum(channel_errors)) + 1e-8

        # Rank channels by normalized contribution
        attributions: list[Attribution] = []
        indexed_errors = list(enumerate(channel_errors))
        indexed_errors.sort(key=lambda x: x[1], reverse=True)

        for idx, err in indexed_errors[:top_k]:
            ch_name = self.channel_names[idx]
            contribution = float(err / total_error)
            attributions.append(
                Attribution(
                    driver=ch_name,
                    module="health",
                    contribution=round(contribution, 4),
                    direction="increase",
                )
            )

        return attributions
