"""Tests for Phase 3 Debris Collision Risk AI modules."""
from datetime import UTC, datetime

import numpy as np
from ml.common.protocols import RiskModule
from ml.common.schemas import Attribution, ModuleResult
from ml.debris.cdm_classifier import CDMRiskClassifier
from ml.debris.module import DebrisRiskModule
from ml.debris.pc_engine import FosterCollisionProbabilityEngine
from ml.debris.propagator import SGP4Propagator
from ml.debris.scorer import compute_debris_risk_score
from ml.debris.screener import ConjunctionScreener
from ml.evaluation.debris_eval import evaluate_screening_benchmark, evaluate_sgp4_error_vs_horizon

# Reference Sentinel-2A and Debris TLEs
TLE_S2A_1 = "1 40697U 15028A   26292.50000000  .00000100  00000-0  20000-4 0  9991"
TLE_S2A_2 = "2 40697  98.5700 125.0000 0001200  85.0000 275.1000 14.30820000500001"

TLE_DEB_1 = "1 29834U 99025DF  26292.50000000  .00001500  00000-0  15000-3 0  9992"
TLE_DEB_2 = "2 29834  98.6000 125.0200 0015000  90.0000 270.0000 14.30825000450002"


def test_sgp4_propagator_sanity() -> None:
    """Test SGP4 analytical propagation yields physically sound LEO states."""
    prop = SGP4Propagator.from_tle(TLE_S2A_1, TLE_S2A_2, name="SENTINEL-2A")
    dt = datetime(2026, 10, 20, 12, 0, 0, tzinfo=UTC)

    r, v = prop.propagate_datetime(dt)
    assert r.shape == (3,)
    assert v.shape == (3,)

    # LEO orbit altitude ~786 km -> distance from Earth center ~7164 km
    radius = float(np.linalg.norm(r))
    assert 6800.0 <= radius <= 7500.0

    # LEO orbital speed ~7.4 - 7.6 km/s
    speed = float(np.linalg.norm(v))
    assert 7.0 <= speed <= 8.0

    env = prop.get_orbit_envelope()
    assert 700.0 <= env["perigee_altitude_km"] <= 850.0
    assert 95.0 <= env["inclination_deg"] <= 102.0


def test_conjunction_screening_and_tca_refinement() -> None:
    """Test 3-stage screener discovers close approach and refines TCA."""
    prim = SGP4Propagator.from_tle(TLE_S2A_1, TLE_S2A_2, name="SENTINEL-2A")
    sec = SGP4Propagator.from_tle(TLE_DEB_1, TLE_DEB_2, name="FENGYUN-DEB")

    screener = ConjunctionScreener(
        coarse_altitude_buffer_km=50.0,
        kd_distance_threshold_km=50.0,
        coarse_step_seconds=60.0,
    )

    start_dt = datetime(2026, 10, 20, 0, 0, 0, tzinfo=UTC)
    conjs = screener.screen_pair(prim, sec, start_dt, horizon_hours=48.0)

    assert len(conjs) >= 1
    closest = conjs[0]
    assert closest["miss_distance_km"] < 50.0
    assert closest["miss_distance_m"] == closest["miss_distance_km"] * 1000.0
    assert closest["relative_velocity_kms"] >= 0.0


def test_foster_pc_engine_known_cases() -> None:
    """Test Foster 2-D collision probability properties and known bounds."""
    engine = FosterCollisionProbabilityEngine(hard_body_radius_m=5.0)

    # 1. Zero miss distance (maximum collision hazard)
    res_zero = engine.compute_screening_pc(miss_distance_m=0.0)
    pc_zero = res_zero["pc"]
    assert 1e-4 <= pc_zero <= 1.0
    assert res_zero["risk_class"] == "CRITICAL"
    assert res_zero["screening_grade"] is True
    assert res_zero["pc_method"] == "foster_2d_screening"

    # 2. Large miss distance (10 km separation)
    res_far = engine.compute_screening_pc(miss_distance_m=10000.0)
    assert res_far["pc"] <= 1e-10
    assert res_far["risk_class"] == "NOMINAL"

    # 3. Monotonicity: larger miss distance produces strictly smaller Pc
    res_50 = engine.compute_screening_pc(miss_distance_m=50.0)
    res_100 = engine.compute_screening_pc(miss_distance_m=100.0)
    res_200 = engine.compute_screening_pc(miss_distance_m=200.0)
    assert res_zero["pc"] > res_50["pc"] > res_100["pc"] > res_200["pc"] >= 0.0

    # 4. Explicit CDM covariance calculation
    res_cdm = engine.compute_cdm_pc(miss_distance_m=200.0, c_obs_b=15.0, c_obs_t=400.0, c_obs_n=40.0)
    assert 0.0 <= res_cdm["pc"] <= 1.0
    assert res_cdm["screening_grade"] is False


def test_debris_risk_score_mapping_and_overrides() -> None:
    """Test risk mapping function adheres to Pc >= 1e-4 CRITICAL override."""
    # Critical threshold: Pc >= 1e-4 MUST produce r_d >= 0.90
    score_crit = compute_debris_risk_score(pc=1.5e-4, miss_distance_m=300.0, time_to_tca_hours=12.0)
    assert score_crit >= 0.90

    # Extreme critical: Pc >= 1e-3 forces r_d = 1.00
    score_extreme = compute_debris_risk_score(pc=2.0e-3, miss_distance_m=50.0, time_to_tca_hours=4.0)
    assert score_extreme == 1.0

    # Nominal: Pc < 1e-7 maps to 0.0
    score_nom = compute_debris_risk_score(pc=5.0e-8, miss_distance_m=8000.0, time_to_tca_hours=48.0)
    assert score_nom == 0.0

    # Watch: 1e-6 <= Pc < 1e-5
    score_watch = compute_debris_risk_score(pc=5.0e-6, miss_distance_m=1500.0, time_to_tca_hours=36.0)
    assert 0.20 <= score_watch <= 0.50


def test_xgboost_cdm_classifier() -> None:
    """Test XGBoost CDM model fitting, prediction, and attributions."""
    np.random.seed(42)
    # Generate synthetic training batch
    x_mat = np.random.uniform(10.0, 500.0, size=(40, 7)).astype(np.float32)
    x_mat[:, 6] = np.random.uniform(-8.0, -3.0, size=40)  # log10_pc
    y = (x_mat[:, 6] >= -4.0).astype(int)

    clf = CDMRiskClassifier(n_estimators=15)
    clf.fit(x_mat, y)
    assert clf.is_fitted

    prob, pclass, ev = clf.predict_risk(x_mat[0])
    assert 0.0 <= prob <= 1.0
    assert pclass in ["CRITICAL", "WARNING", "WATCH", "NOMINAL"]
    assert "prob_critical" in ev

    attributions = clf.explain(x_mat[0], top_k=3)
    assert len(attributions) == 3
    assert all(isinstance(a, Attribution) for a in attributions)


def test_debris_risk_module_contract() -> None:
    """Test DebrisRiskModule implements RiskModule protocol."""
    module = DebrisRiskModule()
    assert isinstance(module, RiskModule)

    module.fit()
    assert module.is_fitted

    # Score conjunction event
    event = {
        "miss_distance_m": 450.0,
        "time_to_tca_hours": 18.0,
        "pc": 1.8e-4,
        "secondary_id": "DEB-9999",
    }
    result = module.score(event, asset_id="SENTINEL-2A")

    assert isinstance(result, ModuleResult)
    assert result.score >= 0.90  # Critical override
    assert result.asset_id == "SENTINEL-2A"
    assert result.synthetic is True
    assert result.evidence["risk_class"] == "CRITICAL"

    attributions = module.explain(event, result)
    assert len(attributions) == 3
    assert attributions[0].driver == "pc_collision_probability"
    assert attributions[0].contribution > 0.40


def test_debris_evaluation_harness() -> None:
    """Test evaluation harness helper functions."""
    sgp4_eval = evaluate_sgp4_error_vs_horizon()
    assert sgp4_eval["error_24h_km"] > 0.0
    assert sgp4_eval["error_72h_km"] > sgp4_eval["error_24h_km"]

    scr_eval = evaluate_screening_benchmark()
    assert scr_eval["found_seeded_conjunction"] is True
