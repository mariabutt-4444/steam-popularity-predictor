.PHONY: help install pipeline eda run-backend run-frontend test docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install        Install Python and Frontend dependencies"
	@echo "  make pipeline       Run ETL pipeline from CSV fallback"
	@echo "  make pipeline-api   Run ETL pipeline with live Steam API extraction"
	@echo "  make eda            Run structured EDA analysis engine"
	@echo "  make run-backend    Start FastAPI backend server on :8000"
	@echo "  make run-frontend   Start Vite React development server on :3000"
	@echo "  make test           Execute pytest test suite"
	@echo "  make docker-up      Start containerized stack via Docker Compose"
	@echo "  make docker-down    Stop and tear down Docker Compose containers"

install:
	pip install -r requirements.txt
	cd frontend && npm install

pipeline:
	python -m etl.run_pipeline --source csv

pipeline-api:
	python -m etl.run_pipeline --source api

eda:
	python -m eda.analysis

run-backend:
	uvicorn backend.app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

test:
	pytest tests/ -v

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
