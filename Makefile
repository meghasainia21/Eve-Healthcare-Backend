.PHONY: help install run migrate migrate-new downgrade seed test test-cov docker-up docker-down docker-logs lint

help:
	@echo "Common commands:"
	@echo "  make install       Install Python dependencies"
	@echo "  make run           Run the API locally with uvicorn --reload"
	@echo "  make migrate       Apply Alembic migrations (upgrade head)"
	@echo "  make migrate-new msg='...'  Autogenerate a new migration"
	@echo "  make downgrade     Roll back the last migration"
	@echo "  make seed          Populate the database with demo data"
	@echo "  make test          Run the test suite"
	@echo "  make test-cov      Run tests with a coverage report"
	@echo "  make docker-up     Build and start everything with docker-compose"
	@echo "  make docker-down   Stop and remove docker-compose containers"
	@echo "  make docker-logs   Tail the API container logs"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(msg)"

downgrade:
	alembic downgrade -1

seed:
	python -m scripts.seed_data

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=term-missing

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api
