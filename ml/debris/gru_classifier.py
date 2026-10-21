"""Bidirectional GRU and LSTM neural sequence classifiers for Conjunction Data Messages (CDMs)."""
import torch
from torch import nn


class DebrisGRUClassifierNet(nn.Module):
    """Bidirectional GRU classifier predicting probability of critical conjunction.

    Ingests sequential CDM updates (B, seq_len, in_channels) leading up to TCA.
    Aggregates temporal dynamics using multi-layer bidirectional GRU and dual pooling.
    """

    def __init__(
        self,
        input_dim: int = 7,
        hidden_dim: int = 32,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Bidirectional GRU
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Output classifier projection: 2 * hidden_dim for forward + backward states
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2 * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: Tensor of shape (B, seq_len, input_dim)
        Returns: Logits of shape (B, 1) or probabilities if calibrated.
        """
        # gru_out shape: (B, seq_len, 2 * hidden_dim)
        gru_out, _ = self.gru(x)

        # Aggregate via concatenation of last step and temporal mean pooling
        last_step = gru_out[:, -1, :]
        mean_pool = torch.mean(gru_out, dim=1)
        pooled = torch.cat([last_step, mean_pool], dim=-1)

        logits = self.classifier(pooled)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            logits = self.forward(x)
            return torch.sigmoid(logits)


class DebrisLSTMClassifierNet(nn.Module):
    """Bidirectional LSTM classifier predicting probability of critical conjunction."""

    def __init__(
        self,
        input_dim: int = 7,
        hidden_dim: int = 32,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2 * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        mean_pool = torch.mean(lstm_out, dim=1)
        pooled = torch.cat([last_step, mean_pool], dim=-1)
        return self.classifier(pooled)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return torch.sigmoid(self.forward(x))


__all__ = ["DebrisGRUClassifierNet", "DebrisLSTMClassifierNet"]
