# Gestion d'état — Zustand et State Machine de jeu

## Vue d'ensemble

La gestion d'état dans InstantMusic se répartit en deux niveaux :

| Niveau           | Technologie      | Usage                                                |
| ---------------- | ---------------- | ---------------------------------------------------- |
| **État global**  | Zustand stores   | Utilisateur connecté, partie en cours, notifications |
| **État du jeu**  | React useReducer | State machine du déroulement d'une partie            |
| **État serveur** | TanStack Query   | Données récupérées via API (cache)                   |
| **État local**   | useState         | UI temporaire (modales, formulaires)                 |

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GESTION D'ÉTAT                                 │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │   authStore      │  │   gameStore      │  │ notificationStore   │ │
│  │   (Zustand)      │  │   (Zustand)      │  │   (Zustand)         │ │
│  │                  │  │                  │  │                     │ │
│  │ user             │  │ currentGame      │  │ pendingInvitations  │ │
│  │ accessToken      │  │ setCurrentGame   │  │ achievementToasts   │ │
│  │ isAuthenticated  │  │ updateGame       │  │                     │ │
│  │                  │  │                  │  │                     │ │
│  │ [persisté]       │  │ [mémoire]        │  │ [mémoire]           │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              useGamePlayReducer (React useReducer)           │   │
│  │                                                              │   │
│  │  État:  idle → waiting_for_round → playing → showing_results │   │
│  │                      → game_over                             │   │
│  │                                                              │   │
│  │  Actions: GAME_STARTED, ROUND_STARTED, ROUND_ENDED, ...      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. `authStore.ts` — État d'authentification

### Qu'est-ce que Zustand ?

Zustand est une bibliothèque de **gestion d'état global** pour React. L'idée est simple : créer un "store" (magasin de données) accessible depuis n'importe quel composant sans avoir à passer des `props` en cascade.

Comparaison avec les alternatives :

```
Redux (classique)              Zustand (moderne)
──────────────────             ─────────────────
actions.js                     Un seul fichier
reducers.js         vs         store.ts
selectors.js                   3-5 lignes de setup
middleware.js
~100 lignes                    ~20 lignes
```

### Structure du store

```typescript
// store/authStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  avatar_url: string | null
  coins_balance: number
  // ... autres champs
}

interface AuthState {
  // ÉTAT
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  // ACTIONS
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  updateUser: (partial: Partial<User>) => void
  setTokens: (accessToken: string, refreshToken: string) => void
}

export const useAuthStore = create<AuthState>()(
  // persist() sauvegarde l'état dans localStorage automatiquement
  persist(
    (set) => ({
      // État initial
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      // Action : connexion réussie
      login: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      // Action : déconnexion
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),

      // Action : mise à jour partielle du profil
      updateUser: (partial) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...partial } : null,
        })),

      // Action : nouveaux tokens (après refresh)
      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),
    }),
    {
      name: 'auth-storage', // Clé dans localStorage
      // Ne persister que les données sensibles utiles
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
```

### Utilisation dans les composants

```typescript
// Lecture d'une valeur
function Header() {
  const user = useAuthStore(state => state.user)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)

  return (
    <nav>
      {isAuthenticated ? (
        <span>Bonjour, {user?.username}</span>
      ) : (
        <a href="/login">Se connecter</a>
      )}
    </nav>
  )
}

// Utilisation d'une action
function LoginForm() {
  const login = useAuthStore(state => state.login)

  const handleLogin = async (credentials) => {
    const response = await authService.login(credentials)
    // Mise à jour du store global
    login(response.user, response.access, response.refresh)
  }
}

// Accès depuis un service (en dehors d'un composant)
const accessToken = useAuthStore.getState().accessToken
```

### Persistance avec `localStorage`

Le middleware `persist` de Zustand sérialise automatiquement l'état en JSON dans le `localStorage`. Ainsi, si l'utilisateur ferme et rouvre l'onglet, il reste connecté.

```
localStorage
├── "auth-storage"  →  { user: {...}, accessToken: "eyJ...", ... }
└── ...
```

> **Sécurité** : les tokens JWT sont stockés en `localStorage`. Cette approche est courante mais présente un risque XSS. Une alternative plus sécurisée serait les cookies `HttpOnly`, mais cela nécessite des ajustements backend.

---

## 2. `gameStore.ts` — Données de la partie en cours

Ce store contient les **métadonnées** de la partie (pas l'état de jeu temps réel, qui est géré par le reducer).

```typescript
// store/gameStore.ts
import { create } from 'zustand'

interface GameState {
  // ÉTAT
  currentGame: Game | null

  // ACTIONS
  setCurrentGame: (game: Game | null) => void
  updateGame: (partial: Partial<Game>) => void
  clearGame: () => void
}

export const useGameStore = create<GameState>()((set) => ({
  currentGame: null,

  // Définir la partie en cours (après création ou join)
  setCurrentGame: (game) => set({ currentGame: game }),

  // Mise à jour partielle (ex: statut change)
  updateGame: (partial) =>
    set((state) => ({
      currentGame: state.currentGame
        ? { ...state.currentGame, ...partial }
        : null,
    })),

  // Quitter la partie
  clearGame: () => set({ currentGame: null }),
}))
```

### Données stockées dans `currentGame`

```typescript
interface Game {
  id: number
  room_code: string           // Ex: "AZERTY"
  status: GameStatus          // 'waiting' | 'in_progress' | ...
  game_mode: GameMode         // 'classique' | 'rapide' | ...
  answer_mode: 'mcq' | 'text'
  guess_target: 'title' | 'artist'
  total_rounds: number
  current_round: number
  round_duration: number      // Secondes par round
  timer_start_round: number   // Secondes d'attente entre rounds
  score_display_duration: number
  host: User
  players: GamePlayer[]
  playlist: Playlist
}
```

---

## 3. `notificationStore.ts` — Notifications et invitations

```typescript
// store/notificationStore.ts
import { create } from 'zustand'

interface GameInvitation {
  id: number
  from_user: User
  game_room_code: string
  game_mode: GameMode
  expires_at: string
}

interface AchievementToast {
  id: string               // UUID pour la key React
  achievement: Achievement
  points_earned: number
}

interface NotificationState {
  // ÉTAT
  pendingInvitations: GameInvitation[]
  achievementToasts: AchievementToast[]

  // ACTIONS
  addInvitation: (invitation: GameInvitation) => void
  removeInvitation: (invitationId: number) => void
  addAchievementToast: (data: AchievementToast) => void
  dismissAchievementToast: (toastId: string) => void
}

export const useNotificationStore = create<NotificationState>()((set) => ({
  pendingInvitations: [],
  achievementToasts: [],

  addInvitation: (invitation) =>
    set((state) => ({
      pendingInvitations: [...state.pendingInvitations, invitation],
    })),

  removeInvitation: (invitationId) =>
    set((state) => ({
      pendingInvitations: state.pendingInvitations.filter(
        (inv) => inv.id !== invitationId
      ),
    })),

  addAchievementToast: (data) =>
    set((state) => ({
      achievementToasts: [...state.achievementToasts, data],
    })),

  dismissAchievementToast: (toastId) =>
    set((state) => ({
      achievementToasts: state.achievementToasts.filter(
        (t) => t.id !== toastId
      ),
    })),
}))
```

---

## 4. `useGamePlayReducer.ts` — State Machine du jeu

### Qu'est-ce qu'un Reducer ?

Un **reducer** est une fonction pure qui prend un état et une action, et retourne un nouvel état. C'est le pattern utilisé dans React avec `useReducer` (ou Redux). Il est idéal pour les états complexes avec de nombreuses transitions.

```
État actuel + Action → Nouveau état
     (état)    (action)    (état')

Exemple :
  { phase: 'idle' } + GAME_STARTED → { phase: 'waiting_for_round' }
```

### Machine d'état du jeu

```
                    ┌──────────────────────────────────────────────┐
                    │              ÉTATS DU JEU                    │
                    └──────────────────────────────────────────────┘

  Début
    │
    ▼
┌─────────┐  GAME_STARTED   ┌──────────────────┐
│  idle   │ ─────────────►  │ waiting_for_round │
└─────────┘                 └────────┬─────────┘
                                     │
                            ROUND_STARTED
                                     │
                                     ▼
                            ┌────────────────┐
                    ┌────── │    playing     │
                    │       └────────────────┘
                    │              │
             BONUS_ACTIVATED  ROUND_ENDED
             PLAYER_ANSWERED       │
                    │              ▼
                    └──►  ┌─────────────────┐
                          │ showing_results │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │                 │
                    NEXT_ROUND         GAME_FINISHED
                          │                 │
                          ▼                 ▼
                 waiting_for_round     ┌──────────┐
                                       │ game_over │
                                       └──────────┘
```

### Définition des types

```typescript
// Types de l'état
type GamePhase =
  | 'idle'              // Avant le début
  | 'waiting_for_round' // Entre deux rounds
  | 'playing'           // Round en cours
  | 'showing_results'   // Résultats du round
  | 'game_over'         // Partie terminée

interface GamePlayState {
  phase: GamePhase
  currentRound: number
  totalRounds: number
  currentQuestion: Question | null
  players: GamePlayer[]
  myScore: number
  myRank: number
  correctAnswer: string | null
  roundScores: RoundScore[]
  finalResults: FinalResult | null
  hasAnswered: boolean
  isAudioPlaying: boolean
  activeBonus: BonusType | null
}

// Types des actions
type GamePlayAction =
  | { type: 'GAME_STARTED'; payload: GameStartedPayload }
  | { type: 'ROUND_STARTED'; payload: RoundStartedPayload }
  | { type: 'PLAYER_ANSWERED'; payload: PlayerAnsweredPayload }
  | { type: 'ROUND_ENDED'; payload: RoundEndedPayload }
  | { type: 'NEXT_ROUND' }
  | { type: 'BONUS_ACTIVATED'; payload: BonusActivatedPayload }
  | { type: 'GAME_FINISHED'; payload: GameFinishedPayload }
  | { type: 'RESET' }
```

### Implémentation du reducer

```typescript
// hooks/useGamePlayReducer.ts
const initialState: GamePlayState = {
  phase: 'idle',
  currentRound: 0,
  totalRounds: 0,
  currentQuestion: null,
  players: [],
  myScore: 0,
  myRank: 0,
  correctAnswer: null,
  roundScores: [],
  finalResults: null,
  hasAnswered: false,
  isAudioPlaying: false,
  activeBonus: null,
}

function gamePlayReducer(
  state: GamePlayState,
  action: GamePlayAction
): GamePlayState {
  switch (action.type) {

    case 'GAME_STARTED':
      return {
        ...state,
        phase: 'waiting_for_round',
        totalRounds: action.payload.total_rounds,
        players: action.payload.players,
      }

    case 'ROUND_STARTED':
      return {
        ...state,
        phase: 'playing',
        currentRound: action.payload.round_number,
        currentQuestion: action.payload.question,
        correctAnswer: null,
        roundScores: [],
        hasAnswered: false,
        isAudioPlaying: true,
        activeBonus: null,
      }

    case 'PLAYER_ANSWERED':
      // Marquer visuellement qu'un joueur a répondu
      return {
        ...state,
        players: state.players.map(player =>
          player.user.id === action.payload.player_id
            ? { ...player, has_answered: true }
            : player
        ),
        // Si c'est moi
        hasAnswered:
          state.hasAnswered ||
          action.payload.player_id === getCurrentUserId(),
      }

    case 'ROUND_ENDED':
      return {
        ...state,
        phase: 'showing_results',
        correctAnswer: action.payload.correct_answer,
        roundScores: action.payload.scores,
        players: mergeUpdatedPlayers(state.players, action.payload.rankings),
        myScore: action.payload.my_score ?? state.myScore,
        myRank: action.payload.my_rank ?? state.myRank,
        isAudioPlaying: false,
      }

    case 'NEXT_ROUND':
      return {
        ...state,
        phase: 'waiting_for_round',
        currentQuestion: null,
        correctAnswer: null,
      }

    case 'BONUS_ACTIVATED':
      return {
        ...state,
        activeBonus: action.payload.bonus_type,
        // Effets visuels selon le type de bonus
        currentQuestion: action.payload.bonus_type === 'fifty_fifty'
          ? removeTwoWrongAnswers(state.currentQuestion)
          : state.currentQuestion,
      }

    case 'GAME_FINISHED':
      return {
        ...state,
        phase: 'game_over',
        finalResults: action.payload,
      }

    case 'RESET':
      return initialState

    default:
      return state
  }
}

export const useGamePlayReducer = () => {
  const [gameState, dispatch] = useReducer(gamePlayReducer, initialState)
  return { gameState, dispatch }
}
```

### Utilisation dans `GamePlayPage`

```typescript
// pages/game/GamePlayPage.tsx
function GamePlayPage() {
  const { roomCode } = useParams()
  const { gameState, sendAnswer, sendStartGame, sendNextRound } =
    useGameWebSocket(roomCode!)

  // Rendu conditionnel selon la phase
  return (
    <div>
      {gameState.phase === 'idle' && (
        <button onClick={sendStartGame}>Démarrer</button>
      )}

      {gameState.phase === 'waiting_for_round' && (
        <RoundLoadingScreen
          roundNumber={gameState.currentRound + 1}
        />
      )}

      {gameState.phase === 'playing' && gameState.currentQuestion && (
        <>
          {/* Composant adapté au mode de jeu */}
          <QuizQuestion
            question={gameState.currentQuestion}
            onAnswer={sendAnswer}
            hasAnswered={gameState.hasAnswered}
          />

          {/* Scores en temps réel */}
          <LiveScoreboard players={gameState.players} />

          {/* Activation de bonus */}
          <BonusActivator />
        </>
      )}

      {gameState.phase === 'showing_results' && (
        <RoundResultsScreen
          correctAnswer={gameState.correctAnswer}
          scores={gameState.roundScores}
          onNext={sendNextRound}
        />
      )}

      {gameState.phase === 'game_over' && (
        // Redirection vers la page résultats
        <Navigate to={`/game/${roomCode}/results`} />
      )}
    </div>
  )
}
```

---

## 5. Flux de données complet — Diagramme

```
┌──────────────────────────────────────────────────────────────────┐
│                  CYCLE DE VIE D'UNE PARTIE                      │
└──────────────────────────────────────────────────────────────────┘

1. CONNEXION
   ──────────
   GamePlayPage monte
        │
        ▼
   useGameWebSocket(roomCode)
        │
        ▼
   WebSocket connecté → ws://backend/ws/game/{roomCode}/


2. DÉMARRAGE (hôte clique "Start")
   ──────────────────────────────
   Hôte clique bouton "Démarrer"
        │
        ▼
   sendStartGame()  →  WS: { type: "start_game" }
        │
        ▼  [côté serveur : génère les rounds, démarre la partie]
        │
   WS reçoit: { type: "game_started", data: {...} }
        │
        ▼
   dispatch({ type: 'GAME_STARTED', payload: data })
        │
        ▼
   gameState.phase = 'waiting_for_round'
        │
        ▼
   React re-render → affiche RoundLoadingScreen


3. ROUND EN COURS
   ──────────────
   WS reçoit: { type: "round_started", data: { question, audio_url } }
        │
        ▼
   dispatch({ type: 'ROUND_STARTED', payload: data })
        │
        ▼
   gameState.phase = 'playing'
        │
        ▼
   React re-render → affiche QuizQuestion + audio joue


4. RÉPONSE
   ────────
   Joueur clique une réponse
        │
        ▼
   sendAnswer("Shape of You")  →  WS: { type: "player_answer", answer: "..." }
        │
        ▼
   [Côté serveur : valide, calcule le score]
        │
   WS reçoit: { type: "player_answered", data: { player_id: 42 } }
        │
        ▼
   dispatch({ type: 'PLAYER_ANSWERED', ... })
        │
        ▼
   gameState.players[42].has_answered = true  (indicateur visuel)


5. FIN DE ROUND
   ─────────────
   WS reçoit: { type: "round_ended", data: { correct_answer, scores } }
        │
        ▼
   dispatch({ type: 'ROUND_ENDED', payload: data })
        │
        ▼
   gameState.phase = 'showing_results'
   gameState.correctAnswer = "Shape of You"
   gameState.roundScores = [...]
        │
        ▼
   React re-render → affiche RoundResultsScreen


6. ROUND SUIVANT (repeat étapes 3-5)

7. FIN DE PARTIE
   ──────────────
   WS reçoit: { type: "game_finished", data: { final_scores } }
        │
        ▼
   dispatch({ type: 'GAME_FINISHED', payload: data })
        │
        ▼
   gameState.phase = 'game_over'
        │
        ▼
   <Navigate to="/game/{roomCode}/results" />
```

---

## 6. Récapitulatif — Quand utiliser quel store

```
┌──────────────────────────────────────────────────────────────────┐
│  Question : qui a besoin de cette donnée ?                       │
│                                                                  │
│  Toute l'appli          → authStore (user, isAuthenticated)      │
│  (ex: Header, pages protégées)                                   │
│                                                                  │
│  Pages de jeu           → gameStore (currentGame) +             │
│  (Lobby, Play, Results) │  useGamePlayReducer (phase, question)  │
│                                                                  │
│  Notifications          → notificationStore                      │
│  (invitations, toasts)                                           │
│                                                                  │
│  Un seul composant      → useState local                         │
│  (modal ouverte/fermée)                                          │
│                                                                  │
│  Données API            → TanStack Query                         │
│  (profil, leaderboard)                                           │
└──────────────────────────────────────────────────────────────────┘
```
