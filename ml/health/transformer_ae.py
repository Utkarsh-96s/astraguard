"""Transformer Autoencoder with Multi-Head Self-Attention for telemetry anomaly detection."""
import math

import torch
from torch import nn


class PositionalEncoding(nn.Module):
    """Sinusoidal temporal positional encoding."""

    def __init__(self, d_model: int, max_len: int = 512) -> None:
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, W, d_model)
        seq_len = x.size(1)
        return x + self.pe[:, :seq_len]


class MultiHeadSelfAttention(nn.Module):
    """Explicit scaled dot-product multi-head self-attention with universal ONNX support."""

    def __init__(self, d_model: int, nhead: int = 4, dropout: float = 0.1) -> None:
        super().__init__()
        assert d_model % nhead == 0, "d_model must be divisible by nhead"
        self.d_model = d_model
        self.nhead = nhead
        self.d_k = d_model // nhead

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, W, _ = x.shape
        Q = self.q_proj(x).view(B, W, self.nhead, self.d_k).transpose(1, 2)
        K = self.k_proj(x).view(B, W, self.nhead, self.d_k).transpose(1, 2)
        V = self.v_proj(x).view(B, W, self.nhead, self.d_k).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        attn = torch.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        context = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, W, self.d_model)
        return self.out_proj(context)


class SelfAttentionEncoderLayer(nn.Module):
    """Explicit self-attention block fully compatible with ONNX export."""

    def __init__(self, d_model: int, nhead: int, dim_feedforward: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.self_attn = MultiHeadSelfAttention(d_model=d_model, nhead=nhead, dropout=dropout)
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, src: torch.Tensor) -> torch.Tensor:
        src2 = self.self_attn(src)
        src = self.norm1(src + self.dropout1(src2))
        src2 = self.linear2(self.dropout(torch.relu(self.linear1(src))))
        src = self.norm2(src + self.dropout2(src2))
        return src


class TransformerAutoencoderNet(nn.Module):
    """Multi-Head Self-Attention Transformer Autoencoder for spacecraft telemetry sequences."""

    def __init__(
        self,
        input_dim: int,
        d_model: int = 32,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 64,
        latent_dim: int = 16,
        dropout: float = 0.1,
        max_len: int = 256,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.d_model = d_model
        self.latent_dim = latent_dim

        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model=d_model, max_len=max_len)

        layers = [
            SelfAttentionEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ]
        self.transformer_encoder = nn.Sequential(*layers)

        # Bottleneck compression and expansion
        self.to_latent = nn.Linear(d_model, latent_dim)
        self.from_latent = nn.Linear(latent_dim, d_model)

        self.output_proj = nn.Linear(d_model, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (B, W, C)
        projected = self.input_proj(x)
        encoded = self.pos_encoder(projected)
        transformed = self.transformer_encoder(encoded)

        # Bottleneck
        latent = torch.relu(self.to_latent(transformed))
        reconstructed_feat = torch.relu(self.from_latent(latent))
        out = self.output_proj(reconstructed_feat)
        return out
