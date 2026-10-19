"""XGBoost classifier for Conjunction Data Message (CDM) risk prediction."""
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score

from ml.common.schemas import Attribution

CDM_FEATURE_NAMES = [
    "time_to_tca_hours",
    "miss_distance_m",
    "relative_velocity_ms",
    "c_obs_b",
    "c_obs_t",
    "c_obs_n",
    "log10_pc",
]


class CDMRiskClassifier:
    """XGBoost model predicting final conjunction criticality from intermediate CDMs."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.08,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state

        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            eval_metric="logloss",
        )
        self.is_fitted = False
        self.feature_names = list(CDM_FEATURE_NAMES)

    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> "CDMRiskClassifier":
        """Fit XGBoost model on CDM features."""
        if isinstance(X, pd.DataFrame):
            X_mat = X[self.feature_names].values
        else:
            X_mat = X

        self.model.fit(X_mat, y)
        self.is_fitted = True
        return self

    def predict_risk(self, cdm_dict_or_row: dict[str, Any] | pd.Series | np.ndarray) -> tuple[float, str, dict[str, Any]]:
        r"""Predict probability of CRITICAL conjunction ($P_c \ge 10^{-4}$) and class.

        Returns:
            prob_critical: float in [0.0, 1.0]
            predicted_class: "CRITICAL", "WARNING", "WATCH", or "NOMINAL"
            evidence: dictionary with model diagnosis details
        """
        if not self.is_fitted:
            raise RuntimeError("CDMRiskClassifier is not fitted yet.")

        vec = self._to_feature_vector(cdm_dict_or_row)
        probs = self.model.predict_proba(vec.reshape(1, -1))[0]

        # In binary classification, probs[1] is probability of critical
        prob_crit = float(probs[1]) if len(probs) > 1 else float(probs[0])

        if prob_crit >= 0.70:
            pred_class = "CRITICAL"
        elif prob_crit >= 0.45:
            pred_class = "WARNING"
        elif prob_crit >= 0.20:
            pred_class = "WATCH"
        else:
            pred_class = "NOMINAL"

        evidence = {
            "model_type": "xgboost_cdm_classifier",
            "prob_critical": round(prob_crit, 4),
            "predicted_class": pred_class,
            "feature_values": {name: round(float(vec[i]), 4) for i, name in enumerate(self.feature_names)},
        }
        return prob_crit, pred_class, evidence

    def explain(self, cdm_dict_or_row: dict[str, Any] | pd.Series | np.ndarray, top_k: int = 4) -> list[Attribution]:
        """Produce feature-level attributions for the CDM prediction."""
        if not self.is_fitted:
            raise RuntimeError("CDMRiskClassifier is not fitted yet.")

        # Use gain-based feature importances weighted by sample values
        vec = self._to_feature_vector(cdm_dict_or_row)
        importances = self.model.feature_importances_

        raw_weights = importances * (np.abs(vec) + 1.0)
        total_w = float(np.sum(raw_weights)) + 1e-8
        normalized = raw_weights / total_w

        indexed = sorted(enumerate(normalized), key=lambda x: x[1], reverse=True)
        attributions: list[Attribution] = []

        for idx, weight in indexed[:top_k]:
            fname = self.feature_names[idx]
            attributions.append(
                Attribution(
                    driver=fname,
                    module="debris",
                    contribution=round(float(weight), 4),
                    direction="increase",
                )
            )

        return attributions

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
        """Compute ROC-AUC and PR-AUC scores on held-out test CDMs."""
        if not self.is_fitted:
            raise RuntimeError("CDMRiskClassifier is not fitted yet.")

        probs = self.model.predict_proba(X_test)[:, 1]
        roc_auc = float(roc_auc_score(y_test, probs))
        pr_auc = float(average_precision_score(y_test, probs))

        return {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
        }

    def _to_feature_vector(self, data: dict[str, Any] | pd.Series | np.ndarray) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return data.astype(np.float32)

        vec = np.zeros(len(self.feature_names), dtype=np.float32)
        for i, name in enumerate(self.feature_names):
            if isinstance(data, dict):
                val = data.get(name, 0.0)
            else:
                val = data.get(name, 0.0)
            vec[i] = float(val)
        return vec
