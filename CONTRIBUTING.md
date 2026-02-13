# Contributing to GitHub Tamagotchi

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Set up pre-commit hooks (recommended):
   ```bash
   pre-commit install
   ```
4. Copy `.env.example` to `.env` and configure your environment

## Code Quality Standards

We maintain high code quality standards using automated tools:

### Formatting
- **Black**: Code formatter (line length: 100)
- **isort**: Import sorting

Run formatters:
```bash
make format
# or
black . && isort .
```

### Linting
- **flake8**: Style guide enforcement
- **mypy**: Static type checking

Run linters:
```bash
make lint
make type-check
```

### Testing
- **pytest**: Test framework
- Minimum 80% code coverage expected
- All tests must pass before merging

Run tests:
```bash
make test
# or with coverage
make test-cov
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the code quality standards
3. Add tests for new functionality
4. Ensure all tests pass and coverage is maintained
5. Run all quality checks: `make all`
6. Commit with clear, descriptive messages
7. Push to your fork and create a pull request
8. Wait for CI checks to pass
9. Address any review feedback

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
```
Add pet evolution stage calculation
Fix hunger decay rate calculation
Update README with setup instructions
```

## Testing Guidelines

- Write unit tests for all new functions and classes
- Use fixtures for common test setup
- Mock external dependencies (GitHub API, etc.)
- Test edge cases and error conditions
- Keep tests focused and readable

## Code Review Checklist

Before submitting a PR, ensure:
- [ ] Code follows project style (Black, isort)
- [ ] All linting checks pass (flake8, mypy)
- [ ] Tests are added for new functionality
- [ ] All tests pass
- [ ] Documentation is updated if needed
- [ ] No sensitive data (tokens, keys) in code
- [ ] Commit messages are clear and descriptive

## Questions or Issues?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase
- Suggestions for improvements

Thank you for contributing!
