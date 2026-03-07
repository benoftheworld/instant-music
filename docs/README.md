# Documentation InstantMusic

Documentation fonctionnelle et technique du projet InstantMusic — quiz musical multijoueur temps réel.

## Sommaire

### Architecture

| Document                                                 | Description                                                                                 |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [Plan d'optimisation](architecture/plan-optimisation.md) | Plan d'amélioration de l'architecture pour un projet professionnel, maintenable et évolutif |

### Documentation technique

| Document                                                           | Description                                                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| [WebSocket](technique/websocket.md)                                | Fonctionnement des WebSocket : Django Channels, consumer, protocole, messages, reconnexion |
| [Celery & Redis](technique/celery-redis.md)                        | Tâches asynchrones Celery, broker Redis, cache, channel layer                              |
| [Communication Frontend / Backend](technique/communication-api.md) | API REST, authentification JWT, intercepteurs Axios, stores Zustand, TanStack Query        |
| [Déroulement d'une partie](technique/deroulement-partie.md)        | Cycle de vie complet d'une partie : création, lobby, rounds, scoring, résultats            |

### Monitoring

| Document                                           | Description                                                 |
| -------------------------------------------------- | ----------------------------------------------------------- |
| [Dashboards & Métriques](monitoring/dashboards.md) | Prometheus, Grafana, ELK, métriques applicatives et système |

## Architecture globale

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                          │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    Nginx (reverse proxy)                  │
│              TLS 1.2/1.3 · Rate limiting                 │
├──────────┬───────────┬──────────────┬───────────────────┤
│ /        │ /api/     │ /ws/         │ /admin/           │
│ Frontend │ Django    │ Django       │ Jazzmin           │
│ React    │ REST API  │ Channels WS  │ Admin             │
└──────────┴─────┬─────┴──────┬───────┴───────────────────┘
                 │            │
      ┌──────────▼────────────▼──────────┐
      │      Django (Gunicorn/Uvicorn)    │
      │         ASGI Application          │
      └──┬──────────┬──────────┬─────────┘
         │          │          │
    ┌────▼───┐ ┌───▼────┐ ┌──▼──────────┐
    │PostgreSQL│ │ Redis  │ │   Celery     │
    │   15    │ │   7    │ │ Worker+Beat  │
    └────────┘ └────────┘ └─────────────┘
```

## Stack technique

| Composant        | Technologie                | Version            |
| ---------------- | -------------------------- | ------------------ |
| Backend          | Django + DRF + Channels    | 5.1                |
| Frontend         | React + TypeScript + Vite  | 18                 |
| State management | Zustand                    | 5.x                |
| Data fetching    | TanStack Query             | 5.x                |
| Base de données  | PostgreSQL                 | 15                 |
| Cache / Broker   | Redis                      | 7                  |
| Tâches async     | Celery + Beat              | 5.3                |
| Reverse proxy    | Nginx                      | Alpine             |
| Monitoring       | Prometheus + Grafana + ELK | 2.51 / 10.4 / 8.13 |
| CI/CD            | GitHub Actions             | -                  |
| Conteneurisation | Docker Compose             | v2                 |
