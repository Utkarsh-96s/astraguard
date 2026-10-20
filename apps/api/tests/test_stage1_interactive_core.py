"""Unit and integration tests for Stage 1 - Interactive Core.

Tests F5 (Fault Injection Lab & Detector Arena), F4 (Counterfactual Explainer),
and F10 (Phone Alert Bot / Telegram Webhook Dispatcher).
"""
import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_telemetry_channels(client: AsyncClient) -> None:
    """Test GET /api/v1/health/channels returns available channels."""
    res = await client.get("/api/v1/health/channels")
    assert res.status_code == 200
    data = res.json()
    assert "channels" in data
    assert "wheel_temp" in data["channels"]
    assert "bus_current" in data["channels"]


@pytest.mark.asyncio
async def test_fault_injection_drift_and_arena(client: AsyncClient) -> None:
    """Test POST /api/v1/health/inject-fault with thermal drift and check Detector Arena."""
    res = await client.post(
        "/api/v1/health/inject-fault",
        json={
            "asset_id": "SENTINEL-2A",
            "fault_type": "drift",
            "channel": "wheel_temp",
            "magnitude": 1.5,
            "duration_steps": 25,
            "window_size": 64,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["fault_type"] == "drift"
    assert data["channel"] == "wheel_temp"
    assert "waveform" in data
    assert len(data["waveform"]) == 64
    assert any(w["is_fault_active"] for w in data["waveform"])

    # Verify Detector Arena
    arena = data["arena"]
    assert "lstm" in arena
    assert "isoforest" in arena
    assert "verdict" in arena

    lstm = arena["lstm"]
    iso = arena["isoforest"]

    assert lstm["model_name"] == "PyTorch LSTM Autoencoder"
    assert iso["model_name"] == "Isolation Forest (Baseline)"
    assert "effective_score" in lstm
    assert "reconstruction_error" in lstm
    assert "attributions" in lstm
    assert len(lstm["attributions"]) >= 1
    # Check that wheel_temp is the top attribution
    assert lstm["attributions"][0]["channel"] == "wheel_temp"

    # Verify Counterfactual
    cf = data["counterfactual"]
    assert "target_level" in cf
    assert cf["target_level"] == "NOMINAL"
    assert "actionable_guidance" in cf
    assert cf["counterfactual_achieved"] is True

    # Verify Temporal Heatmap
    heatmap = data["temporal_heatmap"]
    assert len(heatmap) == 8
    assert "dominant_channel" in heatmap[0]


@pytest.mark.asyncio
async def test_fault_injection_spike_and_stuck(client: AsyncClient) -> None:
    """Test POST /api/v1/health/inject-fault with transient spike and stuck sensor."""
    # 1. Transient Spike
    res_spike = await client.post(
        "/api/v1/health/inject-fault",
        json={
            "asset_id": "SENTINEL-2A",
            "fault_type": "spike",
            "channel": "bus_current",
            "magnitude": 1.2,
            "duration_steps": 15,
        },
    )
    assert res_spike.status_code == 200
    assert res_spike.json()["fault_type"] == "spike"

    # 2. Frozen / Stuck Sensor
    res_stuck = await client.post(
        "/api/v1/health/inject-fault",
        json={
            "asset_id": "SENTINEL-2A",
            "fault_type": "stuck",
            "channel": "gyro_rate_x",
            "magnitude": 1.0,
            "duration_steps": 20,
        },
    )
    assert res_stuck.status_code == 200
    assert res_stuck.json()["fault_type"] == "stuck"


@pytest.mark.asyncio
async def test_counterfactual_sensitivity_endpoint(client: AsyncClient) -> None:
    """Test POST /api/v1/health/counterfactual endpoint."""
    res = await client.post(
        "/api/v1/health/counterfactual",
        json={
            "asset_id": "SENTINEL-2A",
            "channel": "wheel_temp",
            "target_reduction_pct": 35.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "counterfactual" in data
    assert "actionable_guidance" in data["counterfactual"]
    assert "temporal_heatmap" in data


@pytest.mark.asyncio
async def test_phone_alert_bot_lifecycle(client: AsyncClient) -> None:
    """Test bot alert preview, dispatch, and mobile inline action handling."""
    # First create an alert via elevated risk evaluation
    eval_res = await client.post(
        "/api/v1/risk/evaluate",
        json={
            "asset_id": "SENTINEL-2A",
            "r_h": 0.15,
            "r_d": 0.95,
            "r_e": 0.10,
            "evidence": {"pc": 3.1e-4},
        },
    )
    assert eval_res.status_code == 200

    alerts_res = await client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # 1. Preview Telegram bot dispatch
    prev_res = await client.get(f"/api/v1/bot/preview/{alert_id}")
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["alert_id"] == alert_id
    assert "telegram_payload" in prev_data
    payload = prev_data["telegram_payload"]
    assert "text" in payload
    assert "reply_markup" in payload
    assert "inline_keyboard" in payload["reply_markup"]

    # 2. Trigger dispatch
    disp_res = await client.post(f"/api/v1/bot/dispatch/{alert_id}")
    assert disp_res.status_code == 200
    disp_data = disp_res.json()
    assert "dispatch_status" in disp_data

    # 3. Simulate mobile operator tapping "Approve" button
    action_res = await client.post(
        "/api/v1/bot/action",
        json={
            "alert_id": alert_id,
            "action": "approve",
            "operator": "FlightDirector_Mobile",
            "note": "Approved maneuver via Telegram inline button",
        },
    )
    assert action_res.status_code == 200
    action_data = action_res.json()
    assert action_data["status"] == "ACKNOWLEDGED"
    assert action_data["action"] == "APPROVE"


@pytest.mark.asyncio
async def test_feature_flags_guard_stage1(client: AsyncClient) -> None:
    """Test that disabling feature flags returns 403 on protected routes."""
    os.environ["ASTRA_FEATURE_FAULT_INJECTION_LAB"] = "false"
    try:
        res = await client.post(
            "/api/v1/health/inject-fault",
            json={"channel": "wheel_temp", "fault_type": "drift"},
        )
        assert res.status_code == 403
    finally:
        os.environ.pop("ASTRA_FEATURE_FAULT_INJECTION_LAB", None)
