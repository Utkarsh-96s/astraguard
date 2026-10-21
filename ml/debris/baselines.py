"""Baselines and calibration utilities for Conjunction Data Message (CDM) sequences."""

import numpy as np
import xgboost as xgb
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

CDM_FEATURE_NAMES = [
    "time_to_tca_hours",
    "miss_distance_m",
    "relative_velocity_ms",
    "c_obs_b",
    "c_obs_t",
    "c_obs_n",
    "log10_pc",
]


class LatestCDMThresholdBaseline:
    """Operational physical screening baseline using only the latest CDM.

    Flags CRITICAL if the latest CDM miss distance is <= 1000m or Foster Pc >= 1e-4.
    """

    def __init__(self, miss_threshold_m: float = 1000.0, pc_threshold: float = 1e-4) -> None:
        self.miss_threshold_m = miss_threshold_m
        self.pc_threshold = pc_threshold
        self.is_fitted = True

    def fit(self, X_seq: np.ndarray, y: np.ndarray) -> "LatestCDMThresholdBaseline":
        return self

    def predict_proba(self, X_seq: np.ndarray) -> np.ndarray:
        """Predict probabilities based on latest CDM's log10_pc and miss distance.

        X_seq: (N, seq_len, num_features). Feature 1 = miss_distance_m, feature 6 = log10_pc.
        """
        N = X_seq.shape[0]
        probs = np.zeros((N, 2), dtype=np.float32)

        for i in range(N):
            latest_miss = float(X_seq[i, -1, 1])
            latest_log_pc = float(X_seq[i, -1, 6])

            # Sigmoid-based continuous probability centered at Foster threshold (1e-4)
            # or miss distance below 1000m
            score_pc = 1.0 / (1.0 + np.exp(-(latest_log_pc - (-4.0)) * 2.0))
            score_miss = 1.0 / (1.0 + np.exp((latest_miss - self.miss_threshold_m) / 500.0))
            prob_crit = float(np.clip(max(score_pc, score_miss), 0.001, 0.999))
            probs[i, 1] = prob_crit
            probs[i, 0] = 1.0 - prob_crit

        return probs

    def predict(self, X_seq: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X_seq)[:, 1]
        return (probs >= 0.5).astype(int)


class XGBoostSequenceBaseline:
    """Feature-engineered XGBoost baseline over temporal CDM sequences.

    Computes temporal summary statistics across CDM updates:
    - Latest values for each of the 7 features
    - Min miss distance across all updates
    - Max Pc (or max log10_pc)
    - Trend slope of miss distance (latest - first)
    - Trend slope of Pc
    - Final radial covariance (c_obs_b)
    """

    def __init__(self, n_estimators: int = 80, max_depth: int = 3, random_state: int = 42) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=0.08,
            random_state=random_state,
            eval_metric="logloss",
        )
        self.is_fitted = False

    def _extract_sequence_features(self, X_seq: np.ndarray) -> np.ndarray:
        """Extract tabular summary features from 3D CDM sequence array (N, seq_len, 7)."""
        N, _seq_len, _n_feat = X_seq.shape
        feature_rows: list[np.ndarray] = []

        for i in range(N):
            seq = X_seq[i]  # (seq_len, 7)
            latest = seq[-1]  # 7 features
            min_miss = np.min(seq[:, 1])
            max_log_pc = np.max(seq[:, 6])
            miss_slope = (seq[-1, 1] - seq[0, 1]) / max(1.0, (seq[0, 0] - seq[-1, 0]))
            pc_slope = (seq[-1, 6] - seq[0, 6]) / max(1.0, (seq[0, 0] - seq[-1, 0]))
            mean_b = np.mean(seq[:, 3])

            row = np.concatenate([latest, [min_miss, max_log_pc, miss_slope, pc_slope, mean_b]])
            feature_rows.append(row)

        return np.array(feature_rows, dtype=np.float32)

    def fit(self, X_seq: np.ndarray, y: np.ndarray) -> "XGBoostSequenceBaseline":
        X_tab = self._extract_sequence_features(X_seq)
        self.model.fit(X_tab, y)
        self.is_fitted = True
        return self

    def predict_proba(self, X_seq: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("XGBoostSequenceBaseline is not fitted yet.")
        X_tab = self._extract_sequence_features(X_seq)
        return self.model.predict_proba(X_tab)

    def predict(self, X_seq: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X_seq)[:, 1]
        return (probs >= 0.5).astype(int)


class DebrisProbabilityCalibrator:
    """Probability calibration engine using Platt scaling and temperature scaling.

    Calculates Expected Calibration Error (ECE) and Brier Score.
    """

    def __init__(self, n_bins: int = 10) -> None:
        self.n_bins = n_bins
        self.temp: float = 1.0
        self.platt_a: float = 1.0
        self.platt_b: float = 0.0
        self.is_calibrated: bool = False

    def fit(self, uncalibrated_probs: np.ndarray, y_true: np.ndarray) -> "DebrisProbabilityCalibrator":
        """Fit Platt scaling parameters via logistic regression on log-odds."""
        probs = np.clip(uncalibrated_probs, 1e-6, 1.0 - 1e-6)
        log_odds = np.log(probs / (1.0 - probs))

        from sklearn.linear_model import LogisticRegression

        lr = LogisticRegression(solver="lbfgs")
        lr.fit(log_odds.reshape(-1, 1), y_true)

        self.platt_a = float(lr.coef_[0, 0])
        self.platt_b = float(lr.intercept_[0])
        self.is_calibrated = True
        return self

    def calibrate(self, uncalibrated_probs: np.ndarray) -> np.ndarray:
        """Apply fitted Platt scaling to uncalibrated probabilities."""
        if not self.is_calibrated:
            return uncalibrated_probs

        probs = np.clip(uncalibrated_probs, 1e-6, 1.0 - 1e-6)
        log_odds = np.log(probs / (1.0 - probs))
        calibrated_log_odds = self.platt_a * log_odds + self.platt_b
        return 1.0 / (1.0 + np.exp(-calibrated_log_odds))

    @staticmethod
    def compute_ece(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error (ECE) over confidence bins."""
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        total_samples = len(probs)

        for b in range(n_bins):
            low, high = bin_edges[b], bin_edges[b + 1]
            mask = (probs >= low) & (probs < high) if b < n_bins - 1 else (probs >= low) & (probs <= high)
            bin_count = int(np.sum(mask))
            if bin_count > 0:
                bin_acc = float(np.mean(y_true[mask]))
                bin_conf = float(np.mean(probs[mask]))
                ece += (bin_count / total_samples) * abs(bin_acc - bin_conf)

        return float(ece)

    @staticmethod
    def compute_brier_score(probs: np.ndarray, y_true: np.ndarray) -> float:
        """Compute Brier Score (Mean Squared Error in probability space)."""
        return float(brier_score_loss(y_true, probs))

    @staticmethod
    def evaluate_model(probs: np.ndarray, y_true: np.ndarray) -> dict[str, float]:
        """Compute full suite of classification and calibration metrics."""
        roc_auc = float(roc_auc_score(y_true, probs))
        pr_auc = float(average_precision_score(y_true, probs))
        brier = DebrisProbabilityCalibrator.compute_brier_score(probs, y_true)
        ece = DebrisProbabilityCalibrator.compute_ece(probs, y_true)
        binary_preds = (probs >= 0.5).astype(int)
        acc = float(np.mean(binary_preds == y_true))

        return {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4),
            "accuracy": round(acc, 4),
        }


__all__ = [
    "CDM_FEATURE_NAMES",
    "DebrisProbabilityCalibrator",
    "LatestCDMThresholdBaseline",
    "XGBoostSequenceBaseline",
]
