# Architecture d'InstantMusic

## Vue d'ensemble

InstantMusic est une application full-stack conteneurisée. Ce document décrit
l'architecture des composants, leurs interactions et les flux de données principaux.

---

## Composants Docker

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker network: app-network                                    │
│                                                                 │
│  ┌──────────┐    ┌──────────────────────────────────────────┐  │
│  │  Nginx   │    │  Backend (Gunicorn + uvicorn workers)    │  │
│  │ :80/:443 │───►│  Django 5.1 + Channels + Celery         │  │
│  │          │    │  :8000                                   │  │
│  └──────────┘    └──────────────┬───────────────────────────┘  │
│        │                        │                               │
│  ┌─────┴──────┐     ┌───────────┼──────────┐                   │
│  │  Frontend  │     ▼           ▼          ▼                   │
│  │  nginx:80  │  ┌──────┐  ┌───────┐  ┌──────────────┐        │
│  │  (SPA)     │  │  DB  │  │ Redis │  │ Celery Beat  │        │
│  └────────────┘  │ :5432│  │ :6379 │  │ (scheduler)  │        │
│                  └──────┘  └───────┘  └──────────────┘        │
│                                │                               │
│                         ┌──────┴──────┐                        │
│                         │   Celery    │                        │
│                         │   Worker    │                        │
│                         └─────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Applications Django

| App              | Responsabilité                                         |
|------------------|--------------------------------------------------------|
| `users`          | Modèle utilisateur personnalisé (`AUTH_USER_MODEL`)    |
| `authentication` | JWT, Google OAuth 2.0, endpoints de connexion          |
| `games`          | Logique de jeu, WebSocket consumer, services           |
| `playlists`      | Intégration API Deezer, gestion des playlists          |
| `achievements`   | Système de succès, attribution rétroactive             |
| `stats`          | Statistiques joueurs, classements                      |
| `administration` | Mode maintenance (middleware), outils admin            |
| `core`           | Health check endpoint                                   |

---

## Flux WebSocket (partie quiz)

```
Client (navigateur)
    │
    │  WebSocket upgrade: /ws/game/<room_code>/
    ▼
Nginx ─── proxy_pass + HTTP upgrade ───► Daphne (ASGI)
                                              │
                                         Django Channels Router
                                              │
                                         GameConsumer
                                              │
                                    ┌─────── Redis ────────┐
                                    │  Channel Layer        │
                                    │  (group: game_<code>) │
                                    └──────────────────────┘
                                              │
                            Broadcast à tous les consumers du groupe
```

### Messages WebSocket

| Direction       | Type                | Description                          |
|----------------|---------------------|--------------------------------------|
| Client → Server | `player_join`       | Rejoindre une salle                  |
| Client → Server | `start_game`        | Lancer la partie (hôte uniquement)   |
| Client → Server | `player_answer`     | Soumettre une réponse                |
| Server → Client | `start_round`       | Début d'un round (extrait musical)   |
| Server → Client | `end_round`         | Fin d'un round + résultats           |
| Server → Client | `next_round`        | Passage au round suivant             |
| Server → Client | `finish_game`       | Fin de partie + classement final     |

---

## Système de scoring

La formule de score pour une bonne réponse est :

```
score = 1000 + int((1 - response_time / max_time) * 500)
```

- Réponse correcte en début de timer → ~1500 points
- Réponse correcte en fin de timer → ~1000 points
- Mauvaise réponse → 0 point

---

## Tâches asynchrones (Celery)

| Tâche                         | Planification        | Description                    |
|-------------------------------|---------------------|--------------------------------|
| `award_retroactive_achievements` | Manuel (deploy)  | Attribution initiale des succès |
| `recalculate_user_stats`      | Manuel (deploy)      | Recalcul des stats joueurs     |
| Tâches Celery Beat             | Via `DatabaseScheduler` | Tâches planifiées via DB    |

---

## Services externes

| Service       | Usage                           | Authentification |
|---------------|---------------------------------|-----------------|
| **Deezer**    | Extraits musicaux 30 secondes   | Aucune (API publique) |
| **Google OAuth** | Connexion sociale            | Client ID + Secret (optionnel) |
| **Gmail SMTP** | Emails transactionnels (prod)  | App password Gmail |

---

## Configuration des environnements

| Variable               | Dev                      | Production              |
|------------------------|--------------------------|-------------------------|
| `DEBUG`                | `True`                   | `False`                 |
| Serveur ASGI           | Uvicorn `--reload`       | Gunicorn + uvicorn workers (×4) |
| Base de données        | Container PostgreSQL     | Container PostgreSQL (volume persistant) |
| Email                  | Console backend          | SMTP Gmail              |
| Fichiers statiques     | Servis par Django        | Nginx → `/app/staticfiles/` |
| Frontend               | Vite dev server `:3000`  | Build statique → Nginx  |

---

## Stack de monitoring (optionnelle)

Activée via `docker-compose.monitoring.yml` :

```
Prometheus   :9090  — Collecte des métriques (backend /metrics, node-exporter)
Grafana      :3001  — Dashboards (admin/admin par défaut)
Elasticsearch :9200 — Stockage des logs
Logstash     :5044  — Ingestion et parsing des logs
Kibana       :5601  — Visualisation des logs
```

Lancer avec :

```bash
make monitoring-up
```
