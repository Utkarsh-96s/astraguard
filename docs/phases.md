# Phases — ASTRA-GUARD

Durations are relative effort units (adjust to your deadline). Each phase has an **exit gate**; do not start the next until it passes. **Critical path for a demo: P0 → P1 → P2 → P3 → P5 → P6 → P7 → P8.** P4 (disaster) can degrade to pretrained/simulated if time is short.

| Phase | Name | Effort |
|---|---|---|
| 0 | Foundation & scaffolding | S |
| 1 | Data & simulation layer | M |
| 2 | Spacecraft Health AI | M |
| 3 | Debris Collision Risk AI | M |
| 4 | Disaster Intelligence AI | M–L |
| 5 | Mission Risk Engine + XAI | M |
| 6 | Backend API, alerts, realtime | M |
| 7 | Dashboard | L |
| 8 | Demo Mode & scenario | S–M |
| 9 | Evaluation, hardening, docs, pitch | M |
| 10 | Future work (post-hackathon) | — |

---
## Phase 0 — Foundation
- Monorepo layout (architecture.md §4), `docker-compose.yml`, `.env.example`, Makefile.
- FastAPI skeleton + `/healthz`; Next.js skeleton + Tailwind tokens from design.md.
- CI: ruff, mypy, pytest, eslint, tsc.
- Postgres/Timescale + Alembic baseline.
**Exit gate:** `docker compose up` shows web + API health; CI green.

## Phase 1 — Data & Simulation
- Download scripts + small committed samples: ESA-ADB subset (or SMAP/MSL), CelesTrak GP snapshot, Kelvins subset, a few Sen1Floods11 chips.
- **Synthetic generators:** telemetry (nominal + injected drift/spike/stuck faults), debris encounter geometry, flood/fire tiles.
- Ingestion services + DB loaders; data cards in `docs/data.md`.
**Exit gate:** sample + synthetic data queryable via API; notebook shows plots.

## Phase 2 — Spacecraft Health AI
- Preprocess/windowing; IsoForest baseline; LSTM autoencoder.
- Scoring calibration, persistence filter.
- SHAP / channel-level attribution.
- Evaluation script → `evaluation/results/health.json`.
**Exit gate:** LSTM vs baseline comparison with event-wise metrics + false alarms/day; explanations visible in notebook.

## Phase 3 — Debris Collision Risk AI
- SGP4 propagation (+ unit tests vs known ephemerides).
- Conjunction screening, TCA refinement, Pc (Foster).
- XGBoost risk model on Kelvins CDMs; metrics file.
- Risk-score mapping function.
**Exit gate:** screening finds seeded conjunction in synthetic case; ROC/PR metrics reported; SGP4 error-vs-horizon plot.

## Phase 4 — Disaster Intelligence AI
- U-Net training/fine-tuning (flood first; fire optional); inference pipeline producing masks + area.
- Change detection (differencing fallback → siamese if time).
- Observation priority score.
**Exit gate:** IoU/F1 on held-out chips; overlay PNG + GeoJSON footprint served by API.

## Phase 5 — Mission Risk Engine + XAI
- Fusion (architecture.md §5.4) with YAML-config weights; overrides; cross-effects.
- Attribution aggregation; NL rationale templates; recommendation rules.
- Property-based tests.
**Exit gate:** scripted inputs yield expected levels; every output has drivers + rationale.

## Phase 6 — Backend API, Alerts, Realtime
- All routers in architecture.md §7; WebSocket feeds.
- Scheduler running modules; snapshot persistence; alert dedup/cooldown/escalation.
- Email/webhook notifier; operator actions + audit log.
**Exit gate:** end-to-end API test: ingest → score → alert → ack, all logged.

## Phase 7 — Dashboard
- Pages per design.md: Overview, Health, Debris, Disaster, Alerts, Models, Demo.
- Globe/ground track, Pc trend chart, SHAP bar, alert drawer, timeline scrubber.
- Responsive + accessibility pass.
**Exit gate:** all pages live on real API; Lighthouse a11y ≥ 90; matches design.md.

## Phase 8 — Demo Mode
- ScenarioPlayer + YAML scenario ("Day in the life", PRD §9).
- Controls (play/pause/seek/speed), "SIMULATED" badges, reset.
- Headless integration test asserting level transitions.
**Exit gate:** one-click replay reproduces identical results; test passes.

## Phase 9 — Evaluation, Hardening, Docs, Pitch
- Consolidate metrics → Models page + slide numbers (replace deck claims with measured values).
- Fix deck issues (PRD §11); verify all references.
- README (quickstart, architecture GIF), demo video script, troubleshooting.
- Load/latency test; 24 h soak (headless).
**Exit gate:** fresh clone → `make demo` works; every number in the deck traceable to a results file.

## Phase 10 — Future Work
Digital twin, maneuver planner (what-if ΔV), multi-satellite coordination, React Native alerts app, RBAC, streaming (Kafka/MQTT), on-board edge inference (quantized models).