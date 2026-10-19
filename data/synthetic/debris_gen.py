"""Synthetic debris encounter and CDM generator.

Generates realistic close approaches between a primary asset and secondary space debris,
including time-to-TCA progressions with evolving collision probabilities (Pc).
All records are marked with synthetic=True.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd


def generate_conjunction_event(
    primary_id: str = "ASSET-SAT-01",
    secondary_id: int = 99824,
    tca: datetime | None = None,
    miss_distance_km: float = 0.420,
    relative_velocity_kms: float = 14.2,
    pc: float = 1.8e-4,
    synthetic: bool = True,
) -> dict[str, Any]:
    """Generate a single Conjunction entity record."""
    if tca is None:
        tca = datetime.now(UTC) + timedelta(hours=18)

    # Classify risk level
    if pc >= 1e-4:
        risk_class = "CRITICAL"
    elif pc >= 1e-5:
        risk_class = "HIGH"
    elif pc >= 1e-6:
        risk_class = "MEDIUM"
    else:
        risk_class = "LOW"

    return {
        "id": f"CONJ-{primary_id}-{secondary_id}-{int(tca.timestamp())}",
        "primary_id": primary_id,
        "secondary_id": secondary_id,
        "tca": tca,
        "miss_km": float(miss_distance_km),
        "rel_vel_kms": float(relative_velocity_kms),
        "pc": float(pc),
        "pc_method": "foster_2d_screening",
        "risk_class": risk_class,
        "synthetic": synthetic,
    }


def generate_cdm_progression(
    conjunction_id: str = "CONJ-SAMPLE-01",
    tca: datetime | None = None,
    num_updates: int = 8,
    initial_pc: float = 1.2e-6,
    final_pc: float = 2.4e-4,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a series of Conjunction Data Messages (CDMs) leading up to TCA.
    
    Mimics real tracking campaigns where radar/optical updates refine the miss
    distance and cause collision probability to trend upward or downward.
    """
    rng = np.random.default_rng(seed)

    if tca is None:
        tca = datetime(2026, 10, 20, 12, 0, 0, tzinfo=UTC)

    # CDM updates from T-72h down to T-4h
    hours_before = np.geomspace(72.0, 4.0, num_updates)
    timestamps = [tca - timedelta(hours=float(h)) for h in hours_before]

    # Pc trending logarithmically from initial_pc to final_pc with sensor noise
    log_pcs = np.linspace(np.log10(initial_pc), np.log10(final_pc), num_updates)
    pcs = 10.0 ** (log_pcs + rng.normal(0, 0.15, num_updates))

    # Miss distance trending toward closest point
    miss_distances_m = np.linspace(4200.0, 310.0, num_updates) + rng.normal(0, 50.0, num_updates)
    rel_vel = 14.25 + rng.normal(0, 0.05, num_updates)

    records: list[dict[str, Any]] = []
    for i in range(num_updates):
        records.append({
            "cdm_id": f"{conjunction_id}-CDM-{i+1}",
            "created_at": timestamps[i],
            "tca": tca,
            "time_to_tca_hours": round(float(hours_before[i]), 2),
            "miss_distance_m": round(float(miss_distances_m[i]), 2),
            "relative_velocity_ms": round(float(rel_vel[i] * 1000.0), 1),
            "c_obs_b": float(rng.uniform(10.0, 50.0)),
            "c_obs_t": float(rng.uniform(10.0, 50.0)),
            "c_obs_n": float(rng.uniform(10.0, 50.0)),
            "pc": float(pcs[i]),
            "risk_level": "CRITICAL" if pcs[i] >= 1e-4 else ("WARNING" if pcs[i] >= 1e-5 else "WATCH"),
            "synthetic": True,
        })

    return pd.DataFrame(records)
