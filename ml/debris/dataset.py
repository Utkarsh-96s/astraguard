"""Dataset loader and synthetic generator for ESA Kelvins CDM sequences."""
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np

CDM_FEATURE_NAMES = [
    "time_to_tca_hours",
    "miss_distance_m",
    "relative_velocity_ms",
    "c_obs_b",
    "c_obs_t",
    "c_obs_n",
    "log10_pc",
]


def generate_kelvins_cdm_dataset(
    num_events: int = 120,
    seq_len: int = 10,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]], str]:
    """Generate a multi-event CDM progression dataset modeling ESA Kelvins conjunction sequences.

    Each event consists of seq_len sequential CDM updates leading up to TCA (from T-72h down to T-4h).
    Roughly 35% of events represent critical conjunctions (Pc >= 1e-4, miss distance < 1000m)
    where covariance contracts onto an elevated risk profile.

    Returns:
        X_seq: Array shaped (num_events, seq_len, 7).
        y: Binary labels shaped (num_events,), where 1 = CRITICAL conjunction.
        event_metadata: List of dicts describing each conjunction encounter.
        data_hash: Deterministic SHA-256 hash of dataset.
    """
    rng = np.random.default_rng(seed)
    X_seq = np.zeros((num_events, seq_len, len(CDM_FEATURE_NAMES)), dtype=np.float32)
    y = np.zeros(num_events, dtype=np.float32)
    metadata: list[dict[str, Any]] = []

    # Normalized time progression: geomspace from 72h down to 4h
    hours_before = np.geomspace(72.0, 4.0, seq_len)

    for i in range(num_events):
        is_critical = 1 if (i % 3 == 0) else 0
        y[i] = float(is_critical)

        tca = datetime(2026, 10, 25, 0, 0, 0, tzinfo=UTC) + timedelta(hours=i * 6)
        conjunction_id = f"CONJ-KELVINS-{i+1:04d}"

        if is_critical:
            # Trajectory converging to dangerous close approach
            start_miss = float(rng.uniform(3000.0, 6000.0))
            end_miss = float(rng.uniform(150.0, 850.0))
            start_pc = float(rng.uniform(1e-7, 5e-6))
            end_pc = float(rng.uniform(1.2e-4, 8.5e-4))
        else:
            # Safe divergence or harmless flyby
            start_miss = float(rng.uniform(4000.0, 12000.0))
            end_miss = float(rng.uniform(2500.0, 18000.0))
            start_pc = float(rng.uniform(1e-9, 1e-6))
            end_pc = float(rng.uniform(1e-9, 4e-5))

        miss_profile = np.linspace(start_miss, end_miss, seq_len) + rng.normal(0, 40.0, seq_len)
        miss_profile = np.clip(miss_profile, 50.0, 50000.0)

        log_pcs = np.linspace(np.log10(start_pc), np.log10(end_pc), seq_len) + rng.normal(0, 0.1, seq_len)
        log_pcs = np.clip(log_pcs, -12.0, -2.0)

        rel_vel = float(rng.uniform(11.5, 15.2)) * 1000.0  # m/s

        # Covariance terms (B, T, N standard deviations in meters)
        # In real radar tracking, uncertainties contract as TCA nears
        c_b_start = float(rng.uniform(40.0, 120.0))
        c_b_end = float(rng.uniform(10.0, 35.0))
        c_b = np.linspace(c_b_start, c_b_end, seq_len) + rng.normal(0, 2.0, seq_len)

        c_t = np.linspace(float(rng.uniform(80.0, 250.0)), float(rng.uniform(25.0, 70.0)), seq_len)
        c_n = np.linspace(float(rng.uniform(50.0, 150.0)), float(rng.uniform(15.0, 45.0)), seq_len)

        for step in range(seq_len):
            X_seq[i, step, 0] = float(hours_before[step])
            X_seq[i, step, 1] = float(miss_profile[step])
            X_seq[i, step, 2] = float(rel_vel + rng.normal(0, 5.0))
            X_seq[i, step, 3] = float(max(5.0, c_b[step]))
            X_seq[i, step, 4] = float(max(10.0, c_t[step]))
            X_seq[i, step, 5] = float(max(5.0, c_n[step]))
            X_seq[i, step, 6] = float(log_pcs[step])

        metadata.append(
            {
                "conjunction_id": conjunction_id,
                "is_critical": bool(is_critical),
                "tca": tca.isoformat(),
                "final_miss_distance_m": round(float(miss_profile[-1]), 1),
                "final_pc": float(10.0 ** log_pcs[-1]),
                "final_log10_pc": round(float(log_pcs[-1]), 3),
            }
        )

    # Compute deterministic SHA-256 hash of dataset
    hasher = hashlib.sha256()
    hasher.update(X_seq.tobytes())
    hasher.update(y.tobytes())
    data_hash = hasher.hexdigest()

    return X_seq, y, metadata, data_hash


__all__ = ["CDM_FEATURE_NAMES", "generate_kelvins_cdm_dataset"]
