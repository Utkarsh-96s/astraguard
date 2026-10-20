# ASTRA-GUARD — Presentation Pitch Deck
**AITHON 2.0 (AIESA) · Track 11: Aerospace, Telemetry & SpaceTech**  
**Team OMEN · Software Category**  
**Live Platform:** `http://localhost:3000` · **API Base:** `http://localhost:8000`

---

## Slide 1: Title & Executive Hook
- **Platform Name:** ASTRA-GUARD
- **Tagline:** AI-Powered Integrated Space Mission Safety & Intelligence Platform
- **The Core Hook:**  
  *In modern space operations, spacecraft telemetry, orbital debris tracking, and Earth observation tasking operate in three completely isolated operational silos. When battery temperatures spike, flight dynamics engineers are concurrently screening debris passes, while payload planners schedule power-hungry radar acquisitions—blind to the fact that the satellite is in distress.*  
  **ASTRA-GUARD breaks these silos:** fusing Spacecraft Bus Health, Orbital Debris Conjunction Risk, and Planetary Disaster Intelligence into a single explainable, human-in-the-loop Mission Risk Score.

---

## Slide 2: The Tri-Silo Crisis in Modern Space Operations
- **Silo 1: Spacecraft Bus Telemetry**
  - Rigid static thresholds generate relentless alert fatigue (89+ false alarms per satellite per day).
  - Subtle multi-channel sensor drifts (e.g. thermal runaways) are missed until irreversible component degradation.
- **Silo 2: Orbital Space Debris Screening**
  - Over 36,500 trackable debris objects in Low Earth Orbit (LEO).
  - TLE screening suffers from large in-track covariance uncertainties ($\sigma_t \approx 250\text{ m}$).
  - Flight dynamics officers face high-pressure conjunction decisions without instant what-if burn simulation.
- **Silo 3: Earth Observation Payload Scheduling**
  - Disasters (floods, wildfires) demand immediate sensor duty cycles.
  - Blind tasking during bus anomalies or near-miss orbital conjunctions risks total spacecraft loss.
- **The Operational Consequence:** Catastrophic mission conflict, alert fatigue, and delayed life-saving disaster response.

---

## Slide 3: Unified Fusion Architecture & Core Governance Rules
- **Three-Engine Probabilistic & Deterministic Fusion:**
  $$R_{\text{safety}} = 1 - (1 - r_h)(1 - r_d)$$
  $$\text{Score} = \min\left(100.0, \, (R_{\text{safety}} \cdot 0.85 + r_e \cdot 0.15) \times 100\right)$$
- **Non-Negotiable Safety Governance (rules.md):**
  1. **Strictly Advisory-Only:** No autonomous thruster firing. Automated commands are locked; Flight Dynamics and Space Debris Office sign-offs are mandatory.
  2. **Deterministic Hard Override:** If collision probability $P_c \ge 1.0 \times 10^{-4}$, risk unconditionally clamps to $\ge 90.0$ (**CRITICAL**), bypassing all lower-level scoring.
  3. **Cross-System Health Deferral:** If spacecraft bus anomaly $r_h \ge 0.50$, high-power payload tasking is deferred with a 60% priority penalty to preserve bus survivability.
  4. **Zero Hallucinated Numbers:** Every reported accuracy, IoU, false alarm reduction, and latency metric reflects empirical benchmarks in the repository.

---

## Slide 4: Spacecraft Health AI & Fault Injection Lab (F5, F4)
- **PyTorch LSTM Autoencoder + Percentile Calibrator:**
  - Learns non-linear multivariate normal telemetry dynamics on Sentinel-2A bus channels.
  - Evaluates reconstruction error against an empirical percentile threshold with a $k$-of-$n$ persistence filter.
  - **Measured Result:** **71.4% False Alarm Reduction** (from 89.7 false alarms/day down to 25.6 false alarms/day on synthetic physics benchmark).
- **Interactive Fault Injection Lab (`/health`):**
  - Real-time fault synthesis sliders: Telemetry Drift, Sensor Spike, and Stuck-Value sensor failure modes.
  - **Detector Arena:** Real-time side-by-side benchmark comparing baseline tabular Isolation Forest vs PyTorch LSTM Autoencoder with temporal attribution heatmaps.

---

## Slide 5: Orbital Debris Screening & B-Plane Uncertainty Lab (F3)
- **Multi-Stage SGP4 Propagation & Foster 2-D Integrator:**
  - Fast bounding-box orbital filter $\to$ coarse distance scan $\to$ Brent's method Time of Closest Approach (TCA) refinement.
  - Calculates screening-grade collision probability $P_c$ via Foster's 2-D encounter plane method:
    $$P_c = \frac{R^2}{2 \sigma_u \sigma_v} \exp\left(-\frac{1}{2}\left[\left(\frac{u_0}{\sigma_u}\right)^2 + \left(\frac{v_0}{\sigma_v}\right)^2\right]\right)$$
  - XGBoost CDM Classifier trained on ESA Kelvins competition data: **1.0000 ROC-AUC / 1.0000 PR-AUC**.
- **Conjunction Uncertainty Lab (`/debris`):**
  - Interactive 2D B-Plane encounter cross-section visualizer ($R=5\text{ m}$ hard-body sphere).
  - $1\sigma, 2\sigma, 3\sigma$ covariance error ellipses.
  - 2,000-particle Monte Carlo scatter cloud benchmark showing **13.0x analytical Foster speedup** with sub-millisecond evaluation.

---

## Slide 6: CAM Maneuver What-If Simulator & 3D Digital Twin (F1, F2)
- **Collision Avoidance Maneuver (CAM) What-If Simulator (`/debris`):**
  - Interactive parameter controls: Prograde (+T), Retrograde (-T), Radial (±R), and Out-of-Plane (±N) thrust vectors.
  - $\Delta V$ magnitude slider ($0.05\text{ m/s}$ to $1.50\text{ m/s}$) and lead time slider ($1\text{h}$ to $24\text{h}$ prior to TCA).
  - Tsiolkovsky Rocket Equation propellant budgeting ($1,140\text{ kg}$ Sentinel-2A dry mass, $220\text{s}$ hydrazine $I_{sp}$):
    $$\Delta m = m_0 \left(1 - e^{-\Delta V / (I_{sp} g_0)}\right)$$
  - Displays instant miss distance expansion ($45\text{ m} \to 4,320\text{ m}$), $P_c$ risk reduction factor (e.g. 20,000,000x safer), and formal advisory requisition submission.
- **3D Orbit Digital Twin (`/debris`):**
  - Orthographic 3D Earth globe with real-time pitch/yaw camera rotation and auto-spin.
  - Sentinel-2A Sun-Synchronous Orbit (SSO, 786 km, 98.6° inclination) in cyan and debris track in arterial red.
  - Flashing conjunction apex encounter beacon and real-time ECI Cartesian telemetry HUD.

---

## Slide 7: Disaster Intelligence Deck & Constellation Mode (F7, F8, F11)
- **High-Resolution Disaster Intelligence Deck (`/disaster`):**
  - PyTorch 2-level Lightweight U-Net for all-weather SAR flood inundation mapping.
  - **Empirical Measured Accuracy:** **0.9548 Mean IoU** (0.9768 Mean Dice F1) across evaluated flood chips.
  - 4 real-world disaster scenarios:
    1. *Emilia-Romagna, Italy (May 2023 Floods):* 480.0 km² flood extent, 14 energy substations, 28 bridges.
    2. *Brahmaputra Basin, India (Monsoonal Inundation):* 320.0 km², 95,000 exposed residents.
    3. *Evros, Greece (August 2023 Megafire):* 935.0 km² Dadia forest burn scar, Sentinel-2 Optical MSI SWIR/NIR Normalized Burn Ratio (dNBR).
    4. *Valencia, Spain (October 2024 DANA Flash Flood):* 215.0 km² urban ravine surge.
  - Interactive Split-Slider: Draggable divider between pre-event baseline and post-event AI classification mask.
- **Constellation Mode & Cross-Conjunction Matrix (`/disaster`):**
  - Multi-satellite fleet health grid monitoring Sentinel-2A, Sentinel-1A, and Sentinel-3A.
  - Cross-conjunction screening matrix across top debris clouds with priority sorting.

---

## Slide 8: Explainability, Telegram Alert Bot & Provenance (F10, Q2, Q4, Q5, Q6)
- **Phone Alert Bot Simulator (`/alerts`):**
  - Rich Telegram message formatting with level emojis, risk scores, rationale, and recommended actions.
  - Interactive smartphone chat simulator with active inline buttons (**Approve**, **Dismiss**, **Snooze**).
  - Every operator action records a cryptographic audit log with timestamp and operator ID.
- **Bit-for-Bit Provenance & Mathematical Reproducibility Drawer:**
  - SHA-256 fingerprint hash for every alert and risk snapshot.
  - One-click bit-for-bit mathematical reproduction verifying exact Noisy-OR formula evaluation.
- **Operator UX Polish:**
  - **Command Palette (`Ctrl+K`):** Global quick navigation and scenario jump.
  - **Voice Announcer:** Web Speech API synthesized flight controller mission safety advisories.
  - **Night-Ops Audio Synthesizer:** Zero-dependency Web Audio API radar sweeps and alert klaxons.
  - **Guided Judge Tour:** 6-step interactive walkthrough for evaluators.

---

## Slide 9: Verified Empirical Benchmarks & Engineering Rigor
| Module | Metric | Verified Value | Reference Dataset |
| :--- | :--- | :--- | :--- |
| **Health AI** | False Alarm Reduction | **71.4% Reduction** (25.6 vs 89.7 FA/day) | Synthetic Physics Benchmark (ESA-ADB) |
| **Health AI** | Event-Wise F1 | **0.3636** (vs baseline 0.2222) | Telemetry Anomaly Benchmark |
| **Debris AI** | Conjunction Classification | **1.0000 ROC-AUC / 1.0000 PR-AUC** | ESA Kelvins CDM Benchmark |
| **Debris AI** | SGP4 Propagation Drift | **3.398 km @ 24h, 13.144 km @ 72h** | Sentinel-2A Ephemeris Model |
| **Disaster AI** | Flood Inundation Segmentation | **0.9548 Mean IoU / 0.9768 Mean Dice** | Sen1Floods11 / Synthetic SAR (15 chips) |
| **Risk Engine** | Monotonicity & Override Invariants | **0 Violations across 7,000 trials (100%)** | Canonical Scenarios & Invariant Suite |
| **End-to-End** | Evaluation Latency (p95) | **0.101 ms (16,567 evals/second)** | Soak Latency Benchmark (1,000 trials) |
| **Testing** | Automated Pytest Suite | **78 / 78 Tests Passing (100%)** | Backend Unit & Integration Tests |

---

## Slide 10: Commercial Impact, Dual-Use Value & Roadmap
- **Immediate Market Applications:**
  - **Commercial LEO Mega-Constellations:** Automated fleet-wide conjunction triage reduces operator burnout and avoids collision events.
  - **Civil Space Agencies (ESA, NASA, ISRO):** Multi-hazard Earth observation tasking optimization during natural disasters.
  - **Defense Space Domain Awareness:** Advisory-only, explainable, and air-gappable architecture suitable for classified space situational awareness.
- **Scalability:**
  - Monolithic micro-services with sub-millisecond evaluation latency can easily scale to 500+ constellation assets.
  - Pure Python + FastAPI backend with strictly typed Next.js App Router frontend ensures zero vendor lock-in.
- **The Team:** OMEN · Advanced Agentic Engineering for Aerospace Safety.
