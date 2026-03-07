# Prometheus — Métriques InstantMusic

## Introduction à Prometheus

### Qu'est-ce que Prometheus ?

Prometheus est un système de **surveillance** (monitoring) open source créé par SoundCloud (oui, une entreprise musicale !). Il collecte et stocke des **métriques** — des données numériques qui décrivent l'état d'un système à un instant donné.

**Exemples de métriques** :
- "Il y a eu 1547 requêtes HTTP sur `/api/games/` depuis le démarrage"
- "La latence médiane des requêtes est de 45ms"
- "Il y a actuellement 5 parties en cours"
- "Redis utilise 234 MB de mémoire"

### Concept de scraping (mode "pull")

Contrairement à d'autres systèmes de monitoring où les applications *envoient* leurs métriques (mode "push"), Prometheus les *tire* (mode "pull") :

```
Mode PUSH (ex: StatsD)          Mode PULL (Prometheus)
────────────────────────        ──────────────────────
Application ──metrics──► Serveur    Serveur ──GET /metrics──► Application
(initiative : l'application)        (initiative : le serveur)
```

L'avantage du pull : le serveur Prometheus contrôle la fréquence, et si une application tombe, on le détecte immédiatement (la cible ne répond plus).

### Format des métriques (OpenMetrics)

Chaque application expose ses métriques sur un endpoint HTTP au format texte standardisé :

```
# HELP instantmusic_games_active Nombre de parties en cours
# TYPE instantmusic_games_active gauge
instantmusic_games_active 5.0

# HELP instantmusic_http_requests_total Nombre total de requêtes HTTP
# TYPE instantmusic_http_requests_total counter
instantmusic_http_requests_total{method="GET",endpoint="/api/games/",status_code="200"} 1547.0
instantmusic_http_requests_total{method="POST",endpoint="/api/games/",status_code="201"} 23.0
instantmusic_http_requests_total{method="GET",endpoint="/api/auth/me/",status_code="401"} 5.0
```

### Types de métriques

| Type          | Description                                   | Exemple                       |
| ------------- | --------------------------------------------- | ----------------------------- |
| **Counter**   | Compteur qui monte toujours                   | Nombre total de requêtes      |
| **Gauge**     | Valeur variable (monte et descend)            | Parties actives, RAM utilisée |
| **Histogram** | Distribution de valeurs + percentiles         | Durée des requêtes            |
| **Summary**   | Similaire histogram, percentiles pre-calculés | Latence                       |

### PromQL — Langage de requête

Prometheus dispose de son propre langage de requête appelé **PromQL** (Prometheus Query Language). Quelques exemples :

```promql
# Nombre de requêtes par seconde (rate sur 5 minutes)
rate(instantmusic_http_requests_total[5m])

# Latence p99 (99e percentile) des requêtes HTTP
histogram_quantile(0.99, rate(instantmusic_http_request_duration_seconds_bucket[5m]))

# Taux d'erreur HTTP 5xx
sum(rate(instantmusic_http_requests_total{status_code=~"5.."}[5m]))
  /
sum(rate(instantmusic_http_requests_total[5m]))

# Parties actuellement actives
instantmusic_games_active

# Parties créées au total par mode de jeu
sum by (mode) (instantmusic_games_created_total)
```

---

## Configuration Prometheus

### Fichier `prometheus.yml`

```yaml
# _devops/monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s      # Fréquence de collecte des métriques
  evaluation_interval: 15s  # Fréquence d'évaluation des règles d'alerte

alerting:
  alertmanagers:
    - static_configs:
        - targets: []  # Alertmanager si configuré

# Règles d'alerte (fichiers séparés)
rule_files:
  - "alert_rules.yml"

# Cibles à surveiller
scrape_configs:

  # Backend Django
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/metrics/'

  # Métriques système (CPU, RAM, disque)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Métriques Redis
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Prometheus lui-même (auto-monitoring)
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

---

## Métriques custom (`apps/core/prometheus_metrics.py`)

InstantMusic définit **19 métriques custom** qui couvrent tous les aspects de l'application.

### 1. Métriques HTTP

#### `instantmusic_http_requests_total`
**Type** : Counter
**Labels** : `method`, `endpoint`, `status_code`
**Description** : Compte le nombre total de requêtes HTTP traitées.

```python
from prometheus_client import Counter

http_requests_total = Counter(
    'instantmusic_http_requests_total',
    'Nombre de requêtes HTTP',
    ['method', 'endpoint', 'status_code']
)

# Utilisation dans le middleware
http_requests_total.labels(
    method='GET',
    endpoint='/api/games/',
    status_code='200'
).inc()
```

**Requête PromQL utile** :
```promql
# Top 10 des endpoints les plus appelés
topk(10, sum by (endpoint) (rate(instantmusic_http_requests_total[5m])))
```

#### `instantmusic_http_request_duration_seconds`
**Type** : Histogram
**Labels** : `method`, `endpoint`
**Description** : Mesure la durée de chaque requête HTTP.

```python
http_request_duration = Histogram(
    'instantmusic_http_request_duration_seconds',
    'Durée des requêtes HTTP',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Utilisation
with http_request_duration.labels(method='POST', endpoint='/api/games/').time():
    # Code de la requête
    response = view_function(request)
```

**Requête PromQL utile** :
```promql
# Latence p95 sur les 5 dernières minutes
histogram_quantile(
  0.95,
  rate(instantmusic_http_request_duration_seconds_bucket[5m])
)
```

#### `instantmusic_http_requests_in_progress`
**Type** : Gauge
**Labels** : `method`
**Description** : Nombre de requêtes HTTP actuellement en cours de traitement.

```python
http_in_progress = Gauge(
    'instantmusic_http_requests_in_progress',
    'Requêtes HTTP en cours',
    ['method']
)
```

---

### 2. Métriques WebSocket

#### `instantmusic_ws_connections_total`
**Type** : Counter
**Labels** : `action` (`connect` ou `disconnect`)
**Description** : Compte les connexions et déconnexions WebSocket.

#### `instantmusic_ws_connections_active`
**Type** : Gauge
**Labels** : aucun
**Description** : Nombre de connexions WebSocket ouvertes actuellement.

```python
ws_active = Gauge(
    'instantmusic_ws_connections_active',
    'Connexions WebSocket actives'
)

# Dans GameConsumer
async def websocket_connect(self, event):
    ws_active.inc()

async def websocket_disconnect(self, event):
    ws_active.dec()
```

#### `instantmusic_ws_messages_total`
**Type** : Counter
**Labels** : `direction` (`sent`/`received`), `message_type`
**Description** : Compte les messages WebSocket par type.

---

### 3. Métriques de jeu

#### `instantmusic_games_created_total`
**Type** : Counter
**Labels** : `mode` (classique, rapide, etc.)
**Description** : Nombre de parties créées par mode de jeu.

#### `instantmusic_games_active`
**Type** : Gauge
**Labels** : aucun
**Description** : Nombre de parties actuellement en cours.

#### `instantmusic_games_finished_total`
**Type** : Counter
**Labels** : `mode`
**Description** : Nombre de parties terminées par mode de jeu.

#### `instantmusic_answers_total`
**Type** : Counter
**Labels** : `is_correct` (`true`/`false`), `game_mode`
**Description** : Nombre de réponses soumises et leur correction.

**Requête PromQL utile** :
```promql
# Taux de bonnes réponses global
sum(rate(instantmusic_answers_total{is_correct="true"}[1h]))
/
sum(rate(instantmusic_answers_total[1h]))
```

#### `instantmusic_answer_response_time_seconds`
**Type** : Histogram
**Labels** : `game_mode`
**Description** : Distribution des temps de réponse des joueurs.

**Requête PromQL utile** :
```promql
# Temps de réponse médian par mode
histogram_quantile(
  0.50,
  sum by (game_mode, le) (
    rate(instantmusic_answer_response_time_seconds_bucket[1h])
  )
)
```

#### `instantmusic_scores_earned`
**Type** : Histogram
**Labels** : `game_mode`
**Description** : Distribution des scores gagnés par round.

---

### 4. Métriques API externes

#### `instantmusic_external_api_requests_total`
**Type** : Counter
**Labels** : `service` (deezer, lrclib, lyrics_ovh), `endpoint`
**Description** : Nombre d'appels vers les APIs externes.

#### `instantmusic_external_api_errors_total`
**Type** : Counter
**Labels** : `service`, `error_type`
**Description** : Erreurs des APIs externes (timeout, 4xx, 5xx).

#### `instantmusic_external_api_duration_seconds`
**Type** : Histogram
**Labels** : `service`
**Description** : Durée des appels vers les APIs externes.

**Requête PromQL utile** :
```promql
# Taux d'erreur Deezer
sum(rate(instantmusic_external_api_errors_total{service="deezer"}[5m]))
/
sum(rate(instantmusic_external_api_requests_total{service="deezer"}[5m]))
```

---

### 5. Métriques Celery

#### `instantmusic_celery_tasks_total`
**Type** : Counter
**Labels** : `task_name`, `status` (success, failure, retry)
**Description** : Nombre de tâches Celery par résultat.

#### `instantmusic_celery_task_duration_seconds`
**Type** : Histogram
**Labels** : `task_name`
**Description** : Durée d'exécution des tâches Celery.

```python
# Décorateur pour instrumenter une tâche Celery
@shared_task
def check_achievements_async(user_id, game_id):
    task_name = 'check_achievements'

    with celery_task_duration.labels(task_name=task_name).time():
        try:
            result = _do_check_achievements(user_id, game_id)
            celery_tasks_total.labels(
                task_name=task_name, status='success'
            ).inc()
            return result
        except Exception as e:
            celery_tasks_total.labels(
                task_name=task_name, status='failure'
            ).inc()
            raise
```

---

### 6. Métriques infrastructure

#### `instantmusic_cache_operations_total`
**Type** : Counter
**Labels** : `operation` (get, set, delete), `result` (hit, miss)
**Description** : Opérations Redis cache (pour mesurer le taux de hit/miss).

**Requête PromQL utile** :
```promql
# Taux de hit du cache Redis
sum(rate(instantmusic_cache_operations_total{operation="get",result="hit"}[5m]))
/
sum(rate(instantmusic_cache_operations_total{operation="get"}[5m]))
```

#### `instantmusic_db_query_duration_seconds`
**Type** : Histogram
**Labels** : aucun
**Description** : Durée des requêtes vers PostgreSQL.

---

## Tableau récapitulatif complet

| Métrique                                     | Type      | Labels                        | Description           |
| -------------------------------------------- | --------- | ----------------------------- | --------------------- |
| `instantmusic_http_requests_total`           | Counter   | method, endpoint, status_code | Requêtes HTTP         |
| `instantmusic_http_request_duration_seconds` | Histogram | method, endpoint              | Durée requêtes HTTP   |
| `instantmusic_http_requests_in_progress`     | Gauge     | method                        | Requêtes en cours     |
| `instantmusic_ws_connections_total`          | Counter   | action                        | Connexions WebSocket  |
| `instantmusic_ws_connections_active`         | Gauge     | —                             | WS actives            |
| `instantmusic_ws_messages_total`             | Counter   | direction, message_type       | Messages WS           |
| `instantmusic_games_created_total`           | Counter   | mode                          | Parties créées        |
| `instantmusic_games_active`                  | Gauge     | —                             | Parties en cours      |
| `instantmusic_games_finished_total`          | Counter   | mode                          | Parties terminées     |
| `instantmusic_answers_total`                 | Counter   | is_correct, game_mode         | Réponses soumises     |
| `instantmusic_answer_response_time_seconds`  | Histogram | game_mode                     | Temps de réponse      |
| `instantmusic_scores_earned`                 | Histogram | game_mode                     | Points gagnés         |
| `instantmusic_external_api_requests_total`   | Counter   | service, endpoint             | Appels API externes   |
| `instantmusic_external_api_errors_total`     | Counter   | service, error_type           | Erreurs API externes  |
| `instantmusic_external_api_duration_seconds` | Histogram | service                       | Durée appels externes |
| `instantmusic_celery_tasks_total`            | Counter   | task_name, status             | Tâches Celery         |
| `instantmusic_celery_task_duration_seconds`  | Histogram | task_name                     | Durée tâches Celery   |
| `instantmusic_cache_operations_total`        | Counter   | operation, result             | Opérations cache      |
| `instantmusic_db_query_duration_seconds`     | Histogram | —                             | Durée requêtes DB     |

---

## Accès à Prometheus

### Interface web

Prometheus expose une UI web minimaliste sur `http://localhost:9090` :

```
┌──────────────────────────────────────────────────────────────┐
│  Prometheus                                                  │
│                                                              │
│  [Expression input...............................] [Execute]  │
│                                                              │
│  Targets :  Status > Targets                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  backend (1/1 up)     http://backend:8000/api/metrics/│   │
│  │  node-exporter (1/1)  http://node-exporter:9100/...  │   │
│  │  redis-exporter (1/1) http://redis-exporter:9121/... │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Vérifier que les métriques sont bien collectées

```bash
# Vérifier que le backend expose ses métriques
curl http://localhost:8000/api/metrics/

# Vérifier que Prometheus scrape bien les targets
# → UI : http://localhost:9090/targets
# → Tous les targets doivent être en "UP"
```

### Exemples de requêtes PromQL utiles pour InstantMusic

```promql
# Requêtes par seconde globales
sum(rate(instantmusic_http_requests_total[1m]))

# Erreurs par seconde
sum(rate(instantmusic_http_requests_total{status_code=~"5.."}[1m]))

# Latence p50, p95, p99
histogram_quantile(0.50, rate(instantmusic_http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(instantmusic_http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(instantmusic_http_request_duration_seconds_bucket[5m]))

# Parties actives en ce moment
instantmusic_games_active

# Taux de bonnes réponses
sum(rate(instantmusic_answers_total{is_correct="true"}[1h]))
/ sum(rate(instantmusic_answers_total[1h])) * 100

# Score moyen par mode de jeu
histogram_quantile(0.50,
  sum by (game_mode, le) (instantmusic_scores_earned_bucket)
)
```
