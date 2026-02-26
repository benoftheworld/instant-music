# =============================================================================
# InstantMusic — Makefile
# =============================================================================
# Commande unique pour toutes les opérations DevOps.
# Prérequis : Docker, Docker Compose v2, git
#
# Utilisation :
#   make deploy-prod     Déployer en production
#   make deploy-dev      Lancer en développement
#   make status          État des services (production)
#   make logs            Logs en temps réel (production)
#   make rollback        Revenir à la version précédente (production)
#   make lint            Vérification du code (ruff + bandit)
#   make format          Formatage automatique (ruff format)
#   make test            Lancer tous les tests
#   make backup          Sauvegarder la base de données
# =============================================================================

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

DEPLOY_SCRIPT  := ./_devops/script/deploy.sh
COMPOSE_PROD   := _devops/docker/docker-compose.prod.yml
COMPOSE_DEV    := _devops/docker/docker-compose.yml
COMPOSE_MON    := _devops/docker/docker-compose.monitoring.yml

# Récupère le fichier .env.prod si présent
ENV_FILE       := $(wildcard _devops/docker/.env.prod)
COMPOSE_EXTRA  := $(if $(ENV_FILE),--env-file $(ENV_FILE),)

DC_PROD        := docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA)
DC_DEV         := docker compose -f $(COMPOSE_DEV)

# ─── Déploiement ─────────────────────────────────────────────────────────────

.PHONY: deploy-prod
deploy-prod: ## Déployer en production (git pull + build + migrate + static)
	@$(DEPLOY_SCRIPT) production

.PHONY: deploy-dev
deploy-dev: ## Lancer l'environnement de développement
	@$(DEPLOY_SCRIPT) development

.PHONY: deploy-prod-no-pull
deploy-prod-no-pull: ## Déployer en production sans git pull
	@$(DEPLOY_SCRIPT) production --no-pull

.PHONY: rollback
rollback: ## Revenir à la version précédente (production)
	@$(DEPLOY_SCRIPT) production --rollback

# ─── Monitoring ──────────────────────────────────────────────────────────────

.PHONY: status
status: ## État de tous les services (production)
	@$(DEPLOY_SCRIPT) production --status

.PHONY: logs
logs: ## Logs en temps réel — tous les services (production)
	@$(DC_PROD) logs -f --tail=100

.PHONY: logs-backend
logs-backend: ## Logs du service backend (production)
	@$(DC_PROD) logs -f --tail=100 backend

.PHONY: logs-nginx
logs-nginx: ## Logs du service nginx (production)
	@$(DC_PROD) logs -f --tail=100 nginx

.PHONY: logs-dev
logs-dev: ## Logs en développement
	@$(DC_DEV) logs -f --tail=100

.PHONY: monitoring-up
monitoring-up: ## Lancer la stack de monitoring (ELK + Prometheus + Grafana)
	@docker compose -f $(COMPOSE_PROD) -f $(COMPOSE_MON) $(COMPOSE_EXTRA) up -d
	@echo "Kibana   -> http://localhost:5601"
	@echo "Grafana  -> http://localhost:3001  (admin/admin)"
	@echo "Prometheus -> http://localhost:9090"

.PHONY: monitoring-down
monitoring-down: ## Arrêter la stack de monitoring
	@docker compose -f $(COMPOSE_PROD) -f $(COMPOSE_MON) $(COMPOSE_EXTRA) down

# ─── Développement ───────────────────────────────────────────────────────────

.PHONY: dev-up
dev-up: ## Démarrer les services de développement
	@$(DC_DEV) up -d

.PHONY: dev-down
dev-down: ## Arrêter les services de développement
	@$(DC_DEV) down

.PHONY: dev-shell
dev-shell: ## Shell interactif dans le container backend (dev)
	@$(DC_DEV) exec backend bash

.PHONY: dev-createsuperuser
dev-createsuperuser: ## Créer un superutilisateur (dev)
	@$(DC_DEV) exec backend python manage.py createsuperuser

.PHONY: dev-migrate
dev-migrate: ## Appliquer les migrations (dev)
	@$(DC_DEV) exec backend python manage.py migrate

.PHONY: dev-makemigrations
dev-makemigrations: ## Créer de nouvelles migrations (dev)
	@$(DC_DEV) exec backend python manage.py makemigrations

# ─── Linters & Qualité du code ───────────────────────────────────────────────

.PHONY: lint
lint: lint-python lint-yaml ## Lancer tous les linters

.PHONY: lint-python
lint-python: ## Ruff check + bandit sur le backend
	@echo "== ruff check =="
	@ruff check backend/
	@echo "== ruff format --check =="
	@ruff format --check backend/
	@echo "== bandit =="
	@bandit -r backend/ -c pyproject.toml -ll -q
	@echo "Python lint OK"

.PHONY: lint-yaml
lint-yaml: ## Yamllint sur tous les fichiers YAML
	@yamllint -c _devops/linter/.yamllint.yml .

.PHONY: format
format: ## Formatage automatique du backend avec ruff
	@ruff format backend/
	@ruff check --fix backend/
	@echo "Format OK"

.PHONY: typecheck
typecheck: ## Vérification des types avec mypy
	@mypy backend/ --config-file backend/pyproject.toml

# ─── Tests ───────────────────────────────────────────────────────────────────

.PHONY: test
test: test-backend test-frontend ## Lancer tous les tests

.PHONY: test-backend
test-backend: ## Tests backend (pytest)
	@cd backend && pytest -q

.PHONY: test-frontend
test-frontend: ## Tests frontend (vitest)
	@cd frontend && npm test --silent

.PHONY: test-coverage
test-coverage: ## Couverture de code (backend + frontend)
	@cd backend && pytest --cov=apps --cov-report=html -q
	@cd frontend && npm run test:coverage

# ─── Base de données ─────────────────────────────────────────────────────────

.PHONY: backup
backup: ## Sauvegarder la base de données de production
	@./_devops/script/backup.sh

.PHONY: prod-shell
prod-shell: ## Shell interactif dans le container backend (prod)
	@$(DC_PROD) exec backend bash

.PHONY: prod-dbshell
prod-dbshell: ## Shell PostgreSQL (prod)
	@$(DC_PROD) exec db psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-instantmusic}

.PHONY: prod-createsuperuser
prod-createsuperuser: ## Créer un superutilisateur (prod)
	@$(DC_PROD) exec backend python manage.py createsuperuser

# ─── Pre-commit ──────────────────────────────────────────────────────────────

.PHONY: pre-commit-install
pre-commit-install: ## Installer les hooks git pre-commit
	@pre-commit install
	@echo "Hooks pre-commit installes."

.PHONY: pre-commit-run
pre-commit-run: ## Lancer pre-commit sur tous les fichiers
	@pre-commit run --all-files

# ─── Aide ─────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Afficher cette aide
	@echo ""
	@echo "  InstantMusic — Makefile"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'
	@echo ""
