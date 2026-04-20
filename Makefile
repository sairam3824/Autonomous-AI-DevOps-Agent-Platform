.PHONY: setup dev build up down test test-frontend seed logs clean help

COMPOSE_FILE := infra/docker/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Full setup: build, start, and seed
	bash infra/scripts/setup.sh

dev: ## Start in dev mode (hot reload)
	bash infra/scripts/dev.sh

build: ## Build Docker images
	docker compose -f $(COMPOSE_FILE) build

up: ## Start all services
	docker compose -f $(COMPOSE_FILE) up -d

down: ## Stop all services
	docker compose -f $(COMPOSE_FILE) down

test: ## Run backend tests
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend lint and type check
	cd frontend && npm run lint && npm run type-check

seed: ## Seed the database with demo data
	bash infra/scripts/seed.sh

logs: ## Tail service logs
	docker compose -f $(COMPOSE_FILE) logs -f

clean: ## Stop services and remove volumes
	docker compose -f $(COMPOSE_FILE) down -v
	rm -rf backend/__pycache__ backend/.pytest_cache backend/faiss_index backend/*.db
	rm -rf frontend/.next frontend/node_modules
