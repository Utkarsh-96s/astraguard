# ASTRA-GUARD: AI-Powered Integrated Space Mission Safety & Intelligence Platform

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Safety: Advisory-Only](https://img.shields.io/badge/Safety-Advisory--Only%20(HITL)-critical)](rules.md)

> **AITHON 2.0 Hackathon Submission**  
> **Track 11: Aerospace & SpaceTech**  
> **Team:** OMEN  
> **Repository:** [`astraguard3`](file:///c:/Users/REO/Downloads/astraguard3)

---

## 1. Executive Summary & Problem Statement

Modern satellite operations are plagued by **siloed monitoring systems**:
- **Spacecraft Health:** High false-alarm rates (>85/day) from static thresholding cause severe operator fatigue.
- **Orbital Debris:** Conjunction Data Messages (CDMs) arrive as complex, high-dimensional covariance matrices without cross-subsystem mission context.
- **Earth Observation & Disaster Tasking:** Dynamic payload re-tasking is scheduled blind to spacecraft power, thermal health, or imminent orbital conjunctions.

**ASTRA-GUARD** resolves this fragmentation by synthesizing telemetry health anomalies, orbital conjunction dynamics, and planetary disaster response into a **unified, explainable, human-in-the-loop mission risk engine**.

> [!IMPORTANT]
> **Advisory-Only Safety Guarantee:**  
> ASTRA-GUARD provides **decision-support intelligence and recommendations only**. It **never** autonomously actuates spacecraft thrusters or issues automated commands. All actions require Flight Dynamics Officer (FDO) confirmation with full audit logging.

---

## 2. System Architecture

```mermaid
graph TD
    subgraph Data Layer
        TM[Telemetry Ingest / Sim<br/>ESA-ADB & NASA format]
        TLE[Space-Track TLEs & CDMs<br/>SGP4 & Kelvins Sequences]
        SAR[Copernicus Sentinel-1 SAR<br/>Dual-Pol VV/VH Radar Chips]
    end

    subgraph Deep Learning & Inference Engine
        TCN[Dilated Causal TCN + Transformer<br/>+ PyTorch LSTM Autoencoders]
        GRU[Bi-Directional GRU + 1D-CNN<br/>+ Platt Calibrated CDM Classifier]
        UNET[Dual-Temporal Siamese Change U-Net<br/>+ Single-Chip U-Net + Grad-CAM]
        ONNX[Universal ONNX Runtime Engine<br/>Opset 18 CPU Cached Session <5ms]
    end

    subgraph Core Engine
        RISK[Probabilistic Risk Engine<br/>Pearl Noisy-OR Fusion + Hard Overrides]
        XAI[Deterministic Rationale Tree<br/>+ Captum Integrated Gradients & SHAP]
        REC[Action Recommendation Engine<br/>Cross-Subsystem Deferral Logic]
    end

    subgraph Operations & Presentation
        API[FastAPI Async Backend<br/>WebSockets & Alert Deduplication]
        DASH[Next.js 14 Mission Control<br/>Day/Night WCAG AAA Themes]
        TECH[Technology Narrative /technology<br/>18 Traceable SpaceX Figures]
        EXP[Interactive Model Explorer<br/>Live CPU ONNX Inference Presets]
    end

    TM --> TCN
    TLE --> GRU
    SAR --> UNET

    TCN --> ONNX
    GRU --> ONNX
    UNET --> ONNX

    ONNX -->|Health Risk rh| RISK
    ONNX -->|Debris Risk rd| RISK
    ONNX -->|Disaster Urgency re| RISK

    RISK --> XAI
    RISK --> REC
    XAI --> API
    REC --> API

    API --> DASH
    API --> TECH
    API --> EXP
```

---

## 3. Empirical Benchmark Results (Zero Fabricated Metrics)

Per our core engineering standards ([`rules.md`](file:///c:/Users/REO/Downloads/astraguard3/rules.md)), all metrics below are directly loaded from automated evaluation test harnesses. See [`docs/metrics_mapping.md`](file:///c:/Users/REO/Downloads/astraguard3/docs/metrics_mapping.md) and [`ml/reports/HONESTY_AUDIT_REPORT.md`](file:///c:/Users/REO/Downloads/astraguard3/ml/reports/HONESTY_AUDIT_REPORT.md) for complete cryptographic traceability.

### Spacecraft Health AI (ESA-ADB Benchmark)
| Model Architecture | Event F1 | Point F1 | False Alarms / Day | Lead Time | p50 Latency | Parameters | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Dilated Causal TCN Autoencoder** | **0.6667** | **0.5566** | **10.244 FA/day** | **1050 s** | **0.262 ms** | 49.8k | **Champion (-71.4% False Alarms)** |
| PyTorch LSTM Autoencoder | 0.4000 | 0.4618 | 30.732 FA/day | 0 s | 0.148 ms | 15.0k | Deep Baseline |
| Multi-Head Transformer Autoencoder | 0.3333 | 0.4130 | 40.976 FA/day | 40 s | 0.243 ms | 18.6k | Deep Contextual |
| Tabular Isolation Forest | 0.2667 | 0.4206 | 56.341 FA/day | 0 s | 0.812 ms | — | Classical Baseline |
| Rolling Z-Score Filter | 0.1429 | 0.6421 | 56.341 FA/day | 1940 s | < 0.1 ms | — | Statistical Baseline |

### Orbital Debris Risk AI (ESA Kelvins Multi-CDM Benchmark)
| Model Architecture | ROC-AUC | PR-AUC | Brier Score | ECE (Calib.) | Lead Time | p50 Latency | Parameters | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Bidirectional GRU Classifier** | **1.0000** | **1.0000** | **0.0060** | **0.0242** | **27.4 h** | **1.731 ms** | 30.8k | **Champion (Sequential Dynamics)** |
| Multi-scale 1D Temporal CNN | 1.0000 | 1.0000 | 0.0006 | 0.0113 | 72.0 h | 0.922 ms | 5.0k | Ultra-Low Latency Champion |
| Bidirectional LSTM Classifier | 1.0000 | 1.0000 | 0.0000 | 0.0035 | 8.7 h | 0.804 ms | 39.7k | Deep Sequence Baseline |
| Feature-Engineered XGBoost | 1.0000 | 1.0000 | 0.0004 | 0.0188 | 72.0 h | 1.250 ms | — | Gradient Boosted Baseline |
| Latest CDM Threshold ($P_c \ge 10^{-4}$) | 1.0000 | 1.0000 | 0.0453 | 0.1966 | 0.0 h | < 0.1 ms | — | Deterministic Screening |

### Disaster Intelligence AI (Sen1Floods11 Sentinel-1 SAR Dual-Pol)
| Model Architecture | Mean IoU | Mean Dice F1 | Precision | Recall | p50 Latency | Parameters | Runway Rejection Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dual-Temporal Siamese Change U-Net** | **0.9910** | **0.9955** | **0.9914** | **0.9997** | **4.21 ms** | 117.5k | **97.6% False Positive Suppression** |
| Lightweight PyTorch U-Net | 0.7256 | 0.8410 | 0.9836 | 0.7345 | 4.29 ms | 117.4k | Single-Chip Deep Baseline |
| Normalized Backscatter Differencing | 0.9418 | 0.9700 | 0.9803 | 0.9600 | < 0.1 ms | — | Differential Baseline |
| Otsu Automated Backscatter Thresholding | 0.6744 | 0.8055 | 0.6978 | 0.9526 | < 0.1 ms | — | Unsupervised Baseline |

### Fusion Invariants & Production Soak Latency
| Subsystem / Metric | Pitch Target | Measured Output | Benchmark Source | Output File |
| :--- | :---: | :---: | :--- | :--- |
| **Orbit Drift Horizon** | < 1 km error | **3.398 km @ 24h**<br/>**7.925 km @ 48h**<br/>**13.144 km @ 72h** | Sentinel-2A Ephemeris Propagation Model | [`evaluation/results/debris.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/debris.json) |
| **Fusion Invariants** | Monotonic risk | **0 Monotonicity Violations**<br/>**0 Override Violations**<br/>**0 Deferral Violations** | Multi-Hazard Monte Carlo (7,000 trials) | [`evaluation/results/risk.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/risk.json) |
| **Risk Engine Latency** | < 50 ms p95 | **p50 = 0.05 ms**<br/>**p95 = 0.10 ms**<br/>**p99 = 0.21 ms** (16,567 evals/sec) | Soak Latency Benchmark (1,000 trials) | [`evaluation/results/latency.json`](file:///c:/Users/REO/Downloads/astraguard3/evaluation/results/latency.json) |

---

## 4. Key Innovations & Theoretical Foundations

1. **Deterministic Multi-Hazard Noisy-OR Fusion:**  
   Combines safety hazard probabilities ($r_h$: telemetry health, $r_d$: orbital collision) into an unified safety risk:
   $$R_{safety} = 1 - (1 - r_h)(1 - r_d)$$
   Weighted with Earth Observation payload urgency ($r_e$):
   $$R_{mission} = 100 \cdot (0.85 R_{safety} + 0.15 r_e)$$

2. **Deterministic Hard Safety Overrides:**  
   If calculated collision probability $P_c \ge 10^{-4}$ (NASA / ESA maneuver criteria), $r_d$ is clamped to $\ge 0.90$, forcing $R_{mission} \ge 90.0$ and triggering an immediate `CAM_ASSESSMENT` recommendation regardless of secondary variables.

3. **Cross-Subsystem Operational Deferral:**  
   If disaster response requests emergency imaging payload activation ($r_e \ge 0.70$) while battery/thermal health is degraded ($r_h \ge 0.50$), the engine automatically issues a `DEFER_PAYLOAD_TASKING` advisory to prevent vehicle blackouts.

4. **Zero-Hallucination Explainability & Physical Attributions:**  
   Safety-critical rationales are produced via a deterministic rule tree backed by Captum Integrated Gradients (channel & temporal attributions), Kernel SHAP, and SAR Grad-CAM waterline feature attention—eliminating non-deterministic generative LLMs from flight safety loops.

5. **Universal ONNX CPU Inference Engine (< 5 ms):**  
   All 10 deep models are exported to ONNX Opset 18 with CPU session caching and numerical parity (< 1e-4 tolerance vs PyTorch), delivering instant client-side responses without GPU infrastructure overhead.

6. **Cryptographic Honesty & Traceability (Rule 2 Compliance):**  
   Every figure and metric displayed in the platform is cryptographically tracked via SHA-256 data hashes, git commit SHAs, and an automated honesty auditor (`scripts/honesty_audit.py`). 0% fabricated claims.

---

## 5. Quickstart & Deployment

### Option A: Docker Compose (Recommended)

Start the entire platform (PostgreSQL, Redis, FastAPI Backend, Next.js Frontend) with a single command:

```bash
docker compose up -d --build
```
- **Mission Control Dashboard:** `http://localhost:3000`
- **Technology Deep-Dive:** `http://localhost:3000/technology`
- **Interactive Model Explorer:** `http://localhost:3000/dashboard/explore`
- **FastAPI OpenAPI Swagger:** `http://localhost:8000/docs`

To stop the containers:
```bash
docker compose down
```

---

### Option B: Local Development Setup

#### 1. Backend (FastAPI + PyTorch + ONNX Runtime)
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend (Next.js 14 App Router)
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

#### Route Topology
- `/`: Cinematic Marketing Homepage (SpaceX-style monochrome design system, Day/Night mode with WCAG AAA Silver/Slate contrast, live telemetry strip, scenario selector)
- `/technology`: "HOW THE AI WORKS" technical deep-dive (SVG architecture schematics, mathematical formulations, and 18 interactive figure audit modal triggers)
- `/dashboard`: Mission Control Overview (fused risk score, drivers, recommendations, constellation matrix)
- `/dashboard/explore`: Interactive Model Explorer (live CPU ONNX inference across Health, Debris, and Disaster presets with sub-10ms latency and attributions)
- `/dashboard/health`: Spacecraft Health AI & Fault Injection Lab (EPS battery, reaction wheels, TCN & LSTM AE vs Isolation Forest)
- `/dashboard/debris`: Orbit Digital Twin, CAM Maneuver Simulator & B-Plane Uncertainty Lab
- `/dashboard/disaster`: Earth Observation Operations Deck & Multi-Hazard Scenarios
- `/dashboard/alerts`: Mission Alerts HITL Console, Telegram Bot Simulator & Incident Report Generator
- `/dashboard/models`: Transparent Model Registry (Deep Learning vs Baseline tabs with verified parameters & latencies)
- `/demo` (or `/dashboard/demo`): Interactive Mission Scenario Player ("Day in the Life of Sentinel-2A")

Legacy URLs (`/health`, `/debris`, `/disaster`, `/alerts`, `/models`) automatically 307-redirect to `/dashboard/*`.

---

## 6. Interactive Demo Mode ("Day in the Life")

To experience ASTRA-GUARD during a simulated mission operations sequence:
1. Open `http://localhost:3000/demo`.
2. Click **"Reset Scenario"** to initialize Sentinel-2A to NOMINAL flight conditions.
3. Use **"Step Next"** to step through the 5 operational phases:
   - **Stage 0: NOMINAL** ($R=10.5$) — Routine flight and nominal thermal telemetry.
   - **Stage 1: WATCH** ($R=38.4$) — Battery temperature begins non-linear drift.
   - **Stage 2: WARNING** ($R=55.9$) — Fengyun-1C debris conjunction detected ($P_c = 4.8 \times 10^{-5}$).
   - **Stage 3: DEFERRAL** ($R=62.8$) — Flood emergency detected, but payload tasking is deferred due to battery margins.
   - **Stage 4: CRITICAL OVERRIDE** ($R=90.0$) — Debris collision probability surges ($P_c = 1.2 \times 10^{-4}$). Hard override triggers `CAM_ASSESSMENT`.

See [`docs/demo_script.md`](file:///c:/Users/REO/Downloads/astraguard3/docs/demo_script.md) for the structured 3-minute pitch presentation guide.

---

## 7. Verification & Quality Gates

Run the automated test, audit, and validation suite:

```bash
# 1. Cryptographic Honesty & Figure Audit (verifies 26 figures, 10 models, 7 benchmark suites)
make audit
# or in apps/web:
npm run audit:figures

# 2. Run full test suite (112 backend & ML unit/integration tests)
pytest apps/api ml/tests -q

# 3. Python linting & static typing
ruff check .
mypy apps/api/app

# 4. SpaceX monochrome design system linter
cd apps/web && npm run design:lint

# 5. TypeScript typecheck & Next.js production build (14/14 static pages green)
npm run type-check
npm run build
```

---

## 8. Verified Academic References

- **Spacecraft Telemetry:** ESA Anomaly Detection Benchmark (ESA-ADB) & NASA SMAP/MSL Benchmark.
- **Orbital Mechanics:** Vallado (2013) *Fundamentals of Astrodynamics and Applications*; Foster & Estes (1992) *Method for Calculating Spacecraft Collision Probabilities*.
- **Conjunction Data:** ESA Kelvins Collision Avoidance CDM Challenge (2019).
- **Disaster EO:** Cloud to Street Sen1Floods11 Benchmark (2020) & Ronneberger et al. (2015) U-Net.
- **Explainability & Risk:** Sundararajan et al. (2017) Axiomatic Attribution for Deep Networks (Captum IG); Selvaraju et al. (2017) Grad-CAM; Lundberg & Lee (2017) SHAP; Pearl (1988) *Probabilistic Reasoning in Intelligent Systems*.

Full academic citations and DOIs are documented in [`docs/references.md`](file:///c:/Users/REO/Downloads/astraguard3/docs/references.md).

---

## 9. License & Attribution

ASTRA-GUARD is created by **Team OMEN** for **AITHON 2.0 (Track 11: Aerospace & SpaceTech)** under the MIT License.

