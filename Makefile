.PHONY: uv-setup app format lint lint-fix typecheck check

uv-setup:
	uv venv --clear
	uv pip install -r requirements.txt

app:
	uv run python -m src.apps.status_display.main

format:
	uv run ruff format src

lint:
	uv run ruff check src

lint-fix:
	uv run ruff check --fix src

typecheck:
	uv run pyrefly check

check: lint typecheck

