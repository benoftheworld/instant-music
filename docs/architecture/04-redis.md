# Architecture — Redis

> Ce document explique ce qu'est Redis, comment il fonctionne, et les trois roles qu'il joue dans InstantMusic.

---

## Sommaire

- [Qu'est-ce que Redis ?](#quest-ce-que-redis-)
- [Comment Redis stocke les donnees](#comment-redis-stocke-les-donnees)
- [Les 3 roles de Redis dans InstantMusic](#les-3-roles-de-redis-dans-instantmusic)
  - [Role 1 : Cache Django](#role-1--cache-django)
  - [Role 2 : Channel Layer WebSocket](#role-2--channel-layer-websocket)
  - [Role 3 : Broker Celery](#role-3--broker-celery)
- [Schema des bases Redis](#schema-des-bases-redis)
- [Exemples de cles Redis](#exemples-de-cles-redis)
- [Configuration](#configuration)

---

## Qu'est-ce que Redis ?

**Redis** (Remote Dictionary Server) est une base de donnees tres particuliere : elle stocke toutes ses donnees directement **en memoire vive (RAM)**, contrairement a PostgreSQL qui les ecrit sur le disque dur.

### L'analogie du bureau

Imaginez deux types de stockage :
- **PostgreSQL** (base de donnees traditionnelle) = une armoire avec des dossiers. Tres organise, peut contenir enormement de donnees, mais pour chercher quelque chose il faut ouvrir l'armoire, trouver le bon tiroir, feuilleter les dossiers.
- **Redis** (base de donnees en memoire) = votre bureau. Tout est a portee de main, l'acces est instantane, mais vous ne pouvez pas tout y poser (la memoire RAM est limitee).

Redis est donc utilise pour les donnees :
- **auxquelles on accede tres souvent** (centaines de fois par seconde)
- **qui n'ont pas besoin de vivre eternellement** (peuvent etre regenerees)
- **qui doivent etre partagees entre plusieurs processus** (plusieurs workers backend)

### Performances

Redis peut traiter **100 000 a 1 000 000 operations par seconde**, la ou PostgreSQL plafonne a quelques milliers. C'est cet ecart de performance qui justifie d'utiliser Redis en complement d'une base de donnees traditionnelle.

---

## Comment Redis stocke les donnees

Redis est une base de donnees **cle-valeur** (key-value). Chaque information est stockee sous la forme :

```
"cle" → valeur
```

C'est comme un dictionnaire Python : vous donnez une cle, vous obtenez la valeur associee.

### Types de donnees supportes

Redis ne stocke pas uniquement des textes. Il supporte plusieurs structures :

```
STRING   : "utilisateur:42:prenom" → "Alice"
           La valeur la plus simple. Une cle, une valeur texte.

HASH     : "utilisateur:42" → { prenom: "Alice", score: 1500, niveau: 3 }
           Comme un objet/dictionnaire. Utile pour regrouper des champs.

LIST     : "taches:celery" → ["tache1", "tache2", "tache3"]
           Une liste ordonnee. Utilisee par Celery comme file d'attente.

SET      : "parties:actives" → {"ABC123", "DEF456", "GHI789"}
           Un ensemble sans doublons. Utile pour les listes d'IDs.

SORTED SET: "classement:global" → {Alice: 1500, Bob: 1200, Charlie: 800}
           Comme un set, mais avec un score pour trier. Parfait pour les classements.

PUBSUB   : canal "game_ABC123" → broadcast de messages
           Systeme de messages en temps reel. Utilise par Django Channels.
```

### TTL (Time To Live) — les donnees qui s'expirent

Une fonctionnalite cle de Redis : on peut definir un **TTL** (duree de vie) sur n'importe quelle cle. Apres ce delai, la donnee est automatiquement supprimee.

```
SETEX "session:alice" 3600 "données de session..."
# Cette cle sera supprimee automatiquement apres 3600 secondes (1 heure)
```

C'est parfait pour un cache : les donnees expires se nettoient toutes seules.

---

## Les 3 roles de Redis dans InstantMusic

```
┌──────────────────────────────────────────────────────────────────────┐
│                           REDIS :6379                                 │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │     BASE 0       │  │     BASE 1       │  │     BASE 2       │   │
│  │                  │  │                  │  │                  │   │
│  │  BROKER CELERY   │  │  CACHE DJANGO    │  │  CHANNEL LAYER   │   │
│  │                  │  │                  │  │  (WebSockets)    │   │
│  │  Files d'attente │  │  Resultats API   │  │  Groupes et      │   │
│  │  de taches       │  │  Sessions        │  │  messages en     │   │
│  │  asynchrones     │  │  Classements     │  │  temps reel      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Role 1 : Cache Django

#### Probleme resolu

Imaginons que 100 joueurs consultent le classement global en meme temps. Sans cache :
- 100 requetes SQL vers PostgreSQL
- Chaque requete calcule et retrie tout le classement
- PostgreSQL est sature

Avec cache Redis :
- La premiere requete calcule le classement et le stocke dans Redis
- Les 99 suivantes lisent depuis Redis en quelques microsecondes
- PostgreSQL ne recoit qu'une seule requete

#### Donnees mises en cache

| Cle Redis                     | Contenu                              | TTL                         |
| ----------------------------- | ------------------------------------ | --------------------------- |
| `cache:leaderboard:global`    | Top 100 joueurs, scores              | 5 minutes                   |
| `cache:user:42:profile`       | Profil public de l'utilisateur 42    | 10 minutes                  |
| `cache:playlist:deezer:12345` | Morceaux de la playlist Deezer       | 1 heure                     |
| `cache:achievements:list`     | Liste de tous les succes disponibles | 1 heure                     |
| `blacklist:token:eyJ...`      | Token JWT invalide (logout)          | Jusqu'a expiration du token |

#### Comment Django utilise le cache

```python
from django.core.cache import cache

# Stocker dans le cache (TTL = 300 secondes)
cache.set("leaderboard:global", players_data, timeout=300)

# Lire depuis le cache
data = cache.get("leaderboard:global")
if data is None:
    # Pas en cache : calculer et stocker
    data = compute_leaderboard()
    cache.set("leaderboard:global", data, timeout=300)

# Supprimer du cache (ex: quand les donnees changent)
cache.delete("leaderboard:global")
```

---

### Role 2 : Channel Layer WebSocket

#### Le probleme du temps reel avec plusieurs workers

Imaginons 3 joueurs dans la meme salle. Chacun est connecte a un worker Django different :

```
Alice  ←──WebSocket──→ Worker Django 1
Bob    ←──WebSocket──→ Worker Django 2
Charlie←──WebSocket──→ Worker Django 3
```

Quand Alice envoie une reponse, le Worker 1 la recoit. Mais comment prevenir Bob et Charlie qui sont connectes a des workers differents ?

Sans Redis channel layer, les workers sont isoles et ne peuvent pas se parler.

#### La solution : le channel layer Redis

Redis agit comme un **tableau d'affichage partagé** entre tous les workers :

```
Alice  ←──WS──→  Worker 1
Bob    ←──WS──→  Worker 2       Redis Channel Layer
Charlie←──WS──→  Worker 3      ┌─────────────────────┐
                                │  Groupe "game_ABC123"│
                                │  ┌────────────────┐  │
Worker 1 envoie un message ────→│  │ channel_alice  │  │
au groupe "game_ABC123"         │  │ channel_bob    │  │
                                │  │ channel_charlie│  │
                                │  └────────────────┘  │
                                └─────────────────────┘
                                          │
                       ┌──────────────────┼──────────────────┐
                       ▼                  ▼                   ▼
                  Worker 1           Worker 2            Worker 3
                  (envoie a Alice)  (envoie a Bob)  (envoie a Charlie)
```

#### Donnees stockees par le channel layer

```
# Mapping channel_name → groupe(s)
asgi:group:game_ABC123 = SET {
    "specific.abc123!abc",   # channel d'Alice
    "specific.def456!def",   # channel de Bob
    "specific.ghi789!ghi"    # channel de Charlie
}

# Message en transit (PubSub)
asgi:group:game_ABC123 → message JSON
```

---

### Role 3 : Broker Celery

#### Comment fonctionne la file d'attente

Redis agit comme une **boite aux lettres** entre le serveur web et les workers Celery :

```
PRODUCTEUR (Backend Django)          CONSOMMATEUR (Celery Worker)

  game terminee                        Worker surveille la file
       │                               en permanence (poll)
       ▼                                        │
  check_and_award.delay(42)                     │
       │                                        │
       ▼                                        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  REDIS (Broker)  - BASE 0                                    │
  │                                                              │
  │  File "celery" (LIST Redis) :                               │
  │  [                                                           │
  │    { "task": "check_and_award", "kwargs": {"game_id": 42} } │
  │    { "task": "purge_invitations", "kwargs": {} }            │
  │    { "task": "debug_task", "kwargs": {} }                   │
  │  ]                                                           │
  │                                                              │
  │  Resultats des taches :                                      │
  │  "celery-task-meta-d3b07384" → { "status": "SUCCESS",       │
  │                                   "result": {...} }          │
  └─────────────────────────────────────────────────────────────┘
```

Les operations Redis utilisees par Celery :
- `RPUSH` : ajouter une tache en fin de file (le backend)
- `BLPOP` : depiler une tache (le worker attend bloquant si vide)
- `SET` / `GET` : stocker et lire les resultats des taches

---

## Schema des bases Redis

```
redis:6379
│
├── DB 0  (BROKER CELERY)
│   │
│   ├── _kombu.binding.celery              # Binding de la file Celery
│   ├── celery                             # File des taches (LIST)
│   ├── celery-task-meta-<uuid>            # Resultats des taches
│   └── celerybeat-schedule                # Planning Celery Beat
│
├── DB 1  (CACHE DJANGO)
│   │
│   ├── :1:cache.leaderboard.global        # Classement global
│   ├── :1:cache.user.<id>.profile         # Profils utilisateurs
│   ├── :1:cache.playlist.deezer.<id>      # Playlists Deezer
│   ├── :1:cache.achievements.list         # Liste des succes
│   └── :1:blacklist.token.<token_hash>    # Tokens JWT revoqués
│
└── DB 2  (CHANNEL LAYER WEBSOCKET)
    │
    ├── asgi:group:game_<code>             # Groupes de jeu (SET)
    ├── asgi:group:notifications_<uid>    # Groupes de notifications (SET)
    └── asgi:message:<channel_name>       # Messages en transit
```

---

## Exemples de cles Redis

### Cache

```bash
# Inspecter le contenu du cache depuis le shell Django
# make dev-shell → python manage.py shell

from django.core.cache import cache

# Lister toutes les cles (attention, coute cher en prod)
# Ne pas faire en production !

# Lire une cle specifique
cache.get("leaderboard:global")
# → [{"username": "alice", "score": 1500}, ...]

# Duree de vie restante
cache._cache.get_client().ttl(":1:cache.leaderboard.global")
# → 287  (secondes restantes)
```

### Redis CLI (depuis le conteneur)

```bash
# Entrer dans le conteneur Redis
docker compose exec redis redis-cli

# Lister les cles du cache (DB 1)
SELECT 1
KEYS *

# Voir la valeur d'une cle
GET ":1:cache.leaderboard.global"

# Voir le TTL restant (en secondes, -1 = pas de TTL, -2 = cle inexistante)
TTL ":1:cache.leaderboard.global"

# Voir les membres du groupe WebSocket "game_ABC123" (DB 2)
SELECT 2
SMEMBERS "asgi:group:game_ABC123"

# Compter les taches en attente (DB 0)
SELECT 0
LLEN "celery"
```

### Sortie typique

```
127.0.0.1:6379[2]> SMEMBERS "asgi:group:game_ABC123"
1) "specific.8f3a!abc123456"
2) "specific.2b9c!def789012"
3) "specific.7e1d!ghi345678"

127.0.0.1:6379[2]> SCARD "asgi:group:game_ABC123"
(integer) 3    ← 3 joueurs connectes dans la salle ABC123
```

---

## Configuration

### Dans les settings Django

```python
# backend/config/settings/base.py

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",  # DB 1 pour le cache
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # Degradation gracieuse si Redis indisponible
        }
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
            "capacity": 1500,          # Max messages en attente par groupe
            "expiry": 10,              # Expiration des messages en secondes
        },
    },
}

CELERY_BROKER_URL = "redis://redis:6379/0"       # DB 0 pour Celery
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
```

### Ports et connexions

| Service          | Variable            | Valeur dev                          |
| ---------------- | ------------------- | ----------------------------------- |
| Cache            | `REDIS_URL`         | `redis://redis:6379/1`              |
| Channel Layer    | Config Channels     | `redis://redis:6379` (DB 2 interne) |
| Broker Celery    | `CELERY_BROKER_URL` | `redis://redis:6379/0`              |
| Acces direct dev | -                   | `localhost:6379`                    |

### Variables d'environnement

```bash
# .env
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Considerations en production

En production, Redis devrait etre configure avec :
- **`maxmemory`** : limite la quantite de RAM utilisable (ex: `maxmemory 512mb`)
- **`maxmemory-policy`** : politique d'eviction si la memoire est pleine (`allkeys-lru` recommande pour un cache)
- **Persistence** : `RDB` (snapshots) et/ou `AOF` (append-only file) selon les besoins
- **Mot de passe** : `requirepass motdepassefort`
- **Acces reseau** : uniquement depuis le reseau Docker interne (pas expose sur internet)
