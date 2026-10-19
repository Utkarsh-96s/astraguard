# Rules — ASTRA-GUARD (agent + contributor rules)

These are binding for any AI agent (Antigravity) or human working in this repo. Read `memory.md` first every session.

## 1. Prime Directives
1. **Advisory only.** Never write code that sends commands to a spacecraft or auto-executes maneuvers.
2. **No fabricated results.** Never hard-code accuracy numbers. Metrics shown in UI/docs must come from `ml/evaluation` outputs. If unmeasured, display "not yet evaluated".
3. **Label synthetic data.** Every synthetic dataset/record carries `synthetic=true` and the UI shows a "SIMULATED" badge.
4. **Explainable by default.** Any risk score or alert must ship with drivers + rationale.
5. **Deterministic safety path.** No LLM output may influence scores, levels or recommendations. LLMs only for optional, clearly-labelled summaries.
6. **Verify references.** Never invent papers/URLs/datasets. If unsure, mark `TODO-VERIFY` in `docs/references.md`.

## 2. Tech Stack (do not deviate without logging in memory.md)
- Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, pytest, ruff, mypy.
- ML: scikit-learn, XGBoost, PyTorch, SHAP, sgp4/skyfield, pandas, numpy, rasterio.
- Frontend: Next.js (App Router) + TypeScript (strict), Tailwind, Recharts, react-globe.gl. No other UI framework.
- DB: PostgreSQL (+TimescaleDB). SQLite only for local tests.
- Infra: Docker, docker compose, GitHub Actions, NGINX.
- **No** MERN/Mongo/Express, **no** React Native in MVP.

## 3. Code Standards
- Python: type hints everywhere, `ruff` + `mypy --strict` clean, docstrings on public functions, no wildcard imports, functions < 60 lines when practical.
- TypeScript: `strict: true`, no `any` (use `unknown` + narrowing), components < 200 lines, hooks for data fetching (TanStack Query).
- Config via env + YAML (`config/`); no magic numbers in logic (thresholds/weights live in config).
- Reproducibility: set seeds (`numpy`, `torch`, `random`); log model version + data hash with every prediction.
- Errors: never swallow exceptions; return typed error responses; structured logs.

## 4. Architecture Rules
- Each AI module implements the `RiskModule` interface (see architecture.md §5). No cross-imports between `ml/health`, `ml/debris`, `ml/disaster`; they communicate only through `risk_engine`.
- API routers contain no business logic — call `services/`.
- Demo Mode must reuse the real ingestion path.
- DB changes only via Alembic migrations.
- Every endpoint has a Pydantic response model and an OpenAPI description.

## 5. ML Rules
- Fit scalers/thresholds on **training/nominal data only** (no leakage). Time-based splits, never random shuffles for time series.
- Report event-wise metrics + false alarms/day for anomaly detection; don't headline plain accuracy.
- Always compare against a simple baseline (IsoForest / threshold / differencing) before claiming the deep model helps.
- Pc from TLEs must be labelled *screening-grade*; show assumed covariance.
- Save models with metadata (`model_registry`): version, data hash, metrics, params.

## 6. Testing
- Unit tests for: SGP4 propagation sanity, conjunction screening, Pc function (known cases), risk fusion (property tests: monotonic in each input, bounds 0–100), alert dedup.
- Integration test: run the full demo scenario headless → asserts the expected level transitions at expected times.
- Frontend: component tests (vitest + RTL) for severity badges, alert list; Playwright smoke for demo flow.
- Min coverage target: 70% backend core, 100% of risk fusion.

## 7. Security
- No secrets in git; `.env.example` only. Space-Track/SMTP/SMS creds from env.
- Validate all inputs; limit upload sizes; sanitize file paths.
- CORS allow-list; rate-limit write routes.

## 8. Git & Process
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Branch per phase task: `phase-N/<slug>`. PRs must reference a phase item and pass CI.
- After each completed phase item: update `memory.md` (status, decisions, known issues).
- Don't commit raw datasets (>5 MB); commit `data/samples/` and download scripts.

## 9. Agent Behaviour (Antigravity)
- Work **phase by phase** per `phases.md`; do not jump ahead. Stop at each phase exit gate and summarize.
- Before coding a phase: write a short plan artifact; after: produce a verification artifact (tests run, screenshots of UI, metrics).
- If a requirement conflicts with these rules, stop and ask; log the decision in `memory.md`.
- Prefer small, reviewable diffs. No unrelated refactors.
- Don't download huge datasets automatically; write scripts + document sizes and let the user trigger.
- Browser-verify UI changes against `design.md`.

## 10. Definition of Done (per task)
Code + tests + types + lint pass · docs/memory updated · works under `docker compose up` · no hard-coded metrics · UI matches design tokens.