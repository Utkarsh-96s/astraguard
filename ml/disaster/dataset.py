"""Dataset loader and synthetic generator for multi-temporal SAR disaster chips."""
import hashlib
from typing import Any

import numpy as np


def generate_sar_flood_dataset(
    num_chips: int = 30,
    size: int = 128,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], str]:
    """Generate multi-temporal SAR chips with permanent water, flood inundation, and edge cases.

    Returns:
        chips: Array of shape (num_chips, 2, size, size) where channel 0=pre, channel 1=post.
               Normalized to [0.0, 1.0].
        masks: Ground truth flood change masks (num_chips, 1, size, size) with 1=new inundation.
        metadata: Dictionary containing failure case indices, coordinates, and statistics.
        data_hash: Deterministic SHA-256 hash.
    """
    rng = np.random.default_rng(seed)
    chips = np.zeros((num_chips, 2, size, size), dtype=np.float32)
    masks = np.zeros((num_chips, 1, size, size), dtype=np.float32)
    meta_chips: list[dict[str, Any]] = []

    # Grid for topography
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)

    for i in range(num_chips):
        # 1. Base topography: river valley + hills
        river_center = 0.3 * np.sin(3.0 * yy)
        dist_to_river = np.abs(xx - river_center)

        # Baseline dry terrain backscatter (~0.45..0.65 in normalized units)
        pre_sar = 0.50 + 0.12 * np.cos(2.0 * xx) + rng.normal(0, 0.05, (size, size))
        post_sar = pre_sar.copy() + rng.normal(0, 0.02, (size, size))

        # Permanent river water (low backscatter in both pre and post)
        perm_water = dist_to_river < 0.10
        pre_sar[perm_water] = 0.12 + rng.normal(0, 0.02, int(np.sum(perm_water)))
        post_sar[perm_water] = 0.12 + rng.normal(0, 0.02, int(np.sum(perm_water)))

        # Flood inundation (expands valley from width 0.10 to ~0.35..0.50)
        flood_width = float(rng.uniform(0.25, 0.45))
        inundation_zone = (dist_to_river >= 0.10) & (dist_to_river < flood_width)

        # Specular reflection causes backscatter drop in flooded region
        post_sar[inundation_zone] = 0.14 + rng.normal(0, 0.025, int(np.sum(inundation_zone)))
        masks[i, 0] = inundation_zone.astype(np.float32)

        # 2. Inject realistic failure case in designated chips:
        failure_type = "none"
        if i % 5 == 1:
            # Specular urban runway false positive: flat dry runway (strip of low backscatter)
            failure_type = "specular_runway"
            runway_mask = (np.abs(yy - 0.6) < 0.04) & (np.abs(xx) < 0.7)
            pre_sar[runway_mask] = 0.14 + rng.normal(0, 0.015, int(np.sum(runway_mask)))
            post_sar[runway_mask] = 0.14 + rng.normal(0, 0.015, int(np.sum(runway_mask)))
            # Note: Runway is NOT inundated, so mask remains 0! Classical differencing will trigger false alarm.

        elif i % 5 == 2:
            # Vegetation canopy false negative: flooded area under dense forest
            failure_type = "vegetation_canopy"
            canopy_mask = (dist_to_river >= 0.10) & (dist_to_river < 0.25) & (yy > 0.2)
            # Double-bounce scattering maintains high backscatter despite underlying water
            post_sar[canopy_mask] = 0.42 + rng.normal(0, 0.04, int(np.sum(canopy_mask)))

        # Clip to valid [0, 1] range
        chips[i, 0] = np.clip(pre_sar, 0.0, 1.0)
        chips[i, 1] = np.clip(post_sar, 0.0, 1.0)

        meta_chips.append(
            {
                "chip_id": f"SAR-CHIP-{i+1:03d}",
                "flood_pixels": int(np.sum(masks[i, 0])),
                "flood_fraction": round(float(np.mean(masks[i, 0])), 4),
                "failure_type": failure_type,
            }
        )

    hasher = hashlib.sha256()
    hasher.update(chips.tobytes())
    hasher.update(masks.tobytes())
    data_hash = hasher.hexdigest()

    return chips, masks, {"chips": meta_chips}, data_hash


__all__ = ["generate_sar_flood_dataset"]
