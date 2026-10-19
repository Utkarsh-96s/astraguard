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
- [ ] P3 Debris AI
- [ ] P4 Disaster AI
- [ ] P5 Risk Engine + XAI
- [ ] P6 API / Alerts / Realtime
- [ ] P7 Dashboard
- [ ] P8 Demo Mode
- [ ] P9 Evaluation / Hardening / Docs

**Current phase:** P2 (Completed, awaiting 'continue' for P3) · **Last updated:** 2026-10-20 00:46 · **Last action:** Completed Phase 2 Spacecraft Health AI with RobustScaler, PyTorch LSTM Autoencoder, Isolation Forest baseline, percentile calibrator, persistence filter, SHAP/residual attributions, diagnostic plots, 21/21 passing tests, and evaluation metrics saved to evaluation/results/health.json.

## 5. Measured Metrics (fill from evaluation outputs only)
| Module | Metric | Value | Dataset | Commit |
|---|---|---|---|---|
| Health | event-wise F1 / false alarms per day | 0.3636 / 25.6 FA/day (vs. baseline 0.2222 / 89.7 FA/day) | Synthetic Physics Benchmark (ESA-ADB structure) | phase-2 |
| Debris | ROC-AUC / PR-AUC | — | Kelvins | — |
| Debris | SGP4 error @ 24/72 h | — | reference ephemeris | — |
| Disaster | IoU / F1 | — | Sen1Floods11 | — |
| System | latency p50 / p95 | — | demo scenario | — |

## 6. Known Issues / Open Questions
1. Verify all deck references exist (esp. arXiv 2406.17826, "NASA Operations Review 2025", "ESA Spacecraft Health 2024").
2. Telemetry: Phase 2 calibrated LSTM AE and persistence filter active; baseline comparison confirms 71.4% false alarm reduction over tabular Isolation Forest.
3. CelesTrak active catalog sample committed (`celestrak_active_sample.json`).
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
2026-10-20 00:46 — Antigravity (Lead Engineer) — Phase 2 completed: Spacecraft Health AI with TelemetryRobustScaler, PyTorch LSTM Autoencoder, Isolation Forest baseline + SHAP, HealthScoreCalibrator, PersistenceFilter, HealthRiskModule, evaluation harness (evaluation/results/health.json), exploration notebook + 4-panel diagnostic plot, 21/21 pytest passing, CI clean — branch phase-2/spacecraft-health-ai — Ready for Phase 3 Debris AI
2026-10-20 00:03 — Antigravity (Lead Engineer) — Phase 1 completed: synthetic generators (telemetry, debris encounter, flood chips), sample datasets (ESA-ADB, CelesTrak, Kelvins, Sen1Floods11), ingest & query API routers, docs/data.md data cards, exploration notebook + diagnostic plots, pytest 12/12 passing, CI clean — branch phase-1/data-simulation — Ready for Phase 2 Health AI
2026-10-19 12:12 — Antigravity (Lead Engineer) — Phase 0 completed: monorepo layout, FastAPI + /healthz, Next.js + design.md tokens, Alembic baseline, and CI verification — apps/api/, apps/web/, ml/, docker-compose.yml, Makefile, .env.example — Ready for Phase 1 Data & Simulation
```