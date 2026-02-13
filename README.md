# gh-tamagotchi

Tamagotchi for your GitHub profile

## Development

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure your environment variables.

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

## CI/CD

The project uses GitHub Actions for continuous integration. On every push and pull request, the following checks run:

- Unit tests (pytest)
- Security checks (bandit, safety)
