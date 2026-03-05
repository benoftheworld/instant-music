"""Métriques Prometheus applicatives pour InstantMusic.

Ce module centralise toutes les métriques custom exposées sur /metrics/.
Les métriques sont organisées en catégories :
  - HTTP : requêtes API, latence, codes de réponse
  - WebSocket : connexions, messages, joueurs connectés
  - Jeux : parties créées, rounds joués, réponses soumises
  - Services externes : appels Deezer API, YouTube API
  - Celery : tâches exécutées, durée, erreurs
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# ─── Info ───────────────────────────────────────────────────────────────────

APP_INFO = Info(
    "instantmusic",
    "Informations sur l'application InstantMusic",
)

# ─── HTTP ───────────────────────────────────────────────────────────────────

HTTP_REQUESTS_TOTAL = Counter(
    "instantmusic_http_requests_total",
    "Nombre total de requêtes HTTP",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "instantmusic_http_request_duration_seconds",
    "Durée des requêtes HTTP en secondes",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "instantmusic_http_requests_in_progress",
    "Nombre de requêtes HTTP en cours de traitement",
    ["method"],
    multiprocess_mode="livesum",
)

# ─── WebSocket ──────────────────────────────────────────────────────────────

WS_CONNECTIONS_TOTAL = Counter(
    "instantmusic_ws_connections_total",
    "Nombre total de connexions WebSocket",
    ["action"],  # connect, disconnect
)

WS_CONNECTIONS_ACTIVE = Gauge(
    "instantmusic_ws_connections_active",
    "Nombre de connexions WebSocket actives",
    multiprocess_mode="livesum",
)

WS_MESSAGES_TOTAL = Counter(
    "instantmusic_ws_messages_total",
    "Nombre total de messages WebSocket",
    ["direction", "message_type"],  # direction: inbound/outbound
)

# ─── Jeux ───────────────────────────────────────────────────────────────────

GAMES_CREATED_TOTAL = Counter(
    "instantmusic_games_created_total",
    "Nombre total de parties créées",
    ["mode"],
)

GAMES_ACTIVE = Gauge(
    "instantmusic_games_active",
    "Nombre de parties actuellement en cours",
    multiprocess_mode="livesum",
)

GAMES_FINISHED_TOTAL = Counter(
    "instantmusic_games_finished_total",
    "Nombre total de parties terminées",
    ["mode"],
)

PLAYERS_IN_GAMES = Gauge(
    "instantmusic_players_in_games",
    "Nombre total de joueurs dans des parties actives",
    multiprocess_mode="livesum",
)

ANSWERS_TOTAL = Counter(
    "instantmusic_answers_total",
    "Nombre total de réponses soumises",
    ["is_correct", "game_mode"],
)

ANSWER_RESPONSE_TIME = Histogram(
    "instantmusic_answer_response_time_seconds",
    "Temps de réponse des joueurs en secondes",
    ["game_mode"],
    buckets=(1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0),
)

ROUND_DURATION_SECONDS = Histogram(
    "instantmusic_round_duration_seconds",
    "Durée effective des rounds en secondes",
    ["question_type"],
    buckets=(5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 120.0, 300.0),
)

SCORES_EARNED = Histogram(
    "instantmusic_scores_earned",
    "Distribution des points gagnés par réponse",
    ["game_mode"],
    buckets=(0, 5, 10, 25, 50, 75, 100, 150, 200),
)

# ─── Services externes ─────────────────────────────────────────────────────

EXTERNAL_API_REQUESTS_TOTAL = Counter(
    "instantmusic_external_api_requests_total",
    "Nombre total d'appels aux APIs externes",
    ["service", "endpoint"],  # service: deezer, youtube, lrclib
)

EXTERNAL_API_ERRORS_TOTAL = Counter(
    "instantmusic_external_api_errors_total",
    "Nombre total d'erreurs d'appels aux APIs externes",
    ["service", "error_type"],
)

EXTERNAL_API_DURATION_SECONDS = Histogram(
    "instantmusic_external_api_duration_seconds",
    "Durée des appels aux APIs externes en secondes",
    ["service"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ─── Celery ─────────────────────────────────────────────────────────────────

CELERY_TASKS_TOTAL = Counter(
    "instantmusic_celery_tasks_total",
    "Nombre total de tâches Celery exécutées",
    ["task_name", "status"],  # status: success, failure, retry
)

CELERY_TASK_DURATION_SECONDS = Histogram(
    "instantmusic_celery_task_duration_seconds",
    "Durée d'exécution des tâches Celery en secondes",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
)

# ─── Cache ──────────────────────────────────────────────────────────────────

CACHE_OPERATIONS_TOTAL = Counter(
    "instantmusic_cache_operations_total",
    "Nombre total d'opérations de cache",
    ["operation", "result"],  # operation: get/set, result: hit/miss
)

# ─── Base de données ────────────────────────────────────────────────────────

DB_QUERY_DURATION_SECONDS = Histogram(
    "instantmusic_db_query_duration_seconds",
    "Durée des requêtes SQL en secondes",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
