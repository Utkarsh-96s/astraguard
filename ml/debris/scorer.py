"""Debris collision risk scoring and mapping functions."""
import numpy as np


def compute_debris_risk_score(
    pc: float,
    miss_distance_m: float,
    time_to_tca_hours: float,
) -> float:
    """Map collision probability, miss distance, and time-to-TCA to normalized risk score r_d in [0.0, 1.0].

    Adheres strictly to architecture.md §5.2 and §5.4:
    - Pc >= 1e-4 forces r_d >= 0.90 (hard override to CRITICAL)
    - Pc >= 1e-3 forces r_d = 1.00
    - Pc < 1e-7 maps to ~0.00 (NOMINAL)
    """
    if pc <= 0.0:
        return 0.0

    log_pc = float(np.log10(max(pc, 1e-12)))

    # 1. Base score from log10(Pc)
    if log_pc < -7.0:
        base_score = 0.0
    elif log_pc < -5.0:
        # Range [-7.0, -5.0) -> [0.00, 0.35)
        base_score = 0.35 * ((log_pc - (-7.0)) / 2.0)
    elif log_pc < -4.0:
        # Range [-5.0, -4.0) -> [0.35, 0.89)  (WATCH -> WARNING)
        base_score = 0.35 + 0.54 * (log_pc - (-5.0))
    elif log_pc < -3.0:
        # Range [-4.0, -3.0) -> [0.90, 1.00)  (CRITICAL)
        base_score = 0.90 + 0.10 * (log_pc - (-4.0))
    else:
        # log_pc >= -3.0 -> 1.00
        base_score = 1.0

    # 2. Modulate by miss distance (<1 km raises risk slightly, >5 km lowers)
    miss_factor = 0.0
    if miss_distance_m < 500.0 and base_score < 0.90:
        miss_factor = 0.05 * (1.0 - (miss_distance_m / 500.0))

    # 3. Urgency modulation if TCA is imminent (<24 hours remaining)
    urgency_boost = 0.0
    if time_to_tca_hours < 24.0 and base_score >= 0.35 and base_score < 0.90:
        urgency_boost = 0.05 * (1.0 - (time_to_tca_hours / 24.0))

    final_score = base_score + miss_factor + urgency_boost

    # Hard override: If Pc >= 1e-4, final score must be >= 0.90
    if pc >= 1.0e-4:
        final_score = max(final_score, 0.90)

    return float(np.clip(round(final_score, 4), 0.0, 1.0))
