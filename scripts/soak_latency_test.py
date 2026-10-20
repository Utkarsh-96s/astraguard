"""Latency & Soak Benchmark for ASTRA-GUARD Mission Risk Engine & Alert Lifecycle."""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("apps/api"))

from ml.risk_engine.engine import MissionRiskEngine
from ml.risk_engine.schemas import RiskSnapshot


def run_latency_benchmark(num_trials: int = 1000) -> dict:
    """Execute risk evaluation benchmark over N trials and compute latency percentiles."""
    print(f"Running ASTRA-GUARD Latency & Soak Benchmark ({num_trials} trials)...")
    engine = MissionRiskEngine()

    latencies_ms: list[float] = []

    # Seed random generator for reproducibility
    rng = np.random.default_rng(42)

    for i in range(num_trials):
        # Generate random inputs
        r_h = float(rng.uniform(0.0, 1.0))
        r_d = float(rng.uniform(0.0, 1.0))
        r_e = float(rng.uniform(0.0, 1.0))
        pc = float(rng.uniform(1e-8, 1e-3)) if rng.random() > 0.5 else None

        t0 = time.perf_counter()
        snapshot: RiskSnapshot = engine.evaluate(
            asset_id="SENTINEL-2A",
            health_input=r_h,
            debris_input=r_d,
            disaster_input=r_e,
            pc=pc,
            evidence={"trial": i},
        )
        t1 = time.perf_counter()

        elapsed_ms = (t1 - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        # Invariant check: ensure valid output structure
        assert 0.0 <= snapshot.score <= 100.0
        assert snapshot.level is not None
        assert len(snapshot.drivers) > 0
        assert len(snapshot.rationale) > 0

    p50 = float(np.percentile(latencies_ms, 50))
    p90 = float(np.percentile(latencies_ms, 90))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    mean_lat = float(np.mean(latencies_ms))
    max_lat = float(np.max(latencies_ms))

    results = {
        "trials": num_trials,
        "mean_latency_ms": round(mean_lat, 3),
        "p50_latency_ms": round(p50, 3),
        "p90_latency_ms": round(p90, 3),
        "p95_latency_ms": round(p95, 3),
        "p99_latency_ms": round(p99, 3),
        "max_latency_ms": round(max_lat, 3),
        "throughput_evals_per_sec": round(1000.0 / max(0.001, mean_lat), 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out_dir = os.path.join("evaluation", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "latency.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Latency Results: p50={p50:.2f}ms, p95={p95:.2f}ms, throughput={results['throughput_evals_per_sec']} evals/sec")
    print(f"Results saved to: {out_path}")
    return results


if __name__ == "__main__":
    run_latency_benchmark()
