# Routes API — Référence complète — InstantMusic

> Documentation exhaustive de toutes les routes REST de l'API InstantMusic. Pour chaque groupe : tableau récapitulatif, exemples de payload JSON, codes HTTP retournés et politique d'authentification.

---

## Table des matières

1. [Conventions générales](#conventions-générales)
2. [Authentification (`/api/auth/`)](#authentification-apiauth)
3. [Utilisateurs (`/api/users/`)](#utilisateurs-apiusers)
4. [Parties (`/api/games/`)](#parties-apigames)
5. [Playlists (`/api/playlists/`)](#playlists-apiplaylists)
6. [Succès (`/api/achievements/`)](#succès-apiachievements)
7. [Statistiques (`/api/stats/`)](#statistiques-apistats)
8. [Administration (`/api/administration/`)](#administration-apiadministration)
9. [Boutique (`/api/shop/`)](#boutique-apishop)
10. [Infrastructure](#infrastructure)

---

## Conventions générales

### Authentification

Toutes les routes protégées nécessitent un **Bearer JWT** dans l'en-tête HTTP :

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Le token d'accès a une durée de vie de **24 heures**. Passée cette durée, utiliser `/api/auth/token/refresh/` pour obtenir un nouveau token.

### Format des erreurs

```json
{
  "detail": "Message d'erreur lisible"
}

// Erreurs de validation (400)
{
  "field_name": ["Message d'erreur de validation"]
}

// Erreurs multiples
{
  "username": ["Ce nom d'utilisateur est déjà pris."],
  "email": ["Entrez une adresse email valide."]
}
```

### Pagination

Les listes paginées suivent ce format :

```json
{
  "count": 150,
  "next": "https://api.instantmusic.fr/api/games/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Codes HTTP standards

| Code                      | Signification                            |
| ------------------------- | ---------------------------------------- |
| `200 OK`                  | Succès (GET, PATCH)                      |
| `201 Created`             | Ressource créée (POST)                   |
| `204 No Content`          | Suppression réussie (DELETE)             |
| `400 Bad Request`         | Données invalides                        |
| `401 Unauthorized`        | Token manquant ou expiré                 |
| `403 Forbidden`           | Accès refusé (permissions insuffisantes) |
| `404 Not Found`           | Ressource inexistante                    |
| `409 Conflict`            | Conflit (ex: joueur déjà dans la partie) |
| `429 Too Many Requests`   | Rate limit atteint                       |
| `503 Service Unavailable` | Mode maintenance actif                   |

---

## Authentification `/api/auth/`

### Tableau récapitulatif

| Méthode | URL                                 | Description         | Auth                   |
| ------- | ----------------------------------- | ------------------- | ---------------------- |
| `POST`  | `/api/auth/register/`               | Créer un compte     | Public                 |
| `POST`  | `/api/auth/login/`                  | Connexion           | Public                 |
| `POST`  | `/api/auth/logout/`                 | Déconnexion         | JWT                    |
| `POST`  | `/api/auth/token/refresh/`          | Rafraîchir le token | Public (refresh token) |
| `POST`  | `/api/auth/password/reset/`         | Demande de reset    | Public                 |
| `POST`  | `/api/auth/password/reset/confirm/` | Confirmer le reset  | Public (token email)   |
| `POST`  | `/api/auth/google/`                 | OAuth 2.0 Google    | Public                 |

---

### `POST /api/auth/register/`

Crée un nouveau compte utilisateur et retourne une paire de tokens JWT.

**Request :**
```json
{
  "username": "alice_dupont",
  "email": "alice@example.com",
  "password": "MotDePasseSecurise123!",
  "password_confirm": "MotDePasseSecurise123!"
}
```

**Response `201 Created` :**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice_dupont",
    "email": "alice@example.com",
    "avatar": null,
    "total_games_played": 0,
    "total_wins": 0,
    "total_points": 0,
    "coins_balance": 0,
    "created_at": "2026-03-07T10:00:00Z"
  },
  "access": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Codes HTTP :**
- `201` : Compte créé avec succès
- `400` : Données invalides (email déjà utilisé, mots de passe différents, etc.)

---

### `POST /api/auth/login/`

**Request :**
```json
{
  "email": "alice@example.com",
  "password": "MotDePasseSecurise123!"
}
```

**Response `200 OK` :**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice_dupont",
    "email": "alice@example.com",
    "avatar": "https://cdn.instantmusic.fr/avatars/alice.jpg",
    "total_games_played": 45,
    "total_wins": 12,
    "total_points": 48250,
    "coins_balance": 320,
    "win_rate": 26.7
  },
  "access": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Codes HTTP :**
- `200` : Connexion réussie
- `400` : Identifiants manquants
- `401` : Email ou mot de passe incorrect

---

### `POST /api/auth/logout/`

Invalide (blackliste) le refresh token pour empêcher son réutilisation.

**Request :**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Response `204 No Content`** (corps vide)

**Codes HTTP :**
- `204` : Déconnexion réussie
- `400` : Token refresh manquant ou déjà blacklisté
- `401` : Access token invalide

---

### `POST /api/auth/token/refresh/`

**Request :**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Response `200 OK` :**
```json
{
  "access": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiJ9..."
}
```

> Note : Le refresh token est **rotatif** — l'ancien est invalidé et un nouveau est retourné à chaque renouvellement.

**Codes HTTP :**
- `200` : Tokens renouvelés
- `401` : Refresh token expiré ou blacklisté

---

### `POST /api/auth/password/reset/`

**Request :**
```json
{
  "email": "alice@example.com"
}
```

**Response `200 OK` :**
```json
{
  "detail": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."
}
```

> Retourne toujours `200` pour ne pas révéler si l'email existe.

---

### `POST /api/auth/password/reset/confirm/`

**Request :**
```json
{
  "token": "abc123def456...",
  "uid": "MjA",
  "new_password": "NouveauMotDePasse456!",
  "new_password_confirm": "NouveauMotDePasse456!"
}
```

**Response `200 OK` :**
```json
{
  "detail": "Mot de passe réinitialisé avec succès."
}
```

**Codes HTTP :**
- `200` : Succès
- `400` : Token invalide ou expiré, mots de passe non correspondants

---

### `POST /api/auth/google/`

Authentification via Google OAuth 2.0. Le frontend récupère le code d'autorisation Google et l'envoie au backend.

**Request :**
```json
{
  "code": "4/0AcvDMrBkXx8g...",
  "redirect_uri": "https://instantmusic.fr/auth/google/callback"
}
```

**Response `200 OK` :**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice_dupont",
    "email": "alice@gmail.com",
    "avatar": "https://lh3.googleusercontent.com/..."
  },
  "access": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiJ9...",
  "is_new_user": false
}
```

**Codes HTTP :**
- `200` : Connexion réussie (compte existant)
- `201` : Nouveau compte créé
- `400` : Code Google invalide ou expiré

---

## Utilisateurs `/api/users/`

### Tableau récapitulatif

| Méthode  | URL                        | Description                  | Auth               |
| -------- | -------------------------- | ---------------------------- | ------------------ |
| `GET`    | `/api/users/`              | Liste des utilisateurs       | JWT                |
| `GET`    | `/api/users/{id}/`         | Profil d'un utilisateur      | JWT                |
| `PATCH`  | `/api/users/{id}/`         | Mettre à jour le profil      | JWT (propriétaire) |
| `DELETE` | `/api/users/{id}/`         | Supprimer le compte          | JWT (propriétaire) |
| `GET`    | `/api/users/friends/`      | Liste des amitiés            | JWT                |
| `POST`   | `/api/users/friends/`      | Envoyer une demande d'amitié | JWT                |
| `GET`    | `/api/users/friends/{id}/` | Détail d'une amitié          | JWT                |
| `PATCH`  | `/api/users/friends/{id}/` | Accepter ou refuser          | JWT                |
| `DELETE` | `/api/users/friends/{id}/` | Supprimer une amitié         | JWT                |
| `GET`    | `/api/users/teams/`        | Liste des équipes            | JWT                |
| `POST`   | `/api/users/teams/`        | Créer une équipe             | JWT                |
| `GET`    | `/api/users/teams/{id}/`   | Détail d'une équipe          | JWT                |
| `PATCH`  | `/api/users/teams/{id}/`   | Modifier l'équipe            | JWT (owner/admin)  |
| `DELETE` | `/api/users/teams/{id}/`   | Supprimer l'équipe           | JWT (owner)        |

---

### `GET /api/users/{id}/`

**Response `200 OK` :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice_dupont",
  "avatar": "https://cdn.instantmusic.fr/avatars/alice.jpg",
  "total_games_played": 45,
  "total_wins": 12,
  "total_points": 48250,
  "coins_balance": 320,
  "win_rate": 26.7,
  "created_at": "2025-01-15T10:00:00Z",
  "team": {
    "id": "660e8400-...",
    "name": "Les Champions",
    "role": "member"
  }
}
```

**Codes HTTP :**
- `200` : Succès
- `401` : Non authentifié
- `404` : Utilisateur introuvable

---

### `PATCH /api/users/{id}/`

Mise à jour partielle du profil. Seul le propriétaire du compte peut modifier son profil.

**Request (multipart/form-data pour l'avatar) :**
```
Content-Type: multipart/form-data

avatar: [fichier image]
username: alice_new
```

**Response `200 OK` :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice_new",
  "avatar": "https://cdn.instantmusic.fr/avatars/alice_new.jpg",
  "updated_at": "2026-03-07T10:30:00Z"
}
```

**Codes HTTP :**
- `200` : Succès
- `400` : Données invalides
- `403` : Tentative de modification du compte d'un autre utilisateur

---

### `POST /api/users/friends/`

**Request :**
```json
{
  "to_user": "661e8400-e29b-41d4-a716-446655440001"
}
```

**Response `201 Created` :**
```json
{
  "id": "770e8400-...",
  "from_user": { "id": "550e...", "username": "alice_dupont" },
  "to_user": { "id": "661e...", "username": "bob_martin" },
  "status": "pending",
  "created_at": "2026-03-07T10:00:00Z"
}
```

**Codes HTTP :**
- `201` : Demande envoyée
- `400` : Demande déjà envoyée ou amitié déjà existante
- `404` : Utilisateur destinataire introuvable

---

### `PATCH /api/users/friends/{id}/`

Accepter ou refuser une demande d'amitié reçue.

**Request :**
```json
{
  "status": "accepted"
}
```

**Response `200 OK` :**
```json
{
  "id": "770e8400-...",
  "from_user": { "id": "550e...", "username": "alice_dupont" },
  "to_user": { "id": "661e...", "username": "bob_martin" },
  "status": "accepted",
  "updated_at": "2026-03-07T10:05:00Z"
}
```

**Codes HTTP :**
- `200` : Succès
- `400` : Statut invalide
- `403` : Seul le destinataire peut accepter/refuser

---

### `POST /api/users/teams/`

**Request :**
```json
{
  "name": "Les Champions",
  "description": "Équipe de joueurs passionnés de musique des années 90"
}
```

**Response `201 Created` :**
```json
{
  "id": "660e8400-...",
  "name": "Les Champions",
  "description": "Équipe de joueurs passionnés de musique des années 90",
  "avatar": null,
  "owner": {
    "id": "550e8400-...",
    "username": "alice_dupont"
  },
  "members_count": 1,
  "total_games": 0,
  "total_wins": 0,
  "total_points": 0,
  "created_at": "2026-03-07T10:00:00Z"
}
```

**Codes HTTP :**
- `201` : Équipe créée
- `400` : Nom déjà pris ou données invalides
- `409` : L'utilisateur est déjà propriétaire d'une équipe

---

## Parties `/api/games/`

### Tableau récapitulatif

| Méthode  | URL                                     | Description                   | Auth       | Throttle |
| -------- | --------------------------------------- | ----------------------------- | ---------- | -------- |
| `GET`    | `/api/games/`                           | Liste des parties             | JWT        | —        |
| `POST`   | `/api/games/`                           | Créer une partie              | JWT        | 10/min   |
| `GET`    | `/api/games/{room_code}/`               | Détail d'une partie           | JWT        | —        |
| `PATCH`  | `/api/games/{room_code}/`               | Modifier la config            | JWT (hôte) | —        |
| `DELETE` | `/api/games/{room_code}/`               | Supprimer                     | JWT (hôte) | —        |
| `POST`   | `/api/games/{room_code}/join/`          | Rejoindre                     | JWT        | 20/min   |
| `POST`   | `/api/games/{room_code}/leave/`         | Quitter                       | JWT        | —        |
| `POST`   | `/api/games/{room_code}/start/`         | Démarrer                      | JWT (hôte) | —        |
| `GET`    | `/api/games/{room_code}/current-round/` | Round en cours                | JWT        | —        |
| `POST`   | `/api/games/{room_code}/answer/`        | Soumettre une réponse         | JWT        | —        |
| `POST`   | `/api/games/{room_code}/end-round/`     | Forcer fin de round           | JWT (hôte) | —        |
| `POST`   | `/api/games/{room_code}/next-round/`    | Round suivant                 | JWT (hôte) | —        |
| `GET`    | `/api/games/{room_code}/results/`       | Résultats finaux              | JWT        | —        |
| `GET`    | `/api/games/{room_code}/results/pdf/`   | PDF des résultats             | JWT        | —        |
| `GET`    | `/api/games/available/`                 | Parties publiques             | JWT        | —        |
| `GET`    | `/api/games/public/`                    | Parties publiques (recherche) | JWT        | —        |
| `GET`    | `/api/games/history/`                   | Historique                    | JWT        | —        |
| `GET`    | `/api/games/leaderboard/`               | Classement global             | JWT        | —        |
| `POST`   | `/api/games/{room_code}/invite/`        | Inviter un ami                | JWT (hôte) | —        |
| `GET`    | `/api/games/my-invitations/`            | Invitations reçues            | JWT        | —        |
| `POST`   | `/api/games/invitations/{id}/accept/`   | Accepter invitation           | JWT        | —        |
| `POST`   | `/api/games/invitations/{id}/decline/`  | Refuser invitation            | JWT        | —        |
| `GET`    | `/api/games/karaoke-songs/`             | Chansons karaoké              | JWT        | —        |
| `GET`    | `/api/games/karaoke-songs/{id}/`        | Détail chanson                | JWT        | —        |

---

### `POST /api/games/`

Crée une nouvelle partie. La `room_code` est générée automatiquement.

**Request :**
```json
{
  "name": "Soirée années 90",
  "mode": "classique",
  "guess_target": "title",
  "max_players": 6,
  "num_rounds": 10,
  "playlist_id": "3155776842",
  "is_public": true,
  "answer_mode": "mcq",
  "round_duration": 30,
  "timer_start_round": 5,
  "score_display_duration": 10
}
```

**Response `201 Created` :**
```json
{
  "id": "880e8400-...",
  "room_code": "AB1C2D",
  "name": "Soirée années 90",
  "host": {
    "id": "550e8400-...",
    "username": "alice_dupont",
    "avatar": "https://cdn.instantmusic.fr/avatars/alice.jpg"
  },
  "mode": "classique",
  "guess_target": "title",
  "status": "waiting",
  "max_players": 6,
  "num_rounds": 10,
  "playlist_id": "3155776842",
  "playlist_name": "Les hits des années 90",
  "playlist_image_url": "https://cdns-images.dzcdn.net/...",
  "is_public": true,
  "answer_mode": "mcq",
  "round_duration": 30,
  "timer_start_round": 5,
  "score_display_duration": 10,
  "players_count": 1,
  "created_at": "2026-03-07T10:00:00Z"
}
```

**Codes HTTP :**
- `201` : Partie créée
- `400` : Données invalides (mode inconnu, playlist inexistante, etc.)
- `429` : Rate limit (10 créations par minute)

---

### `GET /api/games/{room_code}/`

**Response `200 OK` :**
```json
{
  "id": "880e8400-...",
  "room_code": "AB1C2D",
  "name": "Soirée années 90",
  "host": { "id": "550e...", "username": "alice_dupont" },
  "mode": "classique",
  "status": "waiting",
  "max_players": 6,
  "num_rounds": 10,
  "players": [
    {
      "id": "990e8400-...",
      "user": { "id": "550e...", "username": "alice_dupont", "avatar": "..." },
      "score": 0,
      "rank": null,
      "is_connected": true,
      "joined_at": "2026-03-07T10:00:00Z"
    }
  ],
  "created_at": "2026-03-07T10:00:00Z"
}
```

**Codes HTTP :**
- `200` : Succès
- `404` : Partie introuvable

---

### `POST /api/games/{room_code}/join/`

Rejoint une partie en attente. Déclenche un broadcast WebSocket `player_joined` à tous les joueurs connectés.

**Request :** (corps vide)

**Response `200 OK` :**
```json
{
  "game_player_id": "990e8400-...",
  "room_code": "AB1C2D",
  "websocket_url": "ws://localhost:8000/ws/game/AB1C2D/"
}
```

**Codes HTTP :**
- `200` : Partie rejointe
- `400` : Partie pleine ou pas en statut `waiting`
- `409` : Déjà dans la partie
- `429` : Rate limit (20 tentatives par minute)

---

### `POST /api/games/{room_code}/start/`

Démarre la partie : génère tous les rounds et envoie `start_round` via WebSocket.

**Request :** (corps vide, hôte seulement)

**Response `200 OK` :**
```json
{
  "status": "in_progress",
  "rounds_generated": 10,
  "started_at": "2026-03-07T10:05:00Z"
}
```

**Codes HTTP :**
- `200` : Partie démarrée
- `400` : Pas assez de joueurs ou partie déjà démarrée
- `403` : L'appelant n'est pas l'hôte
- `422` : Impossible de générer les rounds (playlist vide ou erreur Deezer)

---

### `GET /api/games/{room_code}/current-round/`

Retourne les informations du round en cours **sans révéler la bonne réponse**.

**Response `200 OK` :**
```json
{
  "round_id": "aa0e8400-...",
  "round_number": 3,
  "question_type": "guess_title",
  "question_text": "Quel est le titre de cette chanson ?",
  "artist_name": "Daft Punk",
  "options": [
    "Get Lucky",
    "One More Time",
    "Around the World",
    "Harder Better Faster Stronger"
  ],
  "preview_url": "https://cdns-preview-4.dzcdn.net/stream/...",
  "duration": 30,
  "started_at": "2026-03-07T10:08:00Z",
  "time_remaining": 22
}
```

**Codes HTTP :**
- `200` : Succès
- `404` : Pas de round en cours (partie terminée ou pas encore démarrée)

---

### `POST /api/games/{room_code}/answer/`

Soumet la réponse d'un joueur au round en cours. Le score est calculé immédiatement.

**Request :**
```json
{
  "round_id": "aa0e8400-...",
  "answer": "Get Lucky",
  "response_time": 8.3
}
```

**Response `200 OK` :**
```json
{
  "is_correct": true,
  "points_earned": 1350,
  "streak_bonus": 100,
  "consecutive_correct": 3,
  "total_score": 4200,
  "correct_answer": "Get Lucky"
}
```

**Codes HTTP :**
- `200` : Réponse enregistrée
- `400` : Round terminé ou réponse déjà soumise pour ce round
- `409` : Round ID ne correspond pas au round actif

---

### `GET /api/games/{room_code}/results/`

Retourne le classement final et les statistiques de la partie terminée.

**Response `200 OK` :**
```json
{
  "game": {
    "id": "880e8400-...",
    "room_code": "AB1C2D",
    "name": "Soirée années 90",
    "mode": "classique",
    "num_rounds": 10,
    "started_at": "2026-03-07T10:05:00Z",
    "finished_at": "2026-03-07T10:20:00Z",
    "duration_seconds": 900
  },
  "leaderboard": [
    {
      "rank": 1,
      "user": { "id": "550e...", "username": "alice_dupont", "avatar": "..." },
      "score": 12450,
      "correct_answers": 9,
      "accuracy": 90.0,
      "best_streak": 5,
      "average_response_time": 7.2
    },
    {
      "rank": 2,
      "user": { "id": "661e...", "username": "bob_martin", "avatar": "..." },
      "score": 10800,
      "correct_answers": 8,
      "accuracy": 80.0,
      "best_streak": 3,
      "average_response_time": 9.1
    }
  ],
  "rounds_summary": [
    {
      "round_number": 1,
      "track_name": "Lose Yourself",
      "artist_name": "Eminem",
      "correct_answer": "Lose Yourself",
      "players_correct": 3,
      "fastest_answer": { "username": "alice_dupont", "time": 3.2 }
    }
  ]
}
```

**Codes HTTP :**
- `200` : Succès
- `400` : Partie pas encore terminée
- `404` : Partie introuvable

---

### `GET /api/games/{room_code}/results/pdf/`

Télécharge un fichier PDF du classement final (généré avec ReportLab).

**Response `200 OK` :**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="instantmusic-AB1C2D-results.pdf"

[Contenu binaire PDF]
```

**Codes HTTP :**
- `200` : PDF généré
- `400` : Partie pas encore terminée

---

### `POST /api/games/{room_code}/invite/`

Invite un utilisateur à rejoindre la partie. L'invitation expire après 30 minutes.

**Request :**
```json
{
  "username": "bob_martin"
}
```

**Response `201 Created` :**
```json
{
  "id": "bb0e8400-...",
  "game": { "room_code": "AB1C2D", "name": "Soirée années 90" },
  "sender": { "username": "alice_dupont" },
  "recipient": { "username": "bob_martin" },
  "status": "pending",
  "expires_at": "2026-03-07T10:30:00Z"
}
```

**Codes HTTP :**
- `201` : Invitation envoyée
- `400` : Utilisateur introuvable ou déjà dans la partie
- `403` : L'appelant n'est pas l'hôte
- `409` : Une invitation en attente existe déjà pour ce joueur

---

### `POST /api/games/invitations/{id}/accept/`

Accepte une invitation et rejoint automatiquement la partie.

**Request :** (corps vide)

**Response `200 OK` :**
```json
{
  "invitation_id": "bb0e8400-...",
  "game_player_id": "cc0e8400-...",
  "room_code": "AB1C2D",
  "websocket_url": "ws://localhost:8000/ws/game/AB1C2D/"
}
```

**Codes HTTP :**
- `200` : Invitation acceptée et partie rejointe
- `400` : Invitation expirée, annulée ou partie pleine
- `403` : L'invitation n'est pas adressée à l'utilisateur connecté

---

### `GET /api/games/history/`

Historique paginé des parties terminées, triées par date décroissante.

**Paramètres de requête :**
- `page` : Numéro de page (défaut: 1)
- `page_size` : Taille de page (max: 50, défaut: 20)
- `mode` : Filtrer par mode de jeu

**Response `200 OK` :**
```json
{
  "count": 150,
  "next": "/api/games/history/?page=2",
  "previous": null,
  "results": [
    {
      "id": "880e8400-...",
      "room_code": "AB1C2D",
      "name": "Soirée années 90",
      "mode": "classique",
      "status": "finished",
      "players_count": 4,
      "winner": { "username": "alice_dupont" },
      "started_at": "2026-03-07T10:05:00Z",
      "finished_at": "2026-03-07T10:20:00Z"
    }
  ]
}
```

---

### `GET /api/games/karaoke-songs/`

**Paramètres de requête :**
- `search` : Filtrer par titre ou artiste

**Response `200 OK` :**
```json
{
  "count": 25,
  "results": [
    {
      "id": "dd0e8400-...",
      "title": "Never Gonna Give You Up",
      "artist": "Rick Astley",
      "album_image_url": "https://...",
      "duration_ms": 213000,
      "is_active": true
    }
  ]
}
```

---

## Playlists `/api/playlists/`

### Tableau récapitulatif

| Méthode | URL                    | Description                   | Auth |
| ------- | ---------------------- | ----------------------------- | ---- |
| `GET`   | `/api/playlists/`      | Recherche de playlists Deezer | JWT  |
| `GET`   | `/api/playlists/{id}/` | Détail d'une playlist         | JWT  |

---

### `GET /api/playlists/`

**Paramètres de requête :**
- `q` (requis) : Terme de recherche
- `limit` : Nombre de résultats (défaut: 20, max: 50)

**Response `200 OK` :**
```json
{
  "data": [
    {
      "id": "3155776842",
      "title": "Les hits des années 90",
      "description": "Les meilleures chansons de la décennie 90",
      "nb_tracks": 50,
      "fans": 125000,
      "picture_medium": "https://cdns-images.dzcdn.net/...",
      "creator": {
        "name": "Deezer Editorial"
      }
    }
  ],
  "total": 45,
  "cached": true
}
```

**Codes HTTP :**
- `200` : Succès
- `400` : Paramètre `q` manquant
- `503` : API Deezer indisponible

---

### `GET /api/playlists/{id}/`

**Response `200 OK` :**
```json
{
  "id": "3155776842",
  "title": "Les hits des années 90",
  "description": "...",
  "nb_tracks": 50,
  "tracks_with_preview": 47,
  "picture_medium": "https://cdns-images.dzcdn.net/...",
  "tracks": [
    {
      "id": "3135556",
      "title": "Smells Like Teen Spirit",
      "artist": { "name": "Nirvana" },
      "album": { "title": "Nevermind", "cover_medium": "..." },
      "duration": 301,
      "preview": "https://cdns-preview-2.dzcdn.net/stream/...",
      "release_date": "1991-09-10"
    }
  ]
}
```

**Codes HTTP :**
- `200` : Succès (potentiellement depuis le cache Redis)
- `404` : Playlist Deezer introuvable

---

## Succès `/api/achievements/`

### Tableau récapitulatif

| Méthode | URL                              | Description                             | Auth |
| ------- | -------------------------------- | --------------------------------------- | ---- |
| `GET`   | `/api/achievements/`             | Tous les succès disponibles             | JWT  |
| `GET`   | `/api/achievements/mine/`        | Succès débloqués (utilisateur connecté) | JWT  |
| `GET`   | `/api/achievements/user/{uuid}/` | Succès d'un utilisateur                 | JWT  |

---

### `GET /api/achievements/`

**Response `200 OK` :**
```json
[
  {
    "id": "ee0e8400-...",
    "name": "Premier pas",
    "description": "Terminer votre première partie",
    "icon": "https://cdn.instantmusic.fr/achievements/first-game.png",
    "points": 10,
    "condition_type": "games_played",
    "condition_value": 1,
    "condition_extra": null
  },
  {
    "id": "ff0e8400-...",
    "name": "Champion toutes catégories",
    "description": "Gagner une partie dans chaque mode de jeu",
    "icon": "https://cdn.instantmusic.fr/achievements/all-modes.png",
    "points": 50,
    "condition_type": "mode_specific",
    "condition_value": 1,
    "condition_extra": "all"
  }
]
```

---

### `GET /api/achievements/mine/`

**Response `200 OK` :**
```json
{
  "unlocked_count": 12,
  "total_count": 43,
  "total_points_earned": 185,
  "achievements": [
    {
      "id": "ee0e8400-...",
      "name": "Premier pas",
      "icon": "...",
      "points": 10,
      "unlocked_at": "2026-01-10T15:30:00Z"
    }
  ]
}
```

---

## Statistiques `/api/stats/`

### Tableau récapitulatif

| Méthode | URL                              | Description                                | Auth |
| ------- | -------------------------------- | ------------------------------------------ | ---- |
| `GET`   | `/api/stats/me/`                 | Stats détaillées de l'utilisateur connecté | JWT  |
| `GET`   | `/api/stats/leaderboard/`        | Classement global                          | JWT  |
| `GET`   | `/api/stats/leaderboard/teams/`  | Classement des équipes                     | JWT  |
| `GET`   | `/api/stats/leaderboard/{mode}/` | Classement par mode                        | JWT  |
| `GET`   | `/api/stats/my-rank/`            | Rang actuel + par mode                     | JWT  |
| `GET`   | `/api/stats/user/{user_id}/`     | Stats publiques d'un profil                | JWT  |

---

### `GET /api/stats/me/`

**Response `200 OK` :**
```json
{
  "user_id": "550e8400-...",
  "username": "alice_dupont",
  "global_stats": {
    "total_games_played": 45,
    "total_wins": 12,
    "win_rate": 26.7,
    "total_points": 48250,
    "average_score_per_game": 1072,
    "best_score_ever": 3200,
    "total_correct_answers": 387,
    "total_answers": 494,
    "accuracy_rate": 78.3,
    "average_response_time": 8.3,
    "best_streak_ever": 9,
    "coins_earned_total": 520
  },
  "stats_by_mode": {
    "classique": {
      "games_played": 20,
      "wins": 8,
      "average_score": 1150,
      "win_rate": 40.0
    },
    "rapide": {
      "games_played": 10,
      "wins": 2,
      "average_score": 980,
      "win_rate": 20.0
    },
    "generation": {
      "games_played": 8,
      "wins": 1,
      "average_score": 890,
      "win_rate": 12.5
    },
    "paroles": {
      "games_played": 5,
      "wins": 1,
      "average_score": 750,
      "win_rate": 20.0
    },
    "karaoke": {
      "games_played": 2,
      "wins": 0,
      "average_score": 600,
      "win_rate": 0.0
    }
  },
  "favorite_mode": "classique",
  "recent_games": [
    {
      "room_code": "AB1C2D",
      "mode": "classique",
      "score": 2100,
      "rank": 1,
      "players_count": 4,
      "finished_at": "2026-03-07T10:20:00Z"
    }
  ]
}
```

---

### `GET /api/stats/leaderboard/`

**Paramètres de requête :**
- `page` : Numéro de page
- `period` : `all_time` (défaut), `week`, `month`

**Response `200 OK` :**
```json
{
  "count": 500,
  "period": "all_time",
  "next": "/api/stats/leaderboard/?page=2",
  "results": [
    {
      "rank": 1,
      "user": {
        "id": "550e8400-...",
        "username": "alice_dupont",
        "avatar": "..."
      },
      "total_points": 48250,
      "total_wins": 12,
      "games_played": 45,
      "win_rate": 26.7
    }
  ]
}
```

---

### `GET /api/stats/my-rank/`

**Response `200 OK` :**
```json
{
  "global_rank": 42,
  "total_players": 500,
  "percentile": 91.6,
  "rank_by_mode": {
    "classique": 15,
    "rapide": 87,
    "generation": 103,
    "paroles": 56,
    "karaoke": null
  }
}
```

---

## Administration `/api/administration/`

### Tableau récapitulatif

| Méthode | URL                                      | Description                   | Auth   |
| ------- | ---------------------------------------- | ----------------------------- | ------ |
| `GET`   | `/api/administration/status/`            | Statut maintenance + bannière | Public |
| `GET`   | `/api/administration/legal/{page_type}/` | Contenu page légale           | Public |

---

### `GET /api/administration/status/`

Consulté par le frontend au démarrage pour afficher l'état du site.

**Response `200 OK` :**
```json
{
  "maintenance_mode": false,
  "maintenance_title": null,
  "maintenance_message": null,
  "banner": {
    "enabled": true,
    "message": "Mise à jour prévue le 15 mars à 2h du matin.",
    "color": "warning",
    "dismissible": true
  }
}
```

**Response quand maintenance activée :**
```json
{
  "maintenance_mode": true,
  "maintenance_title": "Maintenance en cours",
  "maintenance_message": "Nous effectuons une mise à jour. Retour prévu dans 30 minutes.",
  "banner": null
}
```

---

### `GET /api/administration/legal/{page_type}/`

`{page_type}` : `privacy` ou `legal`

**Response `200 OK` :**
```json
{
  "page_type": "privacy",
  "title": "Politique de confidentialité",
  "content": "## 1. Introduction\n\nNous respectons votre vie privée...",
  "updated_at": "2026-01-15T00:00:00Z"
}
```

**Codes HTTP :**
- `200` : Succès
- `404` : Type de page invalide ou page non encore créée

---

## Boutique `/api/shop/`

### Tableau récapitulatif

| Méthode | URL                         | Description                    | Auth |
| ------- | --------------------------- | ------------------------------ | ---- |
| `GET`   | `/api/shop/items/`          | Liste des articles disponibles | JWT  |
| `GET`   | `/api/shop/items/{id}/`     | Détail d'un article            | JWT  |
| `POST`  | `/api/shop/items/{id}/buy/` | Acheter un article             | JWT  |
| `GET`   | `/api/shop/inventory/`      | Inventaire de l'utilisateur    | JWT  |

---

### `GET /api/shop/items/`

**Response `200 OK` :**
```json
[
  {
    "id": "gg0e8400-...",
    "name": "Points doublés",
    "description": "Multiplie vos points par 2 pour le prochain round",
    "icon": "https://cdn.instantmusic.fr/shop/double-points.png",
    "item_type": "bonus",
    "bonus_type": "double_points",
    "cost": 100,
    "is_event_only": false,
    "is_available": true,
    "stock": null,
    "sort_order": 1,
    "user_quantity": 2
  }
]
```

> `user_quantity` : quantité déjà possédée par l'utilisateur connecté.

---

### `POST /api/shop/items/{id}/buy/`

**Request :**
```json
{
  "quantity": 1
}
```

**Response `200 OK` :**
```json
{
  "item": {
    "id": "gg0e8400-...",
    "name": "Points doublés",
    "cost": 100
  },
  "quantity_purchased": 1,
  "new_coins_balance": 220,
  "new_inventory_quantity": 3
}
```

**Codes HTTP :**
- `200` : Achat réussi
- `400` : Article non disponible ou stock épuisé
- `402` : Solde de coins insuffisant

---

### `GET /api/shop/inventory/`

**Response `200 OK` :**
```json
{
  "coins_balance": 220,
  "items": [
    {
      "id": "hh0e8400-...",
      "item": {
        "id": "gg0e8400-...",
        "name": "Points doublés",
        "icon": "...",
        "bonus_type": "double_points"
      },
      "quantity": 3,
      "purchased_at": "2026-03-07T09:00:00Z"
    }
  ]
}
```

---

## Infrastructure

### Tableau récapitulatif

| Méthode | URL            | Description                | Auth         |
| ------- | -------------- | -------------------------- | ------------ |
| `GET`   | `/api/health/` | Health check global        | Public       |
| `GET`   | `/api/ready/`  | Readiness probe            | Public       |
| `GET`   | `/api/alive/`  | Liveness probe             | Public       |
| `GET`   | `/metrics/`    | Métriques Prometheus       | IP whitelist |
| `GET`   | `/api/schema/` | OpenAPI schema (JSON/YAML) | Public       |
| `GET`   | `/api/docs/`   | Interface Swagger UI       | Public       |
| `GET`   | `/api/redoc/`  | Interface ReDoc            | Public       |

---

### `GET /api/health/`

Vérifie la connectivité avec tous les services tiers (DB, Redis, Celery).

**Response `200 OK` :**
```json
{
  "status": "healthy",
  "version": "1.4.2",
  "environment": "production",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 2.3,
      "details": "PostgreSQL 15.4"
    },
    "redis": {
      "status": "ok",
      "latency_ms": 0.8,
      "details": "Redis 7.2"
    },
    "celery": {
      "status": "ok",
      "workers": 2,
      "queues": ["celery", "achievements", "maintenance"]
    }
  },
  "timestamp": "2026-03-07T10:00:00Z"
}
```

**Response `503 Service Unavailable` (service en panne) :**
```json
{
  "status": "unhealthy",
  "checks": {
    "database": { "status": "ok", "latency_ms": 2.3 },
    "redis": {
      "status": "error",
      "error": "Connection refused to redis:6379"
    },
    "celery": { "status": "ok", "workers": 2 }
  },
  "timestamp": "2026-03-07T10:00:00Z"
}
```

---

### `GET /api/ready/`

Readiness probe Kubernetes : retourne `200` si le service est prêt à recevoir du trafic (migrations appliquées, connexions DB établies).

**Response `200 OK` :**
```json
{
  "status": "ready"
}
```

---

### `GET /api/alive/`

Liveness probe Kubernetes : retourne `200` si le processus est en vie.

**Response `200 OK` :**
```json
{
  "status": "alive"
}
```

---

### `GET /metrics/`

Endpoint Prometheus. Retourne les métriques au format texte Prometheus (non JSON).

```
# HELP http_requests_total Total des requêtes HTTP
# TYPE http_requests_total counter
http_requests_total{method="POST",path="/api/games/",status="201"} 1547.0

# HELP http_request_duration_seconds Latence des requêtes HTTP
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",path="/api/games/{room_code}/",le="0.1"} 4200.0
http_request_duration_seconds_bucket{method="GET",path="/api/games/{room_code}/",le="0.5"} 4800.0

# HELP games_created_total Parties créées
# TYPE games_created_total counter
games_created_total{mode="classique"} 890.0
games_created_total{mode="rapide"} 345.0

# HELP players_online_gauge Joueurs actuellement connectés
# TYPE players_online_gauge gauge
players_online_gauge 42.0
```

> Cet endpoint est protégé par whitelist d'IP (Prometheus scraper uniquement). Retourne `403` pour les IPs non autorisées.

---

## WebSocket `/ws/game/{room_code}/`

> L'URL WebSocket n'est pas une route REST. Elle est documentée ici pour référence complète.

**Connexion :**
```
ws://localhost:8000/ws/game/AB1C2D/?token=eyJhbGciOiJIUzI1NiJ9...
```

**Codes de fermeture :**

| Code   | Signification                |
| ------ | ---------------------------- |
| `1000` | Fermeture normale            |
| `4003` | Token JWT invalide ou absent |
| `4004` | Partie introuvable           |
| `4005` | Partie terminée              |

Pour la documentation complète du protocole WebSocket (messages entrants/sortants), voir [02-apps.md — GameConsumer](./02-apps.md#consumer-websocket--gameconsumer).

---

> Voir aussi :
> - [01-structure.md](./01-structure.md) — Structure des dossiers et configuration
> - [02-apps.md](./02-apps.md) — Rôle détaillé de chaque application Django
> - [03-models-mcd.md](./03-models-mcd.md) — MCD complet et documentation des modèles
