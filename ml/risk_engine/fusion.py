"""Core mathematical risk fusion engine implementing Noisy-OR and safety overrides."""
import os
from typing import Any

import yaml

from ml.risk_engine.schemas import RiskLevel


def load_risk_config(config_path: str = "config/risk_engine.yaml") -> dict[str, Any]:
    """Load risk engine configuration parameters from YAML file."""
    search_paths = [
        config_path,
        os.path.join(os.path.dirname(__file__), "..", "..", config_path),
        os.path.abspath(config_path),
    ]

    for path in search_paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)

    # Robust default fallback per architecture.md §5.4
    return {
        "version": "1.0.0-default",
        "fusion": {
            "weight_safety": 0.85,
            "weight_eo": 0.15,
        },
        "thresholds": {
            "nominal_max": 25.0,
            "watch_max": 50.0,
            "warning_max": 75.0,
            "critical_min": 75.0,
        },
        "hard_overrides": {
            "conjunction_pc_critical": 0.0001,
            "health_risk_warning": 0.90,
            "health_degraded_eo_cutoff": 0.50,
        },
    }


class FusionEngine:
    """Computes Noisy-OR safety hazard fusion, mission score, and critical overrides."""

    def __init__(self, config_path: str = "config/risk_engine.yaml") -> None:
        self.config = load_risk_config(config_path)

        fusion_cfg = self.config.get("fusion", {})
        self.w_safety = float(fusion_cfg.get("weight_safety", 0.85))
        self.w_eo = float(fusion_cfg.get("weight_eo", 0.15))

        thresh_cfg = self.config.get("thresholds", {})
        self.nominal_max = float(thresh_cfg.get("nominal_max", 25.0))
        self.watch_max = float(thresh_cfg.get("watch_max", 50.0))
        self.warning_max = float(thresh_cfg.get("warning_max", 75.0))
        self.critical_min = float(thresh_cfg.get("critical_min", 75.0))

        override_cfg = self.config.get("hard_overrides", {})
        self.pc_critical = float(override_cfg.get("conjunction_pc_critical", 1.0e-4))
        self.health_warning = float(override_cfg.get("health_risk_warning", 0.90))
        self.health_cutoff = float(override_cfg.get("health_degraded_eo_cutoff", 0.50))

    def compute_safety_risk(self, r_h: float, r_d: float) -> float:
        """Compute probabilistic Noisy-OR safety hazard: R_safety = 1 - (1 - r_h)(1 - r_d)."""
        clamped_h = max(0.0, min(1.0, float(r_h)))
        clamped_d = max(0.0, min(1.0, float(r_d)))
        safety_prob = 1.0 - ((1.0 - clamped_h) * (1.0 - clamped_d))
        return round(float(max(0.0, min(1.0, safety_prob))), 4)

    def compute_mission_risk(self, r_safety: float, r_e: float) -> float:
        """Compute integrated Mission Risk Score: 100 * (w_safety * R_safety + w_eo * r_e)."""
        clamped_s = max(0.0, min(1.0, float(r_safety)))
        clamped_e = max(0.0, min(1.0, float(r_e)))
        weighted = (self.w_safety * clamped_s) + (self.w_eo * clamped_e)
        score = 100.0 * weighted
        return round(float(max(0.0, min(100.0, score))), 2)

    def evaluate(
        self,
        r_h: float,
        r_d: float,
        r_e: float,
        pc: float | None = None,
        is_persistent_health: bool = False,
    ) -> dict[str, Any]:
        """Perform full fusion calculation with hard overrides and cross-effect flags."""
        r_safety = self.compute_safety_risk(r_h, r_d)
        raw_score = self.compute_mission_risk(r_safety, r_e)

        critical_override = False
        warning_override = False

        # 1. Hard Override Rule: Pc >= 1e-4 forces level >= CRITICAL
        if pc is not None and pc >= self.pc_critical:
            critical_override = True

        # 2. Hard Override Rule: Persistent health score >= 0.90 forces level >= WARNING
        if r_h >= self.health_warning and is_persistent_health:
            warning_override = True

        # Determine level and score elevation
        if critical_override:
            level = RiskLevel.CRITICAL
            final_score = max(raw_score, self.critical_min)
        elif warning_override:
            if raw_score >= self.critical_min:
                level = RiskLevel.CRITICAL
                final_score = raw_score
            else:
                level = RiskLevel.WARNING
                final_score = max(raw_score, self.watch_max)
        else:
            final_score = raw_score
            if final_score < self.nominal_max:
                level = RiskLevel.NOMINAL
            elif final_score < self.watch_max:
                level = RiskLevel.WATCH
            elif final_score < self.warning_max:
                level = RiskLevel.WARNING
            else:
                level = RiskLevel.CRITICAL

        # 3. Cross-Effects: If r_h >= 0.50 -> EO imaging tasks flagged "defer/low-power"
        defer_eo = r_h >= self.health_cutoff

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 2),
            "level": level,
            "r_safety": r_safety,
            "critical_override_applied": critical_override,
            "warning_override_applied": warning_override,
            "defer_eo_payloads": defer_eo,
        }
