"""Unified Mission Risk Engine coordinating fusion, explainability, and recommendations."""
from datetime import UTC, datetime
from typing import Any

from ml.common.schemas import Attribution, ModuleResult
from ml.risk_engine.explainer import (
    AttributionAggregator,
    DeterministicRationaleGenerator,
)
from ml.risk_engine.fusion import FusionEngine
from ml.risk_engine.recommender import RecommendationEngine
from ml.risk_engine.schemas import RiskSnapshot


class MissionRiskEngine:
    """Master coordinator computing fused mission risk, XAI attributions, and recommendations."""

    def __init__(self, config_path: str = "config/risk_engine.yaml") -> None:
        self.fusion = FusionEngine(config_path=config_path)
        self.aggregator = AttributionAggregator()
        self.explainer = DeterministicRationaleGenerator()
        self.recommender = RecommendationEngine()

    def evaluate(
        self,
        asset_id: str = "SENTINEL-2A",
        health_input: ModuleResult | dict[str, Any] | float = 0.0,
        debris_input: ModuleResult | dict[str, Any] | float = 0.0,
        disaster_input: ModuleResult | dict[str, Any] | float = 0.0,
        pc: float | None = None,
        is_persistent_health: bool = False,
        health_attributions: list[Attribution] | None = None,
        debris_attributions: list[Attribution] | None = None,
        disaster_attributions: list[Attribution] | None = None,
        evidence: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        synthetic: bool = True,
    ) -> RiskSnapshot:
        """Evaluate integrated mission risk across all three subsystems.

        Args:
            asset_id: Primary satellite identifier
            health_input: ModuleResult, dictionary, or scalar score [0, 1] for health
            debris_input: ModuleResult, dictionary, or scalar score [0, 1] for debris
            disaster_input: ModuleResult, dictionary, or scalar score [0, 1] for disaster
            pc: Optional collision probability (if not in debris_input)
            is_persistent_health: Whether health anomaly persisted across k-of-n windows
            health_attributions: Optional channel attributions from health module
            debris_attributions: Optional encounter attributions from debris module
            disaster_attributions: Optional priority attributions from disaster module
            timestamp: Evaluation timestamp (defaults to UTC now)
            synthetic: Whether any inputs derive from synthetic data
        """
        now = timestamp or datetime.now(UTC)

        # 1. Parse Health Input
        if isinstance(health_input, ModuleResult):
            r_h = health_input.score
            health_ev = health_input.evidence
        elif isinstance(health_input, dict):
            r_h = float(health_input.get("score", 0.0))
            health_ev = health_input.get("evidence", health_input)
        else:
            r_h = float(health_input)
            health_ev = {}

        # 2. Parse Debris Input
        if isinstance(debris_input, ModuleResult):
            r_d = debris_input.score
            debris_ev = debris_input.evidence
            if pc is None:
                pc = float(debris_ev.get("pc", debris_ev.get("collision_probability", 0.0)))
        elif isinstance(debris_input, dict):
            r_d = float(debris_input.get("score", 0.0))
            debris_ev = debris_input.get("evidence", debris_input)
            if pc is None:
                pc = float(debris_ev.get("pc", debris_ev.get("collision_probability", 0.0)))
        else:
            r_d = float(debris_input)
            debris_ev = {}

        # 3. Parse Disaster Input
        if isinstance(disaster_input, ModuleResult):
            r_e = disaster_input.score
            disaster_ev = disaster_input.evidence
        elif isinstance(disaster_input, dict):
            r_e = float(disaster_input.get("score", 0.0))
            disaster_ev = disaster_input.get("evidence", disaster_input)
        else:
            r_e = float(disaster_input)
            disaster_ev = {}

        combined_evidence = {
            "health": health_ev,
            "debris": debris_ev,
            "disaster": disaster_ev,
        }
        # Flatten top-level keys for easy lookup by explainer/recommender
        for sub_ev in (health_ev, debris_ev, disaster_ev):
            for k, v in sub_ev.items():
                if k not in combined_evidence:
                    combined_evidence[k] = v

        if evidence:
            for k, v in evidence.items():
                combined_evidence[k] = v
            if pc is None and "pc" in evidence:
                pc = float(evidence["pc"])

        # 4. Perform Fusion Math
        fusion_res = self.fusion.evaluate(
            r_h=r_h,
            r_d=r_d,
            r_e=r_e,
            pc=pc,
            is_persistent_health=is_persistent_health,
        )

        score = fusion_res["score"]
        level = fusion_res["level"]
        r_safety = fusion_res["r_safety"]
        crit_override = fusion_res["critical_override_applied"]
        warn_override = fusion_res["warning_override_applied"]
        defer_eo = fusion_res["defer_eo_payloads"]

        # 5. Aggregate Attributions
        drivers = self.aggregator.aggregate(
            r_h=r_h,
            r_d=r_d,
            r_e=r_e,
            r_safety=r_safety,
            health_attributions=health_attributions,
            debris_attributions=debris_attributions,
            disaster_attributions=disaster_attributions,
        )

        # 6. Generate Deterministic Rationale
        rationale = self.explainer.generate_rationale(
            asset_id=asset_id,
            score=score,
            level=level,
            r_h=r_h,
            r_d=r_d,
            r_e=r_e,
            r_safety=r_safety,
            critical_override=crit_override,
            warning_override=warn_override,
            defer_eo=defer_eo,
            drivers=drivers,
            evidence=combined_evidence,
        )

        # 7. Generate Actionable Recommendations
        recommendations = self.recommender.generate_recommendations(
            asset_id=asset_id,
            score=score,
            level=level,
            r_h=r_h,
            r_d=r_d,
            r_e=r_e,
            critical_override=crit_override,
            warning_override=warn_override,
            defer_eo=defer_eo,
            evidence=combined_evidence,
            now=now,
        )

        return RiskSnapshot(
            asset_id=asset_id,
            ts=now,
            score=score,
            level=level,
            r_h=round(r_h, 4),
            r_d=round(r_d, 4),
            r_e=round(r_e, 4),
            r_safety=round(r_safety, 4),
            critical_override_applied=crit_override,
            warning_override_applied=warn_override,
            defer_eo_payloads=defer_eo,
            drivers=drivers,
            rationale=rationale,
            recommendations=recommendations,
            raw_evidence=combined_evidence,
            synthetic=synthetic,
        )
