# Contributing to PyDBAdminKit

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

## Quality checks

```bash
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit
```

Use short-lived branches and Conventional Commits. Public behavior changes must include tests.
