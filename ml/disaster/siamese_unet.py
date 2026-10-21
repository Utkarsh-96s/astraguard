"""Dual-Temporal Siamese and Early-Fusion U-Net for Satellite Radar Change Detection."""
import torch
from torch import nn


class DoubleConv(nn.Module):
    """(Conv2d -> BatchNorm2d -> ReLU) * 2 block."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class SiameseChangeUNet(nn.Module):
    """Dual-temporal change detection U-Net for satellite disaster flood mapping.

    Ingests paired pre-event and post-event SAR chips shaped (B, 2, H, W).
    Predicts pixel-level newly inundated flood extent with skip-connection spatial precision.
    """

    def __init__(
        self,
        in_channels: int = 2,
        out_channels: int = 1,
        base_filters: int = 16,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        f1 = base_filters
        f2 = base_filters * 2
        f3 = base_filters * 4

        # Encoder
        self.inc = DoubleConv(in_channels, f1)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(f1, f2))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(f2, f3))

        # Decoder with skip connections
        self.up1 = nn.ConvTranspose2d(f3, f2, kernel_size=2, stride=2)
        self.conv_up1 = DoubleConv(f3, f2)

        self.up2 = nn.ConvTranspose2d(f2, f1, kernel_size=2, stride=2)
        self.conv_up2 = DoubleConv(f2, f1)

        self.outc = nn.Conv2d(f1, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        x: Tensor of shape (B, 2, H, W) containing [pre_sar, post_sar].
        Returns: Logits of shape (B, 1, H, W).
        """
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)

        # Decoder
        x = self.up1(x3)
        x = torch.cat([x, x2], dim=1)
        x = self.conv_up1(x)

        x = self.up2(x)
        x = torch.cat([x, x1], dim=1)
        x = self.conv_up2(x)

        logits = self.outc(x)
        return logits

    def predict_mask(self, x: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
        with torch.no_grad():
            probs = torch.sigmoid(self.forward(x))
            return (probs > threshold).float()


__all__ = ["SiameseChangeUNet"]
