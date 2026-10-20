"""Evaluation harness for Phase 5 Mission Risk Engine + XAI."""
import json
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from typing import Any

import numpy as np
import pandas as pd

from ml.common.schemas import Attribution
from ml.risk_engine.engine import MissionRiskEngine
from ml.risk_engine.schemas import RiskLevel


def evaluate_canonical_scenarios(engine: MissionRiskEngine) -> list[dict[str, Any]]:
    """Evaluate 4 standard operational mission scenarios."""
    scenarios = [
        {
            "id": "SCENARIO-01-NOMINAL",
            "name": "Nominal Flight Operations",
            "inputs": {
                "r_h": 0.04,
                "r_d": 0.02,
                "r_e": 0.10,
                "pc": 1.2e-7,
                "is_persistent": False,
                "health_attrs": [
                    Attribution(driver="eps_battery_temp_c", module="health", contribution=0.03, direction="increase")
                ],
                "debris_attrs": [
                    Attribution(driver="miss_distance_m", module="debris", contribution=0.01, direction="increase")
                ],
                "disaster_attrs": [
                    Attribution(driver="clear_sky_visibility", module="disaster", contribution=0.05, direction="increase")
                ],
                "evidence": {"description": "Routine LEO orbit"},
            },
            "expected_level": RiskLevel.NOMINAL,
            "expected_deferral": False,
        },
        {
            "id": "SCENARIO-02-HEALTH-ANOMALY",
            "name": "EPS Battery Thermal Runaway Anomaly",
            "inputs": {
                "r_h": 0.68,
                "r_d": 0.05,
                "r_e": 0.25,
                "pc": 3.0e-7,
                "is_persistent": True,
                "health_attrs": [
                    Attribution(driver="eps_battery_temp_c", module="health", contribution=0.65, direction="increase"),
                    Attribution(driver="eps_bus_voltage_v", module="health", contribution=0.25, direction="increase"),
                ],
                "debris_attrs": [
                    Attribution(driver="miss_distance_m", module="debris", contribution=0.02, direction="increase")
                ],
                "disaster_attrs": [
                    Attribution(driver="flooded_area_km2", module="disaster", contribution=0.45, direction="increase")
                ],
                "evidence": {
                    "primary_channel": "eps_battery_temp_c",
                    "anomaly_subsystem": "EPS_BATTERY",
                    "flooded_area_km2": 180.0,
                },
            },
            "expected_level": RiskLevel.WARNING,
            "expected_deferral": True,
        },
        {
            "id": "SCENARIO-03-CRITICAL-CONJUNCTION",
            "name": "Critical Fengyun-1C Debris Conjunction",
            "inputs": {
                "r_h": 0.06,
                "r_d": 0.94,
                "r_e": 0.15,
                "pc": 2.4e-4,  # Breaches 1e-4 critical override
                "is_persistent": False,
                "health_attrs": [
                    Attribution(driver="obc_temp_c", module="health", contribution=0.02, direction="increase")
                ],
                "debris_attrs": [
                    Attribution(driver="pc_collision_probability", module="debris", contribution=0.68, direction="increase"),
                    Attribution(driver="miss_distance_m", module="debris", contribution=0.22, direction="increase"),
                ],
                "disaster_attrs": [],
                "evidence": {
                    "secondary_id": "FENGYUN-1C-DEB-29834",
                    "miss_distance_m": 315.4,
                    "time_to_tca_hours": 14.2,
                    "pc": 2.4e-4,
                },
            },
            "expected_level": RiskLevel.CRITICAL,
            "expected_deferral": False,
        },
        {
            "id": "SCENARIO-04-DISASTER-TASKING",
            "name": "Cyclone Flood Emergency Observation Tasking",
            "inputs": {
                "r_h": 0.16,
                "r_d": 0.08,
                "r_e": 0.88,
                "pc": 2.0e-7,
                "is_persistent": False,
                "health_attrs": [],
                "debris_attrs": [],
                "disaster_attrs": [
                    Attribution(driver="flooded_area_km2", module="disaster", contribution=0.55, direction="increase"),
                    Attribution(driver="population_exposure", module="disaster", contribution=0.30, direction="increase"),
                ],
                "evidence": {
                    "disaster_type": "flood",
                    "disaster_event_id": "DISASTER-CYCLONE-FLOOD-001",
                    "flooded_area_km2": 320.0,
                },
            },
            "expected_level": RiskLevel.WATCH,
            "expected_deferral": False,
        },
    ]

    results: list[dict[str, Any]] = []

    for sc in scenarios:
        inp = sc["inputs"]
        snapshot = engine.evaluate(
            asset_id="SENTINEL-2A",
            health_input=inp["r_h"],
            debris_input=inp["r_d"],
            disaster_input=inp["r_e"],
            pc=inp["pc"],
            is_persistent_health=inp["is_persistent"],
            health_attributions=inp["health_attrs"],
            debris_attributions=inp["debris_attrs"],
            disaster_attributions=inp["disaster_attrs"],
            evidence=inp.get("evidence"),
        )

        assert snapshot.level == sc["expected_level"], (
            f"Scenario {sc['id']} expected level {sc['expected_level']} but got {snapshot.level}"
        )
        assert snapshot.defer_eo_payloads == sc["expected_deferral"], (
            f"Scenario {sc['id']} expected deferral {sc['expected_deferral']} but got {snapshot.defer_eo_payloads}"
        )

        results.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "score": snapshot.score,
            "level": snapshot.level.value,
            "r_safety": snapshot.r_safety,
            "critical_override_applied": snapshot.critical_override_applied,
            "warning_override_applied": snapshot.warning_override_applied,
            "defer_eo_payloads": snapshot.defer_eo_payloads,
            "top_driver": snapshot.drivers[0].driver if snapshot.drivers else "none",
            "top_driver_share": snapshot.drivers[0].percent_of_risk if snapshot.drivers else 0.0,
            "recommendation_count": len(snapshot.recommendations),
            "primary_action": snapshot.recommendations[0].action_code if snapshot.recommendations else "NONE",
            "rationale": snapshot.rationale,
        })

    return results


def evaluate_property_invariants(engine: MissionRiskEngine, num_trials: int = 5000) -> dict[str, Any]:
    """Test mathematical invariants: monotonicity, boundedness, overrides, and determinism."""
    np.random.seed(42)

    # 1. Monotonicity checks
    monotonicity_violations = 0
    for _ in range(num_trials):
        r_h1 = float(np.random.uniform(0.0, 0.9))
        r_d1 = float(np.random.uniform(0.0, 0.9))
        r_e1 = float(np.random.uniform(0.0, 0.9))

        delta_h = float(np.random.uniform(0.0, 0.1))
        delta_d = float(np.random.uniform(0.0, 0.1))
        delta_e = float(np.random.uniform(0.0, 0.1))

        res1 = engine.fusion.evaluate(r_h1, r_d1, r_e1)
        res2 = engine.fusion.evaluate(r_h1 + delta_h, r_d1 + delta_d, r_e1 + delta_e)

        if res2["score"] < res1["score"] - 1e-4:
            monotonicity_violations += 1

    # 2. Hard Override Invariant (Pc >= 1e-4 -> CRITICAL unconditionally)
    override_violations = 0
    for _ in range(1000):
        r_h = float(np.random.uniform(0.0, 0.2))  # healthy
        r_d = float(np.random.uniform(0.0, 0.3))  # low debris score
        r_e = float(np.random.uniform(0.0, 0.2))  # low eo
        pc = float(np.random.uniform(1.0e-4, 1.0e-2))  # critical pc

        res = engine.fusion.evaluate(r_h, r_d, r_e, pc=pc)
        if res["level"] != RiskLevel.CRITICAL or res["score"] < 75.0:
            override_violations += 1

    # 3. Cross-Effect Invariant (r_h >= 0.50 -> defer_eo == True unconditionally)
    deferral_violations = 0
    for _ in range(1000):
        r_h = float(np.random.uniform(0.50, 1.0))
        r_d = float(np.random.uniform(0.0, 1.0))
        r_e = float(np.random.uniform(0.0, 1.0))

        res = engine.fusion.evaluate(r_h, r_d, r_e)
        if not res["defer_eo_payloads"]:
            deferral_violations += 1

    # 4. Determinism Invariant (Identical inputs -> identical outputs)
    snap_a = engine.evaluate("TEST-SAT", 0.35, 0.45, 0.60)
    snap_b = engine.evaluate("TEST-SAT", 0.35, 0.45, 0.60)
    determinism_match = (
        snap_a.score == snap_b.score
        and snap_a.level == snap_b.level
        and snap_a.rationale == snap_b.rationale
        and len(snap_a.recommendations) == len(snap_b.recommendations)
    )

    return {
        "trials_tested": num_trials,
        "monotonicity_violations": monotonicity_violations,
        "override_violations": override_violations,
        "deferral_violations": deferral_violations,
        "determinism_verified": determinism_match,
    }


def run_evaluation() -> dict[str, Any]:
    """Execute complete Phase 5 Mission Risk Engine + XAI evaluation harness."""
    print("================================================================================", flush=True)
    print("ASTRA-GUARD: Running Phase 5 Mission Risk Engine + XAI Evaluation", flush=True)
    print("================================================================================", flush=True)

    engine = MissionRiskEngine()

    print("1. Evaluating Canonical Mission Scenarios...", flush=True)
    scenario_results = evaluate_canonical_scenarios(engine)
    for sc in scenario_results:
        print(
            f"   -> {sc['scenario_id']} ({sc['name']}): Score={sc['score']:.1f} | Level={sc['level']} | "
            f"Action={sc['primary_action']} | Defer EO={sc['defer_eo_payloads']}",
            flush=True,
        )

    print("2. Verifying Mathematical & Behavioral Invariants...", flush=True)
    invariants = evaluate_property_invariants(engine, num_trials=5000)
    print(f"   -> Monotonicity Violations: {invariants['monotonicity_violations']}", flush=True)
    print(f"   -> Hard Override Violations: {invariants['override_violations']}", flush=True)
    print(f"   -> Cross-Effect Deferral Violations: {invariants['deferral_violations']}", flush=True)
    print(f"   -> Determinism Verified: {invariants['determinism_verified']}", flush=True)

    payload = {
        "fusion_formulation": "Noisy-OR: R_safety = 1 - (1 - r_h)(1 - r_d); R_mission = 100 * (0.85*R_safety + 0.15*r_e)",
        "hard_overrides": {
            "conjunction_pc_critical_threshold": 1.0e-4,
            "persistent_health_warning_threshold": 0.90,
            "health_degraded_eo_deferral_threshold": 0.50,
        },
        "canonical_scenarios": scenario_results,
        "invariant_verification": invariants,
        "timestamp": pd.Timestamp.now().isoformat(),
    }

    target_paths = ["evaluation/results/risk.json", "ml/evaluation/results/risk.json"]
    for path in target_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Saved evaluation results to: {path}", flush=True)

    return payload


if __name__ == "__main__":
    run_evaluation()
