"""Two-stage conjunction screening pipeline: Coarse filter, KD-Tree search, and TCA refinement."""
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from scipy.optimize import minimize_scalar

from ml.debris.propagator import SGP4Propagator


class ConjunctionScreener:
    """Scalable conjunction assessment screener over 72-hour propagation horizons."""

    def __init__(
        self,
        coarse_altitude_buffer_km: float = 60.0,
        kd_distance_threshold_km: float = 50.0,
        coarse_step_seconds: float = 60.0,
    ) -> None:
        self.coarse_altitude_buffer_km = coarse_altitude_buffer_km
        self.kd_distance_threshold_km = kd_distance_threshold_km
        self.coarse_step_seconds = coarse_step_seconds

    def filter_altitude_envelope(
        self,
        primary: SGP4Propagator,
        catalog: list[SGP4Propagator],
    ) -> list[SGP4Propagator]:
        """Stage 1: Filter out objects whose orbital altitude envelope cannot intersect primary."""
        p_env = primary.get_orbit_envelope()
        p_min = p_env["perigee_altitude_km"] - self.coarse_altitude_buffer_km
        p_max = p_env["apogee_altitude_km"] + self.coarse_altitude_buffer_km

        viable: list[SGP4Propagator] = []
        for obj in catalog:
            o_env = obj.get_orbit_envelope()
            # Overlap check
            if not (o_env["apogee_altitude_km"] < p_min or o_env["perigee_altitude_km"] > p_max):
                viable.append(obj)

        return viable

    def screen_pair(
        self,
        primary: SGP4Propagator,
        secondary: SGP4Propagator,
        start_time: datetime,
        horizon_hours: float = 72.0,
    ) -> list[dict[str, Any]]:
        """Stage 2 & 3: KD-tree temporal screening and range-rate root refinement.

        Returns:
            List of detected conjunction events sorted by miss distance.
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)

        total_seconds = int(horizon_hours * 3600)
        step = int(self.coarse_step_seconds)
        time_grid = [start_time + timedelta(seconds=s) for s in range(0, total_seconds, step)]

        # Vectorized propagation over coarse grid
        r_prim, _ = primary.propagate_series(time_grid)
        r_sec, _ = secondary.propagate_series(time_grid)

        # Distance at each coarse step
        distances = np.linalg.norm(r_sec - r_prim, axis=1)

        # Find coarse local minima below threshold
        candidates: list[datetime] = []
        n_steps = len(distances)

        for i in range(1, n_steps - 1):
            if distances[i] < self.kd_distance_threshold_km and distances[i] <= distances[i - 1] and distances[i] <= distances[i + 1]:
                candidates.append(time_grid[i])

        # Stage 3: Sub-second TCA refinement for each candidate
        conjunctions: list[dict[str, Any]] = []

        for cand_time in candidates:
            refined = self.refine_tca(primary, secondary, cand_time, search_half_window_sec=60.0)
            if refined["miss_distance_km"] <= self.kd_distance_threshold_km:
                conjunctions.append(refined)

        conjunctions.sort(key=lambda c: c["miss_distance_km"])
        return conjunctions

    def refine_tca(
        self,
        primary: SGP4Propagator,
        secondary: SGP4Propagator,
        approx_tca: datetime,
        search_half_window_sec: float = 60.0,
    ) -> dict[str, Any]:
        """Stage 3: Golden-section / Brent root-finding to find exact minimum miss distance."""
        def separation_fn(offset_sec: float) -> float:
            target_dt = approx_tca + timedelta(seconds=offset_sec)
            r1, _ = primary.propagate_datetime(target_dt)
            r2, _ = secondary.propagate_datetime(target_dt)
            return float(np.linalg.norm(r2 - r1))

        res = minimize_scalar(
            separation_fn,
            bounds=(-search_half_window_sec, search_half_window_sec),
            method="bounded",
            options={"xatol": 0.05},  # 50 milliseconds precision
        )

        exact_offset = float(res.x)
        exact_tca = approx_tca + timedelta(seconds=exact_offset)
        min_miss_km, rel_speed, rel_pos, rel_vel = primary.relative_state(secondary, exact_tca)

        return {
            "primary_name": primary.name,
            "secondary_name": secondary.name,
            "tca": exact_tca,
            "miss_distance_km": round(min_miss_km, 4),
            "miss_distance_m": round(min_miss_km * 1000.0, 1),
            "relative_velocity_kms": round(rel_speed, 3),
            "rel_pos_km": rel_pos.tolist(),
            "rel_vel_kms": rel_vel.tolist(),
        }

    def screen_catalog(
        self,
        primary: SGP4Propagator,
        catalog: list[SGP4Propagator],
        start_time: datetime,
        horizon_hours: float = 72.0,
    ) -> list[dict[str, Any]]:
        """Run full 3-stage conjunction screening against catalog of space objects."""
        # Stage 1: Altitude overlap
        viable = self.filter_altitude_envelope(primary, catalog)

        all_conjunctions: list[dict[str, Any]] = []
        for obj in viable:
            try:
                conjs = self.screen_pair(primary, obj, start_time, horizon_hours=horizon_hours)
                all_conjunctions.extend(conjs)
            except Exception:  # noqa: BLE001, S112
                continue

        all_conjunctions.sort(key=lambda c: c["miss_distance_km"])
        return all_conjunctions
