# Data Cards — ASTRA-GUARD

This document details the datasets, schemas, provenance, licenses, and synthetic fallback generators used across the ASTRA-GUARD platform.

---

## 1. Spacecraft Telemetry

### Real Benchmark Dataset: ESA-ADB (ESA Anomaly Detection Benchmark)
- **Domain:** Spacecraft Operations & Subsystem Health Monitoring
- **Source / Curators:** European Space Agency (ESA) AI & Operations Group
- **Repository:** https://github.com/esa/AD-benchmarking
- **Size:** ~1.2 GB (multi-mission archives)
- **License:** Open Access / Research Use
- **Format:** CSV / Parquet time-series with UTC timestamps and engineering units
- **Fallback / Alternative:** NASA SMAP/MSL telemetry anomaly dataset (Hundman et al.)

### Monitored Core Channels
| Channel ID | Subsystem | Description | Nominal Range | Unit |
|---|---|---|---|---|
| `wheel_temp` | ADCS (Reaction Wheel) | Wheel bearing temperature | 18.0 – 25.0 | °C |
| `bus_current` | EPS (Electrical Power) | Main power bus current draw | 11.5 – 15.0 | A |
| `battery_v` | EPS (Power Storage) | Battery bank voltage | 28.0 – 32.0 | V |
| `gyro_rate_x` | ADCS (Inertial Measurement) | Angular rate about X-axis | -0.05 – +0.05 | °/s |
| `gyro_rate_y` | ADCS (Inertial Measurement) | Angular rate about Y-axis | -0.05 – +0.05 | °/s |
| `gyro_rate_z` | ADCS (Inertial Measurement) | Angular rate about Z-axis | -0.05 – +0.05 | °/s |
| `sun_sensor` | ADCS / Power | Solar radiation intensity | 0 (eclipse) – 1361 | W/m² |

### Synthetic Generator (`data/synthetic/telemetry_gen.py`)
- **Physics Model:** 96-minute LEO orbital thermal & illumination breathing with Gaussian white noise.
- **Injected Fault Modes:**
  - `drift`: Monotonic ramp on reaction wheel temperature or bus current to simulate thermal runaway or mechanical degradation.
  - `spike`: Transient electrical or sensor spikes simulating radiation single-event upsets (SEU).
  - `stuck`: Zero-variance freeze simulating sensor failure.
- **Rules Compliance:** Every record has `synthetic=True` and UI displays a `SIMULATED` badge.

---

## 2. Orbital Elements & Space Debris Catalog

### Source: CelesTrak GP (General Perturbations) Catalog
- **Domain:** Space Situational Awareness (SSA) & Flight Dynamics
- **Source:** CelesTrak (T.S. Kelso) / USSPACECOM 18th Space Defense Squadron
- **Endpoint:** `https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle`
- **Size:** ~4.8 MB (active satellites) / ~15 MB full catalog
- **License:** Public Domain
- **Format:** Standard Two-Line Element (TLE) set / OMM JSON

### Sample Active Orbit Elements
- Primary Asset: `SENTINEL-2A` (NORAD ID `40697`, Sun-synchronous orbit, altitude ~786 km, inclination 98.57°).
- Tracked Debris: `FENGYUN 1C DEB` (NORAD ID `29834`), `COSMOS 2251 DEB` (NORAD ID `34320`).

### Synthetic Generator (`data/synthetic/debris_gen.py`)
- Emits close encounter geometry (miss distance, relative velocity, TCA) and time-series CDMs modeling sensor refinement over 72 hours before TCA.
- Always tagged `synthetic=True`.

---

## 3. Collision Risk (CDM) Data

### Benchmark: ESA Kelvins Spacecraft Collision Avoidance Challenge
- **Domain:** Machine Learning for Conjunction Assessment
- **Curators:** ESA Space Debris Office (SDO)
- **Repository:** https://kelvins.esa.int/collision-avoidance-challenge/
- **Size:** ~180 MB
- **License:** Open Research Use
- **Format:** Time-series of Conjunction Data Messages (CDMs) leading up to Time of Closest Approach (TCA).

### Key CDM Features
- `time_to_tca_hours`: Time remaining until closest approach.
- `miss_distance_m`: Total Euclidean distance at TCA.
- `relative_velocity_ms`: Relative speed between objects.
- `c_obs_b`, `c_obs_t`, `c_obs_n`: Along-track, cross-track, radial covariance uncertainty.
- `pc`: Collision probability (screening-grade when from TLEs; Foster 2-D method).

---

## 4. Earth Observation Disaster Imagery

### Benchmark: Sen1Floods11
- **Domain:** Rapid Flood Inundation & Disaster Response
- **Source:** Cloud to Street / NASA / ESA
- **Repository:** https://github.com/cloudtostreet/Sen1Floods11
- **Size:** ~2.4 GB
- **License:** CC-BY-4.0
- **Data Modality:** Sentinel-1 Synthetic Aperture Radar (SAR) Ground Range Detected (GRD) + Sentinel-2 optical imagery.
- **Ground Truth:** Hand-verified binary water and flood masks.

### Observation Priority Scoring Formula
Per `architecture.md §5.3`:
$$\text{Priority} = 0.40 \cdot \text{area\_norm} + 0.25 \cdot \text{recency} + 0.20 \cdot \text{pop\_proxy} + 0.15 \cdot (1 - \text{cloud\_cover})$$
- Penalized dynamically by revisit gap and spacecraft health status ($r_h \ge 0.5$ triggers deferral).

### Synthetic Chip Generator (`data/synthetic/disaster_gen.py`)
- Produces $128 \times 128$ terrain chips with simulated radar backscatter and binary flood inundation ground truth masks.
- Always tagged `synthetic=True`.
