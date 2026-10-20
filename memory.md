# Memory — ASTRA-GUARD (living project context)

> **Agent: read this file at the start of every session. Update it at the end of every task.**

## 1. Project Snapshot
- **Name:** ASTRA-GUARD — AI-Powered Integrated Space Mission Safety & Intelligence
- **Team:** OMEN · Event: AITHON 2.0 (AIESA) · Track 11 Aerospace, Telemetry & SpaceTech · Category: Software
- **One-liner:** Fuse spacecraft health, debris collision risk and satellite disaster intelligence into one explainable Mission Risk Score with human-in-the-loop recommendations.
- **Source of truth docs:** `prd.md`, `architecture.md`, `rules.md`, `phases.md`, `design.md`.

## 2. Locked Decisions
| # | Decision | Reason |
|---|---|---|
| D1 | Frontend = Next.js + TS; Backend = FastAPI | Deck text; ML in Python. MERN/RN diagram superseded |
| D2 | Mobile app deferred | Scope control |
| D3 | Advisory-only; human approval required | Safety, deck's HITL claim |
| D4 | Risk fusion = noisy-OR on safety + 15% EO priority; Pc ≥ 1e-4 forces CRITICAL | Interpretable, standard conjunction threshold order of magnitude |
| D5 | Pc from TLE = "screening-grade" (assumed covariance) | TLEs lack covariance |
| D6 | No LLM in the scoring/recommendation path | Determinism, safety |
| D7 | "On-board disaster mapping" reframed as ground-segment processing | Realism |
| D8 | Deck metrics (92%, 85%, <1 km, <30 min, >99%) are *targets*, replaced by measured values | Honesty |
| D9 | Data: ESA-ADB, CelesTrak, Kelvins CDM, Sen1Floods11/xBD + synthetic fallback | Public & real |

## 3. Glossary
- **TCA** time of closest approach · **Pc** probability of collision · **CDM** Conjunction Data Message · **TLE/GP** orbital element sets · **SGP4** analytic propagator · **SHAP** Shapley additive explanations · **XAI** explainable AI · **EO** Earth observation · **HITL** human-in-the-loop.

## 4. Status Tracker (agent updates)
- [x] P0 Foundation
- [x] P1 Data & Simulation
- [x] P2 Health AI
- [x] P3 Debris AI
- [x] P4 Disaster AI
- [x] P5 Risk Engine + XAI
- [x] P6 API / Alerts / Realtime
- [ ] P7 Dashboard
- [ ] P8 Demo Mode
- [ ] P9 Evaluation / Hardening / Docs

**Current phase:** P6 (Completed, ready for P7) · **Last updated:** 2026-10-20 11:15 · **Last action:** Completed Phase 6 Backend API, Alerts, Realtime with full router implementations (Assets, Risk, Alerts, Models, WebSockets), async database services (RiskService, AlertService, NotificationDispatcher), alert lifecycle engine (dedup hash, 300s cooldown, escalation bypass), operator action auditing (approve, dismiss, snooze), real-time WebSockets (/ws/alerts, /ws/risk/{asset_id}), 53/53 pytest passing (including test_api_alerts_realtime and test_e2e_pipeline), 0 ruff lint errors.

## 5. Measured Metrics (fill from evaluation outputs only)
| Module | Metric | Value | Dataset | Commit |
|---|---|---|---|---|
| Health | event-wise F1 / false alarms per day | 0.3636 / 25.6 FA/day (vs. baseline 0.2222 / 89.7 FA/day) | Synthetic Physics Benchmark (ESA-ADB structure) | phase-2 |
| Debris | ROC-AUC / PR-AUC | 1.0000 / 1.0000 | ESA Kelvins CDM Benchmark | phase-3 |
| Debris | SGP4 error @ 24/72 h | 3.398 km @ 24h, 13.144 km @ 72h | S2A Ephemeris Model | phase-3 |
| Disaster | IoU / F1 | 0.9548 / 0.9768 (min IoU: 0.9363, max IoU: 0.9676) | Sen1Floods11 / Synthetic SAR (15 chips) | phase-4 |
| Risk Engine | Invariant Violations (Mono/Override/Defer) | 0 / 0 / 0 across 7,000 trials (100% compliant) | Canonical Scenarios & Invariant Benchmark | phase-5 |
| System | latency p50 / p95 | — | demo scenario | — |

## 6. Known Issues / Open Questions
1. Verify all deck references exist (esp. arXiv 2406.17826, "NASA Operations Review 2025", "ESA Spacecraft Health 2024").
2. Telemetry: Phase 2 calibrated LSTM AE and persistence filter active; baseline comparison confirms 71.4% false alarm reduction over tabular Isolation Forest.
3. Debris: SGP4 propagation and Foster 2-D screening-grade calculations verified against seeded near-miss event; XGBoost CDM classifier achieves 1.00 ROC/PR on Kelvins CDM features.
4. GPU availability for U-Net/LSTM training (CPU PyTorch execution validated for LSTM AE).
5. Email/SMS provider choice (default: SMTP + webhook; SMS optional).

## 7. Deck Fix List (for final submission)
- Fix duplicated "Mission Risk Mission Risk" (slide 2).
- Remove `$P_c$` LaTeX artifact; use "Pc".
- Align stack across slide 3 diagram and text.
- Rename "On-board" → "Ground-segment" disaster mapping.
- Replace unverifiable references and unmeasured metrics.

## 8. Session Log (append newest on top)
```
2026-10-20 11:15 — Antigravity (Lead Engineer) — Phase 6 completed: Backend API, Alerts, Realtime with full router implementations (Assets, Risk, Alerts, Models, WebSockets), async database services (RiskService, AlertService, NotificationDispatcher), alert lifecycle engine (dedup hash, 300s cooldown, escalation bypass), operator action auditing (approve, dismiss, snooze), real-time WebSockets (/ws/alerts, /ws/risk/{asset_id}), 53/53 pytest passing (including test_api_alerts_realtime and test_e2e_pipeline), 0 ruff lint errors, Phase 6 verification report generated — branch phase-6/api-alerts-realtime — Ready for Phase 7 Dashboard
2026-10-20 10:15 — Antigravity (Lead Engineer) — Phase 5 completed: Mission Risk Engine + XAI with Noisy-OR fusion (R_safety = 1 - (1-r_h)(1-r_d)), YAML-configurable weights (config/risk_engine.yaml), hard overrides (Pc >= 1e-4 -> CRITICAL, r_h >= 0.90 -> >= WARNING), cross-system health deferral (r_h >= 0.50), AttributionAggregator, DeterministicRationaleGenerator, RecommendationEngine, MissionRiskEngine, evaluation harness (evaluation/results/risk.json: 0 invariant violations across 7,000 trials, 4 canonical scenarios verified), 4-panel diagnostic plot, exploration notebook, 43/43 pytest passing, CI clean — branch phase-5/mission-risk-engine-xai — Ready for Phase 6 Backend API, Alerts, Realtime
2026-10-20 07:30 — Antigravity (Lead Engineer) — Phase 4 completed: Disaster Intelligence AI with UNetSegmenter (PyTorch 2-level U-Net), SARChangeDetector (radar backscatter drop), DisasterPriorityScorer (multi-factor priority + r_h >= 0.50 deferral), GeoJSON footprint and RGBA overlay PNG export, DisasterRiskModule, evaluation harness (evaluation/results/disaster.json: IoU 0.9548, F1 0.9768), 4-panel diagnostic plot, exploration notebook, 34/34 pytest passing, CI clean — branch phase-4/disaster-intelligence-ai — Ready for Phase 5 Mission Risk Engine + XAI
2026-10-20 01:22 — Antigravity (Lead Engineer) — Phase 3 completed: Debris Collision Risk AI with SGP4Propagator, ConjunctionScreener (3-stage + TCA refinement), FosterCollisionProbabilityEngine (2-D B-plane), CDMRiskClassifier (XGBoost), DebrisRiskModule, evaluation harness (evaluation/results/debris.json), 4-panel diagnostic plot, exploration notebook, 28/28 pytest passing, CI clean — branch phase-3/debris-collision-risk-ai — Ready for Phase 4 Disaster AI
2026-10-20 00:46 — Antigravity (Lead Engineer) — Phase 2 completed: Spacecraft Health AI with TelemetryRobustScaler, PyTorch LSTM Autoencoder, Isolation Forest baseline + SHAP, HealthScoreCalibrator, PersistenceFilter, HealthRiskModule, evaluation harness (evaluation/results/health.json), exploration notebook + 4-panel diagnostic plot, 21/21 pytest passing, CI clean — branch phase-2/spacecraft-health-ai — Ready for Phase 3 Debris AI
2026-10-20 00:03 — Antigravity (Lead Engineer) — Phase 1 completed: synthetic generators (telemetry, debris encounter, flood chips), sample datasets (ESA-ADB, CelesTrak, Kelvins, Sen1Floods11), ingest & query API routers, docs/data.md data cards, exploration notebook + diagnostic plots, pytest 12/12 passing, CI clean — branch phase-1/data-simulation — Ready for Phase 2 Health AI
2026-10-19 12:12 — Antigravity (Lead Engineer) — Phase 0 completed: monorepo layout, FastAPI + /healthz, Next.js + design.md tokens, Alembic baseline, and CI verification — apps/api/, apps/web/, ml/, docker-compose.yml, Makefile, .env.example — Ready for Phase 1 Data & Simulation
```