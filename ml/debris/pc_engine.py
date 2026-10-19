"""Foster 2-D Collision Probability (Pc) calculation on the encounter plane."""
from typing import Any

import numpy as np
from scipy import integrate


class FosterCollisionProbabilityEngine:
    """Calculates satellite-debris collision probability using Foster's 2-D encounter plane method."""

    DEFAULT_COMBINED_RADIUS_M = 5.0  # 5-meter combined hard-body sphere (satellite + debris)

    # Standard screening-grade assumed standard deviations in meters (Radial, In-track, Cross-track)
    # Per rules.md §5: TLEs lack covariance; screening-grade assumptions must be explicitly reported.
    DEFAULT_ASSUMED_SIGMA_R_M = 25.0
    DEFAULT_ASSUMED_SIGMA_T_M = 250.0  # In-track (along-track) largest uncertainty
    DEFAULT_ASSUMED_SIGMA_N_M = 50.0   # Cross-track / normal

    def __init__(self, hard_body_radius_m: float = DEFAULT_COMBINED_RADIUS_M) -> None:
        self.hard_body_radius_m = hard_body_radius_m

    def compute_screening_pc(
        self,
        miss_distance_m: float,
        relative_velocity_ms: float = 14000.0,
        sigma_x_m: float | None = None,
        sigma_y_m: float | None = None,
    ) -> dict[str, Any]:
        """Compute screening-grade Pc assuming default or custom covariance ellipse in B-plane.

        Returns:
            Dictionary with pc, risk_class, method, and assumed covariance metadata.
        """
        sig_x = sigma_x_m or self.DEFAULT_ASSUMED_SIGMA_N_M
        sig_y = sigma_y_m or self.DEFAULT_ASSUMED_SIGMA_T_M

        pc = self.compute_foster_2d(
            miss_x_m=miss_distance_m,
            miss_y_m=0.0,
            sigma_x_m=sig_x,
            sigma_y_m=sig_y,
            rho=0.0,
            radius_m=self.hard_body_radius_m,
        )

        risk_class = self.classify_risk(pc)

        return {
            "pc": float(pc),
            "log10_pc": round(float(np.log10(max(pc, 1e-15))), 3),
            "risk_class": risk_class,
            "pc_method": "foster_2d_screening",
            "screening_grade": True,
            "assumed_covariance": True,
            "covariance_parameters": {
                "sigma_x_m": sig_x,
                "sigma_y_m": sig_y,
                "rho": 0.0,
                "hard_body_radius_m": self.hard_body_radius_m,
            },
        }

    def compute_cdm_pc(
        self,
        miss_distance_m: float,
        c_obs_b: float,
        c_obs_t: float,
        c_obs_n: float,
    ) -> dict[str, Any]:
        """Compute Pc using explicit Conjunction Data Message (CDM) covariance parameters."""
        sig_x = float(np.sqrt(max(abs(c_obs_n), 1.0)))
        sig_y = float(np.sqrt(max(abs(c_obs_t), 1.0)))
        rho = 0.0
        if c_obs_b != 0.0:
            rho = float(np.clip(c_obs_b / (sig_x * sig_y + 1e-8), -0.99, 0.99))

        pc = self.compute_foster_2d(
            miss_x_m=miss_distance_m,
            miss_y_m=0.0,
            sigma_x_m=sig_x,
            sigma_y_m=sig_y,
            rho=rho,
            radius_m=self.hard_body_radius_m,
        )

        risk_class = self.classify_risk(pc)

        return {
            "pc": float(pc),
            "log10_pc": round(float(np.log10(max(pc, 1e-15))), 3),
            "risk_class": risk_class,
            "pc_method": "foster_2d_cdm",
            "screening_grade": False,
            "assumed_covariance": False,
            "covariance_parameters": {
                "sigma_x_m": round(sig_x, 2),
                "sigma_y_m": round(sig_y, 2),
                "rho": round(rho, 4),
                "hard_body_radius_m": self.hard_body_radius_m,
            },
        }

    def compute_foster_2d(
        self,
        miss_x_m: float,
        miss_y_m: float,
        sigma_x_m: float,
        sigma_y_m: float,
        rho: float = 0.0,
        radius_m: float = DEFAULT_COMBINED_RADIUS_M,
    ) -> float:
        """Core Foster 2-D integration across hard-sphere cross section.

        Transforms covariance ellipse to principal axes and integrates 2-D Gaussian PDF.
        """
        if sigma_x_m <= 0 or sigma_y_m <= 0:
            return 0.0

        # Rotate to diagonal principal axes (eliminate correlation rho)
        cov_xx = sigma_x_m**2
        cov_yy = sigma_y_m**2
        cov_xy = rho * sigma_x_m * sigma_y_m

        if abs(cov_xy) > 1e-8:
            theta = 0.5 * np.arctan2(2.0 * cov_xy, cov_xx - cov_yy)
            cos_t = np.cos(theta)
            sin_t = np.sin(theta)

            # Eigenvalues (principal variances)
            sig_u2 = cov_xx * cos_t**2 + 2.0 * cov_xy * cos_t * sin_t + cov_yy * sin_t**2
            sig_v2 = cov_xx * sin_t**2 - 2.0 * cov_xy * cos_t * sin_t + cov_yy * cos_t**2

            sig_u = float(np.sqrt(max(sig_u2, 1e-6)))
            sig_v = float(np.sqrt(max(sig_v2, 1e-6)))

            # Rotate coordinates
            u0 = miss_x_m * cos_t + miss_y_m * sin_t
            v0 = -miss_x_m * sin_t + miss_y_m * cos_t
        else:
            sig_u = sigma_x_m
            sig_v = sigma_y_m
            u0 = miss_x_m
            v0 = miss_y_m

        # If hard-sphere radius is much smaller than uncertainty sigma, use analytical approximation
        ratio_u = radius_m / sig_u
        ratio_v = radius_m / sig_v

        if ratio_u < 0.15 and ratio_v < 0.15:
            # First-order Foster series approximation
            exponent = -0.5 * ((u0 / sig_u) ** 2 + (v0 / sig_v) ** 2)
            pc = (radius_m**2 / (2.0 * sig_u * sig_v)) * np.exp(exponent)
            return float(np.clip(pc, 0.0, 1.0))

        # Full 2-D numerical integration over circle: x^2 + y^2 <= R^2
        def integrand(r_val: float, phi_val: float) -> float:
            u = u0 + r_val * np.cos(phi_val)
            v = v0 + r_val * np.sin(phi_val)
            exponent = -0.5 * ((u / sig_u) ** 2 + (v / sig_v) ** 2)
            return (r_val / (2.0 * np.pi * sig_u * sig_v)) * np.exp(exponent)

        result, _ = integrate.dblquad(
            integrand,
            0.0,
            2.0 * np.pi,
            lambda _: 0.0,
            lambda _: radius_m,
        )
        return float(np.clip(result, 0.0, 1.0))

    @staticmethod
    def classify_risk(pc: float) -> str:
        """Classify conjunction severity based on collision probability."""
        if pc >= 1.0e-4:
            return "CRITICAL"
        if pc >= 1.0e-5:
            return "WARNING"
        if pc >= 1.0e-6:
            return "WATCH"
        return "NOMINAL"
