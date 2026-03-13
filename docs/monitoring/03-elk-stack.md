# ELK Stack — Logs InstantMusic

## Introduction à l'ELK Stack

**ELK** est l'acronyme de trois outils open source qui fonctionnent ensemble pour gérer les logs applicatifs :

- **E**lasticsearch — Stocke et indexe les logs
- **L**ogstash — Collecte, transforme et envoie les logs
- **K**ibana — Visualise et explore les logs

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FLUX ELK SIMPLIFIÉ                              │
│                                                                          │
│   Application Django                                                     │
│   (python-json-logger)                                                   │
│          │                                                               │
│          │  JSON logs                                                    │
│          ▼                                                               │
│   ┌─────────────┐     pipeline      ┌───────────────┐   stockage        │
│   │  Logstash   │ ─────────────────► │ Elasticsearch │ ──────────►  DB  │
│   │  :5044      │                    │    :9200      │                  │
│   └─────────────┘                    └───────────────┘                  │
│                                             │                            │
│                                      requêtes DSL                       │
│                                             ▼                            │
│                                      ┌───────────┐                      │
│                                      │  Kibana   │ ← navigateur         │
│                                      │  :5601    │                      │
│                                      └───────────┘                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Elasticsearch

### Qu'est-ce que c'est ?

Elasticsearch est un **moteur de recherche et d'analyse** basé sur Apache Lucene. Bien qu'il puisse stocker tout type de donnée JSON, son super-pouvoir est la **recherche full-text** : il peut chercher dans des millions de documents en millisecondes.

Pour les logs, il sert de base de données avec :
- Indexation automatique de tous les champs JSON
- Recherche par n'importe quel champ (niveau de log, message, user_id...)
- Agrégations (ex: "combien d'erreurs par heure ?")

### Concepts de base

```
Elasticsearch (analogie avec SQL)
├── Index        ≈ Table
│   └── instantmusic-logs-2026.03.07
├── Document     ≈ Ligne
│   └── { "timestamp": "...", "level": "ERROR", "message": "..." }
└── Field        ≈ Colonne
    └── level, message, logger, user_id, ...
```

### Structure d'un document de log

```json
{
  "@timestamp": "2026-03-07T10:30:15.123Z",
  "level": "INFO",
  "logger": "apps.games.consumers",
  "message": "Game started",
  "game_id": 123,
  "room_code": "AZERTY",
  "player_count": 4,
  "host_id": 1,
  "environment": "production",
  "service": "instantmusic-backend",
  "version": "1.2.0"
}
```

### Indices par date

Les logs sont organisés en indices **par jour** (stratégie ILM — Index Lifecycle Management) :

```
instantmusic-logs-2026.03.05  ← logs du 5 mars
instantmusic-logs-2026.03.06  ← logs du 6 mars
instantmusic-logs-2026.03.07  ← logs du 7 mars (aujourd'hui)
```

Cela permet de supprimer facilement les anciens logs (ex: supprimer les indices de plus de 30 jours).

---

## Logstash

### Qu'est-ce que c'est ?

Logstash est un **pipeline de traitement de données**. Il lit des logs depuis diverses sources, les transforme selon des règles, puis les envoie vers une ou plusieurs destinations.

Un pipeline Logstash comporte 3 sections :

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE LOGSTASH                            │
│                                                                 │
│   INPUT           FILTER              OUTPUT                    │
│   ─────           ──────              ──────                    │
│   Où lire      Comment transformer   Où envoyer                │
│                                                                 │
│   fichier      parser JSON           elasticsearch              │
│   TCP/UDP      ajouter champs        stdout (debug)             │
│   Beats        filtrer               fichier                    │
│   stdin        enrichir              kafka                      │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration du pipeline

```ruby
# _devops/monitoring/logstash/pipeline/instantmusic.conf

# ── INPUT : Source des logs ────────────────────────────────────────
input {
  # Lire les logs depuis un fichier
  file {
    path => "/var/log/instantmusic/*.log"
    start_position => "beginning"
    codec => "json"  # Les logs sont déjà en JSON
  }

  # Ou via TCP (port 5000) si le backend envoie directement
  tcp {
    port => 5000
    codec => json_lines
  }
}

# ── FILTER : Transformation des logs ──────────────────────────────
filter {
  # Parser le timestamp
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }

  # Ajouter des métadonnées
  mutate {
    add_field => {
      "environment" => "${APP_ENV:development}"
      "service"     => "instantmusic-backend"
    }
  }

  # Si le log est un log d'erreur HTTP, extraire le status code
  if [level] == "ERROR" and [status_code] {
    mutate {
      convert => { "status_code" => "integer" }
    }
  }

  # Supprimer les champs inutiles
  mutate {
    remove_field => ["host", "path", "@version"]
  }
}

# ── OUTPUT : Destination des logs ─────────────────────────────────
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]

    # Index avec rotation quotidienne
    index => "instantmusic-logs-%{+YYYY.MM.dd}"

    # Template de mapping (optionnel)
    template_name => "instantmusic-logs"
  }

  # Debug : afficher aussi dans stdout (à désactiver en prod)
  # stdout { codec => rubydebug }
}
```

### Configuration de Django pour envoyer des logs JSON

```python
# backend/config/settings/base.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/instantmusic/django.log',
            'formatter': 'json',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'apps.games': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps.authentication': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
        },
    },
}
```

### Utilisation dans le code Django

```python
# backend/apps/games/consumers.py
import logging

logger = logging.getLogger('apps.games')

class GameConsumer(WebsocketConsumer):

    async def start_game(self, data):
        logger.info(
            "Game started",
            extra={
                'game_id': self.game.id,
                'room_code': self.room_code,
                'player_count': await self.game.players.acount(),
                'host_id': self.user.id,
                'game_mode': self.game.game_mode,
            }
        )
        # ...

    async def handle_error(self, error):
        logger.error(
            "Game error",
            extra={
                'game_id': self.game.id,
                'error_type': type(error).__name__,
                'error_message': str(error),
            },
            exc_info=True  # Inclut le traceback complet
        )
```

---

## Kibana

### Qu'est-ce que c'est ?

Kibana est l'**interface web** d'exploration et de visualisation des données Elasticsearch. Pour les logs, c'est votre fenêtre pour comprendre ce qui se passe dans l'application.

### Accès

- URL : `http://localhost:5601` (développement)
- Pas d'authentification en développement (xpack.security désactivé)

### Première configuration — Créer un Index Pattern

Avant de pouvoir explorer les logs, il faut configurer Kibana pour savoir quel index Elasticsearch consulter :

```
1. Aller dans → Menu (hamburger) → Stack Management → Index Patterns
2. Cliquer "Create index pattern"
3. Pattern : "instantmusic-logs-*" (le * couvre tous les jours)
4. Champ de temps : "@timestamp"
5. Cliquer "Create index pattern"
```

### Interface Discover — Explorer les logs

La section **Discover** permet d'explorer les logs en temps réel.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Discover                                                                │
│                                                                          │
│  Search... [level: ERROR]            Last 15 minutes  [Refresh: 30s]    │
│                                                                          │
│  ████████████████████████████████████████████████████ (histogramme)     │
│   0:00   :05   :10   :15   (timeline des logs)                          │
│                                                                          │
│  47 hits                                                                 │
│  ──────────────────────────────────────────────────────────────────────  │
│  ▶ 10:30:15  ERROR  apps.games  Game error: TimeoutError                │
│  ▶ 10:28:42  ERROR  django.request  500 /api/games/123/                 │
│  ▶ 10:25:10  ERROR  apps.games  Answer submission failed                │
└──────────────────────────────────────────────────────────────────────────┘
```

### Exemples de recherches KQL (Kibana Query Language)

```
# Tous les logs d'erreur
level: ERROR

# Erreurs d'une partie spécifique
level: ERROR AND game_id: 123

# Erreurs des 5 dernières minutes (dans le sélecteur de temps)
level: ERROR AND @timestamp >= now-5m

# Trouver tous les démarrages de parties
message: "Game started"

# Parties avec plus de 4 joueurs
player_count >= 4

# Erreurs liées à l'authentification
logger: "apps.authentication" AND level: ERROR

# Logs d'un utilisateur spécifique
host_id: 42

# Recherche dans le message (full-text)
message: "timeout"
```

### Créer un Dashboard de logs

```
1. Aller dans Dashboard → Create dashboard
2. Cliquer "Add visualization"
3. Exemples de visualisations utiles :

   a. Nombre d'erreurs par heure (Bar chart)
      - Axe X : @timestamp (par heure)
      - Axe Y : Count
      - Filtre : level: ERROR

   b. Distribution des niveaux de log (Pie chart)
      - Segmenté par : level

   c. Top 10 des messages d'erreur (Data table)
      - Segmenté par : message
      - Count
      - Filtre : level: ERROR

   d. Ligne de temps des parties créées (Line chart)
      - Filtre : message: "Game started"
```

---

## Flux de logs applicatifs

### Types de logs émis par InstantMusic

```
LEVEL    LOGGER                     EXEMPLE
─────    ──────                     ───────
INFO     apps.games                 "Game AZERTY started by user Alice"
INFO     apps.games.consumers       "Player Bob joined game AZERTY"
INFO     apps.authentication        "User alice@email.com logged in"
WARNING  apps.playlists             "Deezer API rate limit approaching"
ERROR    apps.games                 "Round timer expired without Celery confirmation"
ERROR    django.request             "500 Internal Server Error /api/games/"
ERROR    apps.playlists             "Deezer API error: 503 Service Unavailable"
DEBUG    apps.games.services        "Score calculated: 850 pts for user 42"
```

### Niveaux de log recommandés

| Niveau     | Quand l'utiliser                        | Impact performance    |
| ---------- | --------------------------------------- | --------------------- |
| `DEBUG`    | Développement uniquement, détails fins  | Élevé (nombreux logs) |
| `INFO`     | Événements normaux significatifs        | Moyen                 |
| `WARNING`  | Situations anormales mais récupérables  | Faible                |
| `ERROR`    | Erreurs qui nécessitent attention       | Faible                |
| `CRITICAL` | Erreurs critiques, service indisponible | Faible                |

> En production, le niveau minimum recommandé est `WARNING` pour les loggers applicatifs.

---

## Gestion du cycle de vie des logs (ILM)

Les logs s'accumulent rapidement et peuvent remplir le disque. Il faut configurer une politique de rétention.

```python
# Configuration ILM recommandée via Kibana > Stack Management > ILM

Politique "instantmusic-logs-policy" :
├── Hot phase (logs récents, 0-7 jours)
│   └── Accès en lecture/écriture
│   └── Maximum 50 GB par index
├── Warm phase (logs de 7-30 jours)
│   └── Réduction du nombre de shards
│   └── Accès en lecture seule
└── Delete phase (logs > 30 jours)
    └── Suppression automatique
```

### Commandes utiles Elasticsearch

```bash
# Lister tous les indices
curl http://localhost:9200/_cat/indices?v

# Voir la taille des indices de logs
curl http://localhost:9200/_cat/indices/instantmusic-logs-*?v&h=index,docs.count,store.size

# Supprimer un index manuellement (attention !)
curl -X DELETE http://localhost:9200/instantmusic-logs-2026.01.01

# Compter les logs d'erreur du jour
curl -X GET "http://localhost:9200/instantmusic-logs-$(date +%Y.%m.%d)/_count" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"term": {"level": "ERROR"}}}'
```
