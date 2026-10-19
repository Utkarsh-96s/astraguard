"""Isolation Forest baseline model on engineered telemetry window features with SHAP explainability."""
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

from ml.common.schemas import Attribution
from ml.health.calibrator import HealthScoreCalibrator
from ml.health.preprocessor import extract_window_features


class IsolationForestBaseline:
    """Tabular Isolation Forest baseline model for spacecraft health monitoring."""

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.01,
        random_state: int = 42,
    ) -> None:
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.calibrator = HealthScoreCalibrator()
        self.channel_names: list[str] = []
        self.feature_names: list[str] = []
        self.explainer: Any = None
        self.is_fitted: bool = False

    def fit(self, windows: np.ndarray, channel_names: list[str]) -> "IsolationForestBaseline":
        """Fit Isolation Forest on nominal 3D telemetry windows (N, W, C)."""
        self.channel_names = list(channel_names)
        feat_matrix, feat_names = extract_window_features(windows, self.channel_names)
        self.feature_names = feat_names

        self.model.fit(feat_matrix)

        # Compute nominal anomaly residuals: -score_samples
        nominal_residuals = -self.model.score_samples(feat_matrix)
        self.calibrator.fit(nominal_residuals)

        # Initialize SHAP TreeExplainer if available
        try:
            import shap
            # Use small background sample to optimize TreeExplainer speed
            bg_indices = np.random.RandomState(self.random_state).choice(
                len(feat_matrix), size=min(50, len(feat_matrix)), replace=False
            )
            self.explainer = shap.TreeExplainer(self.model, data=feat_matrix[bg_indices])
        except Exception:  # noqa: BLE001
            self.explainer = None

        self.is_fitted = True
        return self

    def predict_window(self, window: np.ndarray) -> tuple[float, float, dict[str, Any]]:
        """Predict anomaly score for a single window of shape (W, C) or (1, W, C).

        Returns:
            calibrated_score: float in [0.0, 1.0]
            raw_residual: float raw score
            evidence: dict of diagnostic telemetry metadata
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestBaseline is not fitted yet.")

        if window.ndim == 2:
            window = window[None, :, :]

        feat_matrix, _ = extract_window_features(window, self.channel_names)
        raw_residual = float(-self.model.score_samples(feat_matrix)[0])
        calibrated_score = float(self.calibrator.calibrate(raw_residual))

        evidence = {
            "model_type": "isolation_forest_baseline",
            "raw_residual": round(raw_residual, 5),
            "calibrated_score": round(calibrated_score, 4),
            "p95_threshold": round(self.calibrator.p95, 5),
            "p99_threshold": round(self.calibrator.p99, 5),
        }
        return calibrated_score, raw_residual, evidence

    def explain_window(
        self,
        window: np.ndarray,
        top_k: int = 5,
    ) -> list[Attribution]:
        """Compute channel-level explainability attributions using SHAP or feature deviation."""
        if not self.is_fitted:
            raise RuntimeError("IsolationForestBaseline is not fitted yet.")

        if window.ndim == 2:
            window = window[None, :, :]

        feat_matrix, _ = extract_window_features(window, self.channel_names)
        channel_contributions: dict[str, float] = {ch: 0.0 for ch in self.channel_names}

        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(feat_matrix)
                # If shap_values is a list (multiclass), take first array
                if isinstance(shap_values, list):
                    shap_arr = shap_values[0]
                else:
                    shap_arr = shap_values
                shap_sample = shap_arr[0] if shap_arr.ndim > 1 else shap_arr

                # Sum absolute SHAP values belonging to each channel
                for idx, feat_name in enumerate(self.feature_names):
                    ch = feat_name.split("_")[0]
                    # Also handle multi-word channels like wheel_temp, bus_current
                    matched_channel = next((c for c in self.channel_names if feat_name.startswith(c)), ch)
                    val = float(np.abs(shap_sample[idx]))
                    channel_contributions[matched_channel] += val
            except Exception:  # noqa: BLE001
                channel_contributions = self._heuristic_attribution(feat_matrix)
        else:
            channel_contributions = self._heuristic_attribution(feat_matrix)

        total_contrib = sum(channel_contributions.values()) + 1e-8
        attributions: list[Attribution] = []

        # Sort channels by descending contribution
        sorted_channels = sorted(channel_contributions.items(), key=lambda kv: kv[1], reverse=True)
        for ch, raw_val in sorted_channels[:top_k]:
            normalized_contrib = float(raw_val / total_contrib)
            attributions.append(
                Attribution(
                    driver=ch,
                    module="health",
                    contribution=round(normalized_contrib, 4),
                    direction="increase",
                )
            )

        return attributions

    def _heuristic_attribution(self, feat_matrix: np.ndarray) -> dict[str, float]:
        """Fallback channel attribution based on feature magnitude deviations."""
        contributions: dict[str, float] = {ch: 0.0 for ch in self.channel_names}
        feat_sample = feat_matrix[0]
        for idx, feat_name in enumerate(self.feature_names):
            matched_channel = next((c for c in self.channel_names if feat_name.startswith(c)), feat_name)
            contributions[matched_channel] += float(np.abs(feat_sample[idx]))
        return contributions
