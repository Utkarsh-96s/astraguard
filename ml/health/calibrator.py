"""Score calibration to [0, 1] bounds and k-of-n persistence filtering."""
from collections import deque

import numpy as np


class HealthScoreCalibrator:
    """Calibrates raw reconstruction or model residual errors to normalized [0.0, 1.0] risk scores.

    Fitted on nominal training residuals using empirical percentiles.
    Guarantees monotonic increasing mapping: higher residual -> higher risk.
    """

    def __init__(self) -> None:
        self.p50: float = 0.0
        self.p90: float = 0.0
        self.p95: float = 0.0
        self.p99: float = 0.0
        self.p999: float = 0.0
        self.is_fitted: bool = False

    def fit(self, nominal_residuals: np.ndarray) -> "HealthScoreCalibrator":
        """Fit empirical percentiles on nominal validation/training residuals."""
        res = np.asarray(nominal_residuals, dtype=np.float64).flatten()
        if len(res) == 0:
            raise ValueError("Cannot fit calibrator on empty residuals array.")

        self.p50 = float(np.percentile(res, 50))
        self.p90 = float(np.percentile(res, 90))
        self.p95 = float(np.percentile(res, 95))
        self.p99 = float(np.percentile(res, 99))
        self.p999 = float(np.percentile(res, 99.9))

        # Enforce strict monotonicity across threshold anchors
        eps = 1e-6
        if self.p90 <= self.p50:
            self.p90 = self.p50 + eps
        if self.p95 <= self.p90:
            self.p95 = self.p90 + eps
        if self.p99 <= self.p95:
            self.p99 = self.p95 + eps
        if self.p999 <= self.p99:
            self.p999 = self.p99 + eps

        self.is_fitted = True
        return self

    def calibrate(self, residual: float | np.ndarray) -> np.ndarray:
        """Map raw residual to calibrated risk score in [0.0, 1.0]."""
        if not self.is_fitted:
            raise RuntimeError("HealthScoreCalibrator must be fitted before calibration.")

        r = np.asarray(residual, dtype=np.float64)
        is_scalar = r.ndim == 0
        r_flat = np.atleast_1d(r)

        # Monotonic piecewise linear interpolation with smooth asymptotic tail
        # Anchors:
        # r = 0.0      -> 0.00 (Perfect nominal)
        # r = p50      -> 0.15 (Median nominal noise)
        # r = p95      -> 0.40 (Upper nominal boundary / WATCH)
        # r = p99      -> 0.75 (Anomaly detection threshold / WARNING)
        # r = p999     -> 0.95 (Severe anomaly / CRITICAL)
        # r > p999     -> -> 1.0 (Saturation)

        scores = np.zeros_like(r_flat)

        for i, val in enumerate(r_flat):
            if val <= 0.0:
                scores[i] = 0.0
            elif val <= self.p50:
                scores[i] = 0.15 * (val / self.p50)
            elif val <= self.p95:
                scores[i] = 0.15 + 0.25 * ((val - self.p50) / (self.p95 - self.p50))
            elif val <= self.p99:
                scores[i] = 0.40 + 0.35 * ((val - self.p95) / (self.p99 - self.p95))
            elif val <= self.p999:
                scores[i] = 0.75 + 0.20 * ((val - self.p99) / (self.p999 - self.p99))
            else:
                # Exponential saturation towards 1.0
                excess = (val - self.p999) / (self.p999 - self.p99 + 1e-6)
                scores[i] = 0.95 + 0.05 * (1.0 - np.exp(-excess))

        scores = np.clip(scores, 0.0, 1.0)
        return scores[0] if is_scalar else scores


class PersistenceFilter:
    """k-of-n sliding window filter to suppress single-point false alarms.

    Requires at least k of the last n windows to exceed threshold before confirming persistent anomaly.
    """

    def __init__(self, n: int = 5, k: int = 3, threshold: float = 0.50) -> None:
        self.n = n
        self.k = k
        self.threshold = threshold
        self.buffers: dict[str, deque[float]] = {}

    def update(self, asset_id: str, raw_score: float) -> tuple[float, bool, int]:
        """Update window buffer and return: (effective_score, is_sustained, count_above)."""
        if asset_id not in self.buffers:
            self.buffers[asset_id] = deque(maxlen=self.n)

        buf = self.buffers[asset_id]
        buf.append(raw_score)

        count_above = sum(1 for s in buf if s >= self.threshold)
        is_sustained = count_above >= self.k

        if is_sustained:
            # Sustained anomaly: use max or recent mean of active high scores
            effective_score = float(np.mean([s for s in buf if s >= self.threshold]))
        else:
            # If not sustained, scale down transient isolated spike to prevent spurious alert
            effective_score = min(raw_score, self.threshold * 0.85) if count_above > 0 else raw_score

        return effective_score, is_sustained, count_above

    def reset(self, asset_id: str | None = None) -> None:
        """Reset history for a specific asset or all assets."""
        if asset_id:
            self.buffers.pop(asset_id, None)
        else:
            self.buffers.clear()
