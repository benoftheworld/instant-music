# Communication Frontend ↔ Backend — InstantMusic

## Vue d'ensemble

Le frontend communique avec le backend via **deux canaux distincts** :

1. **HTTP REST** (Axios + TanStack Query) — pour les opérations CRUD classiques (créer une partie, récupérer le profil, acheter un bonus...)
2. **WebSocket** (Django Channels) — pour les échanges temps réel pendant le jeu (questions, réponses, scores...)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
│                                                                     │
│   ┌──────────────┐          ┌────────────────────────────────┐      │
│   │  Composants  │          │    WebSocket (jeu temps réel)  │      │
│   │   React      │          │  useWebSocket / useGameWebSocket│      │
│   └──────┬───────┘          └───────────────┬────────────────┘      │
│          │                                  │                       │
│   ┌──────▼───────────────┐                  │ ws://                 │
│   │  TanStack Query      │                  │                       │
│   │  (cache + états)     │                  │                       │
│   └──────┬───────────────┘                  │                       │
│          │                                  │                       │
│   ┌──────▼───────────────┐                  │                       │
│   │  Axios (api.ts)      │                  │                       │
│   │  + intercepteurs JWT │                  │                       │
│   └──────┬───────────────┘                  │                       │
└──────────┼──────────────────────────────────┼─────────────────────┘
           │ HTTPS/HTTP                        │ WSS/WS
           ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND                                     │
│                                                                     │
│   ┌──────────────────┐    ┌──────────────────────────────────┐      │
│   │  Django REST API │    │  Django Channels WebSocket       │      │
│   │  /api/...        │    │  /ws/game/<room>/                │      │
│   └──────────────────┘    └──────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Axios — Instance HTTP centralisée (`services/api.ts`)

### Qu'est-ce qu'Axios ?

Axios est une bibliothèque JavaScript pour faire des **requêtes HTTP** (GET, POST, PUT, DELETE). Elle est plus ergonomique que le `fetch` natif du navigateur car elle :
- Parse automatiquement le JSON
- Gère les erreurs HTTP (codes 4xx/5xx)
- Permet d'ajouter des **intercepteurs** (code exécuté avant/après chaque requête)

### Configuration de l'instance

```typescript
// services/api.ts
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { tokenService } from './tokenService'

// Création d'une instance avec une URL de base
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 secondes max par requête
})

export default api
```

### Intercepteur de requête — Ajout automatique du JWT

L'intercepteur s'exécute **avant** chaque requête et injecte automatiquement le token JWT dans le header `Authorization`. Ainsi, aucun service n'a besoin de gérer le header manuellement.

```typescript
// Intercepteur de REQUÊTE : s'exécute avant chaque appel HTTP
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenService.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config // La requête part avec le header injecté
  },
  (error) => Promise.reject(error)
)
```

### Intercepteur de réponse — Refresh automatique du token

Le token JWT d'accès a une durée de vie courte (ex: 15 minutes). Quand il expire, le backend répond `401 Unauthorized`. L'intercepteur intercepte ce cas et **renouvelle automatiquement** le token avant de relancer la requête originale.

```typescript
// Intercepteur de RÉPONSE : s'exécute après chaque réponse HTTP
api.interceptors.response.use(
  (response) => response, // Succès : on laisse passer

  async (error) => {
    const originalRequest = error.config

    // Si 401 et pas déjà en train de retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true // Marquer pour éviter boucle infinie

      try {
        // Tenter de rafraîchir le token
        const newAccessToken = await tokenService.refresh()

        // Mettre à jour le header pour cette requête
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`

        // Relancer la requête originale avec le nouveau token
        return api(originalRequest)
      } catch (refreshError) {
        // Le refresh a échoué → déconnecter l'utilisateur
        tokenService.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
```

### Flux complet d'une requête HTTP

```
Composant React
     │
     │  useQuery(() => gameService.getGame(id))
     ▼
TanStack Query
     │
     │  Vérifie le cache (données fraîches ?)
     │  Non → déclenche la requête
     ▼
gameService.getGame(id)
     │
     │  return api.get(`/api/games/${id}/`)
     ▼
Axios (api.ts)
     │
     │  Intercepteur requête → ajoute Bearer token
     ▼
     │  GET /api/games/42/
     │  Authorization: Bearer eyJhbGc...
     ▼
Backend Django REST API
     │
     │  Token valide ? Oui → retourne données
     │  Token expiré ? → 401 Unauthorized
     ▼
Axios (intercepteur réponse)
     │
     │  Si 401 :
     │    POST /api/auth/token/refresh/  { refresh: "..." }
     │    → nouveau access token
     │    → relance GET /api/games/42/ avec nouveau token
     │
     │  Sinon : retourne données
     ▼
TanStack Query
     │
     │  Met en cache les données
     │  Met à jour l'état (isSuccess = true)
     ▼
Composant React
     │  Re-render avec les données
```

---

## 2. TanStack Query — Cache et états des requêtes

### Qu'est-ce que TanStack Query ?

TanStack Query (anciennement React Query) est une bibliothèque de **gestion des données serveur**. Elle résout trois problèmes courants :

1. **Cache** : évite de refaire une requête si les données sont récentes
2. **États** : expose `isLoading`, `isError`, `isSuccess` sans `useState` manuel
3. **Synchronisation** : invalidation automatique du cache après une mutation

### Exemple d'utilisation — Requête (useQuery)

```typescript
// Dans un composant React
import { useQuery } from '@tanstack/react-query'
import { gameService } from '../services/gameService'

function GameHistoryPage() {
  const {
    data: games,       // Les données retournées
    isLoading,         // true pendant le chargement
    isError,           // true si la requête a échoué
    error,             // L'objet d'erreur
    refetch,           // Fonction pour relancer manuellement
  } = useQuery({
    queryKey: ['games', 'history'],  // Clé unique pour le cache
    queryFn: () => gameService.getHistory(),
    staleTime: 5 * 60 * 1000,       // Données "fraîches" 5 minutes
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage error={error} />

  return (
    <ul>
      {games?.map(game => (
        <li key={game.id}>{game.room_code}</li>
      ))}
    </ul>
  )
}
```

### Exemple d'utilisation — Mutation (useMutation)

```typescript
// Créer une partie
import { useMutation, useQueryClient } from '@tanstack/react-query'

function CreateGamePage() {
  const queryClient = useQueryClient()

  const createGameMutation = useMutation({
    mutationFn: (data: CreateGamePayload) => gameService.createGame(data),

    onSuccess: (newGame) => {
      // Invalider le cache de la liste des parties
      queryClient.invalidateQueries({ queryKey: ['games'] })

      // Rediriger vers le lobby
      navigate(`/game/lobby/${newGame.room_code}`)
    },

    onError: (error) => {
      // Afficher un toast d'erreur
      toast.error('Impossible de créer la partie')
    },
  })

  const handleSubmit = (formData: CreateGamePayload) => {
    createGameMutation.mutate(formData)
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* ... */}
      <button
        type="submit"
        disabled={createGameMutation.isPending}
      >
        {createGameMutation.isPending ? 'Création...' : 'Créer la partie'}
      </button>
    </form>
  )
}
```

### Cycle de vie du cache TanStack Query

```
                    Requête déclenchée
                           │
                    ┌──────▼──────┐
                    │  isLoading  │  ← Données absentes du cache
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│  isSuccess  │─────┐
              │     └─────────────┘     │
              │                         │
    Cache FRAIS (staleTime)    Cache PÉRIMÉ (après staleTime)
              │                         │
    Données servies          Background refetch
    depuis le cache          (données affichées quand même)
              │                         │
              └─────────┬───────────────┘
                        │
                 ┌──────▼──────┐
                 │  Invalider  │  ← après useMutation.onSuccess()
                 │  le cache   │
                 └──────┬──────┘
                        │
               Prochaine lecture = rechargement
```

### Stratégie de cache par service

| Service             | `staleTime` | `queryKey`             | Invalidation            |
| ------------------- | ----------- | ---------------------- | ----------------------- |
| Profil utilisateur  | 5 min       | `['user', userId]`     | Après updateProfile     |
| Liste des amis      | 2 min       | `['friends']`          | Après add/remove friend |
| Classement          | 1 min       | `['leaderboard']`      | Automatique             |
| Inventaire boutique | 5 min       | `['inventory']`        | Après achat             |
| Historique parties  | 10 min      | `['games', 'history']` | Après fin de partie     |
| Config maintenance  | 30 sec      | `['site-status']`      | —                       |

---

## 3. Zustand — État global

### Qu'est-ce que Zustand ?

Zustand est une bibliothèque de **gestion d'état global** minimaliste pour React. Contrairement à Redux, elle ne nécessite pas de boilerplate complexe. L'état est un simple objet JavaScript avec des fonctions pour le modifier.

> Voir le fichier `03-state-management.md` pour la documentation complète des stores.

### Distinction TanStack Query vs Zustand

|                     | TanStack Query           | Zustand                      |
| ------------------- | ------------------------ | ---------------------------- |
| **Usage**           | Données serveur (API)    | État client (UI)             |
| **Exemples**        | Liste de parties, profil | Token JWT, état du jeu actif |
| **Synchronisation** | Avec le serveur          | Local uniquement             |
| **Persistance**     | Cache en mémoire         | localStorage (optionnel)     |

---

## 4. Service Token (`services/tokenService.ts`)

Ce service gère le **stockage et la lecture** des tokens JWT dans le `localStorage` du navigateur.

```typescript
// services/tokenService.ts
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const tokenService = {
  // Stocker les tokens (après login)
  setTokens: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },

  // Lire le token d'accès
  getAccessToken: (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },

  // Rafraîchir le token d'accès
  refresh: async (): Promise<string> => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refreshToken) throw new Error('No refresh token')

    const response = await axios.post('/api/auth/token/refresh/', {
      refresh: refreshToken
    })

    const newAccessToken = response.data.access
    localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken)
    return newAccessToken
  },

  // Supprimer les tokens (logout)
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}
```

### Flux complet du cycle JWT

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CYCLE DE VIE DU JWT                         │
└─────────────────────────────────────────────────────────────────────┘

1. LOGIN
   ─────
   POST /api/auth/login/  { email, password }
              │
              ▼
   ← { access: "eyJ...", refresh: "eyJ..." }
              │
              ▼
   tokenService.setTokens(access, refresh)
   authStore.setUser(userData)


2. REQUÊTE AUTHENTIFIÉE
   ─────────────────────
   Composant → api.get('/api/profile/')
              │
   Intercepteur request → Authorization: Bearer eyJ...
              │
              ▼
   Backend valide le token → ← 200 OK { user data }


3. TOKEN EXPIRÉ
   ─────────────
   api.get('/api/profile/')
              │
   ← 401 Unauthorized  (token expiré)
              │
   Intercepteur response :
     POST /api/auth/token/refresh/  { refresh: "eyJ..." }
              │
     ← { access: "eyJ... (nouveau)" }
              │
     tokenService.setTokens(newAccess, refresh)
              │
     Relance api.get('/api/profile/')  avec nouveau token
              │
     ← 200 OK { user data }  ← Transparent pour le composant


4. REFRESH EXPIRÉ (session terminée)
   ──────────────────────────────────
   POST /api/auth/token/refresh/
              │
   ← 401 Unauthorized (refresh aussi expiré)
              │
   tokenService.clear()
   authStore.logout()
   window.location.href = '/login'


5. LOGOUT EXPLICITE
   ─────────────────
   POST /api/auth/logout/  { refresh: "eyJ..." }
              │
   tokenService.clear()
   authStore.logout()
```

---

## 5. WebSocket — Communication temps réel

### Pourquoi le WebSocket ?

HTTP est un protocole **requête-réponse** : le client demande, le serveur répond. Pour un jeu multijoueur, on a besoin que le **serveur puisse envoyer des données au client sans qu'il les demande** (ex: "un adversaire a répondu", "le round est terminé"). C'est le rôle des WebSockets : une connexion **bidirectionnelle persistante**.

```
HTTP (requête-réponse)          WebSocket (bidirectionnel)
─────────────────────           ─────────────────────────
Client → Serveur : GET          Client ←→ Serveur (connexion ouverte)
Serveur → Client : 200 OK       Serveur peut envoyer à tout moment
[connexion fermée]              [connexion maintenue]
```

### Architecture WebSocket du projet

```
GamePlayPage
     │
     │  useGameWebSocket(roomCode)
     ▼
useWebSocket.ts
     │
     │  Connexion : ws://localhost:8000/ws/game/{roomCode}/?token={jwt}
     ▼
websocketService.ts
     │
     │  new WebSocket(url)
     │  onmessage → parse JSON → dispatch vers reducer
     │  onclose → reconnexion automatique
     ▼
     │
     │                    ws://
     ▼
Django Channels — GameConsumer
     │
     │  group: game_{roomCode}
     │  Tous les joueurs de la salle
```

### `useWebSocket.ts` — Hook générique

Ce hook bas niveau gère le cycle de vie d'une connexion WebSocket.

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react'
import { tokenService } from '../services/tokenService'

interface UseWebSocketOptions {
  url: string
  onMessage: (data: unknown) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnect,
  onDisconnect,
}: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    // Ajouter le JWT en query string (les headers WS ne sont pas supportés)
    const token = tokenService.getAccessToken()
    const wsUrl = `${url}?token=${token}`

    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('WebSocket connecté')
      onConnect?.()
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }

    wsRef.current.onclose = (event) => {
      console.log('WebSocket fermé', event.code)
      onDisconnect?.()

      // Reconnexion automatique (sauf déconnexion volontaire)
      if (event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000)
      }
    }

    wsRef.current.onerror = (error) => {
      console.error('WebSocket erreur', error)
    }
  }, [url, onMessage, onConnect, onDisconnect])

  useEffect(() => {
    connect()

    // Nettoyage à la destruction du composant
    return () => {
      clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close(1000, 'Component unmounted')
    }
  }, [connect])

  // Envoyer un message
  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { sendMessage }
}
```

### `useGameWebSocket.ts` — Hook spécialisé pour le jeu

Ce hook utilise `useWebSocket` et le connecte à la state machine du reducer.

```typescript
// hooks/useGameWebSocket.ts
import { useWebSocket } from './useWebSocket'
import { useGamePlayReducer } from './useGamePlayReducer'

export const useGameWebSocket = (roomCode: string) => {
  const { dispatch, gameState } = useGamePlayReducer()

  const handleMessage = (message: GameWebSocketMessage) => {
    switch (message.type) {
      case 'game_started':
        dispatch({ type: 'GAME_STARTED', payload: message.data })
        break

      case 'round_started':
        dispatch({ type: 'ROUND_STARTED', payload: message.data })
        break

      case 'round_ended':
        dispatch({ type: 'ROUND_ENDED', payload: message.data })
        break

      case 'player_answered':
        dispatch({ type: 'PLAYER_ANSWERED', payload: message.data })
        break

      case 'bonus_activated':
        dispatch({ type: 'BONUS_ACTIVATED', payload: message.data })
        break

      case 'game_finished':
        dispatch({ type: 'GAME_FINISHED', payload: message.data })
        break

      default:
        console.warn('Message WS inconnu:', message.type)
    }
  }

  const { sendMessage } = useWebSocket({
    url: `${import.meta.env.VITE_WS_URL}/ws/game/${roomCode}/`,
    onMessage: handleMessage,
  })

  return {
    // Actions disponibles pour les composants
    sendAnswer: (answer: string) =>
      sendMessage({ type: 'player_answer', answer }),

    sendStartGame: () =>
      sendMessage({ type: 'start_game' }),

    sendNextRound: () =>
      sendMessage({ type: 'next_round' }),

    sendActivateBonus: (bonusType: string) =>
      sendMessage({ type: 'activate_bonus', bonus_type: bonusType }),

    gameState,
  }
}
```

### Flux complet WebSocket d'une partie

```
GamePlayPage → useGameWebSocket(roomCode)
                       │
           ┌───────────▼────────────────────────────────┐
           │  ws://backend:8000/ws/game/{roomCode}/      │
           │               ?token={jwt}                  │
           └───────────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────┐
        │           MESSAGES CLIENT → SERVEUR         │
        │                                             │
        │  { type: "start_game" }                     │
        │  { type: "player_answer", answer: "..." }   │
        │  { type: "next_round" }                     │
        │  { type: "activate_bonus", bonus_type: "" } │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │           MESSAGES SERVEUR → CLIENT         │
        │                                             │
        │  { type: "game_started", data: {...} }      │
        │  { type: "round_started", data: {          │
        │      round_number, audio_url, choices,      │
        │      timer_duration                         │
        │  }}                                         │
        │  { type: "player_answered", data: {        │
        │      player_id, response_time              │
        │  }}                                         │
        │  { type: "round_ended", data: {            │
        │      correct_answer, scores, rankings       │
        │  }}                                         │
        │  { type: "bonus_activated", data: {...} }   │
        │  { type: "game_finished", data: {           │
        │      final_scores, winner                   │
        │  }}                                         │
        └─────────────────────────────────────────────┘

                       │ dispatch
                       ▼
        useGamePlayReducer (state machine)
                       │
                       ▼
               React Re-render
               (affichage mis à jour)
```

---

## 6. Notifications WebSocket persistant (`notificationWebSocket.ts`)

En dehors du jeu, un second WebSocket reste connecté pour les **notifications en temps réel** (invitations reçues, achievements débloqués). Contrairement au WS de jeu, celui-ci ne se déconnecte pas entre les parties.

```typescript
// services/notificationWebSocket.ts
class NotificationWebSocketService {
  private ws: WebSocket | null = null

  connect(token: string) {
    this.ws = new WebSocket(
      `${WS_BASE_URL}/ws/notifications/?token=${token}`
    )

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      switch (message.type) {
        case 'game_invitation':
          // Ajoute à la liste des invitations en attente
          useNotificationStore.getState().addInvitation(message.data)
          break

        case 'achievement_unlocked':
          // Ajoute un toast de félicitations
          useNotificationStore.getState().addAchievementToast(message.data)
          break
      }
    }
  }

  disconnect() {
    this.ws?.close(1000)
  }
}

export const notificationWS = new NotificationWebSocketService()
```

---

## 7. Services HTTP (`services/`)

Chaque service encapsule les appels API d'un domaine métier.

### `authService.ts`

```typescript
export const authService = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/api/auth/login/', { email, password }),

  register: (data: RegisterPayload) =>
    api.post<User>('/api/auth/register/', data),

  logout: (refreshToken: string) =>
    api.post('/api/auth/logout/', { refresh: refreshToken }),

  forgotPassword: (email: string) =>
    api.post('/api/auth/password-reset/', { email }),

  resetPassword: (uid: string, token: string, newPassword: string) =>
    api.post('/api/auth/password-reset/confirm/', {
      uid, token, new_password: newPassword
    }),
}
```

### `gameService.ts`

```typescript
export const gameService = {
  // Créer une partie
  createGame: (data: CreateGamePayload) =>
    api.post<Game>('/api/games/', data).then(r => r.data),

  // Rejoindre une partie par code
  joinGame: (roomCode: string) =>
    api.post<Game>(`/api/games/${roomCode}/join/`).then(r => r.data),

  // Récupérer une partie
  getGame: (roomCode: string) =>
    api.get<Game>(`/api/games/${roomCode}/`).then(r => r.data),

  // Soumettre une réponse (HTTP fallback, normalement via WS)
  submitAnswer: (gameId: number, roundId: number, answer: string) =>
    api.post(`/api/games/${gameId}/rounds/${roundId}/answer/`, { answer }),

  // Historique
  getHistory: () =>
    api.get<Game[]>('/api/games/history/').then(r => r.data),
}
```

### `shopService.ts`

```typescript
export const shopService = {
  // Liste des items disponibles
  getShopItems: () =>
    api.get<ShopItem[]>('/api/shop/items/').then(r => r.data),

  // Inventaire du joueur
  getInventory: () =>
    api.get<InventoryItem[]>('/api/shop/inventory/').then(r => r.data),

  // Acheter un item
  buyItem: (itemId: number) =>
    api.post<InventoryItem>(`/api/shop/items/${itemId}/buy/`).then(r => r.data),
}
```

---

## Résumé — Choisir le bon canal de communication

```
┌─────────────────────────────────────────────────────┐
│            QUELLE TECHNOLOGIE UTILISER ?            │
└─────────────────────────────────────────────────────┘

Action à réaliser                    → Technologie
──────────────────────────────────────────────────────
Créer/modifier des données            → Axios (api.ts)
  (login, créer partie, acheter...)

Lire des données avec cache           → TanStack Query
  (profil, classement, historique...)

État partagé entre composants         → Zustand store
  (user connecté, partie en cours...)

Réception d'événements temps réel     → WebSocket
  (round_started, player_answered...)

Envoi d'actions en temps réel         → WebSocket
  (player_answer, start_game...)

Notifications push (invitations...)   → WebSocket persistant
  (notificationWebSocket.ts)
```
