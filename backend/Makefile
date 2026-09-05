.PHONY: help build up down logs shell migrate backup test-api test-worker clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker compose build

up: ## Start all services in production mode
	docker compose up -d

up-dev: ## Start all services in development mode
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

down: ## Stop all services
	docker compose down

down-clean: ## Stop services and remove volumes
	docker compose down -v

logs: ## Tail logs from all services
	docker compose logs -f

logs-api: ## Tail API logs
	docker compose logs -f api

logs-worker: ## Tail worker logs
	docker compose logs -f worker

shell: ## Open shell in API container
	docker compose exec api sh

shell-worker: ## Open shell in worker container
	docker compose exec worker sh

migrate: ## Run database migrations
	docker compose exec api alembic upgrade head

migrate-create: ## Create new migration (requires name argument)
	@read -p "Migration name: " name; \
	docker compose exec api alembic revision --autogenerate -m "$$name"

backup: ## Backup PostgreSQL database
	docker compose exec postgres pg_dump -U recon recon > backup_$$(date +%Y%m%d_%H%M%S).sql

restore: ## Restore PostgreSQL database from backup file
	@read -p "Backup file: " file; \
	docker compose exec -T postgres psql -U recon recon < $$file

flower: ## Start Flower monitoring dashboard
	docker compose --profile monitoring up -d flower

flower-down: ## Stop Flower monitoring dashboard
	docker compose --profile monitoring down flower

test-api: ## Test API health endpoint
	curl -s http://127.0.0.1:8000/health | python -m json.tool

test-worker: ## Test Celery worker
	docker compose exec worker celery -A app.core.celery_app inspect ping

clean: ## Remove all containers, volumes, and images
	docker compose down -v
	docker system prune -f --volumes
	docker image prune -a -f
