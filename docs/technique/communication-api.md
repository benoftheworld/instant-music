# Communication Frontend / Backend — Documentation technique

## Vue d'ensemble

Le frontend React communique avec le backend Django via deux canaux :

| Canal         | Protocole  | Usage                           | Bibliothèque           |
| ------------- | ---------- | ------------------------------- | ---------------------- |
| **API REST**  | HTTP/HTTPS | CRUD, authentification, données | Axios + TanStack Query |
| **WebSocket** | WS/WSS     | Temps réel (jeu en cours)       | WebSocket natif        |

```
┌──────────────────────────────────────────┐
│              Frontend React               │
│                                           │
│  ┌─────────────┐    ┌──────────────────┐ │
│  │ TanStack     │    │  WebSocket       │ │
│  │ Query        │    │  Service         │ │
│  │ (useQuery,   │    │  (wsService)     │ │
│  │  useMutation)│    │                  │ │
│  └──────┬──────┘    └────────┬─────────┘ │
│         │                    │            │
│  ┌──────▼──────┐    ┌───────▼──────────┐ │
│  │ Axios        │    │  Native WS       │ │
│  │ (api.ts)     │    │  /ws/game/{code}/│ │
│  └──────┬──────┘    └────────┬─────────┘ │
└─────────┼────────────────────┼───────────┘
          │ HTTP               │ WebSocket
          ▼                    ▼
┌─────────────────────────────────────────┐
│              Nginx (reverse proxy)       │
│  /api/* → backend:8000                   │
│  /ws/*  → backend:8000 (Upgrade)         │
└─────────────────────────────────────────┘
          │                    │
          ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  Django REST      │  │  Django Channels  │
│  Framework        │  │  (ASGI)           │
└──────────────────┘  └──────────────────┘
```

---

## API REST (HTTP)

### Client Axios (`frontend/src/services/api.ts`)

Un singleton `ApiService` encapsule Axios avec deux intercepteurs :

#### Intercepteur de requête (ajout du token JWT)

```typescript
this.api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

Chaque requête HTTP inclut automatiquement le header `Authorization: Bearer <access_token>`.

#### Intercepteur de réponse (refresh automatique)

```typescript
this.api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const response = await axios.post('/api/auth/token/refresh/', {
        refresh: refreshToken,
      });
      localStorage.setItem('access_token', response.data.access);
      return this.api(originalRequest); // Rejeu de la requête originale
    }
  }
);
```

**Flux de refresh** :
1. Une requête reçoit un `401 Unauthorized`
2. Le refresh token est envoyé à `/api/auth/token/refresh/`
3. Le nouveau access token est stocké dans `localStorage`
4. La requête originale est rejouée avec le nouveau token
5. Si le refresh échoue → déconnexion et redirection vers `/login`

### Authentification JWT

| Endpoint                   | Méthode | Description                           | Token requis                     |
| -------------------------- | ------- | ------------------------------------- | -------------------------------- |
| `/api/auth/register/`      | POST    | Inscription                           | Non                              |
| `/api/auth/login/`         | POST    | Connexion (retourne access + refresh) | Non                              |
| `/api/auth/token/refresh/` | POST    | Renouvellement du access token        | Non (refresh token dans le body) |

**Durée de vie des tokens** :
- Access token : **60 minutes**
- Refresh token : **7 jours**

### Endpoints API principaux

| Ressource   | Endpoint                  | Méthodes   | Description                  |
| ----------- | ------------------------- | ---------- | ---------------------------- |
| Parties     | `/api/games/`             | GET, POST  | Liste et création de parties |
| Partie      | `/api/games/{room_code}/` | GET, PATCH | Détails et mise à jour       |
| Playlists   | `/api/playlists/search/`  | GET        | Recherche Deezer             |
| Utilisateur | `/api/users/me/`          | GET, PATCH | Profil courant               |
| Succès      | `/api/achievements/`      | GET        | Liste des succès             |
| Stats       | `/api/stats/leaderboard/` | GET        | Classement global            |
| Amis        | `/api/users/friends/`     | GET, POST  | Gestion des amis             |

### Documentation API auto-générée

DRF-Spectacular génère automatiquement la documentation :
- **Swagger UI** : `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc** : `http://localhost:8000/api/schema/redoc/`
- **Schema OpenAPI** : `http://localhost:8000/api/schema/`

---

## State Management (Zustand)

### AuthStore (`frontend/src/store/authStore.ts`)

```typescript
interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: AuthTokens) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}
```

- **Persistance** : Middleware `persist` sauvegarde dans `localStorage` (clé: `auth-storage`)
- **Synchronisation** : `setAuth()` stocke aussi les tokens dans `localStorage` pour l'intercepteur Axios
- **Déconnexion** : `logout()` nettoie `localStorage` et réinitialise l'état

### GameStore (`frontend/src/store/gameStore.ts`)

```typescript
interface GameState {
  currentGame: Game | null;
  setCurrentGame: (game: Game | null) => void;
  updateGame: (game: Partial<Game>) => void;
}
```

- **Non persisté** : La partie en cours n'est pas sauvegardée entre les sessions
- **Mise à jour partielle** : `updateGame()` permet de merger des champs sans écraser tout l'objet

---

## Data Fetching (TanStack Query)

TanStack Query (React Query) gère le cache côté client, la pagination, et la synchronisation des données serveur.

### Patron d'utilisation

```typescript
// Lecture de données (GET) — cache automatique
const { data: games, isLoading } = useQuery({
  queryKey: ['games'],
  queryFn: () => api.get('/games/').then(res => res.data),
});

// Mutation (POST/PATCH/DELETE) — invalidation du cache
const createGame = useMutation({
  mutationFn: (data) => api.post('/games/', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['games'] });
  },
});
```

### Avantages par rapport à des appels Axios directs

| Aspect        | Axios seul        | TanStack Query                       |
| ------------- | ----------------- | ------------------------------------ |
| Cache         | Manuel            | Automatique (stale-while-revalidate) |
| Loading state | `useState` manuel | `isLoading`, `isFetching` intégrés   |
| Erreurs       | try/catch manuel  | `isError`, `error` intégrés          |
| Refetch       | Manuel            | Auto (focus, interval, invalidation) |
| Déduplication | Non               | Oui (queryKey)                       |

---

## Flux de données complet : exemple « Rejoindre une partie »

```
Joueur                Frontend                   Backend                  Redis
  │                      │                          │                       │
  │ Clic "Rejoindre"     │                          │                       │
  ├─────────────────────►│                          │                       │
  │                      │ POST /api/games/{code}/  │                       │
  │                      │  join/ (Axios + JWT)      │                       │
  │                      ├─────────────────────────►│                       │
  │                      │                          │ Crée GamePlayer       │
  │                      │                          │ en base                │
  │                      │          200 OK          │                       │
  │                      │◄─────────────────────────┤                       │
  │                      │                          │                       │
  │                      │ setCurrentGame(data)      │                       │
  │                      │ (Zustand store)           │                       │
  │                      │                          │                       │
  │                      │ wsService.connect(code)   │                       │
  │                      ├─────────────WS───────────►                       │
  │                      │                          │ group_add(game_{code})│
  │                      │                          ├──────────────────────►│
  │                      │                          │                       │
  │                      │                          │ group_send(           │
  │                      │                          │   player_joined)      │
  │                      │                          ├──────────────────────►│
  │                      │                          │                       │
  │                      │◄──────WS: player_joined──┤◄──────────────────────┤
  │                      │                          │                       │
  │  UI mise à jour      │                          │                       │
  │◄─────────────────────┤                          │                       │
```

---

## Gestion des erreurs

### Côté API (HTTP)

| Code | Signification     | Action frontend                     |
| ---- | ----------------- | ----------------------------------- |
| 200  | Succès            | Affichage des données               |
| 400  | Validation erreur | Affichage des erreurs de formulaire |
| 401  | Token expiré      | Refresh automatique puis rejeu      |
| 403  | Interdit          | Message d'erreur                    |
| 404  | Non trouvé        | Redirection vers 404                |
| 503  | Maintenance       | Affichage page maintenance          |

### Côté WebSocket

| Situation                   | Comportement                                                   |
| --------------------------- | -------------------------------------------------------------- |
| Connexion échouée           | Reconnexion auto (backoff exponentiel, max 5 tentatives)       |
| Message invalide (non-JSON) | Log d'erreur, message ignoré                                   |
| Type de message inconnu     | Réponse `{"type": "error", "message": "Unknown message type"}` |
| Connexion perdue            | Événement `disconnect` émis, tentative de reconnexion          |
| Max reconnexions atteint    | Événement `reconnect_failed` émis                              |

---

## Configuration réseau

### Développement

```
Frontend (Vite dev server)  →  localhost:3000
  proxy /api/* → localhost:8000
  proxy /ws/*  → ws://localhost:8000

Backend (uvicorn)           →  localhost:8000
```

Le proxy Vite est configuré dans `vite.config.ts` pour éviter les problèmes CORS en dev.

### Production

```
Nginx :443 (TLS)
  ├── /         →  frontend:80   (nginx:alpine servant le build React)
  ├── /api/     →  backend:8000  (Gunicorn + uvicorn workers)
  ├── /ws/      →  backend:8000  (Upgrade HTTP → WebSocket)
  └── /admin/   →  backend:8000
```

Headers WebSocket configurés dans Nginx :
```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;  # 24h pour les connexions WS longues
}
```
