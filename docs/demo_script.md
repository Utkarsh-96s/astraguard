# ASTRA-GUARD — AITHON 2.0 Presentation Demo Script
**Track 11: Aerospace & SpaceTech**  
**Team OMEN**  
**Duration:** Exactly 3 Minutes (180 Seconds)  
**Target Audience:** Technical Judges, Mission Operations Experts, Defense & Commercial Satellite Operators  
**Platform URL:** `http://localhost:3000` (Local) / `/demo` (Demo Mode)

---

## Pre-Flight Checklist
- [ ] API backend running (`uvicorn app.main:app --port 8000`)
- [ ] Next.js dashboard running (`npm run dev` at `http://localhost:3000`)
- [ ] Browser open to `http://localhost:3000/demo`
- [ ] Demo scenario initialized (click **"Reset Scenario"** before stepping onto stage)
- [ ] Terminal ready to show `pytest apps/api/tests` if requested

---

## Chronological Pitch Walkthrough

### 0:00 – 0:30 | The Problem & The Core Vision (Slide 1 & Overview)
**Visual:** Browser at `http://localhost:3000/` (Overview Page with Live Risk Gauge & Fleet Status)

> **Speaker:**  
> *"Good morning, esteemed judges. In modern satellite operations, telemetry data is trapped in isolated silos. When battery cell temperatures spike, flight dynamics engineers are concurrently screening orbital debris, while payload controllers schedule earth observation tasking—completely unaware that the spacecraft is entering thermal distress.*  
>  
> *This lack of cross-subsystem awareness leads to two fatal failure modes: **alert fatigue from raw threshold alarms**, and **catastrophic mission conflict**—such as slewing heavy optical instruments right as a close orbital conjunction requires thruster stand-by.*  
>  
> *Meet **ASTRA-GUARD**: the first AI-driven Space Mission Safety & Intelligence platform that fuses Spacecraft Health, Orbital Debris Conjunctions, and Planetary Disaster Tasking into a single, explainable, human-in-the-loop decision engine."*

---

### 0:30 – 1:00 | The Tri-Subsystem Architecture (Pages Tour)
**Visual:** Rapid navigation through `/health`, `/debris`, and `/disaster`.

> **Speaker:**  
> *"Let's look under the hood across our three specialized AI engines:*  
>  
> 1. **Spacecraft Health AI (`/health`):** Rather than static yellow/red thresholds, our PyTorch LSTM Autoencoder learns non-linear nominal telemetry dynamics. Combined with an empirical percentile calibrator and a $k$-of-$n$ persistence filter, it cuts false alarms by **71.4%**—from 89 false alarms per day down to 25.  
>  
> 2. **Orbital Debris Risk AI (`/debris`):** We run SGP4 analytical propagation combined with an analytical Foster 2-D B-Plane collision probability integrator ($P_c$) and an XGBoost CDM risk classifier trained on ESA Kelvins data, hitting an empirical ROC-AUC of **1.0000**.  
>  
> 3. **Disaster Intelligence AI (`/disaster`):** When earthquakes or floods strike, our SAR backscatter U-Net segments flood inundation with a **0.9548 Mean IoU**—instantly generating operational GeoJSON tasking footprints."*

---

### 1:00 – 2:00 | The Live Demonstration: "A Day in the Life" (`/demo`)
**Visual:** Switch to `http://localhost:3000/demo`. Walk through the 5 stages sequentially using the **"Step Next"** button.

> **Speaker:**  
> *"Now let's watch ASTRA-GUARD operate in real-time during a critical mission day for Sentinel-2A."*  
>  
> *(Click: Stage 0 $\to$ Stage 1)*  
> *"**Stage 1: Thermal Drift (WATCH).** Battery cell temperature begins an uncharacteristic upward drift. The LSTM Autoencoder flags an anomaly at $r_h = 0.42$. Notice how the Unified Mission Risk rises gracefully to WATCH, but no false alarms interrupt sleep cycles."*  
>  
> *(Click: Stage 1 $\to$ Stage 2)*  
> *"**Stage 2: Debris Conjunction (WARNING).** Simultaneously, tracking stations detect a Fengyun-1C debris fragment on an intersecting orbital path. Foster 2-D calculates $P_c = 4.8 \times 10^{-5}$ ($r_d = 0.55$). Our probabilistic Noisy-OR fusion immediately escalates the mission risk to 55.9 (WARNING), recommending Conjunction Assessment Monitoring."*  
>  
> *(Click: Stage 2 $\to$ Stage 3)*  
> *"**Stage 3: The Cross-Effect Deferral (DEFERRAL).** Here is where conventional siloed systems fail: A catastrophic flood is detected over California, requesting immediate SAR payload activation. But ASTRA-GUARD's Cross-Effect rules recognize that battery degradation prevents high-power radar tasking. The recommendation engine automatically issues **DEFER_PAYLOAD_TASKING** to protect spacecraft power margins."*  
>  
> *(Click: Stage 3 $\to$ Stage 4)*  
> *"**Stage 4: Collision Imminent (CRITICAL OVERRIDE).** New radar tracking shows the debris orbit tightening. $P_c$ surges to $1.2 \times 10^{-4}$. Because $P_c \ge 10^{-4}$ represents an imminent collision hazard, ASTRA-GUARD triggers a **Deterministic Hard Override**: risk immediately clamps to 90.0 CRITICAL, recommending an emergency Collision Avoidance Maneuver (CAM)."*

---

### 2:00 – 2:30 | Explainable AI, Telegram Bot & Mathematical Provenance
**Visual:** Click on `/alerts`, then open the **"Telegram Bot Simulator"** and **"Provenance Drawer"**.

> **Speaker:**  
> *"Notice what ASTRA-GUARD does **not** do: it does **not** fire thrusters autonomously.  
> Per our core safety architecture, **ASTRA-GUARD is strictly Advisory-Only**.  
>  
> Every recommendation is backed by a deterministic rationale tree and SHAP telemetry feature attributions—no black-box hallucinations.  
>  
> When a critical alert fires, our **Telegram Alert Bot** dispatches instant rich notifications to mobile flight controllers. Right in our phone simulator, operators can tap **Approve**, **Dismiss**, or **Snooze**, instantly logging an immutable audit record with cryptographic timestamping.  
>  
> Furthermore, with our **Cryptographic Provenance Modal**, any alert can be bit-for-bit mathematically verified with its SHA-256 fingerprint, guaranteeing 100% auditability for civil and defense safety boards."*

---

### 2:30 – 3:00 | Engineering Rigor & Conclusion
**Visual:** Navigate to `http://localhost:3000/models` (Verified Model Registry with live JSON badges) and launch the **"Judge Tour"** from the Navbar.

> **Speaker:**  
> *"Finally, we stand on zero fabricated numbers. Every metric you see on this dashboard is directly read from empirical evaluation benchmarks in our codebase:  
> - **71.4% false alarm reduction** on spacecraft bus health (25.6 vs 89.7 FA/day)  
> - **0.9548 Mean IoU** on disaster damage segmentation  
> - **1.0000 ROC-AUC** on CDM debris conjunction classification  
> - **Zero invariant violations** across 7,000 Monte Carlo and canonical trials  
> - And an end-to-end risk evaluation latency of **0.10 milliseconds (p95)**—delivering over 16,000 evaluations per second.  
>  
> Judges can also explore our **6-Step Guided Tour**, test live sensor anomalies in our **Fault Injection Lab**, plan evasive thrust impulses in our **Maneuver What-If Simulator**, and inspect flood damage in our **Disaster Deck**.  
>  
> ASTRA-GUARD gives flight controllers the clarity they need to protect billion-dollar space assets and save lives on Earth.  
>  
> Thank you, and we look forward to your questions."*

---

## Interactive Feature Showcase for Judges

| Feature | Route / Shortcut | What to Demo |
| :--- | :--- | :--- |
| **Guided Judge Tour (Q1)** | Navbar **"Judge Tour"** button | 6-step interactive walkthrough highlighting key mission operations capabilities. |
| **Command Palette (Q4)** | `Ctrl+K` or `Cmd+K` or `/` | Instant keyboard-driven navigation, scenario jumping, and action execution. |
| **Fault Injection Lab (F5)** | `/health` $\to$ **Fault Injection Lab** | Drag thermal drift, spike, and stuck sliders; observe real-time Detector Arena comparing Isolation Forest vs LSTM Autoencoder. |
| **3D Orbit Digital Twin (F1)** | `/debris` $\to$ **3D Orbit Twin** | Drag to rotate Earth globe in ECI coordinates; inspect Sentinel-2A SSO track, debris crossing track, and apex encounter beacon. |
| **CAM What-If Simulator (F2)** | `/debris` $\to$ **CAM What-If Simulator** | Adjust $\Delta V$ burn magnitude (0.05 to 1.50 m/s) and lead time; observe miss distance expansion ($45\text{ m} \to 4,320\text{ m}$), $P_c$ drop factor, and hydrazine fuel cost via Tsiolkovsky equation. |
| **B-Plane Uncertainty Lab (F3)**| `/debris` $\to$ **Uncertainty Lab** | Interactive encounter plane with $1\sigma/2\sigma/3\sigma$ error ellipses, $R=5\text{ m}$ hard-body sphere, and 2,000-particle Monte Carlo scatter cloud. |
| **Disaster Intelligence Deck (F7)**| `/disaster` $\to$ **Disaster Deck** | Drag split slider comparing pre-event baseline vs AI inundation mask across Emilia-Romagna, Evros Megafire, and Valencia flash floods. |
| **Constellation Mode (F8 & F11)**| `/disaster` $\to$ **Constellation Mode** | Multi-satellite fleet health (Sentinel-2A, 1A, 3A) and cross-conjunction screening heatmap. |
| **Live Telemetry Streamer (F9)** | `/disaster` $\to$ **Live Telemetry** | High-rate animated telemetry ticker with speed multiplier (1x, 5x, 20x) and sound effects. |
| **Physics Sandbox (F6)** | `/demo` $\to$ **Physics Sandbox** | Parametric ground-truth generator for telemetry drift, orbit miss distance, and SAR flood area with instant JSON export. |
| **Phone Alert Bot (F10)** | `/alerts` $\to$ **Telegram Bot** | Interactive mobile smartphone chat interface with inline operator actions. |
| **Cryptographic Provenance (Q2)**| `/alerts` $\to$ **Inspect Provenance** | SHA-256 fingerprint audit drawer and bit-for-bit mathematical formula reproduction. |

---

## Anticipated Judge Q&A Cheat Sheet

| Question | Recommended Answer |
| :--- | :--- |
| **"Why not use an LLM for risk decisions?"** | Flight safety requires deterministic guarantees. An LLM can hallucinate or produce non-reproducible outputs. We use Pearl's Noisy-OR probabilistic hazard model with deterministic override boundaries ($P_c \ge 10^{-4} \implies r_d \ge 0.90$) and zero non-deterministic components in the critical safety path. |
| **"What happens if SGP4 ephemeris drifts?"** | SGP4 has known error accumulation (3.4 km at 24h, 13.1 km at 72h). We explicitly label our conjunction screening as 'Screening-Grade' and enforce Foster 2-D B-Plane uncertainty scaling to ensure operators don't rely on uncalibrated precision. |
| **"How do you handle satellite sensor noise?"** | Our LSTM Autoencoder is paired with an empirical percentile calibrator and a temporal $k$-of-$n$ persistence filter (requiring 3 consecutive anomalous windows), rejecting sensor spikes and reducing false alarms by 71.4%. |
| **"Is the system ready for orbital deployment?"** | ASTRA-GUARD is designed as a ground-station mission operations platform with sub-millisecond evaluation latency (p95 = 0.10 ms), ready to ingest standard CCSDS telemetry, NASA/ESA CDM XML/JSON bulletins, and Copernicus SAR imagery. |
| **"How does the CAM Simulator compute fuel cost?"** | We use the ideal rocket equation: $\Delta m = m_0 (1 - e^{-\Delta V / (I_{sp} g_0)})$ with Sentinel-2A's $1,140\text{ kg}$ dry mass and $220\text{ s}$ hydrazine specific impulse. A typical $0.35\text{ m/s}$ collision avoidance burn consumes just $0.185\text{ kg}$ of hydrazine (0.15% of the 120 kg tank). |
| **"Can operators audit past alert decisions?"** | Yes. Every alert carries a SHA-256 hash fingerprint of its raw telemetry drivers and timestamp. The Provenance Drawer provides bit-for-bit mathematical reproduction, ensuring full accountability for civil aviation and space safety regulators. |

