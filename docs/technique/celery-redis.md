# Celery & Redis — Documentation technique

## Vue d'ensemble

InstantMusic utilise **Redis 7** comme composant central pour trois rôles distincts, et **Celery 5.3** pour l'exécution de tâches asynchrones.

```
┌─────────────────────────────────────────────────────┐
│                    Redis 7 (Alpine)                   │
├─────────────────┬─────────────────┬─────────────────┤
│  Channel Layer  │  Cache Django   │  Broker Celery   │
│  (Django        │  (Framework     │  (File d'attente │
│   Channels)     │   Cache)        │   de tâches)     │
└────────┬────────┴────────┬────────┴────────┬────────┘
         │                 │                 │
    WebSocket         Réponses API      Celery Worker
    temps réel        rapides           + Beat
```

## Redis : les trois rôles

### 1. Channel Layer (Django Channels)

Le channel layer permet au WebSocket consumer de diffuser des messages à tous les clients connectés à une même salle de jeu.

**Configuration** (`backend/config/settings/base.py`) :

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env("REDIS_HOST", default="redis"), 6379)],
        },
    },
}
```

**Fonctionnement** :

- Chaque salle de jeu utilise un **group** Redis nommé `game_{room_code}`
- Quand un joueur se connecte, son channel est ajouté au group :
  ```python
  await self.channel_layer.group_add(self.room_group_name, self.channel_name)
  ```
- Pour diffuser un message à tous les joueurs d'une salle :
  ```python
  await self.channel_layer.group_send(
      self.room_group_name,
      {"type": "broadcast_round_start", "round_data": round_data}
  )
  ```
- Redis gère le pub/sub sous-jacent entre les workers ASGI

**Pourquoi Redis et pas In-Memory ?**
En production avec plusieurs workers Gunicorn, le channel layer en mémoire ne fonctionne pas car chaque worker a son propre espace mémoire. Redis assure la communication inter-processus.

### 2. Cache Django

Le cache est utilisé pour stocker des résultats temporaires et éviter des requêtes répétitives.

**Configuration** :

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{env('REDIS_HOST', default='redis')}:6379/1",
    }
}
```

**Utilisations principales** :

| Composant              | Clé                     | TTL     | Description                   |
| ---------------------- | ----------------------- | ------- | ----------------------------- |
| Deezer Service         | `deezer_search_{query}` | 30 min  | Résultats de recherche Deezer |
| Deezer Service         | `deezer_playlist_{id}`  | 1 heure | Détails d'une playlist        |
| Maintenance Middleware | `site_maintenance_mode` | 5 sec   | État du mode maintenance      |

**Bonnes pratiques** :
- Base Redis `1` pour le cache (séparé du broker sur `0`)
- TTL courts pour les données volatiles
- Invalidation explicite quand nécessaire

### 3. Broker Celery

Redis sert de file d'attente (broker) pour les tâches Celery et de backend pour stocker les résultats.

**Configuration** :

```python
CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='redis')}:6379/0"
CELERY_RESULT_BACKEND = f"redis://{env('REDIS_HOST', default='redis')}:6379/0"
```

---

## Celery : tâches asynchrones

### Configuration

**Fichier** : `backend/config/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('instantmusic')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**Paramètres** (`settings/base.py`) :

```python
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Paris"
```

### Services Docker

```yaml
# Worker — exécute les tâches
celery:
  command: celery -A config worker -l info
  depends_on:
    - redis
    - db

# Beat — planificateur de tâches périodiques
celery-beat:
  command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  depends_on:
    - redis
    - db
```

### Celery Beat (tâches planifiées)

Celery Beat utilise `django-celery-beat` avec un `DatabaseScheduler`, ce qui permet de configurer les tâches périodiques directement depuis l'admin Django.

**Cas d'usage** :
- Nettoyage des parties abandonnées (status=waiting depuis > 24h)
- Agrégation des statistiques joueurs
- Vérification et attribution des succès

### Flux d'exécution d'une tâche

```
┌──────────┐     ┌───────────┐     ┌──────────────┐     ┌──────────┐
│  Django   │     │   Redis   │     │   Celery     │     │  Django  │
│  View     │     │  (Broker) │     │   Worker     │     │  ORM     │
└─────┬────┘     └─────┬─────┘     └──────┬───────┘     └────┬─────┘
      │                │                   │                   │
      │ task.delay()   │                   │                   │
      ├───────────────►│                   │                   │
      │                │  Récupère tâche   │                   │
      │                ├──────────────────►│                   │
      │                │                   │  Exécute la       │
      │                │                   │  logique métier   │
      │                │                   ├──────────────────►│
      │                │                   │                   │
      │                │  Stocke résultat  │◄──────────────────┤
      │                │◄──────────────────┤                   │
      │                │                   │                   │
```

### Monitoring Celery

Les métriques Prometheus suivantes sont exposées :

| Métrique                                    | Type      | Labels            | Description                |
| ------------------------------------------- | --------- | ----------------- | -------------------------- |
| `instantmusic_celery_tasks_total`           | Counter   | task_name, status | Nombre de tâches exécutées |
| `instantmusic_celery_task_duration_seconds` | Histogram | task_name         | Durée d'exécution          |

---

## Séparation des bases Redis

| Base                           | Utilisation                    | Raison                |
| ------------------------------ | ------------------------------ | --------------------- |
| `redis://redis:6379/0`         | Celery broker + result backend | Tâches asynchrones    |
| `redis://redis:6379/1`         | Cache Django                   | Résultats temporaires |
| `redis://redis:6379` (default) | Channel Layer                  | WebSocket pub/sub     |

Cette séparation évite les conflits de clés et permet de monitorer indépendamment chaque usage.

## Redis Exporter (monitoring)

Un `redis-exporter` (oliver006/redis_exporter) est déployé dans la stack monitoring pour exposer les métriques Redis vers Prometheus :

- Mémoire utilisée (`redis_memory_used_bytes`)
- Connexions actives (`redis_connected_clients`)
- Commandes par seconde (`redis_commands_processed_total`)
- Keyspace (nombre de clés par base)
- Latence des opérations

## Bonnes pratiques

1. **Pas de données persistantes critiques dans Redis** : Redis est un cache, les données de jeu sont dans PostgreSQL
2. **TTL sur toutes les clés cache** : Évite l'accumulation en mémoire
3. **Monitoring de la mémoire** : Alerter si `redis_memory_used_bytes` approche `maxmemory`
4. **Sérialisation JSON uniquement** : Celery configuré en `json` pour la lisibilité et la compatibilité
5. **Idempotence des tâches** : Les tâches Celery doivent pouvoir être rejouées sans effet de bord
