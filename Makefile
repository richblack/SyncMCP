.PHONY: help install dev-install test test-cov lint format type-check quality clean pre-commit-install pre-commit-run build

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install:  ## Install package in production mode
	pip install -e .

dev-install:  ## Install package with development dependencies
	pip install -e ".[dev]"

test:  ## Run tests without coverage
	pytest tests/ -v

test-cov:  ## Run tests with coverage report
	pytest tests/ -v --cov=syncmcp --cov-report=html --cov-report=term

lint:  ## Run linting with Ruff
	ruff check syncmcp/ tests/

format:  ## Format code with Black and isort
	black syncmcp/ tests/
	isort syncmcp/ tests/ --profile black

format-check:  ## Check code formatting without modifying files
	black --check syncmcp/ tests/
	isort --check-only syncmcp/ tests/ --profile black

type-check:  ## Run type checking with MyPy
	mypy syncmcp/ --ignore-missing-imports

security:  ## Run security checks with Bandit
	bandit -r syncmcp/ -c pyproject.toml

quality: format-check lint type-check  ## Run all code quality checks

clean:  ## Clean build artifacts and caches
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	pre-commit run --all-files

build:  ## Build distribution packages
	python -m build

build-check:  ## Build and check package with twine
	python -m build
	twine check dist/*

# Development workflow shortcuts
dev: dev-install pre-commit-install  ## Set up complete development environment
	@echo "✅ Development environment ready!"
	@echo "Run 'make test' to verify setup"

ci-local: quality test-cov  ## Run CI checks locally before pushing
	@echo "✅ All CI checks passed!"
