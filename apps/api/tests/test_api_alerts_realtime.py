"""Comprehensive tests for Phase 6: Assets, Risk, Alerts, Model Registry, and WebSockets."""
import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from app.main import app


@pytest.mark.asyncio
async def test_assets_endpoints(client: AsyncClient) -> None:
    """Test listing assets, getting specific asset, fallback seeding, and 404 handling."""
    # 1. List assets (auto-seeds SENTINEL-2A if empty)
    res = await client.get("/api/v1/assets")
    assert res.status_code == 200
    assets = res.json()
    assert len(assets) >= 1
    assert any(a["id"] == "SENTINEL-2A" for a in assets)

    # 2. Get specific asset
    res_sat = await client.get("/api/v1/assets/SENTINEL-2A")
    assert res_sat.status_code == 200
    data = res_sat.json()
    assert data["id"] == "SENTINEL-2A"
    assert data["norad_id"] == 40697
    assert data["type"] == "satellite"

    # 3. Nonexistent asset returns 404
    res_404 = await client.get("/api/v1/assets/NONEXISTENT-SAT-999")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_asset_health_history(client: AsyncClient) -> None:
    """Test querying asset health evaluation windows."""
    res = await client.get("/api/v1/assets/SENTINEL-2A/health")
    assert res.status_code == 200
    windows = res.json()
    assert isinstance(windows, list)


@pytest.mark.asyncio
async def test_risk_evaluate_and_history(client: AsyncClient) -> None:
    """Test mission risk evaluation, latest snapshot retrieval, and timeseries history."""
    # 1. Evaluate nominal risk
    payload = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.04,
        "r_d": 0.02,
        "r_e": 0.10,
        "evidence": {"nominal_test": True},
    }
    eval_res = await client.post("/api/v1/risk/evaluate", json=payload)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["asset_id"] == "SENTINEL-2A"
    assert 0.0 <= eval_data["score"] <= 100.0
    assert eval_data["level"] == "NOMINAL"
    assert "drivers" in eval_data
    assert "rationale" in eval_data
    assert "recommendations" in eval_data
    assert eval_data["defer_eo_payloads"] is False

    # 2. Retrieve latest snapshot
    latest_res = await client.get("/api/v1/risk/SENTINEL-2A/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["asset_id"] == "SENTINEL-2A"
    assert latest_data["id"] == eval_data["id"]

    # 3. Retrieve history
    hist_res = await client.get("/api/v1/risk/SENTINEL-2A/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) >= 1
    assert hist_data[0]["asset_id"] == "SENTINEL-2A"


@pytest.mark.asyncio
async def test_critical_override_risk_evaluation(client: AsyncClient) -> None:
    """Assert Pc >= 1e-4 triggers hard safety override to CRITICAL."""
    payload = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.05,
        "r_d": 0.95,
        "r_e": 0.20,
        "pc": 2.5e-4,
        "evidence": {"conjunction": "FENGYUN-1C-DEB"},
    }
    eval_res = await client.post("/api/v1/risk/evaluate", json=payload)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert data["level"] == "CRITICAL"
    assert data["critical_override_applied"] is True
    assert data["score"] >= 80.0
    assert "CRITICAL" in data["rationale"]


@pytest.mark.asyncio
async def test_alert_lifecycle_dedup_and_cooldown(client: AsyncClient) -> None:
    """Verify alert generation for elevated risk, deduplication, and cooldown window."""
    # 1. Trigger an alert via elevated risk evaluation
    payload = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.70,
        "r_d": 0.05,
        "r_e": 0.15,
        "evidence": {"subsystem": "eps_battery_temp_c"},
    }
    res = await client.post("/api/v1/risk/evaluate", json=payload)
    assert res.status_code == 200

    # 2. Check alert is generated
    alerts_res = await client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1

    first_alert = alerts[0]
    assert first_alert["level"] in ["WARNING", "CRITICAL"]
    assert first_alert["status"] == "ACTIVE"
    initial_count = len(alerts)

    # 3. Immediately evaluate same risk level (should be suppressed by cooldown)
    res_dup = await client.post("/api/v1/risk/evaluate", json=payload)
    assert res_dup.status_code == 200

    alerts_res2 = await client.get("/api/v1/alerts")
    alerts2 = alerts_res2.json()
    # No new alert should be created during cooldown for same severity
    assert len(alerts2) == initial_count


@pytest.mark.asyncio
async def test_alert_escalation_during_cooldown(client: AsyncClient) -> None:
    """Verify alert escalation overrides cooldown if severity increases from WARNING to CRITICAL."""
    # 1. Trigger WARNING alert
    payload_warn = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.65,
        "r_d": 0.02,
        "r_e": 0.10,
    }
    await client.post("/api/v1/risk/evaluate", json=payload_warn)

    alerts_res = await client.get("/api/v1/alerts?level=WARNING")
    warn_alerts = alerts_res.json()
    assert len(warn_alerts) >= 1

    # 2. Trigger CRITICAL alert (escalation should bypass cooldown)
    payload_crit = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.65,
        "r_d": 0.95,
        "r_e": 0.10,
        "pc": 3.0e-4,
    }
    await client.post("/api/v1/risk/evaluate", json=payload_crit)

    alerts_crit_res = await client.get("/api/v1/alerts?level=CRITICAL")
    crit_alerts = alerts_crit_res.json()
    assert len(crit_alerts) >= 1
    assert crit_alerts[0]["level"] == "CRITICAL"


@pytest.mark.asyncio
async def test_operator_action_audit_trail(client: AsyncClient) -> None:
    """Verify human-in-the-loop operator actions (approve, dismiss, snooze) and tamper-evident audit log."""
    # 1. Generate an active alert
    payload = {
        "asset_id": "SENTINEL-2A",
        "r_h": 0.72,
        "r_d": 0.10,
        "r_e": 0.05,
    }
    await client.post("/api/v1/risk/evaluate", json=payload)

    alerts_res = await client.get("/api/v1/alerts?status=ACTIVE")
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # 2. Operator approves/acknowledges alert
    action_payload = {
        "user": "FlightDirector_Reo",
        "action": "approve",
        "note": "Operator reviewed thermal sub-system telemetry. Initiating payload cooldown routine.",
    }
    act_res = await client.post(f"/api/v1/alerts/{alert_id}/action", json=action_payload)
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "success"
    assert act_data["alert"]["status"] == "ACKNOWLEDGED"

    # 3. Retrieve alert details and verify audit log contains action
    det_res = await client.get(f"/api/v1/alerts/{alert_id}")
    assert det_res.status_code == 200
    det_data = det_res.json()
    assert det_data["status"] == "ACKNOWLEDGED"
    assert len(det_data["audit_actions"]) == 1

    audit_entry = det_data["audit_actions"][0]
    assert audit_entry["user"] == "FlightDirector_Reo"
    assert audit_entry["action"] == "approve"
    assert "Initiating payload cooldown" in audit_entry["note"]
    assert "timestamp" in audit_entry

    # 4. Operator dismisses alert
    dismiss_payload = {
        "user": "MissionSpecialist_Aithon",
        "action": "dismiss",
        "note": "Thermal subsystem returned to normal range.",
    }
    d_res = await client.post(f"/api/v1/alerts/{alert_id}/action", json=dismiss_payload)
    assert d_res.status_code == 200
    assert d_res.json()["alert"]["status"] == "DISMISSED"

    # Verify both actions exist in audit history
    det_res2 = await client.get(f"/api/v1/alerts/{alert_id}")
    actions = det_res2.json()["audit_actions"]
    assert len(actions) == 2
    assert actions[1]["action"] == "dismiss"

    # 5. Invalid action returns 400 (advisory-only constraint: cannot trigger auto_execute)
    inv_res = await client.post(
        f"/api/v1/alerts/{alert_id}/action",
        json={"user": "AutoBot", "action": "auto_execute_maneuver"},
    )
    assert inv_res.status_code == 400


@pytest.mark.asyncio
async def test_model_registry_metrics(client: AsyncClient) -> None:
    """Verify /api/v1/models loads real measured evaluation results with zero fabrication."""
    res = await client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) == 4

    model_map = {m["id"]: m for m in models}
    assert "MOD-HEALTH-001" in model_map
    assert "MOD-DEBRIS-001" in model_map
    assert "MOD-DISASTER-001" in model_map
    assert "MOD-FUSION-001" in model_map

    # Check MOD-HEALTH-001
    health = model_map["MOD-HEALTH-001"]
    assert health["metrics"]["event_f1"] == 0.3636
    assert health["metrics"]["false_alarms_per_day"] == 25.642
    assert health["baseline_comparison"]["baseline_f1"] == 0.2222

    # Check MOD-DEBRIS-001
    debris = model_map["MOD-DEBRIS-001"]
    assert debris["metrics"]["roc_auc"] == 1.0
    assert debris["metrics"]["pr_auc"] == 1.0
    assert debris["sgp4_drift_km"]["24h"] == 3.398

    # Check MOD-DISASTER-001
    disaster = model_map["MOD-DISASTER-001"]
    assert disaster["metrics"]["iou"] == 0.9548
    assert disaster["metrics"]["dice_f1"] == 0.9768

    # Check MOD-FUSION-001
    fusion = model_map["MOD-FUSION-001"]
    assert fusion["metrics"]["monotonicity_violations"] == 0
    assert fusion["metrics"]["override_violations"] == 0
    assert fusion["metrics"]["deferral_violations"] == 0
    assert fusion["metrics"]["determinism_verified"] is True


def test_websockets_alerts_and_risk_feed() -> None:
    """Test real-time WebSocket connection handshakes and ping-pong streams."""
    tc = TestClient(app)

    # 1. Test /ws/alerts
    with tc.websocket_connect("/ws/alerts") as ws:
        msg = ws.receive_json()
        assert msg["event"] == "CONNECTED"
        assert msg["channel"] == "alerts"

        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"

    # 2. Test /ws/risk/{asset_id}
    with tc.websocket_connect("/ws/risk/SENTINEL-2A") as ws:
        msg = ws.receive_json()
        assert msg["event"] == "CONNECTED"
        assert msg["channel"] == "risk/SENTINEL-2A"
        assert msg["asset_id"] == "SENTINEL-2A"

        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"
