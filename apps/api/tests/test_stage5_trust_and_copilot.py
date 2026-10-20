"""Tests for Stage 5: Trust Layer, Observation Tasking, and Operator Intelligence."""
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.observation_service import observation_service
from app.services.trust_layer_service import trust_layer_service


@pytest.mark.asyncio
async def test_trust_layer_metrics_endpoint() -> None:
    """Verify /api/v1/models/trust endpoint returns complete calibration, drift, and OOD metrics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/models/trust")
        assert res.status_code == 200
        data: dict[str, Any] = res.json()

        # Calibration verification
        assert "calibration" in data
        cal = data["calibration"]
        assert 0.0 <= cal["ece"] <= 0.10
        assert 0.0 <= cal["mce"] <= 0.20
        assert 0.0 <= cal["brier_score"] <= 0.10
        assert len(cal["reliability_bins"]) == 10

        # Drift verification (KS-test)
        assert "drift_monitoring" in data
        channels = data["drift_monitoring"]["channels"]
        assert len(channels) >= 5
        for ch in channels:
            assert 0.0 <= ch["ks_statistic"] <= 1.0
            assert 0.0 <= ch["p_value"] <= 1.0
            assert ch["status"] in ["STABLE", "DRIFT_ALERT", "WARNING"]

        # OOD verification
        assert "out_of_distribution" in data
        ood = data["out_of_distribution"]
        assert 0.0 <= ood["ood_score"] <= 1.0
        assert ood["status"] == "IN_DISTRIBUTION"

        # TLE staleness degradation
        assert "tle_staleness" in data
        tle = data["tle_staleness"]
        assert tle["primary_asset"]["status"] == "FRESH"
        assert tle["secondary_debris"]["status"] == "STALE_WARNING"
        assert len(tle["staleness_curve"]) >= 5


@pytest.mark.asyncio
async def test_observation_tasking_plan_endpoint() -> None:
    """Verify /api/v1/debris/observations returns optimized sensor schedule and covariance reduction."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/debris/observations",
            params={
                "conjunction_id": "CONJ-29834",
                "secondary_name": "FENGYUN-1C-DEB-29834",
                "hours_to_tca": 14.2,
                "sigma_y_m": 250.0,
                "sigma_x_m": 50.0,
            },
        )
        assert res.status_code == 200
        data: dict[str, Any] = res.json()

        assert data["conjunction_id"] == "CONJ-29834"
        assert len(data["scheduled_passes"]) >= 3
        assert data["station_network_size"] >= 4

        # Verify covariance projection math
        cov = data["covariance_projection"]
        assert cov["initial_sigma_in_track_m"] == 250.0
        assert cov["projected_sigma_in_track_m"] < cov["initial_sigma_in_track_m"]
        assert cov["uncertainty_reduction_pct"] >= 70.0
        assert cov["potential_cam_avoidance"] is True
        assert cov["projected_fuel_savings_g"] > 0

        # Verify CCSDS TDM preview format
        tdm = data["tdm_command_preview"]
        assert "CCSDS_TDM_VERS = 2.0" in tdm
        assert "FENGYUN-1C-DEB-29834" in tdm


def test_trust_layer_service_direct() -> None:
    """Verify TrustLayerService unit calculation."""
    metrics = trust_layer_service.get_trust_metrics()
    assert metrics["overall_trust_grade"].startswith("A")
    assert metrics["summary"]["active_models_monitored"] == 4
    assert metrics["summary"]["channels_with_drift_alert"] == 1  # gyro_drift_rate


def test_observation_service_direct() -> None:
    """Verify ObservationService unit calculation."""
    tasking = observation_service.optimize_tasking(
        conjunction_id="TEST-001",
        secondary_name="COSMOS-2251-DEB",
        hours_to_tca=10.0,
    )
    assert tasking["conjunction_id"] == "TEST-001"
    assert tasking["optimal_primary_pass"]["pass_id"] == "PASS-01-TIRA"
