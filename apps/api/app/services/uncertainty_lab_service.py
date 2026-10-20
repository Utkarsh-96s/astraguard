"""Conjunction Uncertainty Lab & B-Plane Monte Carlo Service.

Implements F3: Conjunction Uncertainty Lab.
Computes 2-D B-Plane encounter geometry, covariance error ellipses (1-sigma, 2-sigma, 3-sigma),
and executes Monte Carlo perturbation particle sampling comparing analytical Foster 2-D vs empirical hits.
"""
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np
from ml.debris.pc_engine import FosterCollisionProbabilityEngine


class UncertaintyLabService:
    """Service for encounter plane uncertainty analysis and Monte Carlo collision modeling."""

    def __init__(self) -> None:
        self.pc_engine = FosterCollisionProbabilityEngine()

    def run_bplane_simulation(
        self,
        conjunction_id: str = "CONJ-29834",
        secondary_name: str = "FENGYUN-1C-DEB-29834",
        miss_x_m: float = 315.4,
        miss_y_m: float = 0.0,
        sigma_x_m: float = 50.0,
        sigma_y_m: float = 250.0,
        rho: float = 0.0,
        radius_m: float = 5.0,
        num_trials: int = 2000,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Compute Foster 2-D Pc and run Monte Carlo particles in the B-plane."""
        rng = np.random.default_rng(seed)

        # 1. Analytical Foster 2-D calculation & timing
        t0_foster = time.perf_counter()
        foster_pc = self.pc_engine.compute_foster_2d(
            miss_x_m=miss_x_m,
            miss_y_m=miss_y_m,
            sigma_x_m=sigma_x_m,
            sigma_y_m=sigma_y_m,
            rho=rho,
            radius_m=radius_m,
        )
        t_foster_ms = (time.perf_counter() - t0_foster) * 1000.0

        # 2. Monte Carlo particle sampling in encounter plane
        t0_mc = time.perf_counter()
        cov_xx = sigma_x_m**2
        cov_yy = sigma_y_m**2
        cov_xy = rho * sigma_x_m * sigma_y_m
        cov_matrix = np.array([[cov_xx, cov_xy], [cov_xy, cov_yy]], dtype=np.float64)

        # Generate N perturbations around encounter miss position
        mean_vector = np.array([miss_x_m, miss_y_m], dtype=np.float64)
        samples = rng.multivariate_normal(mean_vector, cov_matrix, size=num_trials)

        # Collision condition: distance from primary satellite origin <= hard body radius
        distances = np.hypot(samples[:, 0], samples[:, 1])
        hits = int(np.sum(distances <= radius_m))
        empirical_pc = float(hits / num_trials)
        t_mc_ms = (time.perf_counter() - t0_mc) * 1000.0

        # 3. Covariance Ellipse Parameters for 2D visualizer
        # Eigenvalues & orientation angle of covariance matrix
        eigvals, eigvecs = np.linalg.eigh(cov_matrix)
        order = eigvals.argsort()[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]

        angle_rad = float(np.arctan2(eigvecs[1, 0], eigvecs[0, 0]))
        angle_deg = float(np.degrees(angle_rad))

        sigma_major = float(np.sqrt(max(eigvals[0], 1e-4)))
        sigma_minor = float(np.sqrt(max(eigvals[1], 1e-4)))

        # Subsample 250 points for browser scatter plot
        scatter_stride = max(1, num_trials // 250)
        scatter_sample = samples[::scatter_stride]
        scatter_points = [
            {
                "x": round(float(pt[0]), 1),
                "y": round(float(pt[1]), 1),
                "is_collision": bool(np.hypot(pt[0], pt[1]) <= radius_m),
            }
            for pt in scatter_sample
        ]

        return {
            "conjunction_id": conjunction_id,
            "secondary_name": secondary_name,
            "encounter_geometry": {
                "miss_x_m": miss_x_m,
                "miss_y_m": miss_y_m,
                "miss_distance_m": round(float(np.hypot(miss_x_m, miss_y_m)), 1),
                "hard_body_radius_m": radius_m,
            },
            "uncertainty_covariance": {
                "sigma_x_m": sigma_x_m,
                "sigma_y_m": sigma_y_m,
                "rho": rho,
                "ellipse_1sigma": {
                    "semi_major_m": round(sigma_major, 1),
                    "semi_minor_m": round(sigma_minor, 1),
                    "angle_deg": round(angle_deg, 2),
                },
                "ellipse_2sigma": {
                    "semi_major_m": round(sigma_major * 2.0, 1),
                    "semi_minor_m": round(sigma_minor * 2.0, 1),
                },
                "ellipse_3sigma": {
                    "semi_major_m": round(sigma_major * 3.0, 1),
                    "semi_minor_m": round(sigma_minor * 3.0, 1),
                },
            },
            "comparison": {
                "foster_2d_analytical_pc": float(foster_pc),
                "monte_carlo_empirical_pc": empirical_pc,
                "monte_carlo_hits": hits,
                "monte_carlo_trials": num_trials,
                "foster_latency_ms": round(t_foster_ms, 3),
                "monte_carlo_latency_ms": round(t_mc_ms, 2),
                "speedup_factor": round(max(1.0, t_mc_ms / max(t_foster_ms, 0.001)), 1),
                "relative_error_pct": round(
                    abs(foster_pc - empirical_pc) / max(foster_pc, 1e-9) * 100.0, 2
                ) if hits > 0 else 0.0,
            },
            "scatter_points": scatter_points,
            "timestamp": datetime.now(UTC).isoformat(),
        }


uncertainty_lab_service = UncertaintyLabService()
