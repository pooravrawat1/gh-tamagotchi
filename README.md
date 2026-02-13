# gh-tamagotchi

[![CI](https://github.com/YOUR_USERNAME/gh-tamagotchi/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/gh-tamagotchi/actions/workflows/ci.yml)

Tamagotchi for your GitHub profile

## Development

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Copy `.env.example` to `.env` and configure your environment variables.

4. (Optional) Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

### Code Quality

Format code with Black:
```bash
black .
```

Sort imports with isort:
```bash
isort .
```

Lint with flake8:
```bash
flake8 .
```

Type check with mypy:
```bash
mypy .
```

Run all checks at once:
```bash
black . && isort . && flake8 . && mypy . && pytest
```

## CI/CD

The project uses GitHub Actions for continuous integration. On every push and pull request, the following checks run:

- Code formatting (Black)
- Import sorting (isort)
- Linting (flake8)
- Type checking (mypy)
- Unit tests (pytest)
- Security checks (bandit, safety)
