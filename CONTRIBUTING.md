# Contributing to GitHub Tamagotchi

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment

## Testing Guidelines

- Write unit tests for all new functions and classes
- Use fixtures for common test setup
- Mock external dependencies (GitHub API, etc.)
- Test edge cases and error conditions
- Keep tests focused and readable

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Commit with clear, descriptive messages
6. Push to your fork and create a pull request
7. Wait for CI checks to pass
8. Address any review feedback

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

## Code Review Checklist

Before submitting a PR, ensure:
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
