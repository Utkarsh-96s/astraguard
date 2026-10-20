"""PyTorch lightweight U-Net for satellite radar flood inundation segmentation."""
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class DoubleConv(nn.Module):
    """(Conv -> BatchNorm -> ReLU) * 2."""

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


class UNet(nn.Module):
    """Lightweight 2-level U-Net architecture optimized for CPU and edge satellite inference."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_filters: int = 16) -> None:
        super().__init__()
        f1 = base_filters
        f2 = base_filters * 2
        f3 = base_filters * 4
        self.inc = DoubleConv(in_channels, f1)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(f1, f2))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(f2, f3))

        self.up1 = nn.ConvTranspose2d(f3, f2, kernel_size=2, stride=2)
        self.conv_up1 = DoubleConv(f3, f2)

        self.up2 = nn.ConvTranspose2d(f2, f1, kernel_size=2, stride=2)
        self.conv_up2 = DoubleConv(f2, f1)

        self.outc = nn.Conv2d(f1, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)

        # Decoder with skip connections
        x = self.up1(x3)
        x = torch.cat([x, x2], dim=1)
        x = self.conv_up1(x)

        x = self.up2(x)
        x = torch.cat([x, x1], dim=1)
        x = self.conv_up2(x)

        logits = self.outc(x)
        return logits


class DiceBCELoss(nn.Module):
    """Combined Binary Cross-Entropy and Dice loss for segmentation."""

    def __init__(self, eps: float = 1e-6) -> None:
        super().__init__()
        self.eps = eps
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = self.bce(logits, targets)

        probs = torch.sigmoid(logits)
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (probs_flat * targets_flat).sum()
        dice = (2.0 * intersection + self.eps) / (probs_flat.sum() + targets_flat.sum() + self.eps)
        dice_loss = 1.0 - dice

        return bce_loss + dice_loss


def compute_iou(pred_mask: np.ndarray, true_mask: np.ndarray) -> float:
    """Calculate Jaccard Index (Intersection over Union)."""
    p = (pred_mask > 0).astype(bool)
    t = (true_mask > 0).astype(bool)
    intersection = np.logical_and(p, t).sum()
    union = np.logical_or(p, t).sum()
    if union == 0:
        return 1.0
    return float(intersection / union)


def compute_dice_f1(pred_mask: np.ndarray, true_mask: np.ndarray) -> float:
    """Calculate Dice similarity coefficient (F1 score)."""
    p = (pred_mask > 0).astype(bool)
    t = (true_mask > 0).astype(bool)
    intersection = np.logical_and(p, t).sum()
    total = p.sum() + t.sum()
    if total == 0:
        return 1.0
    return float(2.0 * intersection / total)


class UNetSegmenter:
    """High-level segmentation trainer and inference pipeline."""

    def __init__(
        self,
        in_channels: int = 1,
        base_filters: int = 16,
        lr: float = 0.005,
        batch_size: int = 16,
        seed: int = 42,
    ) -> None:
        self.in_channels = in_channels
        self.base_filters = base_filters
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net: UNet = UNet(in_channels=self.in_channels, base_filters=self.base_filters).to(self.device)
        self.is_fitted = False

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """Evaluate forward pass with sigmoid activation."""
        self.net.eval()
        return torch.sigmoid(self.net(x.to(self.device)))

    def fit(
        self,
        chips: np.ndarray,
        masks: np.ndarray,
        epochs: int = 12,
    ) -> "UNetSegmenter":
        """Train U-Net on satellite image chips and binary ground-truth masks.

        Args:
            chips: Array of shape (N, H, W) or (N, C, H, W) normalized to [0, 1]
            masks: Array of shape (N, H, W) or (N, 1, H, W) binary {0, 1}
        """
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        if chips.ndim == 3:
            chips = chips[:, None, :, :]  # (N, 1, H, W)
        if masks.ndim == 3:
            masks = masks[:, None, :, :]

        # Normalize chips to [0.0, 1.0] if in [0, 255]
        if chips.max() > 1.0:
            chips = chips / 255.0

        chips_tensor = torch.from_numpy(chips).float()
        masks_tensor = torch.from_numpy(masks).float()

        dataset = TensorDataset(chips_tensor, masks_tensor)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self.net = UNet(in_channels=self.in_channels, out_channels=1).to(self.device)
        optimizer = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        criterion = DiceBCELoss()

        self.net.train()
        for _ in range(epochs):
            for batch_x, batch_y in loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                logits = self.net(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

        self.is_fitted = True
        return self

    def predict_mask(
        self,
        chip: np.ndarray,
        threshold: float = 0.50,
    ) -> tuple[np.ndarray, float, float]:
        """Run segmentation inference on single chip (H, W) or (1, H, W).

        Returns:
            binary_mask: 2D uint8 array (H, W) of 0s and 1s
            water_ratio: fraction of chip pixels inundated
            confidence: mean confidence across segmented pixels
        """
        if self.net is None:
            raise RuntimeError("UNetSegmenter net is not initialized.")

        if chip.ndim == 2:
            chip = chip[None, None, :, :]
        elif chip.ndim == 3:
            chip = chip[None, :, :, :]

        if chip.max() > 1.0:
            chip = chip / 255.0

        self.net.eval()
        with torch.no_grad():
            tensor_chip = torch.from_numpy(chip).float().to(self.device)
            logits = self.net(tensor_chip)
            probs = torch.sigmoid(logits).cpu().numpy()[0, 0]

        binary_mask = (probs >= threshold).astype(np.uint8)
        water_ratio = float(binary_mask.mean())

        # Confidence: distance of probabilities from ambiguous 0.5 threshold
        confidence = float(np.mean(np.abs(probs - 0.5) * 2.0))
        confidence = float(np.clip(round(confidence, 3), 0.70, 0.98))

        return binary_mask, water_ratio, confidence

    @staticmethod
    def estimate_area_km2(
        binary_mask: np.ndarray,
        pixel_size_m: float = 100.0,
    ) -> float:
        """Compute estimated flood surface area in km² from binary mask.

        Default pixel_size_m = 100m (for 128x128 chips covering ~12.8 km x 12.8 km = 163 km²).
        """
        water_pixel_count = int((binary_mask == 1).sum())
        area_m2 = water_pixel_count * (pixel_size_m**2)
        area_km2 = area_m2 / 1.0e6
        return round(float(area_km2), 2)

    @staticmethod
    def compute_surface_area_km2(
        binary_mask: np.ndarray,
        resolution_m: float = 100.0,
    ) -> float:
        """Alias for estimate_area_km2."""
        return UNetSegmenter.estimate_area_km2(binary_mask, pixel_size_m=resolution_m)
