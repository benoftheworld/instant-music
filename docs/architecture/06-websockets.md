# Architecture — WebSockets

> Ce document explique ce qu'est un WebSocket, comment Django Channels les gere, et comment fonctionne le protocole de jeu temps reel d'InstantMusic.

---

## Sommaire

- [HTTP vs WebSocket](#http-vs-websocket)
- [Django Channels et ASGI](#django-channels-et-asgi)
- [Redis comme channel layer](#redis-comme-channel-layer)
- [Routes WebSocket](#routes-websocket)
- [Authentification JWT](#authentification-jwt)
- [Flux complet d'un message](#flux-complet-dun-message)
- [GameConsumer — Messages du jeu](#gameconsumer--messages-du-jeu)
- [NotificationConsumer](#notificationconsumer)
- [Rate limiting WebSocket](#rate-limiting-websocket)
- [Gestion des deconnexions](#gestion-des-deconnexions)

---

## HTTP vs WebSocket

### Le protocole HTTP classique

HTTP est un protocole de type **requete-reponse**. La conversation ressemble a ceci :

```
Navigateur                          Serveur
    │                                   │
    │  "Donne-moi la page d'accueil"    │
    │──────────────────────────────────→│
    │                                   │ (Traitement)
    │  "Voila la page d'accueil"        │
    │←──────────────────────────────────│
    │                                   │
    │  (Connexion fermee)               │
    │                                   │
    │  "Donne-moi le profil d'Alice"    │
    │──────────────────────────────────→│
    │                                   │
    │  "Voila le profil d'Alice"        │
    │←──────────────────────────────────│
    │                                   │
    │  (Connexion fermee)               │
```

C'est parfait pour consulter des pages ou faire des formulaires. Mais pour un quiz en temps reel, c'est un probleme : si Bob envoie une reponse, comment Alice le sait-elle sans recharger la page ?

Une solution naive serait le **polling** : Alice interroge le serveur toutes les secondes ("Est-ce que Bob a repondu ?"). C'est tres inefficace.

### Le protocole WebSocket

WebSocket etablit une **connexion persistante** et **bidirectionnelle** :

```
Navigateur                          Serveur
    │                                   │
    │  "Je veux ouvrir un WebSocket"    │
    │  (requete HTTP Upgrade)           │
    │──────────────────────────────────→│
    │                                   │
    │  "OK, connexion etablie"          │
    │←──────────────────────────────────│
    │                                   │
    │═══════════════════════════════════│ Connexion persistante ouverte
    │                                   │
    │  "Je reponds 'Bohemian Rhapsody'" │  ← Client envoie
    │──────────────────────────────────→│
    │                                   │
    │  "Bob aussi a repondu !"          │  ← Serveur envoie sans qu'Alice demande
    │←──────────────────────────────────│
    │                                   │
    │  "Nouveau round commence !"       │  ← Serveur envoie spontanement
    │←──────────────────────────────────│
    │                                   │
    │═══════════════════════════════════│ (connexion reste ouverte)
```

Avantages pour le quiz :
- Le serveur peut pousser des informations instantanement sans que le client ne demande
- Une seule connexion pour toute la duree de la partie (pas de surcharge)
- Latence tres faible (quelques millisecondes)

### Comparaison

| Aspect         | HTTP                               | WebSocket                                 |
| -------------- | ---------------------------------- | ----------------------------------------- |
| Connexion      | Ouverte et fermee a chaque requete | Persistante pendant toute la session      |
| Direction      | Client → Serveur uniquement        | Bidirectionnel (les deux peuvent initier) |
| Overhead       | Headers HTTP a chaque requete      | Headers uniquement a l'etablissement      |
| Usage ideal    | Consulter des donnees, formulaires | Temps reel, jeux, chat, notifications     |
| Dans le projet | API REST (/api/)                   | Jeu en cours, notifications (/ws/)        |

---

## Django Channels et ASGI

### Le probleme de Django classique

Django a ete concu pour HTTP. Il utilise WSGI (Web Server Gateway Interface), un standard qui ne supporte pas les connexions persistantes.

```
WSGI (classique) :
  - Une requete entre
  - Django la traite
  - Une reponse sort
  - C'est tout

WebSocket :
  - Une connexion s'ouvre
  - Des messages entrent ET sortent
  - La connexion reste ouverte
  - WSGI ne sait pas gerer ca !
```

### La solution : ASGI + Django Channels

**ASGI** (Asynchronous Server Gateway Interface) est la version moderne de WSGI, con pour les connexions asynchrones et persistantes.

**Django Channels** est une extension de Django qui ajoute le support ASGI, et donc les WebSockets, en s'appuyant sur des **consumers** (equivalent des views Django, mais pour les connexions persistantes).

```
config/asgi.py

                    ASGI Application
                          │
                          │ Regarde le type de connexion
                          │
          ┌───────────────┼───────────────┐
          │                               │
   Connexion HTTP                  Connexion WebSocket
          │                               │
    Django WSGI                   Django Channels
    (views classiques)            (consumers)
          │                               │
    APIView, etc.           ┌─────────────┴──────────────┐
                            │                             │
                     /ws/game/<code>/          /ws/notifications/
                            │                             │
                     GameConsumer          NotificationConsumer
```

### Qu'est-ce qu'un Consumer ?

Un consumer ressemble a une view Django, mais au lieu de gerer une requete/reponse, il gere le cycle de vie d'une connexion WebSocket :

```python
class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Appele quand un client se connecte
        # → Verifier l'auth, rejoindre le groupe Redis, envoyer l'etat du jeu

    async def disconnect(self, close_code):
        # Appele quand un client se deconnecte (fermeture, reseau coupe, etc.)
        # → Quitter le groupe Redis, notifier les autres joueurs

    async def receive(self, text_data):
        # Appele quand le client envoie un message
        # → Parser le JSON, dispatcher vers le bon handler

    async def send_to_client(self, event):
        # Appele quand le channel layer envoie un message a ce consumer
        # → Transmettre le message au client via WebSocket
```

---

## Redis comme channel layer

### Le probleme de l'isolation des workers

En production, plusieurs instances du backend tournent en parallele. Deux joueurs dans la meme salle peuvent etre connectes a des workers differents. Sans coordination, les messages ne pourraient pas circuler entre eux.

```
SANS CHANNEL LAYER :

Alice ──WS──→ Worker 1
Bob   ──WS──→ Worker 2

Alice repond au quiz.
Worker 1 la recoit, mais ne peut pas prevenir Bob qui est sur Worker 2.
```

```
AVEC REDIS CHANNEL LAYER :

Alice ──WS──→ Worker 1 ─────→ Redis "group:game_ABC123" ←───── Worker 2 ──WS──→ Bob
                                        │
                               Broadcast le message
                               a TOUS les members du groupe
                                        │
                       ┌───────────────────────────────┐
                       ▼                               ▼
                 Worker 1                         Worker 2
              (renvoie a Alice)               (renvoie a Bob)
```

### Fonctionnement interne

1. A la connexion, le consumer rejoint un **groupe** Redis identifie par le code de la salle :
   ```python
   await self.channel_layer.group_add("game_ABC123", self.channel_name)
   ```

2. Pour envoyer un message a TOUS les joueurs de la salle :
   ```python
   await self.channel_layer.group_send(
       "game_ABC123",
       {"type": "game.start_round", "payload": {...}}
   )
   ```

3. Redis distribue ce message a tous les channels du groupe. Chaque worker concerne recoit la notification et renvoie le message JSON a son client WebSocket.

4. A la deconnexion, le consumer quitte le groupe :
   ```python
   await self.channel_layer.group_discard("game_ABC123", self.channel_name)
   ```

---

## Routes WebSocket

### Configuration du routing

```python
# backend/apps/games/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/game/(?P<room_code>[A-Z0-9]{6})/$",
        consumers.GameConsumer.as_asgi()
    ),
    re_path(
        r"ws/notifications/$",
        consumers.NotificationConsumer.as_asgi()
    ),
]
```

```python
# backend/config/asgi.py

from channels.routing import ProtocolTypeRouter, URLRouter
from apps.authentication.middleware import JwtAuthMiddleware
from apps.games.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### Routes disponibles

| Route                   | Consumer               | Description                                                                     |
| ----------------------- | ---------------------- | ------------------------------------------------------------------------------- |
| `/ws/game/<room_code>/` | `GameConsumer`         | Connexion a une salle de jeu. `room_code` = code a 6 caracteres alphanumeriques |
| `/ws/notifications/`    | `NotificationConsumer` | Canal de notifications personnelles (succes, invitations...)                    |

---

## Authentification JWT

### Le probleme

Les WebSockets ne supportent pas nativement les headers HTTP personnalises lors de la connexion initiale (contrairement aux requetes HTTP classiques). On ne peut donc pas envoyer `Authorization: Bearer <token>` de la facon habituelle.

### La solution : query parameter

Le token JWT est passe en **parametre d'URL** :

```
ws://localhost:8000/ws/game/ABC123/?token=eyJhbGciOiJIUzI1NiJ9...
```

### Middleware d'authentification

Un middleware Django Channels intercepte chaque connexion WebSocket, extrait le token et identifie l'utilisateur avant de passer la main au consumer :

```python
# backend/apps/authentication/middleware.py

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extraire le token depuis le query string
        query_string = scope.get("query_string", b"").decode()
        params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
        token = params.get("token", "")

        # Valider le token JWT
        try:
            user = await authenticate_via_jwt(token)
            scope["user"] = user
        except (InvalidToken, TokenError):
            # Token invalide : fermer la connexion
            await send({"type": "websocket.close", "code": 4001})
            return

        # Passer au consumer
        await super().__call__(scope, receive, send)
```

### Securite

- Le token est valide uniquement pour la duree de vie de l'access token (typiquement 15 minutes)
- Si le token expire pendant la partie, la connexion reste ouverte (la verification est faite uniquement a la connexion)
- Les tokens revoques (logout) sont dans la blacklist Redis et rejetes au niveau du middleware

---

## Flux complet d'un message

Exemple : Alice envoie sa reponse pendant un round

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ COTE CLIENT (navigateur d'Alice)                                                  │
│                                                                                   │
│  const ws = new WebSocket("ws://localhost:8000/ws/game/ABC123/?token=...");      │
│  ws.send(JSON.stringify({                                                         │
│    type: "player_answer",                                                         │
│    payload: {                                                                     │
│      round_id: 3,                                                                 │
│      answer: "Bohemian Rhapsody",                                                 │
│      answer_time_ms: 4230                                                         │
│    }                                                                              │
│  }));                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Message JSON via WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ NGINX (prod uniquement)                                                           │
│                                                                                   │
│  Tunnel WebSocket transparent (pas de modification du message)                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ DJANGO CHANNELS — GameConsumer.receive()                                          │
│                                                                                   │
│  1. Parse le JSON                                                                 │
│  2. Identifie le type "player_answer"                                             │
│  3. Appelle handle_player_answer(data)                                            │
│                                                                                   │
│  async def handle_player_answer(self, data):                                      │
│    round_id = data["round_id"]                                                    │
│    answer = data["answer"]                                                        │
│    time_ms = data["answer_time_ms"]                                               │
│                                                                                   │
│    # Verifications :                                                              │
│    # - Le round est bien en cours ?                                               │
│    # - Alice n'a pas deja repondu ?                                               │
│    # - Le temps n'est pas ecoule ?                                                │
│                                                                                   │
│    # Calcul du score (fonction du temps de reponse)                               │
│    score = calculate_score(answer, correct_answer, time_ms)                       │
│                                                                                   │
│    # Sauvegarde en base (PostgreSQL)                                              │
│    await GameAnswer.objects.acreate(                                              │
│      player=alice, round=round, answer=answer, score=score                        │
│    )                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ channel_layer.group_send("game_ABC123", ...)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ REDIS (Channel Layer)                                                             │
│                                                                                   │
│  Broadcast du message a tous les membres du groupe "game_ABC123"                  │
│  → channel_alice, channel_bob, channel_charlie                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                     ▼
         Worker 1             Worker 2             Worker 3
        (Alice)               (Bob)               (Charlie)
              │                    │                     │
              ▼                    ▼                     ▼
     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
     │ Navigateur   │    │ Navigateur   │    │ Navigateur   │
     │ Alice        │    │ Bob          │    │ Charlie      │
     │              │    │              │    │              │
     │ Recoit :     │    │ Recoit :     │    │ Recoit :     │
     │ {            │    │ {            │    │ {            │
     │  type:       │    │  type:       │    │  type:       │
     │  "answer_    │    │  "answer_    │    │  "answer_    │
     │  received",  │    │  "received", │    │  "received", │
     │  player:     │    │  player:     │    │  player:     │
     │  "alice",    │    │  "alice",    │    │  "alice",    │
     │  score: 950  │    │  score: 950  │    │  score: 950  │
     │ }            │    │ }            │    │ }            │
     └──────────────┘    └──────────────┘    └──────────────┘
```

---

## GameConsumer — Messages du jeu

### Messages Client vers Serveur

Messages envoyes par le **navigateur** vers le **backend**.

| Type            | Description                                             | Payload                                |
| --------------- | ------------------------------------------------------- | -------------------------------------- |
| `player_join`   | Un joueur rejoint la salle                              | `{ room_code, display_name }`          |
| `start_game`    | L'hote demarre la partie                                | `{}` (seul l'hote peut envoyer ca)     |
| `player_answer` | Le joueur soumet sa reponse                             | `{ round_id, answer, answer_time_ms }` |
| `use_bonus`     | Le joueur active un bonus                               | `{ bonus_type, target_player? }`       |
| `player_ready`  | Le joueur indique qu'il est pret pour le prochain round | `{}`                                   |
| `send_reaction` | Le joueur envoie une reaction emoji                     | `{ reaction: "🎉" }`                    |
| `ping`          | Keep-alive (eviter le timeout de la connexion)          | `{}`                                   |

### Messages Serveur vers Client

Messages envoyes par le **backend** vers tous les navigateurs du groupe.

| Type              | Description                            | Payload                                                                       |
| ----------------- | -------------------------------------- | ----------------------------------------------------------------------------- |
| `player_joined`   | Un joueur vient de rejoindre           | `{ player, players_list, is_ready }`                                          |
| `player_left`     | Un joueur a quitte la salle            | `{ player_id, players_list }`                                                 |
| `game_starting`   | La partie va commencer (countdown)     | `{ countdown: 3 }`                                                            |
| `start_round`     | Debut d'un nouveau round               | `{ round_number, total_rounds, track_preview_url, question, choices?, mode }` |
| `answer_received` | Un joueur a repondu (confirmation)     | `{ player_id, answer_time_ms, is_correct? }`                                  |
| `end_round`       | Fin du round, revelation des resultats | `{ correct_answer, scores_delta, leaderboard }`                               |
| `bonus_activated` | Un bonus a ete active                  | `{ player_id, bonus_type, target_player? }`                                   |
| `next_round`      | Passage au round suivant               | `{ round_number, total_rounds }`                                              |
| `finish_game`     | Fin de la partie                       | `{ final_leaderboard, mvp, stats }`                                           |
| `error`           | Erreur (action invalide, etc.)         | `{ code, message }`                                                           |
| `pong`            | Reponse au ping                        | `{}`                                                                          |

### Exemple de message `start_round`

```json
{
  "type": "start_round",
  "payload": {
    "round_number": 3,
    "total_rounds": 10,
    "duration_seconds": 30,
    "mode": "classique",
    "track": {
      "preview_url": "https://cdns-preview.dzcdn.net/...",
      "duration_ms": 30000
    },
    "question": "Quel est le titre de ce morceau ?",
    "choices": [
      "Bohemian Rhapsody",
      "Don't Stop Me Now",
      "We Will Rock You",
      "Somebody to Love"
    ]
  }
}
```

### Exemple de message `end_round`

```json
{
  "type": "end_round",
  "payload": {
    "correct_answer": "Bohemian Rhapsody",
    "answers": [
      {
        "player_id": 1,
        "username": "alice",
        "answer": "Bohemian Rhapsody",
        "is_correct": true,
        "answer_time_ms": 4230,
        "score_earned": 950
      },
      {
        "player_id": 2,
        "username": "bob",
        "answer": "Don't Stop Me Now",
        "is_correct": false,
        "answer_time_ms": 8100,
        "score_earned": 0
      }
    ],
    "leaderboard": [
      { "player_id": 1, "username": "alice", "total_score": 2850 },
      { "player_id": 2, "username": "bob",   "total_score": 1900 }
    ]
  }
}
```

---

## NotificationConsumer

Le `NotificationConsumer` est un canal de notifications personnel. Contrairement au `GameConsumer` (qui est lie a une salle), chaque utilisateur connecte a un canal de notifications unique.

```
Alice (connectee) → /ws/notifications/ → NotificationConsumer
                                               │
                                    Groupe "notifications_1" (alice.id = 1)
                                               │
                             Recevoir notifications de :
                             - Succes debloques (depuis Celery)
                             - Invitations a rejoindre une partie
                             - Defis recus d'amis
                             - Alertes systeme (maintenance...)
```

### Messages recus par le client (serveur → client)

| Type                   | Description                      | Payload                                             |
| ---------------------- | -------------------------------- | --------------------------------------------------- |
| `achievement_unlocked` | Un succes vient d'etre debloque  | `{ achievement_id, name, description, icon }`       |
| `game_invitation`      | Un ami vous invite a une partie  | `{ from_player, room_code, game_mode, expires_at }` |
| `friend_request`       | Demande d'ami recue              | `{ from_player }`                                   |
| `system_message`       | Message systeme (maintenance...) | `{ level: "info"                                    | "warning", message }` |

---

## Rate limiting WebSocket

### Pourquoi limiter les WebSockets ?

Sans rate limiting, un client malveillant pourrait envoyer des milliers de messages par seconde pour saturer le serveur. C'est particulierement problematique pour les WebSockets car la connexion reste ouverte.

### Implementation : sliding window avec Lua dans Redis

Le rate limiting utilise un **script Lua** execute atomiquement dans Redis, implementant une fenetre glissante (sliding window) :

```lua
-- Script Lua : verifier si le client a depasse la limite
-- Parametre 1 : cle Redis (ex: "ratelimit:ws:alice:player_answer")
-- Parametre 2 : timestamp actuel en millisecondes
-- Parametre 3 : fenetre en millisecondes (ex: 1000 = 1 seconde)
-- Parametre 4 : limite max de messages

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

-- Supprimer les entrees trop anciennes (hors de la fenetre)
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Compter les messages dans la fenetre
local count = redis.call('ZCARD', key)

if count < limit then
    -- Sous la limite : autoriser et enregistrer
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, math.ceil(window / 1000))
    return 1  -- autorise
else
    return 0  -- refuse
end
```

### Limites configurees

| Type de message        | Limite      | Fenetre                              |
| ---------------------- | ----------- | ------------------------------------ |
| `player_answer`        | 1 message   | 5 secondes (1 reponse par round max) |
| `use_bonus`            | 3 messages  | 10 secondes                          |
| `send_reaction`        | 5 messages  | 5 secondes                           |
| `ping`                 | 1 message   | 30 secondes                          |
| Tous messages (global) | 30 messages | 1 seconde                            |

Si la limite est depassee, le consumer repond avec un message `error` de code `4029` (rate limited) et peut fermer la connexion si le comportement persiste.

---

## Gestion des deconnexions

### Deconnexion propre (joueur qui quitte volontairement)

```
Client          GameConsumer        Redis              Autres joueurs
   │                 │                 │                    │
   │ Ferme le WS     │                 │                    │
   │────────────────→│                 │                    │
   │                 │ group_discard   │                    │
   │                 │────────────────→│                    │
   │                 │                 │                    │
   │                 │ group_send "player_left"             │
   │                 │──────────────────────────────────────→
   │                 │                 │                    │
   │                 │ Marque le joueur comme deconnecte     │
   │                 │ dans la partie (PostgreSQL)           │
```

### Deconnexion abrupte (reseau coupe, navigateur ferme...)

Le comportement est identique, mais c'est Django Channels qui detecte la deconnexion (timeout sur le socket). Le consumer `disconnect()` est appele automatiquement.

### Reconnexion en cours de partie

Si un joueur se reconnecte avec le meme token a la meme salle :
1. Le consumer detecte que c'est une reconnexion (le joueur existe deja en base)
2. L'etat courant de la partie est envoye au client pour resynchronisation
3. Le joueur reprend la partie normalement

```python
async def connect(self):
    # ...
    game_player = await get_or_create_player(self.user, self.room_code)

    if game_player.is_reconnecting:
        # Envoyer l'etat complet de la partie pour resynchroniser
        await self.send_game_state()
    else:
        # Nouveau joueur : notifier tout le monde
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "player.joined", "player": ...}
        )
```
