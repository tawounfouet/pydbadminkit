.PHONY: install format lint type test test-unit quality build clean db-up db-down

install:
	python -m pip install -e ".[dev,binary]"

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .

type:
	mypy src/pydbadminkit

test:
	pytest

test-unit:
	pytest -m unit

quality:
	ruff format --check .
	ruff check .
	mypy src/pydbadminkit
	pytest -m unit

build:
	python -m build

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

clean:
	rm -rf build dist .coverage coverage.xml htmlcov .pytest_cache .mypy_cache .ruff_cache
