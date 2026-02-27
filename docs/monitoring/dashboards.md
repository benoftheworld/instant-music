# Dashboards & Métriques — Documentation monitoring

## Architecture de monitoring

```
┌──────────────────────────────────────────────────────────────┐
│                    Stack de monitoring                         │
│                                                               │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ Prometheus   │  │  Elasticsearch   │  │   Grafana        │ │
│  │ (scrape 15s) │  │  (indexation)    │  │   (dashboards)   │ │
│  └──────┬──────┘  └────────▲────────┘  └────────┬─────────┘ │
│         │                  │                     │            │
│         │ /metrics         │ TCP:5000            │ PromQL     │
│         ▼                  │                     ▼            │
│  ┌──────────────┐  ┌──────┴──────┐  ┌──────────────────┐    │
│  │ Backend      │  │ Logstash    │  │ Kibana           │    │
│  │ Node Exporter│  │ (pipeline)  │  │ (log search)     │    │
│  │ Redis Export │  └─────────────┘  └──────────────────┘    │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Prometheus

### Sources de métriques (scrape targets)

| Job              | Target                 | Métriques                            |
| ---------------- | ---------------------- | ------------------------------------ |
| `backend`        | `backend:8000/metrics` | Métriques applicatives Django custom |
| `node-exporter`  | `node-exporter:9100`   | CPU, mémoire, disque, réseau         |
| `redis-exporter` | `redis-exporter:9121`  | Métriques Redis                      |
| `prometheus`     | `localhost:9090`       | Métriques internes Prometheus        |

### Métriques applicatives custom

Toutes les métriques sont définies dans `backend/apps/core/prometheus_metrics.py` et préfixées `instantmusic_`.

#### HTTP

| Métrique                                     | Type      | Labels                        | Description            |
| -------------------------------------------- | --------- | ----------------------------- | ---------------------- |
| `instantmusic_http_requests_total`           | Counter   | method, endpoint, status_code | Total de requêtes HTTP |
| `instantmusic_http_request_duration_seconds` | Histogram | method, endpoint              | Latence des requêtes   |
| `instantmusic_http_requests_in_progress`     | Gauge     | method                        | Requêtes en cours      |

Le middleware `PrometheusMetricsMiddleware` (`backend/apps/core/middleware.py`) intercepte chaque requête pour collecter ces métriques. Les URLs sont normalisées (ex: `/api/games/ABC123/` → `/api/games/{room_code}/`) pour éviter l'explosion de cardinalité.

#### WebSocket

| Métrique                             | Type    | Labels                      | Description           |
| ------------------------------------ | ------- | --------------------------- | --------------------- |
| `instantmusic_ws_connections_total`  | Counter | action (connect/disconnect) | Total connexions WS   |
| `instantmusic_ws_connections_active` | Gauge   | —                           | Connexions WS actives |
| `instantmusic_ws_messages_total`     | Counter | direction, message_type     | Messages WS échangés  |

Instrumentées directement dans `GameConsumer` (consumers.py).

#### Jeux

| Métrique                                    | Type      | Labels                | Description                      |
| ------------------------------------------- | --------- | --------------------- | -------------------------------- |
| `instantmusic_games_created_total`          | Counter   | mode                  | Parties lancées                  |
| `instantmusic_games_active`                 | Gauge     | —                     | Parties en cours                 |
| `instantmusic_games_finished_total`         | Counter   | mode                  | Parties terminées                |
| `instantmusic_players_in_games`             | Gauge     | —                     | Joueurs dans des parties actives |
| `instantmusic_answers_total`                | Counter   | is_correct, game_mode | Réponses soumises                |
| `instantmusic_answer_response_time_seconds` | Histogram | game_mode             | Temps de réponse                 |
| `instantmusic_scores_earned`                | Histogram | game_mode             | Distribution des scores          |

Instrumentées dans `GameService` (services.py).

#### APIs externes

| Métrique                                     | Type      | Labels              | Description                  |
| -------------------------------------------- | --------- | ------------------- | ---------------------------- |
| `instantmusic_external_api_requests_total`   | Counter   | service, endpoint   | Appels Deezer/YouTube/LRCLib |
| `instantmusic_external_api_errors_total`     | Counter   | service, error_type | Erreurs d'appels             |
| `instantmusic_external_api_duration_seconds` | Histogram | service             | Latence des appels           |

#### Celery

| Métrique                                    | Type      | Labels            | Description      |
| ------------------------------------------- | --------- | ----------------- | ---------------- |
| `instantmusic_celery_tasks_total`           | Counter   | task_name, status | Tâches exécutées |
| `instantmusic_celery_task_duration_seconds` | Histogram | task_name         | Durée des tâches |

#### Cache

| Métrique                              | Type    | Labels            | Description                 |
| ------------------------------------- | ------- | ----------------- | --------------------------- |
| `instantmusic_cache_operations_total` | Counter | operation, result | Opérations cache (hit/miss) |

---

## Dashboards Grafana

### Accès

| Environnement | URL                          | Authentification            |
| ------------- | ---------------------------- | --------------------------- |
| Développement | `http://localhost:3001`      | admin / admin               |
| Production    | `https://domain.fr/grafana/` | HTTP Basic Auth (.htpasswd) |

### Dashboard "InstantMusic - Système"

**Fichier** : `_devops/monitoring/grafana/provisioning/dashboards/system-overview.json`
**UID** : `instantmusic-system`

Métriques provenant du Node Exporter (prom/node-exporter).

| Panneau                | Type       | Description                                   |
| ---------------------- | ---------- | --------------------------------------------- |
| CPU Usage %            | Stat       | Utilisation CPU moyenne                       |
| Memory Usage %         | Stat       | Utilisation mémoire                           |
| CPU Usage Over Time    | Timeseries | CPU par mode (user, system, iowait...) empilé |
| Memory Usage Over Time | Timeseries | Total vs Utilisé vs Disponible                |
| Disk Usage %           | Gauge      | Occupation disque partition /                 |
| Disk I/O               | Timeseries | Lecture/écriture bytes/s                      |
| Network Traffic        | Timeseries | Réception/émission par interface              |
| Network Errors         | Timeseries | Erreurs et drops réseau                       |
| Load Average           | Timeseries | Charge système 1m, 5m, 15m                    |
| Open File Descriptors  | Stat       | Nombre de FD ouverts                          |
| Running Processes      | Stat       | Processus en exécution                        |

### Dashboard "InstantMusic - Application"

**Fichier** : `_devops/monitoring/grafana/provisioning/dashboards/application-overview.json`
**UID** : `instantmusic-app`

Métriques applicatives custom du backend Django.

| Section                    | Panneaux                                                                            |
| -------------------------- | ----------------------------------------------------------------------------------- |
| **Vue d'ensemble**         | Requêtes HTTP/min, Parties actives, Connexions WS, Taux d'erreur                    |
| **HTTP API**               | Requêtes par endpoint, Latence p50/p95/p99, Codes de réponse                        |
| **Jeux & Joueurs**         | Parties par mode, Parties actives, Réponses correctes/incorrectes, Temps de réponse |
| **WebSocket**              | Connexions actives, Messages par type, Connexions/Déconnexions                      |
| **APIs Externes & Celery** | Appels Deezer/YouTube, Erreurs, Tâches Celery                                       |

---

## Stack ELK (Elasticsearch + Logstash + Kibana)

### Pipeline Logstash

**Fichier** : `_devops/monitoring/logstash/pipeline/logstash.conf`

| Source         | Input       | Format                                            |
| -------------- | ----------- | ------------------------------------------------- |
| Backend Django | TCP :5000   | JSON structuré ou texte (grok)                    |
| Celery Worker  | TCP :5000   | Texte Celery `[timestamp: LEVEL/process] message` |
| Nginx          | Beats :5044 | Access log format combiné                         |

Les logs sont enrichis avec les champs `app=instantmusic` et `component` selon le service source, puis indexés dans Elasticsearch sous le pattern `instantmusic-YYYY.MM.dd`.

### Dashboard Kibana

**Fichier** : `_devops/monitoring/kibana/saved-objects.ndjson`

Objets importables dans Kibana :

| Objet            | Type          | Description                                                                             |
| ---------------- | ------------- | --------------------------------------------------------------------------------------- |
| `instantmusic-*` | Index pattern | Pattern d'index pour les logs                                                           |
| Logs applicatifs | Saved search  | Recherche avec colonnes level, service, module, message                                 |
| Erreurs          | Saved search  | Filtre `level: ERROR or level: CRITICAL`                                                |
| Vue d'ensemble   | Dashboard     | 4 panneaux : volume de logs, répartition par niveau, par service, erreurs dans le temps |

**Import** : Kibana → Stack Management → Saved Objects → Import → `saved-objects.ndjson`

### Accès Kibana

| Environnement | URL                                           |
| ------------- | --------------------------------------------- |
| Développement | `http://localhost:5601`                       |
| Production    | `https://domain.fr/kibana/` (HTTP Basic Auth) |

---

## Démarrage du monitoring

### Développement

```bash
# Démarrer la stack monitoring
make monitoring-up

# Vérifier les services
docker compose -f _devops/docker/docker-compose.yml \
               -f _devops/docker/docker-compose.monitoring.yml ps
```

### Production

```bash
# Démarrer avec auth HTTP
make monitoring-up-prod

# Créer le fichier .htpasswd
make monitoring-htpasswd
```

---

## Alerting (recommandations)

Alertes recommandées à configurer dans Grafana :

| Alerte               | Condition                      | Sévérité |
| -------------------- | ------------------------------ | -------- |
| CPU élevé            | CPU > 90% pendant 5 min        | Warning  |
| Mémoire critique     | RAM > 95% pendant 2 min        | Critical |
| Disque plein         | Disque > 90%                   | Warning  |
| Taux d'erreur HTTP   | 5xx > 5% pendant 3 min         | Critical |
| WebSocket saturé     | Connexions > 200               | Warning  |
| API Deezer en erreur | Erreurs > 10/min pendant 5 min | Warning  |
| Celery bloqué        | 0 tâches/min pendant 10 min    | Warning  |
