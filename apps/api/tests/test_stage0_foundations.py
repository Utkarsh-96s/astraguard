"""Unit and integration tests for Stage 0 - Foundations.

Tests feature flags endpoint, pipeline observability metrics, enriched asset listing,
and cryptographic alert provenance with bit-for-bit reproducibility.
"""
import os

import pytest
from httpx import AsyncClient

from app.services.feature_service import FeatureService
from app.services.observability_service import observability_service


@pytest.mark.asyncio
async def test_feature_flags_endpoint(client: AsyncClient) -> None:
    """Test /api/v1/features endpoint returns configured flags."""
    res = await client.get("/api/v1/features")
    assert res.status_code == 200
    data = res.json()
    assert "flags" in data
    flags = data["flags"]
    assert isinstance(flags, dict)

    # Core features from features.yaml
    assert "fault_injection_lab" in flags
    assert "phone_alert_bot" in flags
    assert "counterfactual_explainer" in flags
    assert "orbit_twin_3d" in flags
    assert "maneuver_simulator" in flags
    assert "conjunction_uncertainty" in flags
    assert "real_event_replay" in flags
    assert "trust_layer" in flags
    assert "incident_report" in flags
    assert "fleet_command_center" in flags
    assert "operator_copilot" in flags
    assert "observation_optimizer" in flags

    # Quick wins
    assert "guided_judge_tour" in flags
    assert "provenance_reproduce" in flags
    assert "pipeline_observability" in flags
    assert "command_palette" in flags
    assert "voice_announcer" in flags
    assert "night_ops_theme" in flags


def test_feature_service_env_override() -> None:
    """Test environment variable overrides for feature flags."""
    service = FeatureService()
    # Baseline
    assert service.is_enabled("fault_injection_lab") is True

    # Override via environment variable
    os.environ["ASTRA_FEATURE_FAULT_INJECTION_LAB"] = "false"
    try:
        assert service.is_enabled("fault_injection_lab") is False
    finally:
        os.environ.pop("ASTRA_FEATURE_FAULT_INJECTION_LAB", None)


@pytest.mark.asyncio
async def test_observability_pipeline_metrics(client: AsyncClient) -> None:
    """Test /metrics/pipeline and /api/v1/metrics/pipeline return measured percentiles."""
    # Record some mock latency samples
    observability_service.record_latency(0.065)
    observability_service.record_latency(0.120)

    for path in ["/metrics/pipeline", "/api/v1/metrics/pipeline"]:
        res = await client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert "latency_ms" in data
        assert "throughput_evals_sec" in data
        assert "active_connections" in data
        assert "queue_depth" in data

        lat = data["latency_ms"]
        assert "p50" in lat
        assert "p90" in lat
        assert "p95" in lat
        assert "p99" in lat
        assert lat["p50"] > 0
        assert lat["p95"] >= lat["p50"]


@pytest.mark.asyncio
async def test_assets_enriched_with_risk_summary(client: AsyncClient) -> None:
    """Test GET /api/v1/assets returns enriched assets with live risk summary and alert counts."""
    # First evaluate risk to create snapshot
    eval_res = await client.post(
        "/api/v1/risk/evaluate",
        json={
            "asset_id": "SENTINEL-2A",
            "r_h": 0.05,
            "r_d": 0.03,
            "r_e": 0.10,
        },
    )
    assert eval_res.status_code == 200

    res = await client.get("/api/v1/assets")
    assert res.status_code == 200
    assets = res.json()
    assert len(assets) >= 1
    s2a = next(a for a in assets if a["id"] == "SENTINEL-2A")
    assert "latest_score" in s2a
    assert "latest_level" in s2a
    assert "active_alerts_count" in s2a
    assert "last_updated" in s2a
    assert s2a["latest_level"] == "NOMINAL"
    assert s2a["latest_score"] > 0.0


@pytest.mark.asyncio
async def test_alert_provenance_and_reproduce(client: AsyncClient) -> None:
    """Test GET /alerts/{id}/provenance and POST /alerts/{id}/reproduce for bit-for-bit identity."""
    # Trigger an alert by evaluating elevated risk (CRITICAL override via Pc >= 1e-4)
    eval_res = await client.post(
        "/api/v1/risk/evaluate",
        json={
            "asset_id": "SENTINEL-2A",
            "r_h": 0.20,
            "r_d": 0.95,
            "r_e": 0.15,
            "evidence": {"pc": 2.5e-4},
        },
    )
    assert eval_res.status_code == 200

    # Retrieve generated alert
    alerts_res = await client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    alert = alerts[0]
    alert_id = alert["id"]

    # 1. Query provenance record
    prov_res = await client.get(f"/api/v1/alerts/{alert_id}/provenance")
    assert prov_res.status_code == 200
    prov = prov_res.json()
    assert prov["alert_id"] == alert_id
    assert "data_window_hash" in prov
    assert len(prov["data_window_hash"]) == 64  # SHA-256
    assert "config_hash" in prov
    assert len(prov["config_hash"]) == 64
    assert "git_commit" in prov
    assert "model_versions" in prov
    assert prov["model_versions"]["health_ai"] == "lstm-ae-v1.0.0"

    # 2. Reproduce evaluation
    repro_res = await client.post(f"/api/v1/alerts/{alert_id}/reproduce")
    assert repro_res.status_code == 200
    repro = repro_res.json()
    assert repro["alert_id"] == alert_id
    assert repro["verification_status"] == "VERIFIED_IDENTICAL"
    assert repro["bit_for_bit_match"] is True
    assert repro["level_match"] is True
    assert repro["score_diff"] < 1e-5
    assert repro["reproduced_score"] == repro["original_score"]
    assert repro["reproduced_level"] == repro["original_level"]
