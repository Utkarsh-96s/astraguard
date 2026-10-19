"""Tests for Phase 1 synthetic data generators."""
import numpy as np
from data.synthetic.debris_gen import generate_cdm_progression, generate_conjunction_event
from data.synthetic.disaster_gen import (
    compute_observation_priority,
    generate_synthetic_chip_arrays,
)
from data.synthetic.telemetry_gen import generate_telemetry_series


def test_telemetry_nominal_generation() -> None:
    """Test nominal telemetry generation without faults."""
    df = generate_telemetry_series(
        asset_id="SAT-TEST-1",
        duration_minutes=30,
        step_seconds=10,
        fault_type=None,
    )
    assert len(df) == 180 * 7  # 180 steps * 7 channels
    assert set(df["channel"].unique()) == {
        "wheel_temp", "bus_current", "battery_v",
        "gyro_rate_x", "gyro_rate_y", "gyro_rate_z", "sun_sensor"
    }
    assert (df["synthetic"] == True).all()  # noqa: E712


def test_telemetry_drift_fault_injection() -> None:
    """Test drift injection causes higher temperature than baseline."""
    df_nominal = generate_telemetry_series(duration_minutes=60, fault_type=None, seed=42)
    df_drift = generate_telemetry_series(duration_minutes=60, fault_type="drift", fault_start_minute=30, seed=42)

    nom_end_temp = df_nominal[(df_nominal["channel"] == "wheel_temp")].iloc[-1]["value"]
    drift_end_temp = df_drift[(df_drift["channel"] == "wheel_temp")].iloc[-1]["value"]

    assert drift_end_temp > nom_end_temp + 5.0


def test_debris_conjunction_generation() -> None:
    """Test conjunction event generation and risk classification."""
    crit_event = generate_conjunction_event(pc=2.5e-4)
    assert crit_event["risk_class"] == "CRITICAL"
    assert crit_event["synthetic"] is True

    med_event = generate_conjunction_event(pc=5.0e-6)
    assert med_event["risk_class"] == "MEDIUM"

    cdm_df = generate_cdm_progression(num_updates=6)
    assert len(cdm_df) == 6
    assert cdm_df["time_to_tca_hours"].iloc[0] > cdm_df["time_to_tca_hours"].iloc[-1]


def test_disaster_observation_priority() -> None:
    """Test observation priority calculation bounds and properties."""
    score_high = compute_observation_priority(area_km2=600.0, hours_ago=1.0, cloud_pct=5.0)
    score_low = compute_observation_priority(area_km2=20.0, hours_ago=70.0, cloud_pct=95.0)

    assert 0.0 <= score_high <= 1.0
    assert 0.0 <= score_low <= 1.0
    assert score_high > score_low


def test_synthetic_chip_generation() -> None:
    """Test synthetic SAR chip and mask dimensions and pixel values."""
    img, mask = generate_synthetic_chip_arrays(size=64, water_ratio=0.30)
    assert img.shape == (64, 64)
    assert mask.shape == (64, 64)
    assert set(np.unique(mask)).issubset({0, 1})
    assert 0.15 < (mask == 1).mean() < 0.45
