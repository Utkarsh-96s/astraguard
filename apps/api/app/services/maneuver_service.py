"""Collision Avoidance Maneuver (CAM) What-If Simulator Service.

Implements F2: Maneuver What-If Simulator.
Simulates prograde, retrograde, radial, and normal thruster impulses
at configurable lead times prior to Time of Closest Approach (TCA),
computing perturbed miss distances, fuel mass consumption, and updated Foster 2-D Pc.
"""
import math
from datetime import UTC, datetime
from typing import Any, Literal

from ml.debris.pc_engine import FosterCollisionProbabilityEngine

ManeuverDirection = Literal["prograde", "retrograde", "radial_out", "radial_in", "out_of_plane"]


class ManeuverService:
    """Service for what-if collision avoidance maneuver optimization and simulation."""

    # Sentinel-2A baseline parameters
    DRY_MASS_KG = 1140.0
    HYDRAZINE_ISP_S = 220.0
    G0_MS2 = 9.80665
    ORBIT_RADIUS_M = 7164000.0  # ~786 km altitude LEO
    MU_EARTH = 3.986004418e14   # m^3 / s^2

    def __init__(self) -> None:
        self.pc_engine = FosterCollisionProbabilityEngine()
        # Mean motion omega (rad/s)
        self.omega = math.sqrt(self.MU_EARTH / (self.ORBIT_RADIUS_M**3))

    def simulate_maneuver(
        self,
        conjunction_id: str = "CONJ-29834",
        secondary_name: str = "FENGYUN-1C-DEB-29834",
        initial_miss_m: float = 315.4,
        relative_velocity_kms: float = 12.42,
        delta_v_ms: float = 0.25,
        direction: ManeuverDirection = "prograde",
        lead_time_hours: float = 8.0,
    ) -> dict[str, Any]:
        """Simulate thruster impulse and recalculate miss distance and Foster Pc."""
        dt_seconds = lead_time_hours * 3600.0

        # Initial baseline Foster screening Pc
        initial_eval = self.pc_engine.compute_screening_pc(
            miss_distance_m=initial_miss_m,
            relative_velocity_ms=relative_velocity_kms * 1000.0,
        )

        # Orbital mechanics perturbation estimation (Hill-Clohessy-Wiltshire model)
        delta_in_track = 0.0
        delta_radial = 0.0
        delta_normal = 0.0

        if direction == "prograde":
            # Prograde impulse increases semimajor axis, resulting in secular in-track drift
            # delta_y ≈ 3 * omega * delta_v * dt^2 / 2 (relative to unperturbed epoch)
            # Scaled for orbital transfer phasing
            delta_in_track = 1.5 * delta_v_ms * dt_seconds
        elif direction == "retrograde":
            delta_in_track = -1.5 * delta_v_ms * dt_seconds
        elif direction == "radial_out":
            # Radial impulse produces periodic oscillation in altitude
            delta_radial = (delta_v_ms / self.omega) * math.sin(self.omega * dt_seconds)
        elif direction == "radial_in":
            delta_radial = -(delta_v_ms / self.omega) * math.sin(self.omega * dt_seconds)
        elif direction == "out_of_plane":
            # Normal impulse rotates orbital inclination plane
            delta_normal = (delta_v_ms / self.omega) * math.sin(self.omega * dt_seconds)

        # Net separation offset
        displacement_vector_m = math.sqrt(delta_in_track**2 + delta_radial**2 + delta_normal**2)

        # Post-maneuver miss distance
        # Assuming conservative perpendicular or constructive separation geometry
        new_miss_m = math.sqrt((initial_miss_m + abs(delta_in_track) * 0.4)**2 + (delta_radial**2 + delta_normal**2))
        new_miss_m = max(new_miss_m, initial_miss_m + displacement_vector_m * 0.25)

        # Recalculate Pc on encounter plane
        new_eval = self.pc_engine.compute_screening_pc(
            miss_distance_m=new_miss_m,
            relative_velocity_ms=relative_velocity_kms * 1000.0,
        )

        # Fuel consumption via Tsiolkovsky equation
        # delta_m = m0 * (1 - exp(-delta_v / (Isp * g0)))
        effective_exhaust_vel = self.HYDRAZINE_ISP_S * self.G0_MS2
        fuel_consumed_kg = self.DRY_MASS_KG * (1.0 - math.exp(-delta_v_ms / effective_exhaust_vel))

        # Risk reduction calculation
        init_pc = max(initial_eval["pc"], 1e-15)
        sim_pc = max(new_eval["pc"], 1e-15)
        reduction_factor = max(1.0, init_pc / sim_pc)

        # Advisory Action Guidance
        if new_eval["risk_class"] == "NOMINAL":
            guidance = (
                f"Optimal CAM candidate: applying {delta_v_ms:.2f} m/s {direction} impulse at T-{lead_time_hours:.1f}h "
                f"increases miss distance from {initial_miss_m:.1f}m to {new_miss_m:.1f}m, dropping Pc by {reduction_factor:,.0f}x "
                f"into safe NOMINAL flight corridor. Hydrazine expenditure: {fuel_consumed_kg:.3f} kg."
            )
        elif new_eval["risk_class"] in ("WATCH", "WARNING"):
            guidance = (
                f"Marginal clearance: {delta_v_ms:.2f} m/s {direction} burn expands miss distance to {new_miss_m:.1f}m. "
                f"Pc remains at {new_eval['pc']:.2e} ({new_eval['risk_class']}). Consider increasing delta-V to >0.45 m/s or advancing burn lead time."
            )
        else:
            guidance = (
                "Insufficient clearance: simulated burn fails to reduce collision risk below hard override threshold (1e-4). "
                "Alternative thrust vector recommended."
            )

        return {
            "conjunction_id": conjunction_id,
            "secondary_name": secondary_name,
            "simulation_inputs": {
                "delta_v_ms": delta_v_ms,
                "direction": direction,
                "lead_time_hours": lead_time_hours,
            },
            "original": {
                "miss_distance_m": round(initial_miss_m, 1),
                "pc": float(initial_eval["pc"]),
                "risk_class": initial_eval["risk_class"],
                "log10_pc": initial_eval["log10_pc"],
            },
            "simulated": {
                "miss_distance_m": round(new_miss_m, 1),
                "displacement_m": round(displacement_vector_m, 1),
                "pc": float(new_eval["pc"]),
                "risk_class": new_eval["risk_class"],
                "log10_pc": new_eval["log10_pc"],
                "fuel_consumed_kg": round(fuel_consumed_kg, 4),
                "pc_reduction_factor": round(reduction_factor, 1),
                "maneuver_feasible": bool(fuel_consumed_kg < 5.0),
            },
            "advisory_directive": guidance,
            "timestamp": datetime.now(UTC).isoformat(),
        }


maneuver_service = ManeuverService()
