"""Tests for Phase 5 Mission Risk Engine, Fusion, and XAI."""
import numpy as np
import pytest
from ml.common.schemas import Attribution
from ml.risk_engine.engine import MissionRiskEngine
from ml.risk_engine.fusion import FusionEngine, load_risk_config
from ml.risk_engine.schemas import OperatorActionType, Recommendation, RiskLevel


def test_load_risk_config() -> None:
    """Test risk engine YAML configuration loading and fallbacks."""
    cfg = load_risk_config()
    assert "fusion" in cfg
    assert pytest.approx(cfg["fusion"]["weight_safety"]) == 0.85
    assert pytest.approx(cfg["fusion"]["weight_eo"]) == 0.15
    assert cfg["hard_overrides"]["conjunction_pc_critical"] == 1.0e-4
    assert cfg["hard_overrides"]["health_degraded_eo_cutoff"] == 0.50


def test_noisy_or_safety_math_and_bounds() -> None:
    """Test probabilistic Noisy-OR safety hazard calculation and invariants."""
    engine = FusionEngine()

    # Boundaries
    assert engine.compute_safety_risk(0.0, 0.0) == 0.0
    assert engine.compute_safety_risk(1.0, 0.0) == 1.0
    assert engine.compute_safety_risk(0.0, 1.0) == 1.0
    assert engine.compute_safety_risk(1.0, 1.0) == 1.0

    # Invariant: R_safety >= max(r_h, r_d)
    for rh in [0.1, 0.4, 0.7]:
        for rd in [0.2, 0.5, 0.8]:
            rs = engine.compute_safety_risk(rh, rd)
            assert rs >= max(rh, rd) - 1e-6
            assert 0.0 <= rs <= 1.0

    # Concrete calculation: r_h = 0.5, r_d = 0.5 -> 1 - (0.5*0.5) = 0.75
    assert pytest.approx(engine.compute_safety_risk(0.5, 0.5), abs=1e-3) == 0.75


def test_mission_risk_score_monotonicity() -> None:
    """Property test: increasing hazards monotonically increases raw mission risk."""
    engine = FusionEngine()
    np.random.seed(123)

    for _ in range(2000):
        rh = float(np.random.uniform(0.0, 0.85))
        rd = float(np.random.uniform(0.0, 0.85))
        re = float(np.random.uniform(0.0, 0.85))

        d_h = float(np.random.uniform(0.0, 0.15))
        d_d = float(np.random.uniform(0.0, 0.15))
        d_e = float(np.random.uniform(0.0, 0.15))

        s1 = engine.evaluate(rh, rd, re)["raw_score"]
        s2 = engine.evaluate(rh + d_h, rd + d_d, re + d_e)["raw_score"]

        assert s2 >= s1 - 1e-4, f"Monotonicity violated: s1={s1}, s2={s2}"


def test_hard_override_pc_critical() -> None:
    """Test Pc >= 1e-4 forces CRITICAL level regardless of low health or disaster score."""
    engine = MissionRiskEngine()

    # Low health and zero disaster priority, but critical conjunction Pc
    snap = engine.evaluate(
        asset_id="SENTINEL-2A",
        health_input=0.01,
        debris_input=0.05,
        disaster_input=0.0,
        pc=1.5e-4,  # Breaches 1e-4 threshold
    )

    assert snap.critical_override_applied is True
    assert snap.level == RiskLevel.CRITICAL
    assert snap.score >= 75.0
    assert "CRITICAL CONJUNCTION EMERGENCY" in snap.rationale

    # Recommendation must be CAM assessment with CRITICAL priority and APPROVE action
    cam_recs = [r for r in snap.recommendations if r.action_code == "CAM_ASSESSMENT"]
    assert len(cam_recs) == 1
    assert cam_recs[0].priority == "critical"
    assert cam_recs[0].required_operator_action == OperatorActionType.APPROVE


def test_hard_override_persistent_health_warning() -> None:
    """Test persistent health anomaly r_h >= 0.90 forces at least WARNING level."""
    engine = MissionRiskEngine()

    snap = engine.evaluate(
        asset_id="SENTINEL-2A",
        health_input=0.92,
        debris_input=0.0,
        disaster_input=0.0,
        is_persistent_health=True,
    )

    assert snap.warning_override_applied is True
    assert snap.level in (RiskLevel.WARNING, RiskLevel.CRITICAL)
    assert snap.score >= 50.0
    assert "SPACECRAFT HEALTH ANOMALY" in snap.rationale


def test_cross_effect_eo_deferral() -> None:
    """Test r_h >= 0.50 triggers EO payload deferral and advisory recommendations."""
    engine = MissionRiskEngine()

    # Nominal health: No deferral, EO tasking allowed
    snap_nom = engine.evaluate(
        asset_id="SENTINEL-2A",
        health_input=0.20,
        debris_input=0.05,
        disaster_input=0.85,
    )
    assert snap_nom.defer_eo_payloads is False
    assert any(r.action_code == "TASK_DISASTER_IMAGERY" for r in snap_nom.recommendations)
    assert not any(r.action_code == "DEFER_EO_PAYLOAD" for r in snap_nom.recommendations)

    # Degraded health >= 0.50: Deferral triggered, imaging postponed
    snap_deg = engine.evaluate(
        asset_id="SENTINEL-2A",
        health_input=0.65,
        debris_input=0.05,
        disaster_input=0.85,
    )
    assert snap_deg.defer_eo_payloads is True
    assert any(r.action_code == "DEFER_EO_PAYLOAD" for r in snap_deg.recommendations)
    assert not any(r.action_code == "TASK_DISASTER_IMAGERY" for r in snap_deg.recommendations)


def test_canonical_scenarios_levels_and_actions() -> None:
    """Test the 4 canonical operational scenarios produce expected levels and actions."""
    engine = MissionRiskEngine()

    # 1. Nominal
    s1 = engine.evaluate("SENTINEL-2A", 0.04, 0.02, 0.10)
    assert s1.level == RiskLevel.NOMINAL
    assert s1.score < 25.0
    assert s1.recommendations[0].action_code == "MONITOR_NOMINAL"
    assert s1.recommendations[0].required_operator_action == OperatorActionType.DISMISS

    # 2. Health Anomaly
    s2 = engine.evaluate("SENTINEL-2A", 0.68, 0.05, 0.25)
    assert s2.level == RiskLevel.WARNING
    assert 50.0 <= s2.score < 75.0
    assert s2.defer_eo_payloads is True

    # 3. Critical Conjunction
    s3 = engine.evaluate("SENTINEL-2A", 0.06, 0.94, 0.15, pc=2.4e-4)
    assert s3.level == RiskLevel.CRITICAL
    assert s3.score >= 75.0
    assert s3.critical_override_applied is True

    # 4. Disaster Observation Tasking
    s4 = engine.evaluate("SENTINEL-2A", 0.16, 0.08, 0.88)
    assert s4.level == RiskLevel.WATCH
    assert 25.0 <= s4.score < 50.0
    assert any(r.action_code == "TASK_DISASTER_IMAGERY" for r in s4.recommendations)


def test_xai_attribution_aggregation_normalization() -> None:
    """Test attribution aggregator scales drivers to 100% of explained risk."""
    engine = MissionRiskEngine()

    health_attrs = [
        Attribution(driver="eps_battery_temp_c", module="health", contribution=0.60, direction="increase"),
        Attribution(driver="eps_bus_voltage_v", module="health", contribution=0.40, direction="increase"),
    ]
    debris_attrs = [
        Attribution(driver="pc_collision_probability", module="debris", contribution=0.70, direction="increase"),
        Attribution(driver="miss_distance_m", module="debris", contribution=0.30, direction="increase"),
    ]

    snap = engine.evaluate(
        asset_id="SENTINEL-2A",
        health_input=0.60,
        debris_input=0.70,
        disaster_input=0.10,
        health_attributions=health_attrs,
        debris_attributions=debris_attrs,
    )

    assert len(snap.drivers) > 0
    total_pct = sum(d.percent_of_risk for d in snap.drivers)
    assert pytest.approx(total_pct, abs=0.5) == 100.0

    for d in snap.drivers:
        assert d.direction in ("increase", "decrease")
        assert d.percent_of_risk >= 0.0
        assert len(d.summary) > 0


def test_deterministic_rationale_and_recommendations() -> None:
    """Test identical inputs generate byte-identical rationale and valid recommendations."""
    engine = MissionRiskEngine()

    ev = {
        "secondary_id": "COSMOS-DEB-1234",
        "miss_distance_m": 420.5,
        "time_to_tca_hours": 18.0,
        "pc": 1.8e-4,
    }

    snap_a = engine.evaluate("SENTINEL-2A", 0.10, 0.90, 0.20, pc=1.8e-4, evidence=ev)
    snap_b = engine.evaluate("SENTINEL-2A", 0.10, 0.90, 0.20, pc=1.8e-4, evidence=ev)

    assert snap_a.rationale == snap_b.rationale
    assert snap_a.score == snap_b.score
    assert len(snap_a.recommendations) == len(snap_b.recommendations)

    for rec in snap_a.recommendations:
        assert isinstance(rec, Recommendation)
        assert rec.required_operator_action in (
            OperatorActionType.APPROVE,
            OperatorActionType.DISMISS,
            OperatorActionType.SNOOZE,
        )
        assert "advisory" in rec.description.lower() or "maintain" in rec.description.lower() or "command" in rec.description.lower()
