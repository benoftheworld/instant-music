# Consumers WebSocket

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Routage WebSocket](#routage-websocket)
- [GameConsumer](#gameconsumer)
  - [Connexion et déconnexion](#connexion-et-déconnexion)
  - [Rate limiting](#rate-limiting)
  - [Messages entrants](#messages-entrants)
  - [Messages sortants](#messages-sortants)
  - [Bonus Fog — script Lua atomique](#bonus-fog--script-lua-atomique)
- [NotificationConsumer](#notificationconsumer)
- [Flux complet d'un message WebSocket](#flux-complet-dun-message-websocket)
- [Gestion des erreurs](#gestion-des-erreurs)

---

## Vue d'ensemble

Django Channels étend Django pour gérer les connexions WebSocket (et autres protocoles asynchrones) via des **consumers** — l'équivalent WebSocket des vues Django.

### Rôle des consumers dans InstantMusic

```
┌─────────────────────────────────────────────────────────────────┐
│                     DJANGO CHANNELS                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Channel Layer (Redis)                                   │   │
│  │                                                          │   │
│  │  Group "game_ABCD1234"  ←──────── GameConsumer (Alice)  │   │
│  │       ↓ broadcast       ←──────── GameConsumer (Bob)    │   │
│  │  ─────────────────────► ──────→ GameConsumer (Charlie)  │   │
│  │                                                          │   │
│  │  Group "notifications_42" ←─── NotificationConsumer     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Chaque connexion WebSocket ouvre une instance dédiée du consumer. Le **channel layer Redis** permet à ces instances de communiquer entre elles en broadcast (un message envoyé au groupe est reçu par toutes les connexions du groupe).

---

## Routage WebSocket

**Fichier :** `backend/apps/games/routing.py`

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/game/(?P<room_code>\w+)/$",
        consumers.GameConsumer.as_asgi(),
    ),
    re_path(
        r"ws/notifications/$",
        consumers.NotificationConsumer.as_asgi(),
    ),
]
```

| URL Pattern                   | Consumer               | Usage                    |
| ----------------------------- | ---------------------- | ------------------------ |
| `ws://host/ws/game/ABCD1234/` | `GameConsumer`         | Partie de quiz en cours  |
| `ws://host/ws/notifications/` | `NotificationConsumer` | Notifications temps réel |

---

## GameConsumer

**Fichier :** `backend/apps/games/consumers.py`

```python
class GameConsumer(AsyncWebsocketConsumer):
    ...
```

`AsyncWebsocketConsumer` est la classe de base de Django Channels pour les consumers asynchrones. Toutes les méthodes sont des coroutines (`async def`).

### Connexion et déconnexion

#### `connect()`

```python
async def connect(self):
    self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
    self.room_group_name = f"game_{self.room_code}"
    self.user = self.scope["user"]
```

Flux de connexion :

```
Client ouvre ws://host/ws/game/ABCD1234/
        │
        ▼
JwtWebSocketMiddleware a déjà validé le token
scope["user"] = User(id=42, username="Alice")
        │
        ▼
connect() est appelé
        │
        ▼
Vérification : La partie "ABCD1234" existe ?
  game = await Game.objects.aget(room_code="ABCD1234")
        │
  ┌─────┴──────┐
  │  Non       │──── await self.close(code=4004)
  └─────┬──────┘     "Game not found"
        │ Oui
        ▼
La partie est en cours ou en attente ?
  game.status in ["waiting", "started"]
        │
  ┌─────┴──────┐
  │  Non       │──── await self.close(code=4005)
  └─────┬──────┘     "Game not active"
        │ Oui
        ▼
await self.channel_layer.group_add(
    self.room_group_name,  # "game_ABCD1234"
    self.channel_name,     # identifiant unique de ce consumer
)
        │
        ▼
await self.accept()
# La connexion WebSocket est établie
```

#### `disconnect()`

```python
async def disconnect(self, close_code):
    await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name,
    )
    # Notifie les autres joueurs du départ
```

---

### Rate limiting

Implémenté via un **script Lua atomique** exécuté dans Redis. L'algorithme utilisé est la **fenêtre glissante** (sliding window).

#### Pourquoi Lua dans Redis ?

L'opération de vérification du rate limit (lecture + incrémentation + expiration) doit être **atomique** — sans atomicité, deux requêtes simultanées pourraient toutes deux passer la vérification alors qu'elles devraient être bloquées. Redis exécute les scripts Lua atomiquement (verrou global).

#### Limites par type de message

```
┌────────────────┬───────────┬──────────────┬────────────────────────────────┐
│ Type message   │ Limit     │ Window       │ Raison                         │
├────────────────┼───────────┼──────────────┼────────────────────────────────┤
│ player_answer  │ 5 msg     │ 10 secondes  │ Anti-spam de réponses          │
│ activate_bonus │ 3 msg     │ 60 secondes  │ Empêche l'abus de bonus        │
│ player_join    │ 5 msg     │ 30 secondes  │ Empêche les reconnexions abusives│
│ start_game     │ 3 msg     │ 60 secondes  │ Empêche les redémarrages accidentels│
│ (défaut)       │ 30 msg    │ 10 secondes  │ Protection générale            │
└────────────────┴───────────┴──────────────┴────────────────────────────────┘
```

#### Algorithme de fenêtre glissante (sliding window)

```
Clé Redis : "ratelimit:{user_id}:{message_type}"
Type : Sorted Set

Requête à t=15.0s (limite: 5/10s)
        │
Script Lua :
  1. ZREMRANGEBYSCORE key 0 (now - 10000)
     → Supprime les entrées de plus de 10s
     → Sorted Set actuel : {12.1, 13.5, 14.2}

  2. ZCARD key
     → count = 3 (< 5) → Passe

  3. ZADD key 15000 "15000-random"
     → Ajoute la requête courante
     → Sorted Set : {12.1, 13.5, 14.2, 15.0}

  4. EXPIRE key 10
     → TTL = 10s (nettoyage automatique)

Résultat : allowed=True, remaining=1
```

Si la limite est dépassée, le consumer renvoie une erreur JSON :
```json
{"type": "rate_limit_exceeded", "message_type": "player_answer", "retry_after": 3}
```

#### Taille maximale des messages

Les messages entrants sont limités à **16 KB** pour éviter les attaques par gros messages. Au-delà, la connexion est fermée avec le code `1009` (message too large).

---

### Messages entrants

#### Validation des messages (`WS_MESSAGE_SCHEMAS`)

Avant d'être traités, tous les messages entrants sont validés contre un schéma JSON :

```python
WS_MESSAGE_SCHEMAS = {
    "player_join": {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
        },
        "required": ["type"],
    },
    "player_answer": {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "answer": {"type": "string", "maxLength": 500},
            "response_time": {"type": "number", "minimum": 0},
        },
        "required": ["type", "answer", "response_time"],
    },
    # ... etc.
}
```

#### Tableau des messages entrants

| Type reçu        | Handler            | Accès requis     | Description               |
| ---------------- | ------------------ | ---------------- | ------------------------- |
| `player_join`    | `player_join()`    | Tous les joueurs | Rejoindre la salle de jeu |
| `player_answer`  | `player_answer()`  | Tous les joueurs | Soumettre une réponse     |
| `start_game`     | `start_game()`     | Hôte uniquement  | Démarrer la partie        |
| `start_round`    | `start_round()`    | Hôte uniquement  | Démarrer un round         |
| `end_round`      | `end_round()`      | Hôte uniquement  | Terminer un round         |
| `next_round`     | `next_round()`     | Hôte uniquement  | Passer au round suivant   |
| `finish_game`    | `finish_game()`    | Hôte uniquement  | Terminer la partie        |
| `activate_bonus` | `activate_bonus()` | Tous les joueurs | Activer un bonus          |

#### Vérification des droits hôte

```python
async def start_game(self, data):
    game = await self._get_game()

    # Vérifie que l'expéditeur est l'hôte
    if game.host_id != self.user.id:
        await self.send_json({
            "type": "error",
            "code": "forbidden",
            "message": "Seul l'hôte peut démarrer la partie"
        })
        return

    # ... logique de démarrage
```

#### Flux de traitement d'un message entrant

```python
async def receive(self, text_data):
    data = json.loads(text_data)  # Désérialisation JSON
    message_type = data.get("type")

    # 1. Rate limiting
    if not await self._check_rate_limit(message_type):
        await self.send_json({"type": "rate_limit_exceeded"})
        return

    # 2. Validation du schéma
    if not self._validate_message(data, message_type):
        await self.send_json({"type": "error", "code": "invalid_message"})
        return

    # 3. Dispatch vers le handler correspondant
    handler = getattr(self, message_type, None)
    if handler:
        await handler(data)
```

---

### Messages sortants

Les messages sont envoyés via le **channel layer Redis** à tous les membres du groupe. Chaque consumer membre reçoit le message et le transmet à son client WebSocket.

#### Tableau des messages sortants

| Broadcast envoyé par | Type dans le groupe | Type reçu par les clients | Description                |
| -------------------- | ------------------- | ------------------------- | -------------------------- |
| `player_join()`      | `player_joined`     | `player_joined`           | Un joueur a rejoint        |
| `disconnect()`       | `player_leave`      | `player_leave`            | Un joueur est parti        |
| `start_game()`       | `game_started`      | `game_started`            | La partie démarre          |
| `start_round()`      | `round_started`     | `round_started`           | Un round démarre           |
| `player_answer()`    | `player_answered`   | `player_answered`         | Un joueur a répondu        |
| `end_round()`        | `round_ended`       | `round_ended`             | Le round est terminé       |
| `next_round()`       | `next_round`        | `next_round`              | Passage au round suivant   |
| `finish_game()`      | `game_finished`     | `game_finished`           | La partie est terminée     |
| `activate_bonus()`   | `bonus_activated`   | `bonus_activated`         | Un bonus a été activé      |
| `BroadcastService`   | `game_updated`      | `game_updated`            | Mise à jour des paramètres |

#### Mécanique du broadcast dans Channels

```python
# Envoi au groupe (tous les consumers connectés le reçoivent)
await self.channel_layer.group_send(
    self.room_group_name,
    {
        "type": "player_joined",  # → appelle la méthode player_joined()
        "player": player_data,
    }
)

# Handler appelé sur chaque consumer du groupe
async def player_joined(self, event):
    # Transmet au client WebSocket de ce consumer
    await self.send(text_data=json.dumps({
        "type": "player_joined",
        "player": event["player"],
    }))
```

> Le champ `"type"` dans le message du groupe est converti en nom de méthode par Django Channels (`"player_joined"` → `self.player_joined(event)`).

---

### Bonus Fog — script Lua atomique

Le bonus **fog** est particulier car il doit être appliqué **atomiquement** lors du démarrage d'un round. S'il était vérifié avec deux opérations Redis séparées, une condition de course (race condition) pourrait permettre au fog d'être appliqué deux fois.

#### Problème de race condition

```
Consumer Alice              Consumer Bob
    │                           │
    │ start_round()             │ start_round()
    │                           │
    ▼                           ▼
GET fog_active?             GET fog_active?
→ True                      → True
    │                           │
    ▼                           ▼
SET fog_active = False      SET fog_active = False
Injecte fog dans round      Injecte fog dans round
    ← Deux fois appliqué ! →
```

#### Solution : script Lua atomique

```lua
-- Script Lua exécuté atomiquement dans Redis
-- KEYS[1] = "fog:{game_id}:{round_number}"
-- ARGV[1] = user_id de l'activateur

local key = KEYS[1]
local activator = ARGV[1]

-- Vérifie si le fog est actif
local current = redis.call("GET", key)
if current == false then
    return {0, nil}  -- Pas de fog actif
end

-- Consomme le fog (opération atomique)
redis.call("DEL", key)

-- Retourne : fog_active=1, activator=user_id
return {1, current}
```

```python
# Usage dans le consumer
result = await self._redis.eval(
    FOG_CONSUME_SCRIPT,
    keys=[f"fog:{game.id}:{round_number}"],
    args=[str(self.user.id)],
)

fog_active = bool(result[0])
fog_activator = result[1]

# Injecte dans les données du round
round_data["fog_active"] = fog_active
round_data["fog_activator"] = fog_activator
```

---

## NotificationConsumer

**Fichier :** `backend/apps/games/consumers.py`

```python
class NotificationConsumer(AsyncWebsocketConsumer):
    ...
```

Consumer dédié aux notifications temps réel personnalisées par utilisateur.

### Groupe de channels personnalisé

Contrairement au `GameConsumer` (groupe partagé entre tous les joueurs d'une partie), chaque utilisateur a son **propre groupe** de notifications :

```
Groupe "notifications_42"  → Uniquement la connexion de l'user 42
Groupe "notifications_7"   → Uniquement la connexion de l'user 7
```

Cela permet d'envoyer des notifications ciblées à un utilisateur précis depuis n'importe quelle vue Django.

### Connexion

```python
async def connect(self):
    self.user = self.scope["user"]

    # Refuse les connexions anonymes
    if not self.user.is_authenticated:
        await self.close(code=4003)
        return

    self.group_name = f"notifications_{self.user.id}"

    await self.channel_layer.group_add(
        self.group_name,
        self.channel_name,
    )
    await self.accept()
```

### Handlers push (serveur → client)

Ces handlers sont appelés quand un autre composant de l'application envoie un message au groupe via le channel layer. Le `NotificationConsumer` n'a pas de messages **entrants** (le client ne lui envoie rien).

| Handler                       | Type de notification   | Émetteur                       | Description                       |
| ----------------------------- | ---------------------- | ------------------------------ | --------------------------------- |
| `notify_game_invitation`      | `game_invitation`      | Vue HTTP d'invitation          | Invitation à rejoindre une partie |
| `notify_invitation_cancelled` | `invitation_cancelled` | Vue HTTP d'annulation          | Invitation annulée par l'hôte     |
| `notify_achievement_unlocked` | `achievement_unlocked` | Tâche Celery `check_and_award` | Achievement débloqué              |

#### Exemple : notification d'achievement depuis Celery

```python
# Dans la tâche Celery (apps/achievements/tasks.py)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

async_to_sync(channel_layer.group_send)(
    f"notifications_{user_id}",
    {
        "type": "notify_achievement_unlocked",
        "achievement": {
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "icon": achievement.icon,
            "coins_reward": achievement.coins_reward,
        }
    }
)
```

```python
# Dans NotificationConsumer
async def notify_achievement_unlocked(self, event):
    await self.send(text_data=json.dumps({
        "type": "achievement_unlocked",
        "achievement": event["achievement"],
    }))
```

---

## Flux complet d'un message WebSocket

Le schéma suivant montre le cycle de vie complet d'un message, depuis le clic du joueur jusqu'à l'affichage chez tous les participants.

### Exemple : soumission d'une réponse (`player_answer`)

```
┌──────────┐         ┌─────────────┐         ┌─────────────┐         ┌──────────┐
│  Alice   │         │   Django    │         │    Redis    │         │   Bob    │
│(Browser) │         │  Channels   │         │(Channel     │         │(Browser) │
└──────────┘         └─────────────┘         │  Layer)     │         └──────────┘
     │                      │                └─────────────┘              │
     │                      │                       │                     │
     │  WS send:             │                       │                     │
     │  {"type":             │                       │                     │
     │   "player_answer",   │                       │                     │
     │   "answer": "Eagles",│                       │                     │
     │   "response_time":4.2}                       │                     │
     │─────────────────────►│                       │                     │
     │                      │                       │                     │
     │                      │ 1. receive(text_data) │                     │
     │                      │ 2. Rate limit check   │                     │
     │                      │    (Lua Redis)────────►                     │
     │                      │◄───────────────────── │                     │
     │                      │    allowed=True        │                     │
     │                      │ 3. Schema validation  │                     │
     │                      │ 4. player_answer()    │                     │
     │                      │                       │                     │
     │                      │ GameService.submit_answer()                 │
     │                      │ → check_answer() → True                     │
     │                      │ → calculate_score() → 916 pts               │
     │                      │ → BonusService.apply() → 916 pts            │
     │                      │ → Crée GameAnswer en DB                     │
     │                      │                       │                     │
     │                      │ channel_layer.        │                     │
     │                      │ group_send(           │                     │
     │                      │   "game_ABCD1234",    │                     │
     │                      │   {type:              │                     │
     │                      │    "player_answered", │                     │
     │                      │    player_id: 42,     │                     │
     │                      │    points: 916,       │                     │
     │                      │    is_correct: true}  │                     │
     │                      │)──────────────────────►                     │
     │                      │                       │                     │
     │                      │                       │  Publie dans        │
     │                      │                       │  "game_ABCD1234"    │
     │                      │                       │                     │
     │                      │◄──────────────────────│                     │
     │  player_answered     │   Distribue à tous    │◄────────────────────│
     │◄─────────────────────│   les consumers       │                     │
     │  {"type":            │   du groupe           │──────────────────►  │
     │   "player_answered", │                       │  player_answered    │
     │   "player_id": 42,   │                       │  ─────────────────► │
     │   "points": 916,     │                       │                     │
     │   "is_correct": true}│                       │                     │
     │                      │                       │                     │
```

### Flux broadcast via BroadcastService (depuis une vue HTTP)

```
Vue HTTP DRF                BroadcastService         Redis Channel Layer
     │                           │                          │
     │  POST /api/games/join/    │                          │
     ▼                           │                          │
Traite la requête               │                          │
Crée GamePlayer en DB           │                          │
     │                           │                          │
     │  broadcast_player_join(   │                          │
     │    room_code, player_data)│                          │
     │──────────────────────────►│                          │
     │                           │  async_to_sync(          │
     │                           │    group_send(           │
     │                           │      "game_ABCD1234",    │
     │                           │      {type:              │
     │                           │       "player_joined",   │
     │                           │       player: {...}}     │
     │                           │    )                     │
     │                           │  )────────────────────►  │
     │                           │                          │  Distribue aux consumers
     │                           │                          │  connectés à "game_ABCD1234"
     │◄──────────────────────────│                          │
     │  Retourne Response 201    │                          │
```

---

## Gestion des erreurs

### Codes de fermeture WebSocket

Les codes `4000-4999` sont réservés aux applications. InstantMusic utilise :

| Code   | Signification                               | Déclenché par            |
| ------ | ------------------------------------------- | ------------------------ |
| `4003` | Non autorisé (token JWT invalide ou expiré) | `JwtWebSocketMiddleware` |
| `4004` | Partie introuvable                          | `GameConsumer.connect()` |
| `4005` | Partie terminée ou non active               | `GameConsumer.connect()` |

### Erreurs JSON dans le canal

Pour les erreurs non fatales (qui ne ferment pas la connexion), le consumer envoie un message d'erreur JSON :

```json
{
    "type": "error",
    "code": "forbidden",
    "message": "Seul l'hôte peut démarrer la partie"
}
```

```json
{
    "type": "error",
    "code": "invalid_message",
    "message": "Champ 'answer' manquant ou invalide"
}
```

```json
{
    "type": "rate_limit_exceeded",
    "message_type": "player_answer",
    "retry_after": 3
}
```

### Reconnexion automatique côté client

Le frontend React gère la reconnexion automatique en cas de déconnexion inattendue (code `1006` — connexion perdue) :

```
Déconnexion inattendue (code 1006)
        │
        ▼
Attente : 1s
        │
        ▼
Tentative de reconnexion
(nouveau token JWT si expiré)
        │
  ┌─────┴──────┐
  │  Succès    │──── Reprend l'état de la partie via l'API REST
  └─────┬──────┘
        │ Échec
        ▼
Attente : 2s, 4s, 8s... (backoff exponentiel)
Max 5 tentatives, puis affiche "Connexion perdue"
```

> Les déconnexions avec les codes `4003`, `4004`, `4005` ne déclenchent **pas** de reconnexion automatique car elles indiquent une erreur irrécupérable (token invalide, partie inexistante).
