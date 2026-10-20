# ASTRA-GUARD — Metrics Traceability & Evaluation Mapping

Per `rules.md` (Prime Directive 2: Zero Fabricated Metrics), this document establishes the formal traceability between preliminary hackathon presentation targets and real empirical measurements stored in `evaluation/results/*.json`.

---

## 1. Consolidated Metrics Mapping Table

| Subsystem / Metric | Pitch Deck Claim | Measured Reality | Benchmark Dataset | Benchmark Output File |
| :--- | :---: | :---: | :--- | :--- |
| **Health AI Anomaly Detection** | "~92% accuracy" | **Event F1 = 0.3636**<br/>**False Alarms/Day = 25.64**<br/>(vs Baseline: 89.75 FA/day, **-71.4% reduction**) | ASTRA-GUARD Synthetic Physics Benchmark (ESA-ADB structure) | [`evaluation/results/health.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/health.json) |
| **Debris Conjunction Risk** | "~85% risk accuracy" | **ROC-AUC = 1.0000**<br/>**PR-AUC = 1.0000**<br/>**Accuracy = 1.0000** | ESA Kelvins Collision Avoidance CDM Dataset | [`evaluation/results/debris.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/debris.json) |
| **SGP4 Orbit Propagation Drift** | "< 1 km error" | **3.398 km @ 24h**<br/>**7.925 km @ 48h**<br/>**13.144 km @ 72h** | Sentinel-2A Ephemeris Drift Model (SGP4 Analytical) | [`evaluation/results/debris.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/debris.json) |
| **Disaster EO Inundation Mapping** | "Instant on-board mapping" | **Mean IoU = 0.9548**<br/>**Mean Dice F1 = 0.9768**<br/>(Min: 0.9363, Max: 0.9676) | Sen1Floods11 Sentinel-1 SAR Dual-Pol Backscatter | [`evaluation/results/disaster.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/disaster.json) |
| **Mission Risk Fusion Invariants** | "Unified risk index" | **0 Monotonicity Violations**<br/>**0 Override Violations**<br/>**0 Deferral Violations**<br/>(5,000 randomized Monte Carlo trials) | Multi-Hazard Mission Risk Invariant Benchmark | [`evaluation/results/risk.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/risk.json) |
| **End-to-End Alert Latency** | "< 30 min end-to-end" | **p50 = 0.05 ms**<br/>**p95 = 0.10 ms**<br/>**p99 = 0.21 ms**<br/>(16,567 evals/sec across 1,000 trials) | Headless Risk Engine Latency & Soak Benchmark | [`evaluation/results/latency.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/latency.json) |

---

## 2. Engineering Rationale for Metric Framing

### 2.1 Anomaly Detection: Event F1 vs. Raw Accuracy
- Raw point-wise accuracy in spacecraft telemetry is dangerously misleading: when anomalies constitute < 1% of the mission timeline, a degenerate model that predicts "NOMINAL" for every second achieves 99% accuracy while missing every catastrophic failure.
- ASTRA-GUARD reports **Event-wise Precision, Recall, and F1**, alongside **False Alarms per Day**.
- The PyTorch LSTM Autoencoder paired with the empirical percentile calibrator and $k$-of-$n$ persistence filter reduces false alarms by **71.4%** compared to standard tabular Isolation Forests (reducing false alarms from 89.7 down to 25.6 per day).

### 2.2 Orbit Drift: Propagation Horizons
- SGP4 is an analytical propagator whose error naturally grows due to unmodeled atmospheric drag perturbations.
- While sub-kilometer accuracy is maintained during the first 6–12 hours, the error horizon is explicitly documented (3.4 km at 24 hours up to 13.1 km at 72 hours).
- Conjunction screening calculates Foster 2-D $P_c$ with explicit **"Screening-Grade"** labels acknowledging assumed covariance.

### 2.3 Disaster Intelligence: Ground-Segment Processing
- High-resolution SAR backscatter differencing and U-Net mask generation are framed as **ground-segment automated ingestion workflows**, operating within minutes of data downlink rather than unproven on-orbit edge hardware.
