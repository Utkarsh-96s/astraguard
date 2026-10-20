"""Maneuver Simulator & Conjunction Uncertainty Router.

Implements F1 (3D Orbit Digital Twin ephemerides), F2 (Maneuver What-If Simulator),
and F3 (Conjunction Uncertainty Lab).
"""
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.feature_service import feature_service
from app.services.maneuver_service import maneuver_service
from app.services.uncertainty_lab_service import uncertainty_lab_service

router = APIRouter(prefix="/debris", tags=["Debris & Maneuver Intelligence"])


class ManeuverSimulationRequest(BaseModel):
    """Payload for collision avoidance maneuver what-if simulation."""

    conjunction_id: str = Field("CONJ-29834", description="Conjunction ID")
    secondary_name: str = Field(
        "FENGYUN-1C-DEB-29834", description="Secondary debris name"
    )
    initial_miss_m: float = Field(
        315.4, ge=1.0, le=50000.0, description="Nominal unperturbed miss distance in meters"
    )
    relative_velocity_kms: float = Field(
        12.42, ge=0.5, le=25.0, description="Encounter relative velocity in km/s"
    )
    delta_v_ms: float = Field(
        0.25, ge=0.01, le=5.0, description="Thruster delta-V burn magnitude in m/s"
    )
    direction: Literal["prograde", "retrograde", "radial_out", "radial_in", "out_of_plane"] = Field(
        "prograde", description="Maneuver burn direction vector"
    )
    lead_time_hours: float = Field(
        8.0, ge=1.0, le=72.0, description="Burn lead time prior to TCA in hours"
    )


class UncertaintyLabRequest(BaseModel):
    """Payload for B-plane encounter plane Monte Carlo simulation."""

    conjunction_id: str = Field("CONJ-29834", description="Conjunction ID")
    secondary_name: str = Field("FENGYUN-1C-DEB-29834", description="Debris object name")
    miss_x_m: float = Field(315.4, description="Encounter miss distance X in B-plane")
    miss_y_m: float = Field(0.0, description="Encounter miss distance Y in B-plane")
    sigma_x_m: float = Field(50.0, ge=5.0, le=1000.0, description="Normal uncertainty 1-sigma")
    sigma_y_m: float = Field(250.0, ge=10.0, le=2000.0, description="Along-track uncertainty 1-sigma")
    rho: float = Field(0.0, ge=-0.99, le=0.99, description="Covariance cross-correlation")
    radius_m: float = Field(5.0, ge=1.0, le=50.0, description="Combined hard body radius in meters")
    num_trials: int = Field(2000, ge=100, le=10000, description="Number of Monte Carlo trials")


@router.post("/simulate-maneuver", summary="Run collision avoidance maneuver what-if simulation")
async def simulate_maneuver(req: ManeuverSimulationRequest) -> dict[str, Any]:
    """Calculate perturbed miss distance, Pc reduction, and propellant consumption."""
    if not feature_service.is_enabled("maneuver_simulator"):
        raise HTTPException(
            status_code=403,
            detail="Maneuver What-If Simulator feature is disabled via feature flags.",
        )

    try:
        return maneuver_service.simulate_maneuver(
            conjunction_id=req.conjunction_id,
            secondary_name=req.secondary_name,
            initial_miss_m=req.initial_miss_m,
            relative_velocity_kms=req.relative_velocity_kms,
            delta_v_ms=req.delta_v_ms,
            direction=req.direction,
            lead_time_hours=req.lead_time_hours,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Maneuver simulation failed: {e!s}"
        ) from e


@router.post("/uncertainty-lab", summary="Run B-plane Monte Carlo uncertainty simulation")
async def run_uncertainty_lab(req: UncertaintyLabRequest) -> dict[str, Any]:
    """Compute Foster 2-D analytical Pc vs. Monte Carlo particle sampling in the encounter plane."""
    if not feature_service.is_enabled("conjunction_uncertainty"):
        raise HTTPException(
            status_code=403,
            detail="Conjunction Uncertainty Lab feature is disabled via feature flags.",
        )

    try:
        return uncertainty_lab_service.run_bplane_simulation(
            conjunction_id=req.conjunction_id,
            secondary_name=req.secondary_name,
            miss_x_m=req.miss_x_m,
            miss_y_m=req.miss_y_m,
            sigma_x_m=req.sigma_x_m,
            sigma_y_m=req.sigma_y_m,
            rho=req.rho,
            radius_m=req.radius_m,
            num_trials=req.num_trials,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Uncertainty lab simulation failed: {e!s}"
        ) from e


@router.get("/orbit-tracks/{asset_id}", summary="Get 3D orbital digital twin coordinates")
async def get_orbit_tracks(asset_id: str) -> dict[str, Any]:
    """Retrieve 3D orbit trajectory waypoints for Sentinel-2A and close-approach debris."""
    if not feature_service.is_enabled("orbit_twin_3d"):
        raise HTTPException(
            status_code=403,
            detail="3D Orbit Digital Twin feature is disabled via feature flags.",
        )

    # Generate 1 orbit period (96 minutes) sampled every 2 minutes
    import math

    primary_points: list[dict[str, Any]] = []
    debris_points: list[dict[str, Any]] = []

    # Sentinel-2A Sun-synchronous orbit: altitude 786 km, inclination 98.6 deg
    inclination_rad = math.radians(98.6)
    period_min = 96.0

    for step in range(48):
        t_min = step * 2.0
        angle = (t_min / period_min) * 2.0 * math.pi

        # Spherical orbital coordinates
        lat = math.degrees(math.asin(math.sin(inclination_rad) * math.sin(angle)))
        lon = math.degrees(angle) % 360.0
        r_km = 6378.137 + 786.0
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        x_eci = r_km * math.cos(lat_rad) * math.cos(lon_rad)
        y_eci = r_km * math.cos(lat_rad) * math.sin(lon_rad)
        z_eci = r_km * math.sin(lat_rad)

        primary_points.append({
            "step": step,
            "time_min": t_min,
            "lat": round(lat, 2),
            "lon": round(lon, 2),
            "alt_km": 786.0,
            "x_eci_km": round(x_eci, 1),
            "y_eci_km": round(y_eci, 1),
            "z_eci_km": round(z_eci, 1),
        })

        # Secondary debris orbit (Fengyun-1C polar fragment, inclination ~99.1 deg, intersecting at step 24)
        deb_angle = angle + math.radians(15.0)
        deb_lat = math.degrees(math.asin(math.sin(math.radians(99.1)) * math.sin(deb_angle)))
        deb_lon = (math.degrees(deb_angle) + 40.0) % 360.0
        if deb_lon > 180.0:
            deb_lon -= 360.0

        deb_r_km = 6378.137 + 789.2
        deb_lat_rad = math.radians(deb_lat)
        deb_lon_rad = math.radians(deb_lon)
        deb_x_eci = deb_r_km * math.cos(deb_lat_rad) * math.cos(deb_lon_rad)
        deb_y_eci = deb_r_km * math.cos(deb_lat_rad) * math.sin(deb_lon_rad)
        deb_z_eci = deb_r_km * math.sin(deb_lat_rad)

        debris_points.append({
            "step": step,
            "time_min": t_min,
            "lat": round(deb_lat, 2),
            "lon": round(deb_lon, 2),
            "alt_km": 789.2,
            "x_eci_km": round(deb_x_eci, 1),
            "y_eci_km": round(deb_y_eci, 1),
            "z_eci_km": round(deb_z_eci, 1),
        })

    return {
        "asset_id": asset_id,
        "orbit_period_minutes": period_min,
        "conjunction_apex_step": 24,
        "primary_track": primary_points,
        "debris_track": debris_points,
        "encounter_summary": {
            "secondary_name": "FENGYUN-1C-DEB-29834",
            "encounter_altitude_km": 786.4,
            "miss_distance_m": 315.4,
            "relative_velocity_kms": 12.42,
        },
    }
