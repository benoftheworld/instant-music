# InstantMusic — Documentation

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Django](https://img.shields.io/badge/Django-5.1-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Introduction

**InstantMusic** est un jeu de quiz musical multijoueur en temps réel. Plusieurs joueurs s'affrontent dans une salle de jeu : chacun entend un extrait musical et doit répondre le plus vite possible aux questions posées (titre, artiste, année de sortie, paroles...). Le joueur le plus rapide et le plus précis remporte le plus de points.

Le projet est une application web moderne, construite sur une architecture découpée en plusieurs services indépendants qui communiquent entre eux. Cette documentation explique comment tous ces services fonctionnent, comment les démarrer, et comment contribuer au projet.

---

## Schema global de l'architecture

```
                         ┌─────────────────────────────────────────────────────────┐
                         │                    UTILISATEURS                          │
                         │          Navigateur web (Chrome, Firefox...)             │
                         └─────────────────────┬───────────────────────────────────┘
                                               │ HTTP / HTTPS / WebSocket
                                               ▼
                         ┌─────────────────────────────────────────────────────────┐
                         │                  NGINX (port 80/443)                    │
                         │              Reverse Proxy + SSL Termination             │
                         │                                                          │
                         │  /           → Frontend React  (port 3000)              │
                         │  /api/       → Backend Django  (port 8000)              │
                         │  /ws/        → WebSocket       (port 8000)              │
                         │  /admin/     → Django Admin     (port 8000)             │
                         └──────┬────────────────────┬───────────────────────────-─┘
                                │                    │
                  ┌─────────────▼──────┐  ┌──────────▼────────────┐
                  │  FRONTEND (: 3000) │  │  BACKEND  (:8000)      │
                  │  React 18 + Vite   │  │  Django 5.1 + DRF      │
                  │  TypeScript        │  │  Django Channels (WS)  │
                  └────────────────────┘  └──────┬───────┬─────────┘
                                                 │       │
                              ┌──────────────────┘       └──────────────────┐
                              │                                               │
                  ┌───────────▼──────────┐                    ┌──────────────▼─────────┐
                  │  POSTGRESQL (:5433)  │                    │   REDIS (:6379)         │
                  │  Base de données     │                    │   Cache + Broker + WS   │
                  │  principale          │                    │   Channel Layer         │
                  └──────────────────────┘                    └──────────────┬──────────┘
                                                                             │
                                                         ┌───────────────────┴────────────────┐
                                                         │                                     │
                                             ┌───────────▼──────────┐  ┌─────────────────────▼──┐
                                             │  CELERY WORKER        │  │   CELERY BEAT           │
                                             │  Taches asynchrones   │  │   Planificateur         │
                                             │  (achievements, RGPD) │  │   (taches periodiques)  │
                                             └──────────────────────┘  └────────────────────────┘
```

---

## Table des matieres

### Demarrage rapide

| Document                       | Description                                       |
| ------------------------------ | ------------------------------------------------- |
| [README.md](./README.md)       | Installation, demarrage et commandes essentielles |
| [CHANGELOG.md](./CHANGELOG.md) | Historique des versions et modifications          |

### Architecture

| Document                                                              | Description                                           |
| --------------------------------------------------------------------- | ----------------------------------------------------- |
| [01 - Vue d'ensemble](./architecture/01-vue-ensemble.md)              | Schema global, roles des composants, choix techniques |
| [02 - Interactions entre composants](./architecture/02-composants.md) | Communication inter-services, flux HTTP/WS/Celery     |
| [03 - Nginx](./architecture/03-nginx.md)                              | Reverse proxy, routage, SSL, securite                 |
| [04 - Redis](./architecture/04-redis.md)                              | Cache, channel layer WebSocket, broker Celery         |
| [05 - Celery](./architecture/05-celery.md)                            | Taches asynchrones, planificateur, workers            |
| [06 - WebSockets](./architecture/06-websockets.md)                    | Temps reel, Django Channels, protocole de jeu         |

### Backend

| Document                                            | Description                                 |
| --------------------------------------------------- | ------------------------------------------- |
| [01 - Structure Django](./backend/01-structure.md)  | Organisation des apps, modeles, conventions |
| [02 - API REST](./backend/02-api.md)                | Endpoints, authentification, serialisation  |
| [03 - WebSocket Consumer](./backend/03-consumer.md) | GameConsumer, messages, logique temps reel  |
| [04 - Celery Tasks](./backend/04-tasks.md)          | Taches async, configuration, monitoring     |

### Frontend

| Document                                            | Description                                       |
| --------------------------------------------------- | ------------------------------------------------- |
| [01 - Structure React](./frontend/01-structure.md)  | Organisation des composants, routing, conventions |
| [02 - State Management](./frontend/02-state.md)     | Zustand, TanStack Query, synchronisation WS       |
| [03 - WebSocket Client](./frontend/03-websocket.md) | Connexion, messages, gestion des etats            |

### Jeu

| Document                                    | Description                                            |
| ------------------------------------------- | ------------------------------------------------------ |
| [01 - Modes de jeu](./game/01-modes.md)     | Classique, Rapide, Generation, Paroles, Karaoke, Mollo |
| [02 - Systeme de bonus](./game/02-bonus.md) | Boutique, bonus, effets en jeu                         |
| [03 - Flux de jeu](./game/03-flux.md)       | Cycle de vie d'une partie, etats, transitions          |

### Deploiement

| Document                                               | Description                                      |
| ------------------------------------------------------ | ------------------------------------------------ |
| [01 - Developpement](./deployment/01-developpement.md) | Setup local, Docker Compose dev, variables d'env |
| [02 - Production](./deployment/02-production.md)       | Docker Compose prod, SSL, variables, securite    |
| [03 - Monitoring](./deployment/03-monitoring.md)       | ELK, Prometheus, Grafana, Jaeger                 |

---

## Guide de navigation rapide

### Je veux demarrer le projet en local

Consulter le [README.md](./README.md) et suivre la section **Installation rapide**.

Commande principale :
```bash
make deploy-dev
```

### Je veux comprendre comment fonctionne le quiz en temps reel

Lire dans l'ordre :
1. [WebSockets - Explication de base](./architecture/06-websockets.md)
2. [Redis - Channel Layer](./architecture/04-redis.md)
3. [Flux de jeu](./game/03-flux.md)

### Je veux ajouter une nouvelle fonctionnalite backend

Lire dans l'ordre :
1. [Structure Django](./backend/01-structure.md)
2. [API REST](./backend/02-api.md)
3. [Conventions de code](./README.md#conventions)

### Je veux comprendre pourquoi on utilise telle technologie

Consulter les pages d'architecture :
- **Pourquoi Redis ?** — [04 - Redis](./architecture/04-redis.md)
- **Pourquoi Celery ?** — [05 - Celery](./architecture/05-celery.md)
- **Pourquoi WebSocket ?** — [06 - WebSockets](./architecture/06-websockets.md)
- **Pourquoi Nginx ?** — [03 - Nginx](./architecture/03-nginx.md)

### Je veux deployer en production

Consulter [02 - Production](./deployment/02-production.md).

---

## Acces locaux (environnement de developpement)

| Service             | URL                                          |
| ------------------- | -------------------------------------------- |
| Frontend React      | http://localhost:3000                        |
| Backend API         | http://localhost:8000                        |
| Django Admin        | http://localhost:8000/admin                  |
| Swagger UI          | http://localhost:8000/api/schema/swagger-ui/ |
| ReDoc               | http://localhost:8000/api/schema/redoc/      |
| Kibana (logs)       | http://localhost:5601                        |
| Grafana (metriques) | http://localhost:3001                        |
| Prometheus          | http://localhost:9090                        |
| Jaeger (tracing)    | http://localhost:16686                       |

---

## Conventions resumees

| Aspect               | Convention                                      |
| -------------------- | ----------------------------------------------- |
| Langue               | Francais (code, docs, commits, branches)        |
| Format des commits   | `type(scope): description`                      |
| Nommage des branches | `feature/<desc>`, `fix/<desc>`, `hotfix/<desc>` |
| Formatage Python     | ruff (88 chars, double quotes, py3.11)          |
| Formatage TypeScript | Prettier (100 chars, single quotes)             |
| Tests backend        | pytest + `@pytest.mark.django_db`               |
| Tests frontend       | vitest + @testing-library/react                 |
