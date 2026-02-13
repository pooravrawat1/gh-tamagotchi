.PHONY: install test clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
