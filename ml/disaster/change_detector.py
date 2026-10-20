"""Change detection pipeline comparing pre- and post-disaster satellite imagery."""
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class ChangeResult:
    """Structured result of multi-temporal SAR flood change detection."""

    new_water_pixels: int
    new_flooded_area_km2: float
    new_water_mask: np.ndarray
    mean_backscatter_drop: float
    expansion_ratio: float
    total_pixels: int
    total_water_km2: float = 0.0

    @property
    def newly_flooded_km2(self) -> float:
        """Alias for new_flooded_area_km2."""
        return self.new_flooded_area_km2

    @property
    def change_mask(self) -> np.ndarray:
        """Alias for new_water_mask."""
        return self.new_water_mask

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class SARChangeDetector:
    """Detects new inundation areas by comparing pre- and post-event radar backscatter."""

    def __init__(
        self,
        backscatter_drop_threshold: float = 0.25,
        threshold_db_drop: float | None = None,
        resolution_m: float = 100.0,
    ) -> None:
        if threshold_db_drop is not None:
            self.drop_threshold = threshold_db_drop
        else:
            self.drop_threshold = backscatter_drop_threshold
        self.resolution_m = resolution_m

    def detect_flood_expansion(
        self,
        pre_chip: np.ndarray,
        post_chip: np.ndarray,
        post_flood_mask: np.ndarray | None = None,
        pixel_size_m: float | None = None,
    ) -> ChangeResult:
        """Compute relative backscatter difference and identify new flood inundation.

        Args:
            pre_chip: Pre-disaster reference radar backscatter (H, W) in [0, 255]
            post_chip: Post-disaster radar backscatter (H, W) in [0, 255]
            post_flood_mask: Optional binary mask of detected water in post image
            pixel_size_m: Pixel dimension in meters (defaults to self.resolution_m)
        """
        px_res = pixel_size_m if pixel_size_m is not None else self.resolution_m
        pre_norm = pre_chip.astype(np.float32) / 255.0
        post_norm = post_chip.astype(np.float32) / 255.0

        # Relative backscatter drop: Water causes specular reflection (darker pixels)
        diff = (pre_norm - post_norm) / (pre_norm + 0.05)

        # Candidate newly inundated pixels where backscatter dropped significantly
        new_water_candidate = (diff > self.drop_threshold).astype(np.uint8)

        # If post segmentation mask provided, intersect with candidate change
        if post_flood_mask is not None:
            new_water_mask = np.logical_and(new_water_candidate == 1, post_flood_mask == 1).astype(np.uint8)
            total_water_pixels = int(post_flood_mask.sum())
        else:
            new_water_mask = new_water_candidate
            post_water_est = (post_norm < 0.25).astype(np.uint8)
            total_water_pixels = int(np.logical_or(new_water_mask == 1, post_water_est == 1).sum())

        new_pixels = int(new_water_mask.sum())
        total_pixels = pre_chip.shape[0] * pre_chip.shape[1]
        new_area_km2 = (new_pixels * (px_res**2)) / 1.0e6
        total_area_km2 = (total_water_pixels * (px_res**2)) / 1.0e6

        pre_water_est = max(1, int((pre_norm < 0.25).sum()))
        expansion_ratio = float(max(1.0, (new_pixels + pre_water_est) / pre_water_est))

        return ChangeResult(
            new_water_pixels=new_pixels,
            new_flooded_area_km2=round(float(new_area_km2), 2),
            new_water_mask=new_water_mask,
            mean_backscatter_drop=round(float(diff.mean()), 3),
            expansion_ratio=round(expansion_ratio, 3),
            total_pixels=total_pixels,
            total_water_km2=round(float(max(total_area_km2, new_area_km2)), 2),
        )

    def detect_flood_extent(
        self,
        pre_chip: np.ndarray,
        post_chip: np.ndarray,
        post_flood_mask: np.ndarray | None = None,
        pixel_size_m: float | None = None,
    ) -> ChangeResult:
        """Alias for detect_flood_expansion."""
        return self.detect_flood_expansion(
            pre_chip, post_chip, post_flood_mask=post_flood_mask, pixel_size_m=pixel_size_m
        )
