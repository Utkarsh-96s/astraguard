"""Temporal Convolutional Network (TCN) Autoencoder with Dilated Causal Convolutions."""
import torch
from torch import nn


class CausalConv1d(nn.Module):
    """1D Convolution with causal padding to prevent future timestep leakage."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dilation: int = 1,
    ) -> None:
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            padding=self.padding,
            dilation=dilation,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, W)
        out = self.conv(x)
        # Chomp the right side of the padding so output length matches input length W
        if self.padding != 0:
            out = out[:, :, : -self.padding]
        return out


class TemporalBlock(nn.Module):
    """Residual block composed of two dilated causal conv layers with skip connection."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        dilation: int = 1,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.conv1 = CausalConv1d(in_channels, out_channels, kernel_size, dilation)
        self.norm1 = nn.BatchNorm1d(out_channels)
        self.act1 = nn.ReLU()
        self.drop1 = nn.Dropout(dropout)

        self.conv2 = CausalConv1d(out_channels, out_channels, kernel_size, dilation)
        self.norm2 = nn.BatchNorm1d(out_channels)
        self.act2 = nn.ReLU()
        self.drop2 = nn.Dropout(dropout)

        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None
        self.act_out = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x if self.downsample is None else self.downsample(x)
        out = self.drop1(self.act1(self.norm1(self.conv1(x))))
        out = self.drop2(self.act2(self.norm2(self.conv2(out))))
        return self.act_out(out + res)


class TCNAutoencoderNet(nn.Module):
    """Temporal Convolutional Network Autoencoder for multivariate telemetry reconstruction."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 32,
        latent_dim: int = 16,
        dilations: tuple[int, ...] = (1, 2, 4, 8),
        kernel_size: int = 3,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder blocks with exponentially growing receptive field
        encoder_layers: list[nn.Module] = []
        curr_channels = input_dim
        for d in dilations:
            encoder_layers.append(
                TemporalBlock(
                    in_channels=curr_channels,
                    out_channels=hidden_dim,
                    kernel_size=kernel_size,
                    dilation=d,
                    dropout=dropout,
                )
            )
            curr_channels = hidden_dim
        self.encoder = nn.Sequential(*encoder_layers)
        self.to_latent = nn.Conv1d(hidden_dim, latent_dim, kernel_size=1)

        # Decoder blocks (symmetrically reconstructing sequence)
        self.from_latent = nn.Conv1d(latent_dim, hidden_dim, kernel_size=1)
        decoder_layers: list[nn.Module] = []
        for d in reversed(dilations):
            decoder_layers.append(
                TemporalBlock(
                    in_channels=hidden_dim,
                    out_channels=hidden_dim,
                    kernel_size=kernel_size,
                    dilation=d,
                    dropout=dropout,
                )
            )
        self.decoder = nn.Sequential(*decoder_layers)
        self.output_conv = nn.Conv1d(hidden_dim, input_dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (B, W, C) -> transpose to (B, C, W)
        x_t = x.transpose(1, 2)
        feat = self.encoder(x_t)
        latent = torch.relu(self.to_latent(feat))

        dec_feat = torch.relu(self.from_latent(latent))
        rec_feat = self.decoder(dec_feat)
        out = self.output_conv(rec_feat)
        # Transpose back to (B, W, C)
        return out.transpose(1, 2)
