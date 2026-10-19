"""Synthetic Earth Observation disaster imagery and event generator.

Generates:
1. Multi-spectral / SAR chips with water bodies and flood inundation zones.
2. DisasterEvent database records with prioritized observation scores.
All generated records carry synthetic=True.
"""

from datetime import UTC, datetime
from typing import Any

import numpy as np


def compute_observation_priority(
    area_km2: float,
    hours_ago: float,
    cloud_pct: float,
    population_proxy: float = 0.7,
) -> float:
    """Compute observation priority score per architecture.md §5.3:
    Score = 0.4*area_norm + 0.25*recency + 0.2*pop_proxy + 0.15*(1 - cloud_cover)
    """
    area_norm = min(1.0, area_km2 / 500.0)
    recency = max(0.0, 1.0 - (hours_ago / 72.0))
    cloud_factor = max(0.0, 1.0 - (cloud_pct / 100.0))

    priority = (
        0.40 * area_norm +
        0.25 * recency +
        0.20 * population_proxy +
        0.15 * cloud_factor
    )
    return round(float(np.clip(priority, 0.0, 1.0)), 3)


def generate_disaster_event(
    event_id: str = "DISASTER-FLOOD-001",
    event_type: str = "flood",
    area_km2: float = 145.8,
    lat: float = 24.8607,
    lon: float = 67.0011,
    cloud_pct: float = 12.0,
    acquired_at: datetime | None = None,
    synthetic: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate an ImageryProduct record and associated DisasterEvent record."""
    if acquired_at is None:
        acquired_at = datetime.now(UTC)

    product_id = f"IMG-{event_id}"
    bbox = {
        "min_lon": lon - 0.5,
        "min_lat": lat - 0.5,
        "max_lon": lon + 0.5,
        "max_lat": lat + 0.5,
    }

    product = {
        "id": product_id,
        "source": "Sentinel-1 SAR",
        "bbox": bbox,
        "acquired_at": acquired_at,
        "cloud_pct": float(cloud_pct),
        "uri": f"data/synthetic/tiles/{product_id}.png",
        "synthetic": synthetic,
    }

    priority = compute_observation_priority(
        area_km2=area_km2,
        hours_ago=2.5,
        cloud_pct=cloud_pct,
        population_proxy=0.75,
    )

    event = {
        "id": event_id,
        "product_id": product_id,
        "type": event_type,
        "area_km2": float(area_km2),
        "mask_uri": f"data/synthetic/masks/{event_id}_mask.png",
        "priority": priority,
        "confidence": 0.92,
        "synthetic": synthetic,
        "created_at": acquired_at,
    }

    return product, event


def generate_synthetic_chip_arrays(
    size: int = 128,
    water_ratio: float = 0.35,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic 2D chip array and binary segmentation mask.
    
    Returns:
        (image_tile, binary_mask) where binary_mask has 1 for flooded pixels.
    """
    rng = np.random.default_rng(seed)

    # Coordinate grid for terrain elevation gradient
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)

    # Elevation valley shape
    elevation = xx**2 + 0.5 * yy + 0.1 * rng.normal(0, 0.2, (size, size))

    # Water settles in lower elevation
    threshold = np.quantile(elevation, water_ratio)
    binary_mask = (elevation < threshold).astype(np.uint8)

    # Synthetic radar backscatter intensity (water has low backscatter/dark)
    backscatter = np.where(binary_mask == 1, rng.normal(30, 8, (size, size)), rng.normal(120, 20, (size, size)))
    backscatter = np.clip(backscatter, 0, 255).astype(np.uint8)

    return backscatter, binary_mask
