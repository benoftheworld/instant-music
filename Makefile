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
COMPOSE_MON_PROD := _devops/docker/docker-compose.monitoring-prod.yml
COMPOSE_SSL_INIT := _devops/docker/docker-compose.ssl-init.yml

# Domaine de production (override via `make <target> DOMAIN=mondomaine.fr`)
DOMAIN         ?= benoftheworld.fr

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
monitoring-up: ## Lancer la stack de monitoring (ELK + Prometheus + Grafana) — DEV
	@docker compose -f $(COMPOSE_DEV) -f $(COMPOSE_MON) $(COMPOSE_EXTRA) up -d
	@echo "Kibana   -> http://localhost:5601"
	@echo "Grafana  -> http://localhost:3001  (admin/admin)"
	@echo "Prometheus -> http://localhost:9090"

.PHONY: monitoring-up-prod
monitoring-up-prod: ## Lancer le monitoring en production (derrière nginx, pas de ports exposés)
	@test -f _devops/nginx/monitoring/.htpasswd || \
	  { echo ""; echo "  ERREUR: fichier .htpasswd manquant."; echo "  Exécuter : make monitoring-htpasswd"; echo ""; exit 1; }
	@docker compose -f $(COMPOSE_MON_PROD) $(COMPOSE_EXTRA) up -d
	@echo ""
	@echo "Monitoring disponible sur https://$(DOMAIN)"
	@echo "  Grafana    -> https://$(DOMAIN)/grafana/"
	@echo "  Prometheus -> https://$(DOMAIN)/prometheus/"
	@echo "  Kibana     -> https://$(DOMAIN)/kibana/"
	@echo ""
	@echo "Connexion protégée par HTTP Basic Auth (utilisateur défini dans .htpasswd)"

.PHONY: monitoring-down
monitoring-down: ## Arrêter la stack de monitoring (dev)
	@docker compose -f $(COMPOSE_DEV) -f $(COMPOSE_MON) $(COMPOSE_EXTRA) down

.PHONY: monitoring-down-prod
monitoring-down-prod: ## Arrêter la stack de monitoring (production)
	@docker compose -f $(COMPOSE_MON_PROD) $(COMPOSE_EXTRA) down

.PHONY: monitoring-kibana-import
monitoring-kibana-import: ## Importer index patterns + dashboards dans Kibana (prod)
	@echo ""
	@echo "Import des saved objects Kibana..."
	@docker compose -f $(COMPOSE_MON_PROD) $(COMPOSE_EXTRA) cp \
	  _devops/monitoring/kibana/saved-objects.ndjson \
	  kibana:/tmp/kibana-saved-objects.ndjson
	@docker compose -f $(COMPOSE_MON_PROD) $(COMPOSE_EXTRA) exec kibana \
	  curl -f -X POST "http://localhost:5601/kibana/api/saved_objects/_import?overwrite=true" \
	  -H "kbn-xsrf: true" \
	  --form "file=@/tmp/kibana-saved-objects.ndjson"
	@echo ""
	@echo "Import terminé. Dashboard disponible sur https://$(DOMAIN)/kibana/"
	@echo ""

.PHONY: monitoring-htpasswd
monitoring-htpasswd: ## Créer le fichier .htpasswd pour protéger les interfaces monitoring
	@echo ""
	@echo "Création du fichier de mots de passe pour le monitoring..."
	@mkdir -p _devops/nginx/monitoring
	@if command -v htpasswd >/dev/null 2>&1; then \
	  htpasswd -c _devops/nginx/monitoring/.htpasswd admin; \
	elif command -v openssl >/dev/null 2>&1; then \
	  echo "htpasswd non trouvé — utilisation d'openssl (installer apache2-utils pour htpasswd natif)"; \
	  HASH=$$(openssl passwd -apr1) && echo "admin:$$HASH" > _devops/nginx/monitoring/.htpasswd; \
	else \
	  docker run --rm -i xmartlabs/htpasswd admin > _devops/nginx/monitoring/.htpasswd; \
	fi
	@echo ""
	@echo ".htpasswd créé dans _devops/nginx/monitoring/.htpasswd"
	@echo "Redémarrer nginx pour appliquer : docker compose -f $(COMPOSE_PROD) restart nginx"

# ─── SSL / Certificats ────────────────────────────────────────────────────────

.PHONY: ssl-init
ssl-init: ## Obtenir le premier certificat SSL Let's Encrypt (première installation)
	@test -n "$(DOMAIN)" || { echo ""; echo "  Usage: make ssl-init DOMAIN=benoftheworld.fr EMAIL=admin@benoftheworld.fr"; echo ""; exit 1; }
	@test -n "$(EMAIL)"  || { echo ""; echo "  Usage: make ssl-init DOMAIN=benoftheworld.fr EMAIL=admin@benoftheworld.fr"; echo ""; exit 1; }
	@echo ""
	@echo "== Étape 1/3 : Démarrage nginx en mode HTTP-only (init)..."
	@docker compose -f $(COMPOSE_PROD) -f $(COMPOSE_SSL_INIT) $(COMPOSE_EXTRA) up -d nginx
	@sleep 3
	@echo "== Étape 2/3 : Obtention du certificat Let's Encrypt (webroot)..."
	@docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA) run --rm --entrypoint certbot certbot certonly \
	  --webroot -w /var/www/certbot \
	  -d $(DOMAIN) \
	  --agree-tos --email $(EMAIL) --no-eff-email
	@echo "== Étape 3/3 : Redémarrage nginx avec la config SSL complète..."
	@docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA) up -d nginx
	@echo ""
	@echo "Certificat SSL obtenu pour $(DOMAIN)!"
	@echo "Le service certbot assure le renouvellement automatique toutes les 12h."

.PHONY: ssl-renew
ssl-renew: ## Forcer le renouvellement du certificat SSL (normalement automatique)
	@docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA) exec certbot certbot renew --quiet
	@docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA) exec nginx nginx -s reload
	@echo "Certificat renouvelé et nginx rechargé."

.PHONY: ssl-status
ssl-status: ## Vérifier l'état et la date d'expiration du certificat SSL
	@docker compose -f $(COMPOSE_PROD) $(COMPOSE_EXTRA) run --rm certbot certbot certificates

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
lint: lint-python lint-frontend lint-yaml ## Lancer tous les linters

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

.PHONY: lint-frontend
lint-frontend: ## ESLint sur le frontend
	@cd frontend && npm run lint
	@echo "Frontend lint OK"

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

.PHONY: backup-cron-install
backup-cron-install: ## Installer un cron de backup quotidien (02h00)
	@(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo "0 2 * * * cd $(CURDIR) && ./_devops/script/backup.sh >> $(CURDIR)/backups/cron.log 2>&1") | crontab -
	@echo "Cron de backup quotidien installe (02h00). Verifiez avec : crontab -l"

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
