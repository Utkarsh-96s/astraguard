"""Export utilities: Transparent RGBA PNG mask overlays and GeoJSON polygons."""
import json
import os
from typing import Any

import numpy as np
from PIL import Image


def export_overlay_png(
    binary_mask: np.ndarray,
    output_path: str,
    color_rgba: tuple[int, int, int, int] = (0, 210, 255, 180),  # Cyan tint for flood waters
) -> str:
    """Generate transparent RGBA PNG overlay from binary segmentation mask.

    0 (non-water) is transparent (0, 0, 0, 0).
    1 (flooded water) is tinted color_rgba.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    h, w = binary_mask.shape

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    water_idx = (binary_mask == 1)

    rgba[water_idx, 0] = color_rgba[0]
    rgba[water_idx, 1] = color_rgba[1]
    rgba[water_idx, 2] = color_rgba[2]
    rgba[water_idx, 3] = color_rgba[3]

    img = Image.fromarray(rgba, mode="RGBA")
    img.save(output_path, "PNG")
    return output_path


def export_geojson_footprint(
    event_id_or_mask: Any = "DISASTER-001",
    bbox: dict[str, float] | None = None,
    area_km2: float = 0.0,
    priority: float = 0.0,
    event_type: str = "flood",
    output_path: str | None = None,
    bounds: tuple[float, float, float, float] | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate GeoJSON FeatureCollection bounding footprint for GIS mapping."""
    if isinstance(event_id_or_mask, str):
        event_id = event_id_or_mask
    else:
        event_id = "DISASTER-FLOOD-CHIP"

    if bounds is not None:
        # Expected tuple: (min_lat, min_lon, max_lat, max_lon)
        min_lat, min_lon, max_lat, max_lon = bounds
    elif bbox is not None:
        min_lon = bbox["min_lon"]
        min_lat = bbox["min_lat"]
        max_lon = bbox["max_lon"]
        max_lat = bbox["max_lat"]
    else:
        min_lon, min_lat, max_lon, max_lat = 0.0, 0.0, 1.0, 1.0

    # Bounding box polygon coordinates (RFC 7946 format: [lon, lat])
    coordinates = [
        [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]
    ]

    feature_props: dict[str, Any] = {
        "event_id": event_id,
        "type": event_type,
        "area_km2": round(area_km2, 2),
        "priority": round(priority, 3),
        "bbox": {
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
        },
    }
    if properties:
        feature_props.update(properties)

    geojson: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": event_id,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates,
                },
                "properties": feature_props,
            }
        ],
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)

    return geojson
