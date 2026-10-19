"""Spacecraft telemetry generator with configurable nominal behavior and fault injection.

Supported fault modes:
- 'drift': Gradual parameter drift (e.g., reaction wheel thermal runaway or current escalation).
- 'spike': Intermittent anomalous transient spikes.
- 'stuck': Sensor freeze (zero variance flatline).
All generated records carry synthetic=True per rules.md §1.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import numpy as np
import pandas as pd

FaultType = Literal["drift", "spike", "stuck"]


def generate_telemetry_series(
    asset_id: str = "ASSET-SAT-01",
    start_time: datetime | None = None,
    duration_minutes: int = 60,
    step_seconds: int = 10,
    fault_type: FaultType | None = None,
    fault_start_minute: int | None = 30,
    fault_channel: str = "wheel_temp",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a multi-channel time-series telemetry DataFrame."""
    rng = np.random.default_rng(seed)

    if start_time is None:
        start_time = datetime(2026, 10, 19, 0, 0, 0, tzinfo=UTC)

    total_steps = int((duration_minutes * 60) / step_seconds)
    timestamps = [start_time + timedelta(seconds=i * step_seconds) for i in range(total_steps)]

    # Base nominal physics models
    # Orbit period approx 96 min (typical 500-700km LEO)
    orbit_fraction = np.linspace(0, (duration_minutes / 96.0) * 2 * np.pi, total_steps)

    # 1. wheel_temp: base 22.0C with slight orbital thermal breathing
    wheel_temp = 22.0 + 1.5 * np.sin(orbit_fraction) + rng.normal(0, 0.2, total_steps)

    # 2. bus_current: base 13.5A with payload power switching noise
    bus_current = 13.5 + 0.8 * np.cos(orbit_fraction) + rng.normal(0, 0.15, total_steps)

    # 3. battery_v: 29.5V, discharges slightly during eclipse
    battery_v = 29.5 + 0.4 * np.sin(orbit_fraction) + rng.normal(0, 0.05, total_steps)

    # 4. gyro_rates: near zero with micro-vibrations
    gyro_x = rng.normal(0.015, 0.003, total_steps)
    gyro_y = rng.normal(0.012, 0.003, total_steps)
    gyro_z = rng.normal(0.018, 0.003, total_steps)

    # 5. sun_sensor: positive in sunlight, 0 in eclipse
    sun_intensity = np.maximum(0.0, 1361.0 * np.sin(orbit_fraction) + rng.normal(0, 10.0, total_steps))

    # Apply fault injections if specified
    if fault_type and fault_start_minute is not None:
        fault_start_idx = int((fault_start_minute * 60) / step_seconds)
        if 0 <= fault_start_idx < total_steps:
            if fault_type == "drift":
                # Linear increase over time
                drift_steps = total_steps - fault_start_idx
                drift_ramp = np.linspace(0, 15.0, drift_steps)
                if fault_channel == "wheel_temp":
                    wheel_temp[fault_start_idx:] += drift_ramp
                elif fault_channel == "bus_current":
                    bus_current[fault_start_idx:] += drift_ramp * 0.5
            elif fault_type == "spike":
                # Injected sharp transient pulses
                num_spikes = max(2, (total_steps - fault_start_idx) // 10)
                spike_indices = rng.choice(np.arange(fault_start_idx, total_steps), size=num_spikes, replace=False)
                if fault_channel == "bus_current":
                    bus_current[spike_indices] += rng.uniform(8.0, 14.0, size=num_spikes)
                elif fault_channel == "wheel_temp":
                    wheel_temp[spike_indices] += rng.uniform(10.0, 20.0, size=num_spikes)
            elif fault_type == "stuck":
                # Sensor freezing at current value with 0 variance
                frozen_val = float(wheel_temp[fault_start_idx] if fault_channel == "wheel_temp" else gyro_x[fault_start_idx])
                if fault_channel == "wheel_temp":
                    wheel_temp[fault_start_idx:] = frozen_val
                elif fault_channel == "gyro_rate_x":
                    gyro_x[fault_start_idx:] = frozen_val

    # Structure into flat telemetry rows
    records: list[dict[str, Any]] = []
    channels = {
        "wheel_temp": wheel_temp,
        "bus_current": bus_current,
        "battery_v": battery_v,
        "gyro_rate_x": gyro_x,
        "gyro_rate_y": gyro_y,
        "gyro_rate_z": gyro_z,
        "sun_sensor": sun_intensity,
    }

    for i, ts in enumerate(timestamps):
        for ch_name, series in channels.items():
            records.append({
                "asset_id": asset_id,
                "ts": ts,
                "channel": ch_name,
                "value": float(series[i]),
                "quality": 1.0,
                "synthetic": True,
            })

    return pd.DataFrame(records)
