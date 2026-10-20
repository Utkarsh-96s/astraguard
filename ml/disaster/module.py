"""Integrated Disaster Intelligence Module implementing RiskModule protocol."""
from datetime import UTC, datetime
from typing import Any

import numpy as np

from ml.common.schemas import Attribution, ModuleResult
from ml.disaster.change_detector import SARChangeDetector
from ml.disaster.priority_scorer import compute_observation_priority
from ml.disaster.unet import UNetSegmenter


class DisasterRiskModule:
    """Disaster Intelligence AI module implementing unified RiskModule contract."""

    name: str = "Disaster Intelligence AI"
    version: str = "0.1.0"

    def __init__(self, in_channels: int = 1) -> None:
        self.unet = UNetSegmenter(in_channels=in_channels)
        self.change_detector = SARChangeDetector()
        self.is_fitted = False

    def fit(self, data: Any = None) -> None:
        """Fit U-Net on satellite training chips or synthetic flood dataset."""
        from data.synthetic.disaster_gen import generate_synthetic_chip_arrays

        chips: list[np.ndarray] = []
        masks: list[np.ndarray] = []

        # Generate 20 synthetic training chips
        for idx in range(20):
            water_ratio = float(0.15 + (idx % 6) * 0.05)
            img, mask = generate_synthetic_chip_arrays(size=128, water_ratio=water_ratio, seed=idx + 10)
            chips.append(img)
            masks.append(mask)

        chips_arr = np.stack(chips, axis=0)
        masks_arr = np.stack(masks, axis=0)

        self.unet.fit(chips_arr, masks_arr, epochs=8)
        self.is_fitted = True

    def score(
        self,
        window: Any,
        asset_id: str = "SENTINEL-2A",
        ts: datetime | None = None,
        spacecraft_health_score: float = 0.0,
    ) -> ModuleResult:
        """Evaluate satellite chip or disaster event and return standardized ModuleResult."""
        timestamp = ts or datetime.now(UTC)

        if isinstance(window, np.ndarray):
            # 2D or 3D chip input
            if not self.is_fitted:
                self.fit()
            mask, water_ratio, conf = self.unet.predict_mask(window)
            area_km2 = self.unet.estimate_area_km2(mask)
            hours_ago = 1.0
            cloud_pct = 0.0
            pop_proxy = 0.75
        elif isinstance(window, dict):
            # Metadata event input
            area_km2 = float(window.get("area_km2", 120.0))
            hours_ago = float(window.get("hours_ago", 2.0))
            cloud_pct = float(window.get("cloud_pct", 5.0))
            pop_proxy = float(window.get("population_proxy", 0.75))
            conf = float(window.get("confidence", 0.92))
            water_ratio = float(min(1.0, area_km2 / 500.0))
        else:
            area_km2 = 100.0
            hours_ago = 1.0
            cloud_pct = 0.0
            pop_proxy = 0.70
            conf = 0.90
            water_ratio = 0.20

        priority_res = compute_observation_priority(
            area_km2=area_km2,
            hours_ago=hours_ago,
            cloud_pct=cloud_pct,
            population_proxy=pop_proxy,
            spacecraft_health_score=spacecraft_health_score,
        )

        evidence = {
            "disaster_type": "flood",
            "flooded_area_km2": area_km2,
            "water_ratio": round(water_ratio, 3),
            "priority_score": priority_res["priority_score"],
            "base_priority": priority_res["base_priority"],
            "deferred_due_to_health": priority_res["deferred"],
            "recommendation": priority_res["recommendation"],
            "components": priority_res["components"],
        }

        return ModuleResult(
            score=priority_res["priority_score"],
            confidence=round(conf, 2),
            evidence=evidence,
            ts=timestamp,
            asset_id=asset_id,
            synthetic=True,
        )

    def explain(
        self,
        window: Any,
        result: ModuleResult | None = None,
    ) -> list[Attribution]:
        """Produce factor attributions for observation priority score."""
        if isinstance(window, dict):
            area = float(window.get("area_km2", 120.0))
            hours = float(window.get("hours_ago", 2.0))
            cloud = float(window.get("cloud_pct", 5.0))
            pop = float(window.get("population_proxy", 0.75))
        else:
            area = 120.0
            hours = 1.0
            cloud = 0.0
            pop = 0.75

        area_comp = 0.40 * min(1.0, area / 500.0)
        recency_comp = 0.25 * max(0.0, 1.0 - (hours / 72.0))
        pop_comp = 0.20 * pop
        clear_comp = 0.15 * max(0.0, 1.0 - (cloud / 100.0))

        total = area_comp + recency_comp + pop_comp + clear_comp + 1e-8

        attributions = [
            Attribution(
                driver="flooded_area_km2",
                module="disaster",
                contribution=round(float(area_comp / total), 4),
                direction="increase",
            ),
            Attribution(
                driver="event_recency",
                module="disaster",
                contribution=round(float(recency_comp / total), 4),
                direction="increase",
            ),
            Attribution(
                driver="population_exposure",
                module="disaster",
                contribution=round(float(pop_comp / total), 4),
                direction="increase",
            ),
            Attribution(
                driver="clear_sky_visibility",
                module="disaster",
                contribution=round(float(clear_comp / total), 4),
                direction="increase",
            ),
        ]
        return attributions
