.PHONY: help setup dev-api dev-web lint type-check test audit ci up down demo notify-selftest

help:
	@echo "ASTRA-GUARD Makefile commands:"
	@echo "  make setup            - Install backend and frontend dependencies"
	@echo "  make dev-api          - Run FastAPI dev server (port 8000)"
	@echo "  make dev-web          - Run Next.js dev server (port 3000)"
	@echo "  make lint             - Run ruff on Python and eslint on TypeScript"
	@echo "  make type-check       - Run mypy and tsc"
	@echo "  make test             - Run pytest"
	@echo "  make audit            - Run cryptographic honesty and figure audit"
	@echo "  make notify-selftest  - Run notification engine end-to-end self-test"
	@echo "  make ci               - Run full CI checks (lint, type-check, test, audit)"
	@echo "  make up               - Start full stack via docker compose"
	@echo "  make down             - Stop docker compose containers"
	@echo "  make demo             - Build and run demo mode stack"

setup:
	cd apps/api && pip install -e ".[dev]"
	cd apps/web && npm install

dev-api:
	cd apps/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

type-check:
	mypy --explicit-package-bases apps/api/app ml
	cd apps/web && npm run type-check

test:
	cd apps/api && pytest -v

notify-selftest:
	python scripts/notify_selftest.py

audit:
	python scripts/honesty_audit.py

audit-figures: audit

ci: lint type-check test audit notify-selftest

up:
	docker compose up -d

down:
	docker compose down

demo:
	docker compose up --build
