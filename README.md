# InstantMusic 🎵

> Quiz musical multijoueur en temps réel — Django · React · WebSocket · Docker

[![CI](https://github.com/benoftheworld/instant-music/actions/workflows/ci.yml/badge.svg)](https://github.com/benoftheworld/instant-music/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)

---

## Sommaire

- [Présentation](#-présentation)
- [Stack technique](#-stack-technique)
- [Architecture](#-architecture)
- [Structure du dépôt](#-structure-du-dépôt)
- [Démarrage rapide (local)](#-démarrage-rapide-local)
- [Déploiement en production](#-déploiement-en-production)
- [Linters & qualité du code](#-linters--qualité-du-code)
- [Tests](#-tests)
- [Documentation](#-documentation)

---

## 🎮 Présentation

InstantMusic est une application web de quiz musical multijoueur en temps réel.
Les joueurs rejoignent des salles, écoutent des extraits musicaux (via l'API Deezer)
et doivent identifier le titre ou l'artiste le plus rapidement possible.

**Fonctionnalités principales :**

- Quiz musical multijoueur en temps réel (WebSocket)
- Scoring dynamique basé sur la rapidité de réponse
- Système d'achievements et de statistiques par joueur
- Authentification locale + Google OAuth 2.0
- Interface d'administration avancée (Jazzmin)
- Stack de monitoring optionnelle (Prometheus · Grafana · ELK)

---

## 🛠 Stack technique

| Couche        | Technologies                                                         |
|---------------|----------------------------------------------------------------------|
| **Backend**   | Django 5.1 · DRF · Django Channels · Daphne · Celery · JWT          |
| **Frontend**  | React 18 · TypeScript · Vite · TanStack Query · Zustand · Tailwind  |
| **Base de données** | PostgreSQL 15                                                  |
| **Cache / Broker** | Redis 7                                                         |
| **Temps réel** | Django Channels (WebSocket) · Daphne ASGI                          |
| **Infra**     | Docker · Docker Compose · Nginx · Gunicorn + uvicorn workers         |
| **CI/CD**     | GitHub Actions (ruff · bandit · hadolint · shellcheck · pytest · vitest · trivy) |
| **API externe** | Deezer (gratuit, sans clé)                                        |

---

## 🏗 Architecture

```
Navigateur
    │
    ▼
Nginx (reverse proxy, SSL, rate-limiting)
    │
    ├─── /          ──►  Frontend (React SPA, container nginx:alpine)
    ├─── /api/      ──►  Backend (Django REST Framework, port 8000)
    ├─── /ws/       ──►  Backend (Django Channels WebSocket, upgrade HTTP→WS)
    └─── /admin/    ──►  Backend (Jazzmin admin)
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               PostgreSQL   Redis    Celery Worker
               (données)    (cache,  (tâches async)
                            broker)
                              │
                         Celery Beat
                         (tâches planifiées)
```

**Flux WebSocket (partie quiz) :**

1. Le client se connecte sur `/ws/game/<room_code>/`
2. Django Channels route vers `GameConsumer`
3. Les messages transitent via un channel layer Redis
4. Le consumer diffuse les événements à tous les joueurs de la salle

Pour plus de détails : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📁 Structure du dépôt

```
instant-music/
│
├── Makefile                    # Façade principale — toutes les commandes DevOps
├── pyproject.toml              # Config des linters (ruff, bandit) — niveau racine
├── .pre-commit-config.yaml     # Hooks git pré-commit
│
├── _devops/                    # Tout ce qui concerne le déploiement et les outils
│   ├── docker/
│   │   ├── docker-compose.yml            # Développement local
│   │   ├── docker-compose.prod.yml       # Production
│   │   ├── docker-compose.monitoring.yml # Stack ELK + Prometheus + Grafana
│   │   └── docker-compose.override.yml.example
│   ├── nginx/
│   │   ├── nginx.conf                    # Config Nginx production
│   │   ├── instantmusic.conf.example     # Config Nginx hors Docker
│   │   └── ssl/                          # Certificats SSL (non versionnés)
│   ├── monitoring/
│   │   ├── grafana/provisioning/         # Dashboards & datasources Grafana
│   │   ├── logstash/                     # Config et pipeline Logstash
│   │   └── prometheus/prometheus.yml     # Config Prometheus
│   ├── script/
│   │   ├── deploy.sh                     # Script de déploiement principal
│   │   └── backup.sh                     # Sauvegarde de la base de données
│   └── linter/
│       ├── .bandit.yml                   # Config Bandit
│       ├── .hadolint.yaml                # Config Hadolint
│       └── .yamllint.yml                 # Config Yamllint
│
├── backend/                    # Application Django
│   ├── config/                 # Settings (base, development, production), ASGI, Celery
│   ├── apps/
│   │   ├── achievements/       # Système d'achievements
│   │   ├── administration/     # Mode maintenance, administration
│   │   ├── authentication/     # JWT, Google OAuth
│   │   ├── core/               # Health check
│   │   ├── games/              # Logique de jeu, WebSocket consumer, services
│   │   ├── playlists/          # Intégration Deezer, gestion des playlists
│   │   ├── stats/              # Statistiques joueurs
│   │   └── users/              # Modèle utilisateur personnalisé
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   └── pyproject.toml          # Config mypy uniquement
│
├── frontend/                   # Application React
│   ├── src/
│   │   ├── components/          # Composants réutilisables
│   │   ├── pages/               # Pages de l'application
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # Appels API et WebSocket
│   │   ├── store/               # Store Zustand
│   │   └── types/               # Types TypeScript
│   └── package.json
│
├── docs/                       # Documentation détaillée
│   ├── ARCHITECTURE.md
│   ├── QUICK_START.md
│   ├── PRODUCTION_DEPLOYMENT.md
│   ├── GAMEPLAY_SYSTEM.md
│   ├── LINTERS.md
│   ├── CONTRIBUTING.md
│   └── SECURITY.md
│
└── .github/
    └── workflows/ci.yml        # Pipeline CI/CD GitHub Actions
```

---

## 🚀 Démarrage rapide (local)

### Prérequis

- Docker 24+ avec Docker Compose v2
- Git

### 1. Cloner le dépôt

```bash
git clone https://github.com/benoftheworld/instant-music.git
cd instant-music
```

### 2. Configurer l'environnement

```bash
cp backend/.env.example backend/.env
# Éditez backend/.env si nécessaire (les valeurs par défaut fonctionnent en dev)
```

### 3. Lancer l'application

```bash
make deploy-dev
```

C'est tout. L'application est disponible sur :

| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend    | http://localhost:8000        |
| Admin      | http://localhost:8000/admin  |
| API docs   | http://localhost:8000/api/schema/swagger-ui/ |

### Commandes utiles en développement

```bash
make logs-dev                        # Logs en temps réel
make dev-shell                       # Shell dans le container backend
make dev-createsuperuser             # Créer un compte admin
make dev-migrate                     # Appliquer les migrations
make dev-makemigrations              # Créer de nouvelles migrations
```

Pour toutes les commandes disponibles :

```bash
make help
```

---

## 🏭 Déploiement en production

> Guide complet : [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)

### Depuis votre VPS

```bash
# 1. Cloner et configurer
git clone https://github.com/benoftheworld/instant-music.git
cd instant-music
cp .env.prod.example .env.prod
nano .env.prod  # Renseigner les variables (DB, SECRET_KEY, domaine, SSL...)

# 2. Déployer (une seule commande)
make deploy-prod
```

### Mise à jour

```bash
# Sur le VPS — récupère le code, rebuild et redémarre automatiquement
make deploy-prod
```

### Rollback

```bash
# Revenir à la version déployée précédemment
make rollback
```

### Monitoring

```bash
# État des services
make status

# Logs en temps réel
make logs

# Logs d'un service spécifique
make logs-backend

# Démarrer la stack de monitoring (Grafana, Prometheus, ELK)
make monitoring-up
```

### Accès directs

```bash
make prod-shell             # Shell dans le container backend
make prod-createsuperuser   # Créer un compte admin
make backup                 # Sauvegarder la base de données
```

---

## 🔍 Linters & qualité du code

| Outil         | Rôle                                    | Config                             |
|---------------|-----------------------------------------|------------------------------------|
| **ruff**      | Lint + formatage Python (remplace black + flake8 + isort) | `pyproject.toml`     |
| **bandit**    | Scan de sécurité Python                 | `pyproject.toml` + `_devops/linter/.bandit.yml` |
| **mypy**      | Vérification des types Python           | `backend/pyproject.toml`           |
| **hadolint**  | Lint Dockerfiles                        | `_devops/linter/.hadolint.yaml`    |
| **shellcheck**| Lint scripts shell                      | (inline CI)                        |
| **yamllint**  | Lint fichiers YAML                      | `_devops/linter/.yamllint.yml`     |
| **prettier**  | Formatage TypeScript/CSS/JSON           | `frontend/.prettierrc`             |
| **ESLint**    | Lint TypeScript/React                   | `frontend/.eslintrc.json`          |

```bash
# Lancer tous les linters
make lint

# Formater automatiquement le code Python
make format

# Vérification des types
make typecheck
```

### Pre-commit (recommandé)

```bash
make pre-commit-install   # Installe les hooks git
# Les hooks s'exécutent ensuite automatiquement à chaque commit
```

---

## 🧪 Tests

```bash
# Tous les tests
make test

# Backend uniquement
make test-backend

# Frontend uniquement
make test-frontend

# Avec rapport de couverture
make test-coverage
```

Le pipeline CI tourne automatiquement tous les tests + linters à chaque push.

---

## 📖 Documentation

| Document | Description |
|---|---|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Installation express |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture détaillée des composants |
| [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) | Guide complet de déploiement VPS |
| [docs/GAMEPLAY_SYSTEM.md](docs/GAMEPLAY_SYSTEM.md) | Système de jeu, scoring, WebSocket |
| [docs/LINTERS.md](docs/LINTERS.md) | Outils de qualité du code |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contribuer au projet |
| [docs/SECURITY.md](docs/SECURITY.md) | Checklist de sécurité production |
| [_devops/README.md](_devops/README.md) | Documentation DevOps |

---

## 📄 Licence

[MIT](LICENSE) — benoftheworld
