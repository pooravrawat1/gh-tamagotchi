.PHONY: install install-dev test lint format type-check clean all

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

lint:
	flake8 .

format:
	black .
	isort .

format-check:
	black --check .
	isort --check-only .

type-check:
	mypy --ignore-missing-imports .

security:
	bandit -r . --exclude ./.git,./.kiro,./tests
	safety check

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache

all: format lint type-check test
