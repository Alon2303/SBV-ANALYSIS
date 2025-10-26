.PHONY: setup install test run-api run-dashboard analyze clean help

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SBV Analysis Pipeline - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Initial setup (create venv, install deps, init db)
	@echo "$(BLUE)Setting up SBV Pipeline...$(NC)"
	./setup.sh

install: ## Install dependencies only
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	playwright install chromium

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

run-api: ## Run FastAPI server
	@echo "$(BLUE)Starting API server...$(NC)"
	uvicorn src.api.app:app --reload

run-dashboard: ## Run Streamlit dashboard
	@echo "$(BLUE)Starting dashboard...$(NC)"
	streamlit run src/dashboard/app.py

analyze: ## Run analysis on example companies
	@echo "$(BLUE)Analyzing example companies...$(NC)"
	python -m src.main analyze data/input/example_companies.csv

analyze-file: ## Run analysis on specific file (usage: make analyze-file FILE=path/to/file.csv)
	@echo "$(BLUE)Analyzing companies from $(FILE)...$(NC)"
	python -m src.main analyze $(FILE)

init-db: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	python -m src.main init

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .ipynb_checkpoints
	rm -f data/sbv.db

clean-all: clean ## Clean everything including venv
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf venv

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check src/ tests/
	black --check src/ tests/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	black src/ tests/

export-csv: ## Export results to CSV
	@echo "$(BLUE)Exporting to CSV...$(NC)"
	curl http://localhost:8000/api/export?format=csv

jupyter: ## Start Jupyter notebook server
	@echo "$(BLUE)Starting Jupyter...$(NC)"
	jupyter notebook notebooks/

