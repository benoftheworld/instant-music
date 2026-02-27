# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commandes essentielles

Toutes les commandes DevOps passent par le **Makefile** à la racine. Prérequis : Docker + Docker Compose v2.

### Développement

```bash
make deploy-dev              # Lancer tout l'environnement local (DB, Redis, Backend, Frontend, Celery)
make logs-dev                # Logs temps réel
make dev-shell               # Shell dans le container backend
make dev-migrate             # Appliquer les migrations Django
make dev-makemigrations      # Créer de nouvelles migrations
make dev-createsuperuser     # Créer un compte admin
```

Accès local : Frontend http://localhost:3000, Backend http://localhost:8000, Admin http://localhost:8000/admin, Swagger http://localhost:8000/api/schema/swagger-ui/

### Tests

```bash
make test                    # Tous les tests (backend + frontend)
make test-backend            # pytest uniquement (cd backend && pytest -q)
make test-frontend           # vitest uniquement (cd frontend && npm test --silent)
make test-coverage           # Rapports de couverture HTML
```

Backend : `pytest` avec `@pytest.mark.django_db` pour les tests nécessitant la DB. Tests dans `backend/apps/<app>/tests.py` ou `backend/apps/<app>/tests/`.
Frontend : `vitest` + `@testing-library/react`. Tests dans `frontend/src/**/__tests__/` ou `*.test.tsx`.

### Linting & formatage

```bash
make lint                    # ruff check + ruff format --check + bandit + yamllint
make format                  # Formatage auto Python (ruff format + ruff check --fix)
make typecheck               # mypy sur le backend
```

Frontend : `cd frontend && npm run lint` (ESLint + Prettier).

Configuration ruff : `pyproject.toml` racine (line-length=88, target py311, double quotes).

## Architecture

Application de quiz musical multijoueur temps réel. Stack :

- **Backend** : Django 5.1 + DRF + Django Channels (WebSocket) + Celery (tâches async) + Redis (cache/broker) + PostgreSQL 15
- **Frontend** : React 18 + TypeScript + Vite + Zustand (state) + TanStack Query (data fetching) + Tailwind CSS
- **Infra** : Docker Compose, Nginx reverse proxy, Gunicorn + uvicorn workers en prod

### Flux réseau

```
Nginx :80/:443
  ├── /         → Frontend (React SPA, nginx:alpine)
  ├── /api/     → Backend Django REST Framework :8000
  ├── /ws/      → Backend Django Channels WebSocket (upgrade HTTP→WS)
  └── /admin/   → Jazzmin admin panel
```

### Flux WebSocket (quiz temps réel)

Le client se connecte sur `/ws/game/<room_code>/`. Django Channels route vers `GameConsumer` (`backend/apps/games/consumers.py`). Les messages transitent via un channel layer Redis (group `game_<code>`).

Messages principaux : `player_join`, `start_game`, `player_answer` (client→serveur) ; `start_round`, `end_round`, `next_round`, `finish_game` (serveur→client).

### Applications Django (`backend/apps/`)

| App              | Rôle                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------ |
| `users`          | Modèle utilisateur custom (`AUTH_USER_MODEL`)                                              |
| `authentication` | JWT (simplejwt) + Google OAuth 2.0                                                         |
| `games`          | Logique de jeu, WebSocket consumer, services, modèles Game/GameRound/GamePlayer/GameAnswer |
| `playlists`      | Intégration API Deezer (extraits musicaux), gestion playlists                              |
| `achievements`   | Système de succès/badges                                                                   |
| `stats`          | Statistiques joueurs, classements                                                          |
| `administration` | Mode maintenance (middleware), outils admin                                                |

`core` (health check) n'a pas d'app dédiée listée dans `LOCAL_APPS` mais existe dans les URLs.

### Fichiers de configuration clés

- **Settings Django** : `backend/config/settings/{base,development,production}.py` — split par environnement
- **ASGI/WebSocket** : `backend/config/asgi.py` — routage Channels
- **Celery** : `backend/config/celery.py`
- **URLs** : `backend/config/urls.py` (HTTP), `backend/apps/games/routing.py` (WebSocket)
- **Docker dev** : `_devops/docker/docker-compose.yml`
- **Docker prod** : `_devops/docker/docker-compose.prod.yml`
- **Monitoring** : `_devops/docker/docker-compose.monitoring.yml` (Prometheus, Grafana, ELK)
- **Nginx prod** : `_devops/nginx/nginx.conf`
- **Linters** : `pyproject.toml` (ruff, bandit), `_devops/linter/` (.hadolint.yaml, .yamllint.yml, .bandit.yml)
- **CI/CD** : `.github/workflows/ci.yml`

## Conventions

- **Langue** : projet en français (docs, commentaires, noms de branches, messages de commit)
- **Commits** : format `type(scope): description` — types : feat, fix, docs, style, refactor, test, chore
- **Branches** : `feature/<desc>`, `fix/<desc>`, `hotfix/<desc>`, `docs/<desc>` depuis `develop` (ou `main`)
- **Python** : ruff format (88 chars, double quotes, py311), bandit pour la sécurité
- **TypeScript** : Prettier (100 chars, single quotes, trailing commas ES5), ESLint
- **Migrations** : versionnées dans Git, ne jamais modifier les migrations existantes mergées sur `main`
- **Variables d'environnement** : toute nouvelle variable doit être documentée dans `.env.example`
- **Pre-commit hooks** : `make pre-commit-install` pour activer (ruff, bandit, etc.)
