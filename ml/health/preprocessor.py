"""Telemetry preprocessing, robust scaling, sliding window generation, and feature extraction."""
import numpy as np
import pandas as pd

CORE_CHANNELS = [
    "wheel_temp",
    "bus_current",
    "battery_v",
    "gyro_rate_x",
    "gyro_rate_y",
    "gyro_rate_z",
    "sun_sensor",
]


class TelemetryRobustScaler:
    """Robust scaler using per-channel median and Interquartile Range (IQR).

    Fit exclusively on nominal telemetry to avoid data leakage (rules.md §5).
    """

    def __init__(self, eps: float = 1e-6) -> None:
        self.eps = eps
        self.medians: dict[str, float] = {}
        self.iqrs: dict[str, float] = {}
        self.channel_names: list[str] = []
        self.is_fitted = False

    def fit(self, data: np.ndarray, channel_names: list[str]) -> "TelemetryRobustScaler":
        """Fit median and IQR per channel on nominal data array of shape (N, C)."""
        self.channel_names = list(channel_names)
        num_channels = data.shape[1]
        for i in range(num_channels):
            col = data[:, i]
            median = float(np.median(col))
            q75, q25 = np.percentile(col, [75, 25])
            iqr = float(q75 - q25)
            if iqr < self.eps:
                iqr = float(np.std(col)) + self.eps
            name = channel_names[i]
            self.medians[name] = median
            self.iqrs[name] = iqr
        self.is_fitted = True
        return self

    def transform(self, data: np.ndarray, channel_names: list[str] | None = None) -> np.ndarray:
        """Transform data array (N, C) or (N, W, C) using fitted median and IQR."""
        if not self.is_fitted:
            raise RuntimeError("TelemetryRobustScaler is not fitted yet.")

        names = channel_names or self.channel_names
        scaled = np.zeros_like(data, dtype=np.float32)

        if data.ndim == 2:
            for i, name in enumerate(names):
                med = self.medians.get(name, 0.0)
                iqr = self.iqrs.get(name, 1.0)
                scaled[:, i] = (data[:, i] - med) / (iqr + self.eps)
        elif data.ndim == 3:
            for i, name in enumerate(names):
                med = self.medians.get(name, 0.0)
                iqr = self.iqrs.get(name, 1.0)
                scaled[:, :, i] = (data[:, :, i] - med) / (iqr + self.eps)
        else:
            raise ValueError(f"Expected 2D or 3D array, got ndim={data.ndim}")

        return scaled

    def inverse_transform(self, data: np.ndarray, channel_names: list[str] | None = None) -> np.ndarray:
        """Revert scaled data back to engineering units."""
        if not self.is_fitted:
            raise RuntimeError("TelemetryRobustScaler is not fitted yet.")

        names = channel_names or self.channel_names
        unscaled = np.zeros_like(data, dtype=np.float32)

        if data.ndim == 2:
            for i, name in enumerate(names):
                med = self.medians.get(name, 0.0)
                iqr = self.iqrs.get(name, 1.0)
                unscaled[:, i] = (data[:, i] * (iqr + self.eps)) + med
        elif data.ndim == 3:
            for i, name in enumerate(names):
                med = self.medians.get(name, 0.0)
                iqr = self.iqrs.get(name, 1.0)
                unscaled[:, :, i] = (data[:, :, i] * (iqr + self.eps)) + med
        return unscaled


def pivot_telemetry_dataframe(
    df: pd.DataFrame,
    channels: list[str] | None = None,
    freq: str = "10s",
) -> tuple[np.ndarray, pd.DatetimeIndex, list[str]]:
    """Convert long-form telemetry DataFrame to aligned 2D numpy matrix.

    Handles forward-filling with limit, backward-filling edges, and ensures fixed Δt.
    Returns:
        matrix: 2D array of shape (T, num_channels)
        time_index: DatetimeIndex of rows
        channel_names: Ordered list of channel names
    """
    target_channels = channels or CORE_CHANNELS
    sub_df = df[df["channel"].isin(target_channels)].copy()
    if not pd.api.types.is_datetime64_any_dtype(sub_df["ts"]):
        sub_df["ts"] = pd.to_datetime(sub_df["ts"])

    pivoted = sub_df.pivot_table(index="ts", columns="channel", values="value", aggfunc="mean")

    # Resample to uniform time series
    resampled = pivoted.resample(freq).mean()
    resampled = resampled.ffill(limit=6).bfill()

    # Reindex columns to target channels order, filling missing channels with 0.0
    for ch in target_channels:
        if ch not in resampled.columns:
            resampled[ch] = 0.0
    resampled = resampled[target_channels]

    matrix = resampled.values.astype(np.float32)
    return matrix, resampled.index, target_channels


def create_sliding_windows(
    data: np.ndarray,
    window_size: int = 64,
    step: int = 1,
) -> np.ndarray:
    """Slice 2D matrix (T, C) into overlapping 3D sliding windows (num_windows, window_size, C)."""
    t_len, num_channels = data.shape
    if t_len < window_size:
        # If less than window_size, pad with first element
        pad_len = window_size - t_len
        pad = np.repeat(data[:1], pad_len, axis=0)
        data = np.vstack([pad, data])
        t_len = data.shape[0]

    num_windows = (t_len - window_size) // step + 1
    windows = np.zeros((num_windows, window_size, num_channels), dtype=np.float32)

    for i in range(num_windows):
        start = i * step
        windows[i] = data[start : start + window_size]

    return windows


def extract_window_features(
    windows: np.ndarray,
    channel_names: list[str],
) -> tuple[np.ndarray, list[str]]:
    """Extract statistical and spectral features per window for tabular baseline models.

    For each channel:
      - mean
      - std
      - min
      - max
      - slope (trend over window)
      - fft_low (low-frequency power)
      - fft_high (high-frequency power)

    Args:
        windows: 3D array of shape (N, W, C)
        channel_names: List of C channel names

    Returns:
        feature_matrix: 2D array of shape (N, C * 7)
        feature_names: List of C * 7 feature names
    """
    _n_windows, w_len, _n_channels = windows.shape
    feature_list: list[np.ndarray] = []
    feature_names: list[str] = []

    time_vec = np.linspace(0.0, 1.0, w_len)
    time_centered = time_vec - time_vec.mean()
    time_var = np.sum(time_centered**2) + 1e-8

    for c_idx, ch in enumerate(channel_names):
        ch_series = windows[:, :, c_idx]  # Shape (N, W)

        # 1. Mean
        ch_mean = np.mean(ch_series, axis=1)
        feature_list.append(ch_mean)
        feature_names.append(f"{ch}_mean")

        # 2. Std
        ch_std = np.std(ch_series, axis=1)
        feature_list.append(ch_std)
        feature_names.append(f"{ch}_std")

        # 3. Min
        ch_min = np.min(ch_series, axis=1)
        feature_list.append(ch_min)
        feature_names.append(f"{ch}_min")

        # 4. Max
        ch_max = np.max(ch_series, axis=1)
        feature_list.append(ch_max)
        feature_names.append(f"{ch}_max")

        # 5. Slope (Linear regression gradient over window)
        centered_series = ch_series - ch_mean[:, None]
        slope = np.sum(centered_series * time_centered[None, :], axis=1) / time_var
        feature_list.append(slope)
        feature_names.append(f"{ch}_slope")

        # 6 & 7. FFT Low and High frequency bands
        fft_vals = np.abs(np.fft.rfft(ch_series, axis=1))[:, 1:]  # Drop DC component
        mid_idx = max(1, fft_vals.shape[1] // 2)
        fft_low = np.mean(fft_vals[:, :mid_idx], axis=1)
        fft_high = np.mean(fft_vals[:, mid_idx:], axis=1) if fft_vals.shape[1] > mid_idx else fft_low
        feature_list.append(fft_low)
        feature_names.append(f"{ch}_fft_low")
        feature_list.append(fft_high)
        feature_names.append(f"{ch}_fft_high")

    feature_matrix = np.column_stack(feature_list).astype(np.float32)
    return feature_matrix, feature_names
