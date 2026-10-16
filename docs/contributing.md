# Contributing Guide

## Development Setup

```bash
# Fork & clone
git clone https://github.com/YOUR_USERNAME/control-red-v9-dev.git
cd control-red-v9-dev/backend

# Install dev dependencies
make install
pip install pytest black flake8 isort pre-commit

# Setup pre-commit
pre-commit install

# Run tests
make test
```

## Code Style

- **Python:** PEP 8, Black formatter, isort
- **JavaScript:** ES6+, 2 spaces indent
- **Commits:** Conventional Commits

## Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactor
- `test`: Add tests
- `docs`: Documentation
- `chore`: Maintenance

**Example:**
```
feat(websocket): add real-time device updates

Implement WebSocket broadcasting for device changes.
Clients now receive instant updates without polling.

Closes #42
```

## Pull Request Process

1. Create feature branch: `git checkout -b feat/your-feature`
2. Make changes + add tests
3. Run tests: `make test`
4. Commit: `git commit -m "feat: your feature"`
5. Push: `git push origin feat/your-feature`
6. Open PR on GitHub

## Testing Requirements

- ✅ Unit tests for new functions
- ✅ Integration tests for API endpoints
- ✅ Coverage must stay > 80%
- ✅ All tests must pass

## Review Checklist

- [ ] Tests pass (`make test`)
- [ ] Coverage > 80% (`pytest --cov`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Conventional Commits followed

## Questions?

Open a Discussion on GitHub.
