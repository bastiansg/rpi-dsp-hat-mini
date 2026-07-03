.PHONY: uv-setup app format lint lint-fix typecheck check start stop restart

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

start:
	pm2 start && pm2 save --force

stop:
	pm2 stop all && pm2 save --force
	pm2 flush

restart: stop start
