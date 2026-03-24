# Contributing

Thanks for your interest in contributing to et-scrapper.

## Development Setup

1. Fork and clone the repository.
2. Install dependencies.

```bash
uv sync
```

1. Run the manual diagnostics script.

```bash
uv run python manual_test.py
```

1. Build docs locally.

```bash
uv pip install -r docs/requirements.txt
uv run sphinx-build -b html docs docs/_build/html
```

## Code Style

- Keep changes focused and small.
- Prefer clear naming and explicit typing.
- Add docstrings for public classes and methods.
- Avoid unrelated refactors in the same pull request.

## Pull Requests

- Use conventional commit messages when possible.
- Include a clear description of what changed and why.
- Add reproduction and validation steps for bug fixes.
- Update docs when behavior or APIs change.

## Reporting Issues

Please include:

- What you expected
- What happened
- Minimal steps to reproduce
- Python version and platform details
