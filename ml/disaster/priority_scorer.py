"""Dynamic observation priority scoring for Earth observation tasking."""
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PriorityResult:
    """Structured result of Earth observation priority scoring."""

    priority_score: float
    base_priority: float
    deferred: bool
    recommendation: str
    feature_contributions: dict[str, float]
    raw_inputs: dict[str, Any]
    health_penalty_applied: bool = False

    @property
    def deferral_flag(self) -> bool:
        """Alias for deferred."""
        return self.deferred

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


def compute_observation_priority(
    area_km2: float,
    hours_ago: float = 1.0,
    cloud_pct: float = 0.0,
    population_proxy: float = 0.75,
    spacecraft_health_score: float = 0.0,
    revisit_gap_hours: float = 12.0,
) -> dict[str, Any]:
    """Calculate observation priority score and health cross-effects.

    Adheres strictly to architecture.md §5.3 and §5.4:
    - Base = 0.40*area_norm + 0.25*recency + 0.20*pop_proxy + 0.15*(1 - cloud_cover)
    - If spacecraft_health_score (r_h) >= 0.5 -> EO task flagged "defer/low-power"
    """
    area_norm = min(1.0, area_km2 / 500.0)
    recency = max(0.0, 1.0 - (hours_ago / 72.0))
    cloud_factor = max(0.0, 1.0 - (cloud_pct / 100.0))
    pop = float(np.clip(population_proxy, 0.0, 1.0))

    area_c = 0.40 * area_norm
    recency_c = 0.25 * recency
    pop_c = 0.20 * pop
    cloud_c = 0.15 * cloud_factor

    base_priority = area_c + recency_c + pop_c + cloud_c
    base_priority = float(np.clip(base_priority, 0.0, 1.0))

    # Cross-effect: Satellite health constraint (architecture.md §5.4)
    # If r_h >= 0.5, spacecraft health is compromised; defer heavy EO imaging payloads
    deferred = False
    effective_priority = base_priority

    if spacecraft_health_score >= 0.50:
        deferred = True
        # Penalize effective imaging priority so safety systems prioritize health recovery
        effective_priority = base_priority * 0.40

    return {
        "priority_score": round(effective_priority, 3),
        "base_priority": round(base_priority, 3),
        "deferred": deferred,
        "recommendation": "defer/low-power" if deferred else "schedule_observation",
        "components": {
            "area_component": round(area_c, 3),
            "recency_component": round(recency_c, 3),
            "population_component": round(pop_c, 3),
            "clear_sky_component": round(cloud_c, 3),
        },
        "feature_contributions": {
            "area_contribution": round(area_c, 3),
            "recency_contribution": round(recency_c, 3),
            "population_contribution": round(pop_c, 3),
            "cloud_clearance_contribution": round(cloud_c, 3),
        },
        "raw_inputs": {
            "area_km2": round(area_km2, 1),
            "hours_ago": round(hours_ago, 1),
            "cloud_pct": round(cloud_pct, 1),
            "population_proxy": round(pop, 2),
            "spacecraft_health_score": round(spacecraft_health_score, 3),
        },
    }


class DisasterPriorityScorer:
    """Class wrapper for computing observation priority and cross-system safety deferrals."""

    def score_priority(
        self,
        inundated_area_km2: float,
        hours_since_event: float = 1.0,
        cloud_cover_pct: float = 0.0,
        population_proxy: float = 0.75,
        spacecraft_health_risk: float = 0.0,
    ) -> PriorityResult:
        """Score priority and return structured PriorityResult."""
        raw_dict = compute_observation_priority(
            area_km2=inundated_area_km2,
            hours_ago=hours_since_event,
            cloud_pct=cloud_cover_pct,
            population_proxy=population_proxy,
            spacecraft_health_score=spacecraft_health_risk,
        )

        return PriorityResult(
            priority_score=raw_dict["priority_score"],
            base_priority=raw_dict["base_priority"],
            deferred=raw_dict["deferred"],
            recommendation=raw_dict["recommendation"],
            feature_contributions=raw_dict["feature_contributions"],
            raw_inputs=raw_dict["raw_inputs"],
            health_penalty_applied=raw_dict["deferred"],
        )
