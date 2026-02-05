.PHONY: test test-unit test-integration test-coverage test-fast clean-test install-test help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-test: ## Install test dependencies
	pip install -r requirements.txt

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest -m unit -v

test-integration: ## Run integration tests only
	pytest -m integration -v

test-service: ## Run service layer tests
	pytest -m service -v

test-agent: ## Run agent tests
	pytest -m agent -v

test-api: ## Run API endpoint tests
	pytest -m api -v

test-auth: ## Run authentication tests
	pytest -m auth -v

test-coverage: ## Run tests with coverage report
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-html: ## Generate HTML coverage report
	pytest --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-fast: ## Run tests excluding slow ones
	pytest -m "not slow" -v

test-file: ## Run specific test file (usage: make test-file FILE=tests/test_chat_service.py)
	pytest $(FILE) -v

test-watch: ## Run tests in watch mode (requires pytest-watch)
	pip install pytest-watch
	ptw -- -v

test-parallel: ## Run tests in parallel (requires pytest-xdist)
	pip install pytest-xdist
	pytest -n auto -v

clean-test: ## Clean test artifacts
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f coverage.xml
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint: ## Run linting checks
	pip install flake8
	flake8 app tests --max-line-length=127 --exclude=venv,__pycache__

format: ## Format code with black
	pip install black
	black app tests

check: lint test ## Run linting and tests

ci: clean-test lint test-coverage ## Run CI pipeline locally

.DEFAULT_GOAL := help
