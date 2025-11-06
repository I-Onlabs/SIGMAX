.PHONY: help install install-dev clean test test-unit test-integration test-soak test-coverage \
        lint format format-check license-check docker-up docker-down docker-logs docker-ps docker-clean \
        init run run-debug run-service benchmark health health-watch analyze-trades \
        import-dashboards db-shell-postgres db-shell-clickhouse setup verify ci status pre-commit-install

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SIGMAX - Algorithmic Crypto Trading Bot$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-25s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy isort pre-commit
	pre-commit install || true

clean: ## Clean build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage htmlcov/ .mypy_cache/

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	pytest tests/unit/ -v --cov=apps --cov=pkg --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	pytest tests/integration/ -v --timeout=3600

test-soak: ## Run soak tests (long-running)
	pytest tests/soak/ -v --timeout=28800

test-coverage: ## Run tests with detailed coverage report
	pytest tests/ --cov=pkg --cov=apps --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

lint: ## Run linters (flake8, mypy)
	flake8 apps/ pkg/ tests/ --max-line-length=100
	mypy apps/ pkg/ --ignore-missing-imports

license-check: ## Check license compliance
	@echo "$(BLUE)Checking license compliance...$(NC)"
	python tools/check_licenses.py

format: ## Format code with black and isort
	black apps/ pkg/ tests/ tools/ --line-length=100
	isort apps/ pkg/ tests/ tools/

format-check: ## Check code formatting without modifying
	black --check apps/ pkg/ tests/ tools/ --line-length=100
	isort --check-only apps/ pkg/ tests/ tools/

docker-up: ## Start Docker infrastructure
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose -f infra/compose/docker-compose.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "$(GREEN)✓ Docker containers started$(NC)"

docker-down: ## Stop Docker infrastructure
	docker-compose -f infra/compose/docker-compose.yml down

docker-logs: ## Show Docker logs
	docker-compose -f infra/compose/docker-compose.yml logs -f

docker-ps: ## Show running Docker containers
	docker-compose -f infra/compose/docker-compose.yml ps

docker-clean: ## Remove Docker containers and volumes
	docker-compose -f infra/compose/docker-compose.yml down -v

init: docker-up ## Initialize databases (requires Docker running)
	@echo "$(BLUE)Initializing databases...$(NC)"
	@sleep 5
	python tools/init_database.py --profile=a
	@echo "$(GREEN)✓ Databases initialized$(NC)"

run: ## Run SIGMAX trading system (Profile A)
	@echo "$(BLUE)Starting SIGMAX (Profile A)...$(NC)"
	python tools/runner.py --profile=a

run-debug: ## Run SIGMAX with debug logging
	@echo "$(BLUE)Starting SIGMAX (debug mode)...$(NC)"
	LOG_LEVEL=DEBUG python tools/runner.py --profile=a

run-service: ## Run a single service (e.g., make run-service SERVICE=ingest)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE variable not set$(NC)"; \
		echo "Usage: make run-service SERVICE=ingest"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting service: $(SERVICE)...$(NC)"
	python -m apps.$(SERVICE).main --profile=a

benchmark: ## Run performance benchmark
	@echo "$(BLUE)Running performance benchmark...$(NC)"
	python tools/benchmark.py --ticks=10000 --symbols=2

health: ## Check system health
	@echo "$(BLUE)Checking system health...$(NC)"
	python tools/health_check.py

health-watch: ## Watch system health continuously
	@echo "$(BLUE)Watching system health (Ctrl+C to stop)...$(NC)"
	python tools/health_check.py --watch --interval=10

analyze-trades: ## Analyze trades (last 7 days)
	@echo "$(BLUE)Analyzing trades...$(NC)"
	python tools/analyze_trades.py --days=7

import-dashboards: ## Import Grafana dashboards
	@echo "$(BLUE)Importing Grafana dashboards...$(NC)"
	./tools/import_dashboards.sh
	@echo "$(GREEN)✓ Dashboards imported$(NC)"

db-shell-postgres: ## Open Postgres shell
	@echo "$(BLUE)Opening Postgres shell...$(NC)"
	docker exec -it sigmax-postgres psql -U sigmax -d sigmax

db-shell-clickhouse: ## Open ClickHouse shell
	@echo "$(BLUE)Opening ClickHouse shell...$(NC)"
	docker exec -it sigmax-clickhouse clickhouse-client

migrate-up: ## Run database migrations (up)
	python tools/init_database.py --profile=a

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

setup: install-dev docker-up init pre-commit-install ## Complete development setup
	@echo ""
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run tests: make test"
	@echo "  2. Start system: make run"
	@echo "  3. Check health: make health"

verify: format-check lint license-check test ## Verify code quality (format, lint, license, test)
	@echo "$(GREEN)✓ All verification checks passed!$(NC)"

ci: format-check lint license-check test-coverage ## Run CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline completed successfully!$(NC)"

status: ## Show system status
	@echo "$(BLUE)SIGMAX System Status$(NC)"
	@echo ""
	@echo "$(GREEN)Docker Containers:$(NC)"
	@docker-compose -f infra/compose/docker-compose.yml ps 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "$(GREEN)Python Processes:$(NC)"
	@ps aux | grep "python.*apps\." | grep -v grep || echo "  No services running"

# Profile shortcuts
profile-a: run ## Run Profile A (alias for 'make run')

profile-b: ## Run Profile B (performance-optimized)
	@echo "$(BLUE)Starting SIGMAX (Profile B)...$(NC)"
	python tools/runner.py --profile=b

# Quick aliases
q: run ## Quick alias for 'make run'
t: test ## Quick alias for 'make test'
f: format ## Quick alias for 'make format'
l: lint ## Quick alias for 'make lint'
h: health ## Quick alias for 'make health'

.DEFAULT_GOAL := help
