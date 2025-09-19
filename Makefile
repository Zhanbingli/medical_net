PYTHON=python3
PIP=pip3
NPM=npm

install:
	cd backend && $(PIP) install -r requirements/dev.txt && $(PIP) install -e .
	cd etl && $(PIP) install -r requirements/dev.txt
	cd frontend && $(NPM) install

backend:
	cd backend && uvicorn app.main:app --reload

etl-check:
	cd etl && pytest

frontend:
	cd frontend && $(NPM) run dev

lint:
	cd backend && ruff check .
	cd backend && mypy app
	cd frontend && $(NPM) run lint

format:
	cd backend && ruff format .
	cd frontend && $(NPM) run format

.PHONY: install backend frontend etl-check lint format
