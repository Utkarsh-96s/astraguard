"""Spacecraft telemetry statistical baselines: Rolling Z-Score and Isolation Forest."""

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from ml.common.schemas import Attribution
from ml.health.isoforest import IsolationForestBaseline


class BaselineDetectionResult(BaseModel):
    """Detection output from a statistical baseline."""
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized anomaly score")
    is_anomaly: bool = Field(..., description="Binary threshold decision")
    raw_metric: float = Field(..., description="Raw z-score or anomaly metric")
    channel_scores: dict[str, float] = Field(default_factory=dict, description="Per-channel deviation")
    attributions: list[Attribution] = Field(default_factory=list, description="Driver attributions")


class RollingZScoreDetector:
    """Rolling window Z-Score baseline for telemetry anomaly detection.

    Computes moving mean and standard deviation per channel over a historical window W.
    Flags an anomaly if max absolute z-score exceeds threshold sigma.
    """

    def __init__(
        self,
        window_size: int = 64,
        threshold_sigma: float = 3.0,
        channels: list[str] | None = None,
        min_std: float = 1e-4,
    ) -> None:
        self.window_size = window_size
        self.threshold_sigma = threshold_sigma
        self.channels = channels or [
            "wheel_temp",
            "bus_current",
            "battery_v",
            "gyro_rate_x",
            "gyro_rate_y",
            "gyro_rate_z",
            "sun_sensor",
        ]
        self.min_std = min_std
        self.means: dict[str, float] = {}
        self.stds: dict[str, float] = {}
        self.is_fitted = False

    def fit(self, df_nominal: pd.DataFrame) -> None:
        """Fit baseline nominal statistics (mean and std) per channel."""
        for ch in self.channels:
            ch_data = df_nominal[df_nominal["channel"] == ch]["value"].dropna().to_numpy()
            if len(ch_data) > 0:
                self.means[ch] = float(np.mean(ch_data))
                self.stds[ch] = float(max(np.std(ch_data), self.min_std))
            else:
                self.means[ch] = 0.0
                self.stds[ch] = 1.0
        self.is_fitted = True

    def score_window(self, window_df: pd.DataFrame) -> BaselineDetectionResult:
        """Compute rolling z-score for the latest time point or window mean."""
        channel_z: dict[str, float] = {}
        attributions: list[Attribution] = []

        for ch in self.channels:
            ch_df = window_df[window_df["channel"] == ch]
            if len(ch_df) == 0:
                channel_z[ch] = 0.0
                continue

            vals = ch_df["value"].to_numpy()
            mean = self.means.get(ch, float(np.mean(vals)))
            std = self.stds.get(ch, float(max(np.std(vals), self.min_std)))

            # Evaluate recent point deviation
            recent_val = float(vals[-1])
            z = abs(recent_val - mean) / max(std, self.min_std)
            channel_z[ch] = float(z)

            if z > 1.0:
                attributions.append(
                    Attribution(
                        driver=ch,
                        module="rolling_zscore",
                        contribution=float(min(1.0, z / 5.0)),
                        direction="increase",
                    )
                )

        # Sort attributions descending by contribution
        attributions.sort(key=lambda a: a.contribution, reverse=True)

        max_z = max(channel_z.values()) if channel_z else 0.0
        # Normalize score into [0, 1] using soft sigmoid mapping
        normalized_score = float(1.0 / (1.0 + np.exp(-(max_z - self.threshold_sigma))))
        is_anomaly = max_z >= self.threshold_sigma

        return BaselineDetectionResult(
            score=round(normalized_score, 4),
            is_anomaly=is_anomaly,
            raw_metric=round(max_z, 4),
            channel_scores=channel_z,
            attributions=attributions,
        )


__all__ = ["BaselineDetectionResult", "IsolationForestBaseline", "RollingZScoreDetector"]
