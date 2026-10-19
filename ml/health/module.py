"""Integrated Spacecraft Health Risk Module implementing RiskModule protocol."""
from datetime import UTC, datetime
from typing import Any, Literal

import numpy as np
import pandas as pd

from ml.common.schemas import Attribution, ModuleResult
from ml.health.calibrator import PersistenceFilter
from ml.health.isoforest import IsolationForestBaseline
from ml.health.lstm_ae import LSTMAutoencoder
from ml.health.preprocessor import (
    CORE_CHANNELS,
    TelemetryRobustScaler,
    create_sliding_windows,
    pivot_telemetry_dataframe,
)


class HealthRiskModule:
    """Spacecraft Health AI module implementing the unified RiskModule contract."""

    name: str = "Spacecraft Health AI"
    version: str = "0.1.0"

    def __init__(
        self,
        active_engine: Literal["lstm", "isoforest"] = "lstm",
        window_size: int = 64,
        window_step: int = 1,
        persistence_n: int = 5,
        persistence_k: int = 3,
        persistence_threshold: float = 0.50,
    ) -> None:
        self.active_engine = active_engine
        self.window_size = window_size
        self.window_step = window_step
        self.channel_names = list(CORE_CHANNELS)

        self.scaler = TelemetryRobustScaler()
        self.lstm_model = LSTMAutoencoder()
        self.isoforest_model = IsolationForestBaseline()
        self.persistence_filter = PersistenceFilter(
            n=persistence_n,
            k=persistence_k,
            threshold=persistence_threshold,
        )
        self.is_fitted: bool = False

    def fit(self, data: pd.DataFrame | np.ndarray) -> None:
        """Fit scaler, LSTM autoencoder, and IsoForest baseline on nominal telemetry."""
        if isinstance(data, pd.DataFrame):
            matrix, _, channels = pivot_telemetry_dataframe(data, channels=self.channel_names)
            self.channel_names = channels
            # Fit scaler strictly on nominal data
            self.scaler.fit(matrix, self.channel_names)
            scaled_matrix = self.scaler.transform(matrix, self.channel_names)
            windows = create_sliding_windows(
                scaled_matrix, window_size=self.window_size, step=self.window_step
            )
        else:
            # Assume 3D array of shape (N, W, C) already scaled or 2D (T, C)
            if data.ndim == 2:
                self.scaler.fit(data, self.channel_names)
                scaled_matrix = self.scaler.transform(data, self.channel_names)
                windows = create_sliding_windows(
                    scaled_matrix, window_size=self.window_size, step=self.window_step
                )
            else:
                windows = data

        # Train both models
        self.lstm_model.fit(windows, self.channel_names)
        self.isoforest_model.fit(windows, self.channel_names)
        self.is_fitted = True

    def score(self, window: Any, asset_id: str = "SAT-DEFAULT", ts: datetime | None = None) -> ModuleResult:
        """Score a sliding window and return a standardized ModuleResult."""
        if not self.is_fitted:
            raise RuntimeError("HealthRiskModule must be fitted before scoring.")

        win_arr = self._resolve_window(window)
        timestamp = ts or datetime.now(UTC)

        # Evaluate via selected engine
        if self.active_engine == "lstm":
            raw_score, _raw_err, evidence = self.lstm_model.predict_window(win_arr)
        else:
            raw_score, _raw_err, evidence = self.isoforest_model.predict_window(win_arr)

        # Apply persistence filter
        effective_score, is_sustained, count_above = self.persistence_filter.update(
            asset_id=asset_id, raw_score=raw_score
        )

        evidence["is_sustained"] = is_sustained
        evidence["persistence_count"] = count_above
        evidence["instantaneous_score"] = raw_score
        evidence["active_engine"] = self.active_engine

        # Confidence: higher when residual is well outside ambiguous transition zones
        confidence = 0.95 if (effective_score < 0.25 or effective_score > 0.70) else 0.85

        return ModuleResult(
            score=round(effective_score, 4),
            confidence=round(confidence, 2),
            evidence=evidence,
            ts=timestamp,
            asset_id=asset_id,
            synthetic=True,
        )

    def explain(self, window: Any, result: ModuleResult | None = None) -> list[Attribution]:
        """Produce top channel-level attributions explaining the risk score."""
        if not self.is_fitted:
            raise RuntimeError("HealthRiskModule must be fitted before producing explanations.")

        win_arr = self._resolve_window(window)
        if self.active_engine == "lstm":
            return self.lstm_model.explain_window(win_arr)
        return self.isoforest_model.explain_window(win_arr)

    def _resolve_window(self, window: Any) -> np.ndarray:
        """Helper to convert DataFrame or array into scaled 3D window (1, W, C)."""
        if isinstance(window, pd.DataFrame):
            matrix, _, channels = pivot_telemetry_dataframe(window, channels=self.channel_names)
            scaled = self.scaler.transform(matrix, channels)
            win_3d = create_sliding_windows(scaled, window_size=self.window_size, step=1)
            return win_3d[-1:]  # Return most recent window
        arr = np.asarray(window, dtype=np.float32)
        if arr.ndim == 2:
            return arr[None, :, :]
        return arr
