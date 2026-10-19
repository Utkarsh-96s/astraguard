"""Integrated Debris Collision Risk Module implementing RiskModule protocol."""
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from ml.common.schemas import Attribution, ModuleResult
from ml.debris.cdm_classifier import CDMRiskClassifier
from ml.debris.pc_engine import FosterCollisionProbabilityEngine
from ml.debris.scorer import compute_debris_risk_score
from ml.debris.screener import ConjunctionScreener


class DebrisRiskModule:
    """Debris Collision Risk AI module implementing unified RiskModule contract."""

    name: str = "Debris Collision Risk AI"
    version: str = "0.1.0"

    def __init__(
        self,
        hard_body_radius_m: float = 5.0,
        enable_xgboost: bool = True,
    ) -> None:
        self.hard_body_radius_m = hard_body_radius_m
        self.pc_engine = FosterCollisionProbabilityEngine(hard_body_radius_m=hard_body_radius_m)
        self.screener = ConjunctionScreener()
        self.classifier = CDMRiskClassifier()
        self.enable_xgboost = enable_xgboost
        self.is_fitted = False

    def fit(self, data: Any = None) -> None:
        """Fit XGBoost CDM model on reference Kelvins CDMs or synthetic training events."""
        # If no data passed, train on default Kelvins sample augmented with synthetic events
        from data.synthetic.debris_gen import generate_cdm_progression

        cdm_records: list[dict[str, Any]] = []
        labels: list[int] = []

        # Generate nominal (low risk) and critical (high risk) CDMs for training
        for seed_idx in range(40):
            crit_flag = (seed_idx % 2 == 0)
            initial_pc = 1e-4 if crit_flag else 1e-7
            final_pc = 3e-4 if crit_flag else 5e-7

            prog = generate_cdm_progression(
                conjunction_id=f"CONJ-TRAIN-{seed_idx:03d}",
                initial_pc=initial_pc,
                final_pc=final_pc,
                num_updates=6,
                seed=seed_idx + 100,
            )
            for _, row in prog.iterrows():
                row_dict = dict(row)
                row_dict["log10_pc"] = float(np.log10(max(row_dict["pc"], 1e-12)))
                cdm_records.append(row_dict)
                labels.append(1 if crit_flag else 0)

        df_train = pd.DataFrame(cdm_records)
        y_train = np.array(labels)

        self.classifier.fit(df_train, y_train)
        self.is_fitted = True

    def score(
        self,
        window: Any,
        asset_id: str = "SAT-DEFAULT",
        ts: datetime | None = None,
    ) -> ModuleResult:
        """Evaluate conjunction event or CDM and return standardized ModuleResult.

        Input can be a CDM dict, Conjunction dict, or DataFrame row.
        """
        timestamp = ts or datetime.now(UTC)
        ev_data = self._resolve_event(window)

        # Extract or compute Pc
        miss_m = float(ev_data.get("miss_distance_m", ev_data.get("miss_km", 1.0) * 1000.0))
        tca_hours = float(ev_data.get("time_to_tca_hours", 24.0))

        if "pc" in ev_data and ev_data["pc"] is not None:
            pc = float(ev_data["pc"])
            pc_calc = {"pc": pc, "risk_class": self.pc_engine.classify_risk(pc), "pc_method": ev_data.get("pc_method", "provided")}
        else:
            pc_calc = self.pc_engine.compute_screening_pc(
                miss_distance_m=miss_m,
                relative_velocity_ms=float(ev_data.get("relative_velocity_ms", 14000.0)),
            )
            pc = pc_calc["pc"]

        risk_score = compute_debris_risk_score(
            pc=pc,
            miss_distance_m=miss_m,
            time_to_tca_hours=tca_hours,
        )

        evidence = {
            "pc": pc,
            "miss_distance_m": round(miss_m, 1),
            "time_to_tca_hours": round(tca_hours, 1),
            "risk_class": pc_calc.get("risk_class", "NOMINAL"),
            "pc_method": pc_calc.get("pc_method", "foster_2d_screening"),
            "secondary_id": ev_data.get("secondary_id", ev_data.get("secondary_name", "UNKNOWN_DEBRIS")),
            "tca": str(ev_data.get("tca", "UNKNOWN")),
        }

        # Optional XGBoost prediction enrichment if fitted
        if self.is_fitted and self.enable_xgboost:
            cdm_input = {
                "time_to_tca_hours": tca_hours,
                "miss_distance_m": miss_m,
                "relative_velocity_ms": float(ev_data.get("relative_velocity_ms", 14000.0)),
                "c_obs_b": float(ev_data.get("c_obs_b", 0.0)),
                "c_obs_t": float(ev_data.get("c_obs_t", 250.0)),
                "c_obs_n": float(ev_data.get("c_obs_n", 50.0)),
                "log10_pc": float(np.log10(max(pc, 1e-12))),
            }
            prob_crit, pred_class, _ml_ev = self.classifier.predict_risk(cdm_input)
            evidence["xgboost_predicted_critical_prob"] = prob_crit
            evidence["xgboost_predicted_class"] = pred_class

        confidence = 0.95 if pc >= 1e-4 or pc < 1e-6 else 0.85

        return ModuleResult(
            score=round(risk_score, 4),
            confidence=round(confidence, 2),
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
        """Produce factor-level explainability attributions for debris conjunction risk."""
        ev_data = self._resolve_event(window)
        pc = float(ev_data.get("pc", 1e-6))
        miss_m = float(ev_data.get("miss_distance_m", ev_data.get("miss_km", 1.0) * 1000.0))
        tca_hours = float(ev_data.get("time_to_tca_hours", 24.0))

        # Relative contributions to risk
        # 1. Collision probability Pc
        pc_contrib = 0.65 if pc >= 1e-4 else (0.45 if pc >= 1e-5 else 0.20)
        # 2. Miss distance
        miss_contrib = 0.25 if miss_m < 1000.0 else 0.10
        # 3. Urgency (time to TCA)
        tca_contrib = 0.20 if tca_hours < 24.0 else 0.10

        total = pc_contrib + miss_contrib + tca_contrib
        norm_pc = pc_contrib / total
        norm_miss = miss_contrib / total
        norm_tca = tca_contrib / total

        attributions = [
            Attribution(
                driver="pc_collision_probability",
                module="debris",
                contribution=round(norm_pc, 4),
                direction="increase" if pc >= 1e-5 else "decrease",
            ),
            Attribution(
                driver="miss_distance_m",
                module="debris",
                contribution=round(norm_miss, 4),
                direction="increase" if miss_m < 1000.0 else "decrease",
            ),
            Attribution(
                driver="time_to_tca_hours",
                module="debris",
                contribution=round(norm_tca, 4),
                direction="increase" if tca_hours < 24.0 else "decrease",
            ),
        ]
        return attributions

    def _resolve_event(self, window: Any) -> dict[str, Any]:
        """Extract event dictionary from dict, Series, or DataFrame."""
        if isinstance(window, dict):
            return window
        if isinstance(window, pd.Series):
            return dict(window)
        if isinstance(window, pd.DataFrame):
            return dict(window.iloc[-1])
        return {}
