.PHONY: help install dev test lint format type-check clean build publish

help:
	@echo "SIGMAX SDK - Development Commands"
	@echo ""
	@echo "install       Install package in development mode"
	@echo "dev           Install with development dependencies"
	@echo "test          Run tests with pytest"
	@echo "lint          Run ruff linter"
	@echo "format        Format code with black"
	@echo "type-check    Run mypy type checker"
	@echo "clean         Remove build artifacts"
	@echo "build         Build distribution packages"
	@echo "publish       Publish to PyPI (requires credentials)"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=sigmax_sdk --cov-report=term-missing

lint:
	ruff check sigmax_sdk tests examples

format:
	black sigmax_sdk tests examples
	ruff check --fix sigmax_sdk tests examples

type-check:
	mypy sigmax_sdk

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

# Development workflow
check: format lint type-check test
	@echo "✓ All checks passed!"
