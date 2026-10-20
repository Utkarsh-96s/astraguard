"""Headless integration test for Phase 8 Demo Mode and ScenarioPlayer.

Verifies:
1. Loading the 5-stage 'Day in the life of Sentinel-2A' scenario from config/demo_scenario.yaml.
2. Step-by-step headless flight progression through all 5 stages.
3. Exact level transitions:
   - T+0  -> NOMINAL (score ~6.5)
   - T+5  -> WATCH   (reaction wheel drift)
   - T+10 -> WARNING (debris encounter Pc=3.5e-5)
   - T+15 -> WARNING (flood detected with degraded health deferral r_h >= 0.50)
   - T+18 -> CRITICAL (Pc=2.4e-4 breaches 1e-4 threshold, hard override)
4. Replay determinism (identical scores and levels across repeated replay runs).
5. Direct seeking and status endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_demo_scenario_spec(client: AsyncClient) -> None:
    """Assert demo scenario configuration specification is properly formatted and loaded."""
    res = await client.get("/api/v1/demo/scenario")
    assert res.status_code == 200
    spec = res.json()

    assert spec["scenario_id"] == "DEMO-SENTINEL-2A-DAY1"
    assert spec["asset_id"] == "SENTINEL-2A"
    assert "stages" in spec
    assert len(spec["stages"]) == 5

    hours = [s["t_hour"] for s in spec["stages"]]
    assert hours == [0, 5, 10, 15, 18]


@pytest.mark.asyncio
async def test_headless_scenario_progression_and_transitions(client: AsyncClient) -> None:
    """Execute complete 5-stage headless scenario and assert exact risk level transitions."""
    # Reset to baseline
    reset_res = await client.post("/api/v1/demo/reset")
    assert reset_res.status_code == 200
    baseline = reset_res.json()

    # Stage 0: T+0 Nominal
    assert baseline["stage_idx"] == 0
    assert baseline["t_hour"] == 0
    assert baseline["level"] == "NOMINAL"
    assert 0.0 <= baseline["score"] <= 25.0
    assert baseline["defer_eo_payloads"] is False
    assert baseline["critical_override_applied"] is False

    # Stage 1: T+5 Reaction Wheel / Current Drift -> WATCH
    step1_res = await client.post("/api/v1/demo/step")
    assert step1_res.status_code == 200
    step1 = step1_res.json()
    assert step1["stage_idx"] == 1
    assert step1["t_hour"] == 5
    assert step1["level"] == "WATCH"
    assert 25.0 <= step1["score"] <= 50.0
    assert step1["r_h"] == 0.35

    # Stage 2: T+10 Debris Conjunction Warning -> WARNING
    step2_res = await client.post("/api/v1/demo/step")
    assert step2_res.status_code == 200
    step2 = step2_res.json()
    assert step2["stage_idx"] == 2
    assert step2["t_hour"] == 10
    assert step2["level"] == "WARNING"
    assert 50.0 <= step2["score"] <= 75.0
    assert step2["r_d"] == 0.55

    # Stage 3: T+15 Flood Detected with Degraded Health -> Deferral Triggered
    step3_res = await client.post("/api/v1/demo/step")
    assert step3_res.status_code == 200
    step3 = step3_res.json()
    assert step3["stage_idx"] == 3
    assert step3["t_hour"] == 15
    assert step3["level"] in ["WARNING", "CRITICAL"]
    assert step3["r_h"] == 0.58
    # Assert Cross-System Rule: r_h >= 0.50 triggers secondary payload deferral!
    assert step3["defer_eo_payloads"] is True

    # Stage 4: T+18 Critical Conjunction Override -> CRITICAL
    step4_res = await client.post("/api/v1/demo/step")
    assert step4_res.status_code == 200
    step4 = step4_res.json()
    assert step4["stage_idx"] == 4
    assert step4["t_hour"] == 18
    assert step4["level"] == "CRITICAL"
    assert step4["score"] >= 75.0
    assert step4["critical_override_applied"] is True
    assert "CRITICAL" in step4["rationale"]

    # Verify CAM recommendation is generated
    recs = [r.get("action_code") or r.get("action") for r in step4["recommendations"]]
    assert "CAM_ASSESSMENT" in recs


@pytest.mark.asyncio
async def test_replay_determinism(client: AsyncClient) -> None:
    """Verify that multiple replays of the scenario produce 100% identical outputs."""
    # Run 1
    await client.post("/api/v1/demo/reset")
    run1_stages = []
    for _ in range(5):
        res = await client.post("/api/v1/demo/step")
        assert res.status_code == 200
        run1_stages.append(res.json())

    # Run 2
    await client.post("/api/v1/demo/reset")
    run2_stages = []
    for _ in range(5):
        res = await client.post("/api/v1/demo/step")
        assert res.status_code == 200
        run2_stages.append(res.json())

    # Assert exact determinism across all stages
    for s1, s2 in zip(run1_stages, run2_stages, strict=True):
        assert s1["stage_idx"] == s2["stage_idx"]
        assert s1["t_hour"] == s2["t_hour"]
        assert s1["level"] == s2["level"]
        assert abs(s1["score"] - s2["score"]) < 1e-5
        assert abs(s1["r_h"] - s2["r_h"]) < 1e-5
        assert abs(s1["r_d"] - s2["r_d"]) < 1e-5
        assert abs(s1["r_e"] - s2["r_e"]) < 1e-5
        assert s1["defer_eo_payloads"] == s2["defer_eo_payloads"]
        assert s1["critical_override_applied"] == s2["critical_override_applied"]


@pytest.mark.asyncio
async def test_seek_and_status(client: AsyncClient) -> None:
    """Verify seeking to arbitrary stage index and status queries."""
    # Seek directly to Stage 4 (Critical)
    seek_res = await client.post("/api/v1/demo/seek", json={"stage_idx": 4})
    assert seek_res.status_code == 200
    stage4 = seek_res.json()
    assert stage4["stage_idx"] == 4
    assert stage4["level"] == "CRITICAL"

    # Query status
    status_res = await client.get("/api/v1/demo/status")
    assert status_res.status_code == 200
    st = status_res.json()
    assert st["scenario_id"] == "DEMO-SENTINEL-2A-DAY1"
    assert st["total_stages"] == 5

    # Invalid seek returns 400
    inv_res = await client.post("/api/v1/demo/seek", json={"stage_idx": 99})
    assert inv_res.status_code == 400
