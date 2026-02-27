# Documentation technique -- WebSocket InstantMusic

> Documentation exhaustive de l'implementation WebSocket pour le jeu de quiz musical multijoueur en temps reel InstantMusic.

---

## Table des matieres

1. [Vue d'ensemble de l'architecture](#1-vue-densemble-de-larchitecture)
2. [Backend : GameConsumer (consumers.py)](#2-backend--gameconsumer-consumerspy)
3. [Service de diffusion (broadcast_service.py)](#3-service-de-diffusion-broadcast_servicepy)
4. [Frontend : WebSocketService (websocketService.ts)](#4-frontend--websocketservice-websocketservicets)
5. [Frontend : Hook useWebSocket (useWebSocket.ts)](#5-frontend--hook-usewebsocket-usewebsocketts)
6. [Diagrammes de sequence](#6-diagrammes-de-sequence)
7. [Metriques Prometheus](#7-metriques-prometheus)
8. [Securite](#8-securite)

---

## 1. Vue d'ensemble de l'architecture

### Stack technologique

| Composant     | Technologie                                           | Role                                     |
| ------------- | ----------------------------------------------------- | ---------------------------------------- |
| Serveur ASGI  | Django Channels 4.0                                   | Gestion des connexions WebSocket         |
| Channel Layer | `channels_redis.core.RedisChannelLayer`               | Bus de messages entre consumers          |
| Routage       | `ProtocolTypeRouter` + `URLRouter`                    | Aiguillage HTTP / WebSocket              |
| Securite      | `AuthMiddlewareStack` + `AllowedHostsOriginValidator` | Authentification et validation d'origine |
| Reverse proxy | Nginx                                                 | Terminaison TLS, upgrade HTTP vers WS    |
| Frontend      | WebSocket natif (API browser)                         | Client compatible Django Channels        |

### Application ASGI (`backend/config/asgi.py`)

Le point d'entree ASGI configure un `ProtocolTypeRouter` qui aiguille les requetes selon leur protocole :

```python
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from apps.games import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
    ),
})
```

**Chaine de middleware WebSocket** (de l'exterieur vers l'interieur) :

1. `AllowedHostsOriginValidator` -- verifie que l'en-tete `Origin` correspond a `ALLOWED_HOSTS`
2. `AuthMiddlewareStack` -- authentifie l'utilisateur via la session Django ou le token JWT
3. `URLRouter` -- route vers le consumer adequat selon l'URL

### Routage WebSocket (`backend/apps/games/routing.py`)

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_code>\w+)/$', consumers.GameConsumer.as_asgi()),
]
```

**Route unique** : `/ws/game/<room_code>/`

- `room_code` : code alphanuemerique identifiant la partie (ex. `ABCD1234`)
- Le consumer extrait ce parametre depuis `self.scope["url_route"]["kwargs"]["room_code"]`

### Channel Layer Redis

Configuration dans `backend/config/settings/base.py` :

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379/0")],
        },
    },
}
```

Chaque partie cree un **groupe Redis** nomme `game_{room_code}`. Tous les joueurs connectes a la meme partie sont membres du meme groupe, ce qui permet la diffusion de messages a tous les participants simultanement via `channel_layer.group_send()`.

### Flux reseau global

```
Client (navigateur)
    |
    | wss://benoftheworld.fr/ws/game/ABCD1234/
    |
    v
Nginx :443 (terminaison TLS)
    |
    | proxy_pass http://backend:8000
    | Upgrade: websocket
    | Connection: upgrade
    |
    v
Django Channels (Daphne/uvicorn)
    |
    | ProtocolTypeRouter → "websocket"
    | AllowedHostsOriginValidator
    | AuthMiddlewareStack
    | URLRouter → GameConsumer
    |
    v
GameConsumer
    |
    | channel_layer.group_add("game_ABCD1234", channel_name)
    | channel_layer.group_send(...)
    |
    v
Redis (Channel Layer)
    |
    | Pubsub vers tous les consumers du groupe
    |
    v
Tous les GameConsumer du groupe → send() vers chaque client
```

---

## 2. Backend : GameConsumer (`consumers.py`)

**Fichier** : `backend/apps/games/consumers.py`

`GameConsumer` herite de `AsyncWebsocketConsumer` (Django Channels). Il gere l'ensemble du cycle de vie WebSocket pour une partie.

### 2.1 Connexion (`connect`)

```python
async def connect(self):
    self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
    self.room_group_name = f"game_{self.room_code}"

    # Rejoindre le groupe Redis
    await self.channel_layer.group_add(
        self.room_group_name, self.channel_name
    )
    await self.accept()

    # Metriques Prometheus
    WS_CONNECTIONS_TOTAL.labels(action="connect").inc()
    WS_CONNECTIONS_ACTIVE.inc()

    # Confirmation de connexion
    await self.send(text_data=json.dumps({
        "type": "connection_established",
        "message": "Connected to game room",
    }))

    # Si l'utilisateur est authentifie : marquer comme connecte et diffuser
    user = self.scope.get("user")
    if user and user.is_authenticated:
        await self._set_player_connected(True)
        game_data = await self.get_game_data()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_join",
                "player": {"user": user.id, "username": user.username},
                "game_data": game_data,
            },
        )
```

**Etapes** :

1. Extraction du `room_code` depuis l'URL
2. Construction du nom de groupe : `game_{room_code}`
3. Ajout du channel au groupe Redis (`group_add`)
4. Acceptation de la connexion WebSocket
5. Incrementation des metriques Prometheus
6. Envoi d'un message de confirmation au client
7. Si l'utilisateur est authentifie :
   - Mise a jour du champ `is_connected` du `GamePlayer` en base
   - Recuperation des donnees completes de la partie (`get_game_data`)
   - Diffusion d'un evenement `player_joined` a tous les membres du groupe

### 2.2 Deconnexion (`disconnect`)

```python
async def disconnect(self, close_code):
    WS_CONNECTIONS_TOTAL.labels(action="disconnect").inc()
    WS_CONNECTIONS_ACTIVE.dec()

    await self.channel_layer.group_discard(
        self.room_group_name, self.channel_name
    )

    user = self.scope.get("user")
    if user and user.is_authenticated:
        await self._set_player_connected(False)
        game_data = await self.get_game_data()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_leave",
                "player": {"user": user.id, "username": user.username},
                "game_data": game_data,
            },
        )
```

**Etapes** :

1. Mise a jour des metriques (deconnexion)
2. Retrait du channel du groupe Redis (`group_discard`)
3. Si authentifie : marquer `is_connected = False` et diffuser `player_leave`

### 2.3 Reception de messages (`receive`)

Le `receive` joue le role de **routeur de messages**. Chaque message entrant est un objet JSON avec un champ `type` qui determine le handler a invoquer.

```python
async def receive(self, text_data):
    data = json.loads(text_data)
    message_type = data.get("type")

    WS_MESSAGES_TOTAL.labels(
        direction="inbound", message_type=message_type or "unknown"
    ).inc()

    if message_type == "player_join":
        await self.player_join(data)
    elif message_type == "player_answer":
        await self.player_answer(data)
    elif message_type == "start_game":
        await self.start_game(data)
    elif message_type == "start_round":
        await self.start_round(data)
    elif message_type == "end_round":
        await self.end_round(data)
    elif message_type == "next_round":
        await self.next_round(data)
    elif message_type == "finish_game":
        await self.finish_game(data)
    else:
        await self.send(text_data=json.dumps(
            {"type": "error", "message": "Unknown message type"}
        ))
```

En cas de JSON invalide, un message d'erreur `{"type": "error", "message": "Invalid JSON"}` est renvoye au client.

### 2.4 Messages entrants (client vers serveur)

| Type            | Description                                                             | Donnees attendues                              |
| --------------- | ----------------------------------------------------------------------- | ---------------------------------------------- |
| `player_join`   | Notification d'arrivee d'un joueur (mode legacy -- preferer l'API REST) | `player` (objet)                               |
| `player_answer` | Soumission d'une reponse par un joueur                                  | `player` (username), `answer`, `response_time` |
| `start_game`    | L'hote demarre la partie                                                | --                                             |
| `start_round`   | Demarrage d'un round                                                    | `round_data` (objet)                           |
| `end_round`     | Fin du round courant                                                    | `results` (objet)                              |
| `next_round`    | Passage au round suivant                                                | `round_data` (objet)                           |
| `finish_game`   | Fin de la partie                                                        | `results` (objet)                              |

**Exemple : soumission de reponse (`player_answer`)**

```python
async def player_answer(self, data):
    player_username = data.get("player")
    answer = data.get("answer")
    response_time = data.get("response_time", 0)

    # Diffuser que le joueur a repondu (sans reveler si c'est correct)
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "broadcast_player_answer",
            "player": player_username,
            "answered": True,
        },
    )
```

> **Note importante** : La verification de la reponse (correcte/incorrecte) et le calcul du score se font cote serveur via l'API REST (`GameService.submit_answer`), pas via le WebSocket. Le WebSocket ne diffuse que le fait qu'un joueur a repondu, sans reveler le resultat.

### 2.5 Messages sortants (serveur vers clients)

Les handlers de diffusion (`broadcast_*`) recoivent les evenements du channel layer et les transmettent au client via `self.send()`.

| Handler                   | Type envoye au client | Contenu                                                    |
| ------------------------- | --------------------- | ---------------------------------------------------------- |
| `broadcast_player_join`   | `player_joined`       | `player` (donnees joueur) + `game_data` (etat complet)     |
| `broadcast_player_leave`  | `player_leave`        | `player` + `game_data`                                     |
| `broadcast_game_update`   | `game_updated`        | `game_data`                                                |
| `broadcast_player_answer` | `player_answered`     | `player` (username) + `answered` (boolean)                 |
| `broadcast_game_start`    | `game_started`        | `game_data`                                                |
| `broadcast_round_start`   | `round_started`       | `round_data`                                               |
| `broadcast_round_end`     | `round_ended`         | `results` (correct_answer, player_scores, updated_players) |
| `broadcast_next_round`    | `next_round`          | `round_data` + `updated_players` (optionnel)               |
| `broadcast_game_finish`   | `game_finished`       | `results` (donnees finales de la partie)                   |

**Exemple : diffusion de fin de round**

```python
async def broadcast_round_end(self, event):
    await self.send(text_data=json.dumps(
        {"type": "round_ended", "results": event["results"]}
    ))
```

Le contenu de `results` pour un `round_ended` est structure ainsi :

```json
{
    "type": "round_ended",
    "results": {
        "correct_answer": "Bohemian Rhapsody",
        "round_data": { ... },
        "player_scores": {
            "alice": {"points_earned": 95, "is_correct": true, "response_time": 3.2},
            "bob": {"points_earned": 0, "is_correct": false, "response_time": 12.1}
        },
        "updated_players": [
            {"id": 1, "user": 42, "username": "alice", "score": 295, "rank": 1, ...},
            {"id": 2, "user": 43, "username": "bob", "score": 120, "rank": 2, ...}
        ]
    }
}
```

### 2.6 Methodes utilitaires

#### `get_game_data()`

Methode decoree avec `@database_sync_to_async` qui recupere l'ensemble des donnees de la partie depuis la base de donnees. Retourne un dictionnaire contenant :

- Identifiant, code de salle, hote, mode, statut
- Configuration de la partie (max_players, playlist_id, answer_mode, guess_target, etc.)
- Liste complete des joueurs avec score, rang, statut de connexion et URL d'avatar
- Horodatages (creation, demarrage, fin)

#### `_set_player_connected(connected: bool)`

Met a jour le champ `is_connected` du `GamePlayer` associe a l'utilisateur courant dans la partie. Utilise `@database_sync_to_async` pour acceder a l'ORM Django depuis le contexte asynchrone.

---

## 3. Service de diffusion (`broadcast_service.py`)

**Fichier** : `backend/apps/games/broadcast_service.py`

Ce module centralise la logique de diffusion WebSocket utilisable depuis un contexte **synchrone** (vues DRF, services Django). Il utilise `async_to_sync` pour envoyer des messages au channel layer Redis depuis du code synchrone.

### 3.1 Principe de fonctionnement

```
Vue DRF (synchrone)
    |
    | broadcast_round_start(room_code, round_obj)
    |
    v
broadcast_service.py
    |
    | async_to_sync(channel_layer.group_send)(
    |     "game_{room_code}",
    |     {"type": "broadcast_round_start", "round_data": {...}}
    | )
    |
    v
Redis Channel Layer
    |
    v
GameConsumer.broadcast_round_start(event)
    |
    v
WebSocket → client
```

### 3.2 Fonctions publiques

| Fonction                 | Signature                             | Description                                                           |
| ------------------------ | ------------------------------------- | --------------------------------------------------------------------- |
| `broadcast_player_join`  | `(room_code, player_data, game_data)` | Notifie qu'un joueur a rejoint la salle                               |
| `broadcast_player_leave` | `(room_code, player_data, game_data)` | Notifie qu'un joueur a quitte la salle                                |
| `broadcast_game_update`  | `(room_code, game_data)`              | Diffuse une mise a jour generale de l'etat de la partie               |
| `broadcast_round_start`  | `(room_code, round_obj)`              | Diffuse le demarrage d'un round (serialise via `GameRoundSerializer`) |
| `broadcast_round_end`    | `(room_code, round_obj, game)`        | Diffuse la fin d'un round avec les resultats detailles                |
| `broadcast_next_round`   | `(room_code, round_obj, game)`        | Diffuse le passage au round suivant avec les scores mis a jour        |
| `broadcast_game_finish`  | `(room_code, game)`                   | Diffuse la fin de la partie avec les resultats finaux                 |

### 3.3 Serialisation des donnees

Les donnees sont serialisees via les serializers DRF (`GameRoundSerializer`, `GameSerializer`) puis converties en dictionnaires JSON-safe grace a `JSONRenderer` :

```python
def _serialize_to_dict(serializer) -> dict:
    raw = JSONRenderer().render(serializer.data)
    return json.loads(raw)
```

### 3.4 Construction des scores et classements

**`_build_player_scores(round_obj)`** -- construit le detail des scores par joueur pour un round donne :

```python
{
    "alice": {"points_earned": 95, "is_correct": true, "response_time": 3.2},
    "bob": {"points_earned": 0, "is_correct": false, "response_time": 12.1}
}
```

**`_build_updated_players(game)`** -- construit la liste ordonnee (par score decroissant) de tous les joueurs :

```python
[
    {"id": 1, "user": 42, "username": "alice", "score": 295, "rank": 1, "is_connected": true, "avatar": "/media/avatars/alice.jpg"},
    {"id": 2, "user": 43, "username": "bob", "score": 120, "rank": 2, "is_connected": true, "avatar": null}
]
```

### 3.5 Exemple d'utilisation dans une vue DRF

```python
# Dans une action de GameViewSet (contexte synchrone)
from apps.games.broadcast_service import broadcast_round_end

def end_current_round(self, request, pk=None):
    game = self.get_object()
    round_obj = game_service.end_round(current_round)
    # ... logique metier ...
    broadcast_round_end(game.room_code, round_obj, game)
    return Response(...)
```

---

## 4. Frontend : WebSocketService (`websocketService.ts`)

**Fichier** : `frontend/src/services/websocketService.ts`

Service singleton gerant la connexion WebSocket cote client. Utilise l'**API WebSocket native du navigateur** (pas Socket.IO), compatible directement avec Django Channels.

### 4.1 Architecture

```typescript
export class WebSocketService {
    private socket: WebSocket | null = null;
    private roomCode: string | null = null;
    private listeners: Map<string, Set<MessageCallback>> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    private intentionalDisconnect = false;
    private connectId = 0;
    // ...
}

export const wsService = new WebSocketService();
```

**Caracteristiques cles** :

- **Singleton exporte** : `wsService` est une instance unique partagee par toute l'application
- **Architecture evenementielle** : `Map<string, Set<callback>>` pour l'abonnement aux evenements
- **Reconnexion automatique** avec backoff exponentiel
- **Generation de `connectId`** pour ignorer les callbacks obsoletes d'anciennes connexions

### 4.2 URL de connexion

```typescript
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';
// URL finale : ws://host/ws/game/{roomCode}/
```

En production avec TLS : `wss://benoftheworld.fr/ws/game/{roomCode}/`

### 4.3 Methodes publiques

#### `connect(roomCode: string): Promise<void>`

Etablit la connexion WebSocket vers la salle de jeu.

```typescript
connect(roomCode: string): Promise<void> {
    this._cleanupSocket();        // Nettoyer toute connexion existante
    this.roomCode = roomCode;
    this.reconnectAttempts = 0;
    this.intentionalDisconnect = false;
    const currentConnectId = ++this.connectId;

    const url = `${WS_BASE_URL}/ws/game/${roomCode}/`;
    return new Promise((resolve, reject) => {
        this.socket = new WebSocket(url);
        // ... handlers onopen, onerror, onclose, onmessage
    });
}
```

**Precautions** :

- Avant chaque connexion, toute socket precedente est nettoyee via `_cleanupSocket()`
- Les timers de reconnexion en cours sont annules
- Un `connectId` est incremente pour invalider les callbacks des anciennes connexions

#### `disconnect(): void`

Deconnexion intentionnelle. Nettoie toutes les ressources.

```typescript
disconnect(): void {
    this.intentionalDisconnect = true;
    this.connectId++;                    // Invalider les callbacks en attente
    // Annuler les timers de reconnexion
    if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
    }
    this.roomCode = null;
    this._cleanupSocket();
    this.listeners.clear();              // Supprimer tous les abonnements
}
```

#### `send(message: WebSocketMessage): void`

Envoie un message JSON au serveur. Verifie que la socket est ouverte avant l'envoi.

```typescript
send(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(message));
    }
}
```

#### `on(event, callback)` / `off(event, callback)`

Systeme d'abonnement/desabonnement aux evenements.

```typescript
// S'abonner a un type d'evenement
wsService.on('player_joined', (data) => {
    console.log('Nouveau joueur :', data.player);
});

// Se desabonner
wsService.off('player_joined', callback);
wsService.off('player_joined');  // Supprimer tous les listeners pour cet evenement
```

#### `isConnected(): boolean`

Retourne `true` si la socket est ouverte et operationnelle.

### 4.4 Gestion des messages entrants

```typescript
this.socket.onmessage = (event) => {
    if (currentConnectId !== this.connectId) return;  // Ignorer si stale

    const data = JSON.parse(event.data) as WebSocketMessage;

    // Emettre vers les listeners generiques
    this._emitEvent('message', data);

    // Emettre vers les listeners specifiques au type
    if (data.type) {
        this._emitEvent(data.type, data);
    }
};
```

Chaque message est donc emis deux fois :
1. Sur le canal `'message'` (catch-all)
2. Sur le canal correspondant au `type` du message (ex. `'player_joined'`, `'round_started'`)

### 4.5 Reconnexion automatique

La reconnexion utilise un **backoff exponentiel** avec les parametres suivants :

| Parametre          | Valeur                              |
| ------------------ | ----------------------------------- |
| Delai initial      | 1 seconde                           |
| Delai maximum      | 10 secondes                         |
| Tentatives maximum | 5                                   |
| Formule            | `min(1000 * 2^tentative, 10000)` ms |

```typescript
private _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this._emitEvent('reconnect_failed', {});
        return;
    }
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    this.reconnectTimeout = setTimeout(() => {
        if (this.roomCode) {
            this.connect(this.roomCode).catch(console.error);
        }
    }, delay);
}
```

**Comportement par tentative** :

| Tentative | Delai avant reconnexion                 |
| --------- | --------------------------------------- |
| 1         | 2 000 ms                                |
| 2         | 4 000 ms                                |
| 3         | 8 000 ms                                |
| 4         | 10 000 ms (plafond)                     |
| 5         | 10 000 ms (plafond)                     |
| > 5       | Abandon, emission de `reconnect_failed` |

La reconnexion n'est **pas declenchee** en cas de deconnexion intentionnelle (`intentionalDisconnect = true`).

### 4.6 Nettoyage de socket (`_cleanupSocket`)

```typescript
private _cleanupSocket() {
    if (this.socket) {
        // Detacher tous les handlers pour eviter les evenements fantomes
        this.socket.onopen = null;
        this.socket.onerror = null;
        this.socket.onclose = null;
        this.socket.onmessage = null;

        if (this.socket.readyState === WebSocket.OPEN ||
            this.socket.readyState === WebSocket.CONNECTING) {
            this.socket.close(1000, 'Cleanup');
        }
        this.socket = null;
    }
}
```

Ce nettoyage est essentiel pour eviter que des handlers d'anciennes sockets ne declenchent des actions inattendues apres une reconnexion.

---

## 5. Frontend : Hook useWebSocket (`useWebSocket.ts`)

**Fichier** : `frontend/src/hooks/useWebSocket.ts`

Hook React encapsulant `wsService` pour une utilisation declarative dans les composants.

### 5.1 Interface

```typescript
export const useWebSocket = (roomCode: string | undefined) => {
    // ...
    return {
        sendMessage,    // (message: WebSocketMessage) => void
        onMessage,      // (event: string, callback) => () => void  (retourne une fonction de cleanup)
        isConnected,    // boolean
    };
};
```

### 5.2 Implementation

```typescript
export const useWebSocket = (roomCode: string | undefined) => {
    const [connected, setConnected] = useState(false);
    const mountedRef = useRef(true);

    useEffect(() => {
        mountedRef.current = true;
        if (!roomCode) return;

        const connect = async () => {
            try {
                await wsService.connect(roomCode);
                if (mountedRef.current) {
                    setConnected(true);
                }
            } catch (error) {
                console.error('Failed to connect to WebSocket:', error);
            }
        };

        connect();

        return () => {
            mountedRef.current = false;
            setConnected(false);
            wsService.disconnect();
        };
    }, [roomCode]);

    const sendMessage = useCallback((message: WebSocketMessage) => {
        wsService.send(message);
    }, []);

    const onMessage = useCallback((event: string, callback: (data: any) => void) => {
        wsService.on(event, callback);
        return () => wsService.off(event, callback);
    }, []);

    return { sendMessage, onMessage, isConnected: connected };
};
```

### 5.3 Cycle de vie

1. **Montage** : si `roomCode` est defini, connexion automatique via `wsService.connect()`
2. **Mise a jour** : si `roomCode` change, deconnexion de l'ancienne salle puis connexion a la nouvelle
3. **Demontage** : deconnexion propre via `wsService.disconnect()`

### 5.4 Protection contre le memory leak

- `mountedRef` empeche les mises a jour d'etat (`setConnected`) apres le demontage du composant
- `onMessage` retourne une fonction de cleanup pour le desabonnement automatique

### 5.5 Exemple d'utilisation dans un composant

```tsx
function GameRoom({ roomCode }: { roomCode: string }) {
    const { sendMessage, onMessage, isConnected } = useWebSocket(roomCode);

    useEffect(() => {
        const cleanup = onMessage('player_joined', (data) => {
            console.log('Joueur rejoint :', data.player.username);
        });
        return cleanup;
    }, [onMessage]);

    const handleAnswer = (answer: string) => {
        sendMessage({
            type: 'player_answer',
            player: currentUser.username,
            answer,
            response_time: elapsedTime,
        });
    };

    return (
        <div>
            <p>Statut : {isConnected ? 'Connecte' : 'Deconnecte'}</p>
            {/* ... interface du jeu ... */}
        </div>
    );
}
```

---

## 6. Diagrammes de sequence

### 6.1 Flux de connexion

```
Client                 Nginx                 Django Channels          GameConsumer             Redis
  |                      |                        |                       |                      |
  |-- GET /ws/game/XYZ/ -->                       |                       |                      |
  |   Upgrade: websocket |                        |                       |                      |
  |   Connection: upgrade|                        |                       |                      |
  |                      |                        |                       |                      |
  |                      |-- proxy_pass --------->|                       |                      |
  |                      |   Upgrade: websocket   |                       |                      |
  |                      |   Connection: upgrade  |                       |                      |
  |                      |                        |                       |                      |
  |                      |                        |-- AllowedHosts ------>|                      |
  |                      |                        |   check Origin        |                      |
  |                      |                        |                       |                      |
  |                      |                        |-- AuthMiddleware ---->|                      |
  |                      |                        |   resolve user        |                      |
  |                      |                        |                       |                      |
  |                      |                        |-- URLRouter -------->|                      |
  |                      |                        |   match /ws/game/XYZ/ |                      |
  |                      |                        |                       |                      |
  |                      |                        |                       |-- group_add -------->|
  |                      |                        |                       |   "game_XYZ"         |
  |                      |                        |                       |                      |
  |                      |                        |                       |-- accept() --------->|
  |<-- 101 Switching Protocols --------------------|                       |                      |
  |                      |                        |                       |                      |
  |<-- {"type": "connection_established"} ---------|                       |                      |
  |                      |                        |                       |                      |
  |                      |                        |                       |-- set_player_connected(True)
  |                      |                        |                       |                      |
  |                      |                        |                       |-- group_send ------->|
  |                      |                        |                       |   broadcast_player_join
  |                      |                        |                       |                      |
  |<-- {"type": "player_joined", ...} ------------|                       |<------ pubsub ------|
  |                      |                        |                       |                      |
```

### 6.2 Flux d'arrivee d'un joueur

```
Nouveau joueur          API REST               broadcast_service        Redis              Autres joueurs
  |                       |                        |                      |                      |
  |-- POST /api/games/    |                        |                      |                      |
  |   XYZ/join/ --------->|                        |                      |                      |
  |                       |                        |                      |                      |
  |                       |-- GamePlayer.create -->|                      |                      |
  |                       |                        |                      |                      |
  |                       |-- broadcast_player_join(room_code, ...) ----->|                      |
  |                       |   async_to_sync(       |                      |                      |
  |                       |     group_send)        |                      |                      |
  |                       |                        |                      |                      |
  |<-- 200 OK ------------|                        |                      |                      |
  |                       |                        |                      |                      |
  |                       |                        |                      |-- pubsub ----------->|
  |                       |                        |                      |   broadcast_player_  |
  |                       |                        |                      |   join               |
  |                       |                        |                      |                      |
  |                       |                        |                      |                [GameConsumer]
  |                       |                        |                      |                      |
  |                       |                        |                      |   <-- {"type": "player_joined",
  |                       |                        |                      |        "player": {...},
  |                       |                        |                      |        "game_data": {...}}
  |                       |                        |                      |                      |
  |-- wsService.connect(XYZ) ----------------------|--------------------->|                      |
  |                       |                        |                      |                      |
  |<-- {"type": "connection_established"} ---------|                      |                      |
  |<-- {"type": "player_joined", ...} -------------|<------ pubsub ------|                      |
  |                       |                        |                      |                      |
```

### 6.3 Flux de soumission de reponse

```
Joueur A               WebSocket              GameConsumer             Redis               Joueur B
  |                       |                       |                      |                      |
  |-- {"type":            |                       |                      |                      |
  |    "player_answer",   |                       |                      |                      |
  |    "player": "alice", |                       |                      |                      |
  |    "answer": "...",   |                       |                      |                      |
  |    "response_time": 3.2}                      |                      |                      |
  |                       |                       |                      |                      |
  |                       |-- receive(data) ----->|                      |                      |
  |                       |                       |                      |                      |
  |                       |                       |-- WS_MESSAGES_TOTAL  |                      |
  |                       |                       |   .inc() (inbound)   |                      |
  |                       |                       |                      |                      |
  |                       |                       |-- group_send ------->|                      |
  |                       |                       |   "broadcast_player_ |                      |
  |                       |                       |    answer"           |                      |
  |                       |                       |                      |                      |
  |                       |                       |                      |-- pubsub ----------->|
  |                       |                       |                      |                      |
  |<-- {"type": "player_answered",                |                      |                      |
  |     "player": "alice",|                       |<------ pubsub ------|                      |
  |     "answered": true} |                       |                      |                      |
  |                       |                       |                      | {"type": "player_answered",
  |                       |                       |                      |  "player": "alice",  |
  |                       |                       |                      |  "answered": true} ->|
  |                       |                       |                      |                      |
  |-- POST /api/games/XYZ/answer/ (API REST) -----|                      |                      |
  |   (verification + scoring cote serveur)       |                      |                      |
  |<-- 200 {"is_correct": true, "points": 95} ----|                      |                      |
  |                       |                       |                      |                      |
```

> **Point cle** : Le WebSocket diffuse uniquement la notification `player_answered` (le joueur a repondu). La verification de la reponse et le calcul du score transitent par l'API REST, ce qui empeche toute triche cote client.

### 6.4 Cycle de vie d'un round

```
Hote                  API REST           broadcast_service       Redis            Tous les joueurs
  |                      |                      |                   |                      |
  |== DEMARRAGE DU ROUND ==========================================|======================|
  |                      |                      |                   |                      |
  |-- POST /api/games/   |                      |                   |                      |
  |   XYZ/start/ ------->|                      |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- GameService        |                   |                      |
  |                       |   .start_round()     |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- broadcast_round_start(room, round) -->|                      |
  |                       |                      |                   |                      |
  |                       |                      |                   |-- pubsub ----------->|
  |                       |                      |                   |                      |
  |<-- 200 OK ------------|                      |                   | {"type":"round_started",
  |                       |                      |                   |  "round_data":{...}} |
  |                       |                      |                   |                      |
  |== JOUEURS REPONDENT ==========================================|======================|
  |                       |                      |                   |                      |
  |                       |                      |                   | (cf. diagramme 6.3)  |
  |                       |                      |                   |                      |
  |== FIN DU ROUND ================================================|======================|
  |                       |                      |                   |                      |
  |-- POST /api/games/    |                      |                   |                      |
  |   XYZ/end_round/ ---->|                      |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- GameService        |                   |                      |
  |                       |   .end_round()       |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- broadcast_round_end(room, round, game)|                      |
  |                       |                      |                   |                      |
  |                       |                      |                   |-- pubsub ----------->|
  |                       |                      |                   |                      |
  |<-- 200 OK ------------|                      |                   | {"type":"round_ended",
  |                       |                      |                   |  "results": {        |
  |                       |                      |                   |    "correct_answer",  |
  |                       |                      |                   |    "player_scores",   |
  |                       |                      |                   |    "updated_players"  |
  |                       |                      |                   |  }}                  |
  |                       |                      |                   |                      |
  |== ROUND SUIVANT ===============================================|======================|
  |                       |                      |                   |                      |
  |-- POST /api/games/    |                      |                   |                      |
  |   XYZ/next_round/ --->|                      |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- GameService        |                   |                      |
  |                       |   .start_round()     |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- broadcast_next_round(room, round, game)                      |
  |                       |                      |                   |                      |
  |                       |                      |                   |-- pubsub ----------->|
  |                       |                      |                   |                      |
  |<-- 200 OK ------------|                      |                   | {"type":"next_round", |
  |                       |                      |                   |  "round_data":{...}, |
  |                       |                      |                   |  "updated_players":  |
  |                       |                      |                   |  [...]}              |
  |                       |                      |                   |                      |
  |== FIN DE PARTIE (dernier round) ===============================|======================|
  |                       |                      |                   |                      |
  |-- POST /api/games/    |                      |                   |                      |
  |   XYZ/finish/ ------->|                      |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- GameService        |                   |                      |
  |                       |   .finish_game()     |                   |                      |
  |                       |                      |                   |                      |
  |                       |-- broadcast_game_finish(room, game) --->|                      |
  |                       |                      |                   |                      |
  |                       |                      |                   |-- pubsub ----------->|
  |                       |                      |                   |                      |
  |<-- 200 OK ------------|                      |                   | {"type":"game_finished",
  |                       |                      |                   |  "results":{...}}    |
  |                       |                      |                   |                      |
```

---

## 7. Metriques Prometheus

**Fichier** : `backend/apps/core/prometheus_metrics.py`

Trois metriques Prometheus sont dediees au suivi des connexions et messages WebSocket :

### 7.1 `instantmusic_ws_connections_total` (Counter)

Compteur du nombre total de connexions et deconnexions WebSocket.

| Label    | Valeurs possibles       | Description   |
| -------- | ----------------------- | ------------- |
| `action` | `connect`, `disconnect` | Type d'action |

**Instrumentation** :

```python
# Dans GameConsumer.connect()
WS_CONNECTIONS_TOTAL.labels(action="connect").inc()

# Dans GameConsumer.disconnect()
WS_CONNECTIONS_TOTAL.labels(action="disconnect").inc()
```

### 7.2 `instantmusic_ws_connections_active` (Gauge)

Jauge du nombre de connexions WebSocket actuellement ouvertes.

```python
# Connexion
WS_CONNECTIONS_ACTIVE.inc()

# Deconnexion
WS_CONNECTIONS_ACTIVE.dec()
```

### 7.3 `instantmusic_ws_messages_total` (Counter)

Compteur du nombre total de messages WebSocket recus (entrants).

| Label          | Valeurs possibles                                                                                                | Description          |
| -------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------- |
| `direction`    | `inbound`                                                                                                        | Direction du message |
| `message_type` | `player_join`, `player_answer`, `start_game`, `start_round`, `end_round`, `next_round`, `finish_game`, `unknown` | Type de message      |

**Instrumentation** :

```python
# Dans GameConsumer.receive()
WS_MESSAGES_TOTAL.labels(
    direction="inbound",
    message_type=message_type or "unknown"
).inc()
```

### 7.4 Requetes PromQL utiles

```promql
# Nombre de connexions WebSocket actives
instantmusic_ws_connections_active

# Taux de connexions par seconde (fenetre 5 min)
rate(instantmusic_ws_connections_total{action="connect"}[5m])

# Repartition des types de messages entrants
rate(instantmusic_ws_messages_total{direction="inbound"}[5m])

# Ratio connexions/deconnexions
rate(instantmusic_ws_connections_total{action="connect"}[5m])
/
rate(instantmusic_ws_connections_total{action="disconnect"}[5m])
```

---

## 8. Securite

### 8.1 Authentification des connexions WebSocket

L'`AuthMiddlewareStack` de Django Channels authentifie les connexions WebSocket en utilisant :

1. **Session Django** : le cookie `sessionid` est transmis automatiquement par le navigateur lors du handshake HTTP initial
2. **Token JWT** : pour les clients qui n'ont pas de session, le token peut etre passe via un parametre de requete ou un header personnalise

Le middleware peuple `self.scope["user"]` avec l'utilisateur Django authentifie. Si l'utilisateur n'est pas authentifie, `scope["user"]` est une instance `AnonymousUser`.

```python
# Dans le consumer
user = self.scope.get("user")
if user and user.is_authenticated:
    # Utilisateur authentifie
    await self._set_player_connected(True)
```

### 8.2 Validation de l'origine

L'`AllowedHostsOriginValidator` verifie que l'en-tete `Origin` de la requete WebSocket correspond a la liste `ALLOWED_HOSTS` definie dans les settings Django :

```python
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
```

Cela empeche les sites tiers d'ouvrir des connexions WebSocket vers le serveur (protection contre le Cross-Site WebSocket Hijacking).

### 8.3 Configuration Nginx pour WebSocket

L'upgrade HTTP vers WebSocket est gere par Nginx via la configuration suivante :

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

**Points importants** :

- `proxy_http_version 1.1` : obligatoire pour le protocole WebSocket
- `Upgrade` et `Connection` : en-tetes necessaires a l'upgrade du protocole
- `proxy_read_timeout 86400` : timeout de 24 heures pour eviter la fermeture prematuree des connexions longue duree
- `X-Forwarded-Proto` : transmet le protocole original (HTTPS) au backend

### 8.4 TLS en production

En production, toutes les connexions utilisent `wss://` (WebSocket Secure) :

1. Le client se connecte a `wss://benoftheworld.fr/ws/game/{roomCode}/`
2. Nginx termine la connexion TLS avec un certificat Let's Encrypt
3. La connexion interne entre Nginx et le backend reste en `ws://` (reseau Docker prive)

```nginx
# Certificats SSL
ssl_certificate /etc/letsencrypt/live/benoftheworld.fr/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/benoftheworld.fr/privkey.pem;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
```

### 8.5 En-tetes de securite

Nginx ajoute des en-tetes de securite HTTP sur toutes les reponses :

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### 8.6 Separation WebSocket / API REST pour la securite du jeu

La soumission de reponses illustre bien cette separation :

- **WebSocket** : diffuse uniquement `player_answered` (le joueur a repondu, sans reveler le resultat)
- **API REST** : recoit la reponse via `POST /api/games/{id}/answer/`, effectue la verification cote serveur et retourne le resultat au joueur concernee

Cette architecture empeche un client malveillant d'intercepter les reponses correctes via le canal WebSocket, car la verification est strictement cote serveur.

---

## Annexe : Recapitulatif des fichiers

| Fichier              | Chemin                                      | Role                                              |
| -------------------- | ------------------------------------------- | ------------------------------------------------- |
| Configuration ASGI   | `backend/config/asgi.py`                    | Point d'entree ASGI, routage protocole            |
| Routage WebSocket    | `backend/apps/games/routing.py`             | Definition des routes WebSocket                   |
| Consumer             | `backend/apps/games/consumers.py`           | Gestion des connexions et messages WS             |
| Service de diffusion | `backend/apps/games/broadcast_service.py`   | Diffusion depuis le contexte synchrone (vues DRF) |
| Metriques Prometheus | `backend/apps/core/prometheus_metrics.py`   | Definition des metriques WS                       |
| Service de jeu       | `backend/apps/games/services.py`            | Logique metier (scoring, rounds, etc.)            |
| Client WebSocket     | `frontend/src/services/websocketService.ts` | Service singleton WS cote client                  |
| Hook React           | `frontend/src/hooks/useWebSocket.ts`        | Hook React pour les composants                    |
| Configuration Nginx  | `_devops/nginx/nginx.conf`                  | Reverse proxy et upgrade WS                       |
| Settings Django      | `backend/config/settings/base.py`           | Configuration channel layer Redis                 |
