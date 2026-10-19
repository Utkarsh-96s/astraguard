# PRD — ASTRA-GUARD
**AI-Powered Integrated Space Mission Safety & Intelligence**
Team OMEN · AITHON 2.0 · Track 11: Aerospace, Telemetry & SpaceTech · Category: Software

> Tagline: *Monitor the spacecraft. Predict the threat. Understand Earth. Support safer mission decisions.*

---

## 1. Problem
Space missions produce **telemetry**, **orbital/debris** and **satellite-image** data in separate silos. Operators must mentally join them to answer one question: *"What needs my attention right now, and why?"*

## 2. Vision
One mission-control dashboard that fuses three AI signals into a single, explainable **Mission Risk Score** with human-in-the-loop recommendations.

## 3. Goals / Non-Goals
**Goals (MVP)**
1. Detect spacecraft telemetry anomalies and explain which channels drove them.
2. Screen for close approaches with debris, estimate collision probability (Pc) and trend it over time.
3. Segment/prioritize disaster observations (flood/fire/damage) from Earth-observation imagery.
4. Fuse the three into one Mission Risk Score + SHAP-style explanation + recommended operator action.
5. Ship a deterministic **Demo Mode** that replays a full scenario end-to-end.

**Non-Goals (MVP)**
- Real spacecraft command/control or autonomous maneuvers (advisory only).
- Live on-board inference (the deck's "on-board disaster mapping" is reframed as *ground-segment* processing).
- Native mobile app, multi-tenant auth, digital twin, multi-satellite coordination (→ Future Work).

## 4. Personas
| Persona | Need |
|---|---|
| Mission Operator | Single prioritized alert queue, minimal false alarms |
| Flight Dynamics Analyst | Conjunction details, Pc trend, maneuver what-if |
| EO / Disaster Analyst | Ranked observation targets, change-detection overlays |
| Judge / Reviewer | A reproducible demo, honest metrics, clear explainability |

## 5. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Ingest telemetry (CSV/Parquet/stream-simulated) into time-series store | P0 |
| FR-2 | Preprocess: resample, normalize, windowing, missing-value handling | P0 |
| FR-3 | Health AI: Isolation Forest baseline + LSTM (autoencoder/forecaster) → anomaly score per window & per channel | P0 |
| FR-4 | Ingest orbital data (CelesTrak GP/TLE; optional Space-Track), propagate with SGP4 | P0 |
| FR-5 | Conjunction screening vs debris catalog (miss distance, TCA, relative velocity) | P0 |
| FR-6 | Pc estimation (2-D Foster method w/ assumed covariance) + ML risk-trend model (XGBoost/LSTM on CDM history) | P1 |
| FR-7 | Disaster AI: U-Net/CNN segmentation (flood/fire/damage) + before/after change detection | P1 |
| FR-8 | Observation prioritization score (affected area, recency, cloud cover, revisit gap) | P1 |
| FR-9 | Mission Risk Engine: fuse sub-scores → score 0–100, level (NOMINAL/WATCH/WARNING/CRITICAL) | P0 |
| FR-10 | Explainability: SHAP attributions + natural-language rationale per alert | P0 |
| FR-11 | Recommendation generator (rule-based templates keyed to risk drivers; human approval required) | P0 |
| FR-12 | Alerts: dashboard feed (P0), email/webhook (P1), SMS (P2/optional) with dedup & cooldown | P0/P1 |
| FR-13 | Dashboard: overview, health, debris, disaster, alert detail, scenario replay | P0 |
| FR-14 | Demo Mode: scripted scenario with play/pause/speed and seeded data | P0 |
| FR-15 | Audit log: every alert, score, model version, operator ack/dismiss | P1 |

## 6. Non-Functional Requirements
- **Reproducibility:** seeded runs; `docker compose up` brings up full stack + demo data.
- **Latency target:** alert generated < 30 s after data arrival in demo; < 30 min end-to-end for batch feeds (deck's claim — measured, not assumed).
- **Explainability:** every alert shows top-k drivers.
- **Safety:** advisory only; all recommendations require operator confirmation.
- **Honesty:** accuracy numbers on slides must come from `evaluation/` outputs (see rules.md).
- **Portability:** open-source stack only.

## 7. Data Sources (real, public)
| Domain | Source |
|---|---|
| Telemetry | **ESA-ADB** (ESA Anomaly Detection Benchmark, ESA Mission1–3); NASA **SMAP/MSL** telemetry anomaly dataset (fallback) |
| Orbital / debris | **CelesTrak** GP/TLE; Space-Track (needs account); ESA DISCOS (optional) |
| Collision risk ML | **ESA Kelvins Collision Avoidance Challenge** CDM dataset |
| Disaster imagery | **Sen1Floods11** (floods), **xBD** (building damage), Copernicus EMS / NASA FIRMS (fires), Sentinel-2 via Copernicus Data Space |
| Fallback | Fully **synthetic generators** (clearly labelled `synthetic=true`) |

## 8. Success Metrics (targets to *validate*)
| Metric | Deck claim | PRD stance |
|---|---|---|
| Anomaly detection accuracy | ~92% | Target; report event-wise precision/recall/F1 on ESA-ADB (accuracy alone is misleading on imbalanced data) |
| Risk prediction accuracy | ~85% | Target; report ROC-AUC/PR-AUC on Kelvins |
| Orbit prediction error | < ~1 km | SGP4 is ~1 km at epoch and degrades over days; state horizon explicitly |
| Alert latency | < 30 min | Measure end-to-end in demo |
| Uptime | > 99% | Not meaningful for a prototype; replace with "runs headless 24 h w/o crash" |

## 9. Demo Scenario ("Day in the life")
1. **T+0** Nominal — score 12.
2. **T+5** Reaction-wheel temp/current drift → Health AI WATCH (SHAP: `wheel_temp`, `bus_current`).
3. **T+10** Debris object conjunction found, Pc rises 1e-6 → 3e-5 → WARNING.
4. **T+15** Flood event detected over a region; satellite is in a degraded state so observation is flagged "defer / lower-power imaging."
5. **T+18** Fused score crosses CRITICAL; recommendation: *"Prepare avoidance maneuver analysis; hold non-essential imaging; operator approval required."*

## 10. Risks
| Risk | Mitigation |
|---|---|
| False alarms | Threshold calibration, persistence filter, cooldown, show confidence |
| TLE-based Pc is approximate (no covariance) | Label as "screening-grade"; use Kelvins CDMs for ML evidence |
| Dataset access/size | Ship small curated samples + synthetic fallback |
| Scope creep (3 AI systems) | Phase gates; P1 modules can degrade to pretrained/simulated |
| Unverifiable claims/refs | See "Deck issues" below |

## 11. Deck Issues to Fix Before Submission
1. **Stack inconsistency:** slide 3 diagram says MERN + React Native; text says React/Next.js + FastAPI. → **Resolved here: Next.js + FastAPI; mobile deferred.**
2. **Typo:** "produces Mission Risk Mission Risk explainable alerts" (slide 2).
3. **Rendering artifact:** `($P_c$)` appears literally in the comparison table.
4. **"Rapid On-board Disaster Mapping"** is not in scope → rename "Rapid ground-segment disaster mapping".
5. **References:** verify each citation (title, authors, DOI/URL) exists; the arXiv ID `2406.17826` and the "NASA Operations Review (2025)" entry must be checked — replace anything unverifiable with real papers (e.g., ESA-ADB paper, Kelvins challenge paper, Sen1Floods11, xBD, SHAP/Lundberg & Lee 2017).
6. **Comparison table** rates the proposal ✓ on everything; soften to what the MVP truly delivers.
7. **Uptime >99% / accuracy numbers** — present as targets or back with measurements.

## 12. Out-of-Scope / Future Work
Digital twin, maneuver planning optimizer, multi-satellite coordination, native mobile app, on-board edge inference, RBAC/multi-tenant.