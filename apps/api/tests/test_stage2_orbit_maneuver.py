"""Unit and integration tests for Stage 2 - Orbit & Maneuver Intelligence.

Tests F1 (3D Orbit Digital Twin ephemerides), F2 (Maneuver What-If Simulator),
and F3 (Conjunction Uncertainty Lab & B-Plane Monte Carlo).
"""
import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_maneuver_what_if_simulation(client: AsyncClient) -> None:
    """Test POST /api/v1/debris/simulate-maneuver with prograde CAM burn."""
    res = await client.post(
        "/api/v1/debris/simulate-maneuver",
        json={
            "conjunction_id": "CONJ-29834",
            "secondary_name": "FENGYUN-1C-DEB-29834",
            "initial_miss_m": 45.0,
            "relative_velocity_kms": 12.42,
            "delta_v_ms": 0.35,
            "direction": "prograde",
            "lead_time_hours": 8.0,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["conjunction_id"] == "CONJ-29834"
    assert "original" in data
    assert "simulated" in data
    assert "advisory_directive" in data

    orig = data["original"]
    sim = data["simulated"]

    # Initial risk should be CRITICAL (miss 45.0m, Pc ~6.7e-4 >= 1e-4)
    assert orig["risk_class"] == "CRITICAL"
    assert orig["pc"] >= 1e-4

    # Post-maneuver miss distance must expand significantly
    assert sim["miss_distance_m"] > orig["miss_distance_m"]
    assert sim["miss_distance_m"] > 1000.0

    # Pc must drop into NOMINAL / low risk
    assert sim["pc"] < orig["pc"]
    assert sim["pc"] < 1e-6
    assert sim["risk_class"] == "NOMINAL"
    assert sim["pc_reduction_factor"] > 100.0

    # Fuel mass should be small and feasible
    assert 0.05 < sim["fuel_consumed_kg"] < 1.0
    assert sim["maneuver_feasible"] is True


@pytest.mark.asyncio
async def test_maneuver_directions(client: AsyncClient) -> None:
    """Test maneuver simulator across different orbital thrust vectors."""
    for direction in ["retrograde", "radial_out", "out_of_plane"]:
        res = await client.post(
            "/api/v1/debris/simulate-maneuver",
            json={
                "conjunction_id": "CONJ-29834",
                "initial_miss_m": 315.4,
                "delta_v_ms": 0.20,
                "direction": direction,
                "lead_time_hours": 6.0,
            },
        )
        assert res.status_code == 200
        sim = res.json()["simulated"]
        assert sim["miss_distance_m"] > 315.4


@pytest.mark.asyncio
async def test_conjunction_uncertainty_lab_monte_carlo(client: AsyncClient) -> None:
    """Test POST /api/v1/debris/uncertainty-lab comparing Foster vs Monte Carlo."""
    res = await client.post(
        "/api/v1/debris/uncertainty-lab",
        json={
            "conjunction_id": "CONJ-29834",
            "secondary_name": "FENGYUN-1C-DEB-29834",
            "miss_x_m": 315.4,
            "miss_y_m": 0.0,
            "sigma_x_m": 50.0,
            "sigma_y_m": 250.0,
            "rho": 0.0,
            "radius_m": 5.0,
            "num_trials": 2000,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert "encounter_geometry" in data
    assert "uncertainty_covariance" in data
    assert "comparison" in data
    assert "scatter_points" in data

    comp = data["comparison"]
    assert "foster_2d_analytical_pc" in comp
    assert "monte_carlo_empirical_pc" in comp
    assert comp["foster_2d_analytical_pc"] > 0
    assert comp["foster_latency_ms"] < 2.0  # Analytical is ultrafast

    # Ellipse parameters
    cov = data["uncertainty_covariance"]
    assert "ellipse_1sigma" in cov
    assert "ellipse_2sigma" in cov
    assert "ellipse_3sigma" in cov
    assert cov["ellipse_1sigma"]["semi_major_m"] == 250.0
    assert cov["ellipse_1sigma"]["semi_minor_m"] == 50.0

    # Scatter points
    pts = data["scatter_points"]
    assert len(pts) >= 100
    assert "x" in pts[0]
    assert "y" in pts[0]


@pytest.mark.asyncio
async def test_3d_orbit_tracks_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/debris/orbit-tracks/SENTINEL-2A returns 3D digital twin coordinates."""
    res = await client.get("/api/v1/debris/orbit-tracks/SENTINEL-2A")
    assert res.status_code == 200
    data = res.json()

    assert data["asset_id"] == "SENTINEL-2A"
    assert "primary_track" in data
    assert "debris_track" in data
    assert len(data["primary_track"]) == 48
    assert len(data["debris_track"]) == 48

    pt = data["primary_track"][0]
    assert -90.0 <= pt["lat"] <= 90.0
    assert -180.0 <= pt["lon"] <= 180.0
    assert pt["alt_km"] == 786.0


@pytest.mark.asyncio
async def test_feature_flags_guard_stage2(client: AsyncClient) -> None:
    """Test that disabling Stage 2 feature flags returns 403."""
    os.environ["ASTRA_FEATURE_MANEUVER_SIMULATOR"] = "false"
    try:
        res = await client.post(
            "/api/v1/debris/simulate-maneuver",
            json={"conjunction_id": "CONJ-29834"},
        )
        assert res.status_code == 403
    finally:
        os.environ.pop("ASTRA_FEATURE_MANEUVER_SIMULATOR", None)
