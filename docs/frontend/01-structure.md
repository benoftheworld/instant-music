# Structure du Frontend — InstantMusic

## Vue d'ensemble

Le frontend d'InstantMusic est une **Single Page Application (SPA)** construite avec React 18 et TypeScript. Une SPA charge une seule page HTML au démarrage, puis gère toute la navigation en JavaScript sans recharger la page. Cela donne une expérience fluide et réactive, idéale pour un quiz musical en temps réel.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Navigateur Web                           │
│                                                                 │
│   index.html  ──►  main.tsx  ──►  App.tsx  ──►  Routes         │
│       │                │               │                        │
│    Point            Montage         Routeur          Pages      │
│   d'entrée          React         React Router      & Composants│
└─────────────────────────────────────────────────────────────────┘
```

---

## Arborescence complète

```
frontend/
│
├── Dockerfile              ← Image Docker pour développement
├── Dockerfile.prod         ← Image Docker pour production (nginx)
├── package.json            ← Dépendances npm et scripts
├── vite.config.ts          ← Configuration Vite (bundler)
├── tsconfig.json           ← Configuration TypeScript
├── tailwind.config.js      ← Configuration Tailwind CSS
├── nginx-spa.conf          ← Config Nginx pour SPA en production
├── .eslintrc.json          ← Règles ESLint (qualité du code)
├── .prettierrc             ← Règles Prettier (formatage)
├── index.html              ← Point d'entrée HTML
│
└── src/
    ├── App.tsx             ← Composant racine + routes React Router
    ├── main.tsx            ← Montage React + providers globaux
    ├── index.css           ← Styles globaux Tailwind CSS
    │
    ├── components/         ← Composants réutilisables
    │   ├── auth/           ← Composants d'authentification
    │   ├── game/           ← 16 composants de jeu
    │   ├── home/           ← 2 composants page d'accueil
    │   ├── karaoke/        ← 2 composants karaoké
    │   ├── layout/         ← 8 composants de mise en page
    │   └── playlist/       ← 2 composants playlist
    │
    ├── constants/          ← Valeurs constantes de l'application
    │   ├── bonuses.ts      ← Définition des types de bonus
    │   ├── defaultPlaylists.ts ← Playlists prédéfinies
    │   └── gameModes.ts    ← Définition des modes de jeu
    │
    ├── hooks/              ← Hooks React personnalisés
    │   ├── useAuth.ts      ← Helpers authentification
    │   ├── useGamePlayReducer.ts ← State machine du jeu
    │   ├── useGameTimer.ts ← Timer compte à rebours
    │   ├── useGameWebSocket.ts ← Gestion messages WebSocket
    │   ├── useSiteStatus.ts ← Polling statut maintenance
    │   └── useWebSocket.ts ← Hook WebSocket générique
    │
    ├── pages/              ← Pages complètes (une par route)
    │   ├── auth/           ← Login, Register, ForgotPassword, ResetPassword
    │   ├── game/           ← Create, Join, Lobby, Play, Results
    │   ├── legal/          ← Privacy, LegalNotice
    │   ├── HomePage.tsx
    │   ├── FriendsPage.tsx
    │   ├── TeamsPage.tsx
    │   ├── TeamPage.tsx
    │   ├── GameHistoryPage.tsx
    │   ├── LeaderboardPage.tsx
    │   ├── ShopPage.tsx
    │   ├── ProfilePage.tsx
    │   ├── PublicProfilePage.tsx
    │   └── NotFoundPage.tsx
    │
    ├── services/           ← Couche d'accès aux données et API
    │   ├── api.ts          ← Instance Axios centralisée
    │   ├── authService.ts  ← login / register / logout
    │   ├── achievementService.ts ← Succès et badges
    │   ├── adminService.ts ← Statut maintenance, pages légales
    │   ├── gameService.ts  ← CRUD parties + réponses
    │   ├── invitationService.ts ← Invitations en partie
    │   ├── notificationWebSocket.ts ← WS persistant notifications
    │   ├── shopService.ts  ← Boutique, inventaire, achats
    │   ├── socialService.ts ← Amis et équipes
    │   ├── soundEffects.ts ← Effets sonores Howler.js
    │   ├── statsService.ts ← Classement et statistiques
    │   ├── tokenService.ts ← Stockage JWT + refresh
    │   ├── websocketService.ts ← Wrapper WebSocket générique
    │   └── youtubeService.ts ← Lecteur iframe YouTube
    │
    ├── store/              ← État global (Zustand)
    │   ├── authStore.ts    ← Utilisateur, tokens, authentification
    │   ├── gameStore.ts    ← Données de la partie en cours
    │   └── notificationStore.ts ← Invitations, toasts succès
    │
    ├── types/
    │   └── index.ts        ← Tous les types TypeScript du projet
    │
    └── utils/              ← Fonctions utilitaires pures
        ├── formatAnswer.ts ← Formatage des réponses
        └── mergeUpdatedPlayers.ts ← Fusion des données joueurs
```

---

## Fichiers de configuration

### `package.json` — Dépendances npm

Ce fichier liste toutes les bibliothèques utilisées par le projet et les scripts disponibles.

```json
{
  "scripts": {
    "dev": "vite",              // Lance le serveur de développement
    "build": "tsc && vite build", // Compile pour la production
    "preview": "vite preview",  // Prévisualise le build
    "lint": "eslint src",       // Vérifie la qualité du code
    "test": "vitest"            // Lance les tests
  }
}
```

**Dépendances principales :**

| Bibliothèque            | Version | Rôle                            |
| ----------------------- | ------- | ------------------------------- |
| `react`                 | 18      | Framework UI principal          |
| `react-dom`             | 18      | Rendu React dans le navigateur  |
| `react-router-dom`      | 6       | Gestion des routes/navigation   |
| `typescript`            | 5       | Typage statique JavaScript      |
| `vite`                  | 7       | Bundler ultra-rapide            |
| `zustand`               | 5       | Gestion d'état global simple    |
| `@tanstack/react-query` | 5       | Fetching et cache des données   |
| `axios`                 | 1.x     | Client HTTP pour les appels API |
| `tailwindcss`           | 3       | Framework CSS utilitaire        |
| `framer-motion`         | 11      | Animations fluides              |
| `howler`                | 2       | Lecture audio cross-browser     |

### `vite.config.ts` — Configuration Vite

Vite est le **bundler** (outil qui assemble tous les fichiers JS/CSS en un seul bundle optimisé). Il est beaucoup plus rapide que Webpack grâce à son utilisation des modules ES natifs.

```typescript
// vite.config.ts (simplifié)
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // En développement, redirige /api → backend:8000
      '/api': 'http://localhost:8000',
      // Redirige /ws → WebSocket backend
      '/ws': { target: 'ws://localhost:8000', ws: true }
    }
  }
})
```

### `tsconfig.json` — Configuration TypeScript

TypeScript est JavaScript avec des **types** : on déclare explicitement ce que contient chaque variable, ce qui évite de nombreux bugs. Le fichier `tsconfig.json` configure comment TypeScript vérifie le code.

```json
{
  "compilerOptions": {
    "target": "ES2020",       // Version JS cible
    "strict": true,           // Mode strict (recommandé)
    "moduleResolution": "bundler",
    "jsx": "react-jsx"        // Support JSX pour React
  }
}
```

### `tailwind.config.js` — Configuration Tailwind CSS

Tailwind CSS est un framework CSS **utilitaire** : au lieu d'écrire des classes CSS custom, on compose directement dans le HTML/JSX avec des classes prédéfinies (`flex`, `p-4`, `text-blue-500`, etc.).

---

## Points d'entrée de l'application

### `index.html`

```html
<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>InstantMusic</title>
  </head>
  <body>
    <!-- Conteneur vide : React va injecter tout le contenu ici -->
    <div id="root"></div>
    <!-- Vite injecte automatiquement le script JS compilé -->
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `main.tsx` — Montage de l'application

C'est ici que React "prend le contrôle" du DOM et que tous les providers globaux sont initialisés.

```tsx
// main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Client TanStack Query avec configuration du cache
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // Données "fraîches" pendant 5 minutes
      retry: 1,                  // 1 seule tentative de retry
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* Provider HTTP/cache */}
    <QueryClientProvider client={queryClient}>
      {/* Provider routage */}
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
```

### `App.tsx` — Routeur principal

```tsx
// App.tsx (structure simplifiée)
import { Routes, Route } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      {/* Routes publiques */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/leaderboard" element={<LeaderboardPage />} />

      {/* Routes protégées : redirige vers /login si non connecté */}
      <Route element={<ProtectedRoute />}>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/game/create" element={<CreateGamePage />} />
        <Route path="/game/play/:roomCode" element={<GamePlayPage />} />
        {/* ... autres routes protégées */}
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
```

---

## Tableau complet des routes

| Route                         | Page                 | Accès   | Description                   |
| ----------------------------- | -------------------- | ------- | ----------------------------- |
| `/`                           | `HomePage`           | Public  | Page d'accueil                |
| `/login`                      | `LoginPage`          | Public  | Connexion                     |
| `/register`                   | `RegisterPage`       | Public  | Inscription                   |
| `/forgot-password`            | `ForgotPasswordPage` | Public  | Réinitialisation mot de passe |
| `/reset-password/:uid/:token` | `ResetPasswordPage`  | Public  | Nouveau mot de passe          |
| `/privacy`                    | `PrivacyPage`        | Public  | Politique de confidentialité  |
| `/legal`                      | `LegalNoticePage`    | Public  | Mentions légales              |
| `/leaderboard`                | `LeaderboardPage`    | Public  | Classement général            |
| `/profile`                    | `ProfilePage`        | Protégé | Mon profil                    |
| `/profile/:id`                | `PublicProfilePage`  | Protégé | Profil d'un autre joueur      |
| `/friends`                    | `FriendsPage`        | Protégé | Gestion des amis              |
| `/teams`                      | `TeamsPage`          | Protégé | Liste des équipes             |
| `/teams/:id`                  | `TeamPage`           | Protégé | Page d'une équipe             |
| `/history`                    | `GameHistoryPage`    | Protégé | Historique des parties        |
| `/game/create`                | `CreateGamePage`     | Protégé | Créer une partie              |
| `/game/join`                  | `JoinGamePage`       | Protégé | Rejoindre une partie          |
| `/game/lobby/:roomCode`       | `GameLobbyPage`      | Protégé | Salle d'attente               |
| `/game/play/:roomCode`        | `GamePlayPage`       | Protégé | Jeu en cours                  |
| `/game/:roomCode/results`     | `GameResultsPage`    | Protégé | Résultats de fin              |
| `/shop`                       | `ShopPage`           | Protégé | Boutique de bonus             |

---

## Composants d'authentification (`components/auth/`)

### `ProtectedRoute.tsx`

Ce composant agit comme un **gardien** : si l'utilisateur n'est pas connecté, il est automatiquement redirigé vers `/login` avant de pouvoir accéder à la page demandée.

```tsx
// components/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)

  if (!isAuthenticated) {
    // Redirige vers login, en mémorisant la page d'origine
    return <Navigate to="/login" replace />
  }

  // Rend la page enfant si connecté
  return <Outlet />
}
```

---

## Composants de jeu (`components/game/`)

C'est le coeur de l'interface utilisateur. Ces composants gèrent l'affichage pendant une partie en cours.

### Vue d'ensemble des composants de jeu

```
GamePlayPage
├── RoundLoadingScreen.tsx     ← Écran de chargement entre les rounds
├── [composant de question selon le mode]
│   ├── QuizQuestion.tsx       ← Question MCQ standard (classique/rapide)
│   ├── GuessArtistQuestion.tsx ← Deviner l'artiste
│   ├── IntroQuestion.tsx      ← Reconnaître l'intro
│   ├── YearQuestion.tsx       ← Deviner l'année de sortie
│   ├── LyricsQuestion.tsx     ← Compléter les paroles (fill-in-blank)
│   ├── KaraokeQuestion.tsx    ← Paroles synchronisées + vidéo YouTube
│   ├── TextModeQuestion.tsx   ← Saisie texte libre
│   ├── SlowQuestion.tsx       ← Audio ralenti (mode Mollo)
│   └── BlindTestInverse.tsx   ← Blind test inversé
├── TextAnswerInput.tsx        ← Champ de saisie pour mode texte
├── BonusActivator.tsx         ← Interface d'activation des bonus
├── LiveScoreboard.tsx         ← Tableau des scores en temps réel
├── VolumeControl.tsx          ← Contrôle du volume audio
├── InviteFriendsModal.tsx     ← Modal d'invitation en partie
└── RoundResultsScreen.tsx     ← Résultats d'un round terminé
```

### Description détaillée de chaque composant

#### `QuizQuestion.tsx`
Le composant principal pour les **modes classique et rapide**. Affiche :
- L'extrait audio Deezer (via Howler.js) avec une barre de progression
- 4 choix de réponse sous forme de boutons
- Un timer visuel décomptant le temps
- Retour visuel (vert/rouge) après la soumission

```
┌──────────────────────────────────────────┐
│  ♪  Extrait en cours...  ████████░░  0:20 │
│                                          │
│  Quel est le titre de cette chanson ?    │
│                                          │
│  ┌──────────────┐  ┌──────────────┐     │
│  │  Shape of You │  │  Blinding... │     │
│  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐     │
│  │  Bad Guy     │  │  Levitating  │     │
│  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────┘
```

#### `GuessArtistQuestion.tsx`
Variante de `QuizQuestion` où l'objectif est d'identifier **l'artiste** plutôt que le titre. Les 4 choix proposent des noms d'artistes.

#### `IntroQuestion.tsx`
Spécialisé pour reconnaître une chanson à partir des **premières secondes** uniquement. L'extrait est plus court et l'interface met l'accent sur l'aspect "reconnaissance rapide".

#### `YearQuestion.tsx`
Pour le mode **Génération**. Les 4 choix sont des années (ex: 1985, 1992, 1998, 2003). Utilise la `release_date` fournie par l'API Deezer.

```
┌──────────────────────────────────────────┐
│  ♪  Don't Stop Me Now — Queen            │
│                                          │
│  En quelle année est sortie             │
│  cette chanson ?                         │
│                                          │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │  1975  │  │  1978  │  │  1981  │  │  1985  │ │
│  └────────┘  └────────┘  └────────┘  └────────┘ │
└──────────────────────────────────────────┘
```

#### `LyricsQuestion.tsx`
Pour le mode **Paroles**. Affiche des paroles avec un ou plusieurs mots manquants à deviner. La réponse peut être en MCQ (4 choix de mots) ou en saisie texte libre.

```
┌──────────────────────────────────────────┐
│  Complète les paroles :                  │
│                                          │
│  "Is this the real life ?               │
│   Is this just _______ ?                │
│   Caught in a landslide..."             │
│                                          │
│  ┌──────────┐  ┌──────────┐            │
│  │ fantasy  │  │  reality  │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │  memory  │  │  misery   │            │
│  └──────────┘  └──────────┘            │
└──────────────────────────────────────────┘
```

#### `KaraokeQuestion.tsx`
Le composant le plus complexe. Intègre :
- Un **lecteur YouTube** (iframe) via `youtubeService.ts`
- Un affichage de paroles **synchronisées** en temps réel (karaoke scrolling)
- Les paroles proviennent de LRCLib (format `.lrc` avec timestamps)
- Le joueur doit chanter/identifier les paroles

#### `TextModeQuestion.tsx`
Wrapper qui combine un composant de question avec `TextAnswerInput.tsx`. Utilisé quand `answer_mode = "text"` au lieu de MCQ.

#### `SlowQuestion.tsx`
Pour le mode **Mollo**. L'audio est joué à vitesse réduite (pitch-shift). Le composant affiche un indicateur visuel "RALENTI" et le gameplay reste identique à `QuizQuestion`.

#### `BlindTestInverse.tsx`
Mode inversé : l'interface affiche le **titre** et les joueurs doivent identifier si c'est bien cette chanson qui joue (oui/non). Renforce le test de mémoire.

#### `TextAnswerInput.tsx`
Champ de saisie texte pour le mode texte libre. Inclut :
- Autocomplétion basique
- Normalisation de la saisie (accents, casse) avant envoi
- Timer d'invalidation automatique à la fin du round

#### `BonusActivator.tsx`
Interface permettant d'activer un bonus depuis son inventaire pendant un round. S'affiche sous forme de barre d'icônes cliquables. Envoie le message WebSocket `activate_bonus`.

#### `LiveScoreboard.tsx`
Tableau des scores mis à jour en **temps réel** via WebSocket. Affiche le rang, le pseudo, l'avatar et le score de chaque joueur. Animé avec Framer Motion lors des changements de classement.

#### `VolumeControl.tsx`
Slider de volume pour l'extrait audio Howler.js. La préférence est mémorisée en `localStorage`.

#### `InviteFriendsModal.tsx`
Modal permettant d'inviter des amis à rejoindre la partie en cours depuis le lobby. Utilise `invitationService.ts` pour envoyer une notification WebSocket à l'ami.

#### `RoundLoadingScreen.tsx`
Écran de transition affiché entre la fin d'un round et le début du suivant. Montre le numéro du round à venir et un compte à rebours (`timer_start_round`).

#### `RoundResultsScreen.tsx`
Affiché après chaque round. Montre :
- La bonne réponse
- Le score gagné par chaque joueur pour ce round
- Le classement mis à jour
- Un bouton "Round suivant" (visible uniquement pour l'hôte)

---

## Composants de layout (`components/layout/`)

Ces composants forment la **structure visuelle** commune à toutes les pages.

```
Layout principal
├── Header.tsx         ← Barre de navigation (logo, menu, avatar)
├── Footer.tsx         ← Pied de page (liens légaux)
├── Sidebar.tsx        ← Menu latéral (si applicable)
├── MainLayout.tsx     ← Wrapper Header + contenu + Footer
├── PageTitle.tsx      ← Titre de page standardisé
├── LoadingSpinner.tsx ← Indicateur de chargement
├── ErrorBoundary.tsx  ← Capture les erreurs React
└── MaintenanceScreen.tsx ← Écran de maintenance (mode admin)
```

### `MaintenanceScreen.tsx`
Affiché quand le backend retourne un statut de maintenance (vérifié par `useSiteStatus.ts`). Bloque l'accès à l'application et affiche un message d'information.

---

## Hooks personnalisés (`hooks/`)

Les **hooks** sont des fonctions React réutilisables qui encapsulent de la logique. Les hooks custom commencent par `use`.

### `useAuth.ts`
```typescript
// Exemples d'utilisation
const { user, isAuthenticated, logout } = useAuth()
const { login, isLoading, error } = useAuth()
```
Fournit des helpers pratiques au-dessus du `authStore` Zustand.

### `useGamePlayReducer.ts`
La **state machine** du jeu côté client. Voir le fichier `03-state-management.md` pour les détails complets.

### `useGameTimer.ts`
```typescript
const { timeLeft, percentage, isExpired } = useGameTimer({
  duration: 30,       // Durée totale en secondes
  onExpire: () => {}  // Callback à la fin
})
```
Gère le compte à rebours d'un round. Retourne le temps restant, le pourcentage pour la barre de progression, et un flag `isExpired`.

### `useGameWebSocket.ts`
```typescript
const { sendMessage, isConnected } = useGameWebSocket(roomCode)

// Envoyer une réponse
sendMessage({ type: 'player_answer', answer: 'Shape of You' })

// Envoyer un bonus
sendMessage({ type: 'activate_bonus', bonus_type: 'double_points' })
```

### `useSiteStatus.ts`
Fait un **polling** (requête répétée à intervalle régulier) vers `/api/admin/site-status/` pour détecter si le site est en maintenance. Si oui, déclenche l'affichage de `MaintenanceScreen`.

### `useWebSocket.ts`
Hook générique bas niveau pour gérer une connexion WebSocket. Gère :
- La connexion initiale avec le token JWT en query string
- La reconnexion automatique en cas de déconnexion
- Le parsing JSON des messages entrants
- Le nettoyage à la destruction du composant

---

## Services (`services/`)

La couche **services** est la seule qui communique avec le monde extérieur (API REST, WebSocket). Aucun composant ne doit appeler directement `fetch()` ou `axios`.

```
services/
├── api.ts                ← Instance Axios + intercepteurs JWT
│
├── HTTP Services (utilisent api.ts)
│   ├── authService.ts    ← POST /api/auth/login/, register/, logout/
│   ├── gameService.ts    ← GET/POST /api/games/
│   ├── shopService.ts    ← GET/POST /api/shop/
│   ├── statsService.ts   ← GET /api/stats/
│   ├── socialService.ts  ← GET/POST /api/social/
│   └── ...
│
├── WebSocket Services
│   ├── websocketService.ts      ← Wrapper WebSocket générique
│   └── notificationWebSocket.ts ← WS persistant /ws/notifications/
│
└── Utilitaires
    ├── tokenService.ts   ← Lecture/écriture JWT en localStorage
    ├── soundEffects.ts   ← Howler.js : sons de jeu
    └── youtubeService.ts ← Contrôle iframe YouTube
```

### `soundEffects.ts` — Howler.js

Howler.js est une bibliothèque audio JavaScript cross-browser qui gère la lecture de fichiers audio (MP3, OGG) avec une API simple.

```typescript
import { Howl } from 'howler'

const sounds = {
  correct: new Howl({ src: ['/sounds/correct.mp3'] }),
  wrong: new Howl({ src: ['/sounds/wrong.mp3'] }),
  roundStart: new Howl({ src: ['/sounds/round-start.mp3'] }),
  gameOver: new Howl({ src: ['/sounds/game-over.mp3'] }),
}

export const playSound = (name: keyof typeof sounds) => {
  sounds[name].play()
}
```

### `youtubeService.ts` — YouTube IFrame API

Pour le mode Karaoké, le contenu vidéo est fourni par YouTube. Ce service gère le lecteur YouTube embarqué via l'API IFrame.

```typescript
// Crée un lecteur YouTube dans un div donné
export const createYouTubePlayer = (
  containerId: string,
  videoId: string,
  onReady: () => void
): YT.Player => {
  return new YT.Player(containerId, {
    videoId,
    events: { onReady }
  })
}
```

---

## Types TypeScript (`types/index.ts`)

Tous les types partagés sont centralisés dans un seul fichier. Exemples :

```typescript
// Types principaux
interface User {
  id: number
  username: string
  email: string
  avatar_url: string | null
  coins_balance: number
}

interface Game {
  id: number
  room_code: string
  status: 'waiting' | 'in_progress' | 'finished' | 'cancelled'
  game_mode: GameMode
  answer_mode: 'mcq' | 'text'
  guess_target: 'title' | 'artist'
  current_round: number
  total_rounds: number
  host: User
  players: GamePlayer[]
}

interface GamePlayer {
  user: User
  score: number
  rank: number
  consecutive_correct: number
  is_connected: boolean
}

type GameMode = 'classique' | 'rapide' | 'generation' | 'paroles' | 'karaoke' | 'mollo'
```

---

## Utilitaires (`utils/`)

### `formatAnswer.ts`

Normalise une réponse texte avant comparaison ou affichage. Gère :
- Suppression des accents (`café` → `cafe`)
- Mise en minuscules
- Suppression des caractères spéciaux
- Gestion des articles (`The Beatles` = `Beatles`)

```typescript
export const normalizeAnswer = (answer: string): string => {
  return answer
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // supprime les accents
    .replace(/[^a-z0-9\s]/g, '')     // supprime les caractères spéciaux
    .trim()
}
```

### `mergeUpdatedPlayers.ts`

Lors des mises à jour WebSocket, seul un sous-ensemble de données joueurs peut être envoyé. Cette fonction fusionne intelligemment les nouvelles données avec l'état existant.

```typescript
export const mergeUpdatedPlayers = (
  existing: GamePlayer[],
  updates: Partial<GamePlayer>[]
): GamePlayer[] => {
  return existing.map(player => {
    const update = updates.find(u => u.user?.id === player.user.id)
    return update ? { ...player, ...update } : player
  })
}
```

---

## Résumé de l'architecture frontend

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PAGES / ROUTES                             │
│         (HomePage, GamePlayPage, ProfilePage, ...)                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ utilisent
┌──────────────────────▼──────────────────────────────────────────────┐
│                        COMPOSANTS                                   │
│     (QuizQuestion, LiveScoreboard, Header, ...)                     │
└──────┬───────────────┬──────────────────┬───────────────────────────┘
       │               │                  │
  lisent/écrivent  utilisent          font appel
       │               │                  │
┌──────▼──────┐  ┌─────▼──────┐  ┌───────▼──────────┐
│   STORES    │  │   HOOKS    │  │    SERVICES       │
│  (Zustand)  │  │ (useQuery, │  │ (api.ts, WS, ...) │
│             │  │  useTimer) │  │                   │
└─────────────┘  └────────────┘  └──────────────────┘
                                          │
                              ┌───────────▼──────────┐
                              │     BACKEND          │
                              │  REST API  WebSocket │
                              └──────────────────────┘
```
