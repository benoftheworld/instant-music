# Applications Django — InstantMusic

> Documentation détaillée du rôle, des modèles, des endpoints, des tâches Celery, des services et des commandes de gestion de chaque application Django du projet.

---

## Table des matières

1. [users](#1-users)
2. [authentication](#2-authentication)
3. [games](#3-games)
4. [playlists](#4-playlists)
5. [achievements](#5-achievements)
6. [administration](#6-administration)
7. [shop](#7-shop)
8. [stats](#8-stats)
9. [core](#9-core)

---

## 1. `users`

### Rôle

Gère l'identité des utilisateurs de la plateforme, les équipes (teams), les demandes d'adhésion et le système d'amitié. Fournit le modèle `User` custom qui remplace `django.contrib.auth.models.User` via `AUTH_USER_MODEL = "users.User"`.

### Particularité : chiffrement des emails

L'adresse email des utilisateurs est chiffrée au repos en base de données via AES Fernet (`cryptography`). Un champ dérivé `email_hash` (HMAC-SHA256) permet les lookups sans déchiffrer toute la table.

```
Email brut : "alice@example.com"
      │
      ├── AES Fernet → Stocké dans email (illisible en DB)
      │
      └── HMAC-SHA256 → Stocké dans email_hash (lookup)
              ↑
        Clé secrète FERNET_KEY (variable d'environnement)
```

### Modèles

| Modèle            | Description                                                 |
| ----------------- | ----------------------------------------------------------- |
| `User`            | Utilisateur custom avec UUID, email chiffré, stats agrégées |
| `Team`            | Équipe de joueurs avec propriétaire et stats collectives    |
| `TeamMember`      | Relation many-to-many User↔Team avec rôle                   |
| `TeamJoinRequest` | Demande d'adhésion à une équipe                             |
| `Friendship`      | Relation d'amitié bidirectionnelle entre utilisateurs       |

### Endpoints API

| Méthode  | URL                        | Description                          | Auth               |
| -------- | -------------------------- | ------------------------------------ | ------------------ |
| `GET`    | `/api/users/`              | Liste des utilisateurs               | JWT                |
| `GET`    | `/api/users/{id}/`         | Profil d'un utilisateur              | JWT                |
| `PATCH`  | `/api/users/{id}/`         | Mise à jour du profil (avatar, etc.) | JWT (propriétaire) |
| `DELETE` | `/api/users/{id}/`         | Suppression du compte                | JWT (propriétaire) |
| `GET`    | `/api/users/friends/`      | Liste des amitiés                    | JWT                |
| `POST`   | `/api/users/friends/`      | Envoyer une demande d'amitié         | JWT                |
| `GET`    | `/api/users/friends/{id}/` | Détail d'une amitié                  | JWT                |
| `PATCH`  | `/api/users/friends/{id}/` | Accepter ou refuser                  | JWT                |
| `DELETE` | `/api/users/friends/{id}/` | Supprimer une amitié                 | JWT                |
| `GET`    | `/api/users/teams/`        | Liste des équipes                    | JWT                |
| `POST`   | `/api/users/teams/`        | Créer une équipe                     | JWT                |
| `GET`    | `/api/users/teams/{id}/`   | Détail d'une équipe                  | JWT                |
| `PATCH`  | `/api/users/teams/{id}/`   | Modifier l'équipe                    | JWT (owner/admin)  |
| `DELETE` | `/api/users/teams/{id}/`   | Supprimer l'équipe                   | JWT (owner)        |

### Commandes de gestion

#### `recalculate_user_stats`

Recalcule les statistiques agrégées de tous les utilisateurs en parcourant leurs `GameAnswer` et `GamePlayer`. Utile après une migration ou une correction de données.

```bash
python manage.py recalculate_user_stats
# Options :
#   --user-id <uuid>   Ne recalculer que pour un utilisateur spécifique
#   --dry-run          Afficher les changements sans les sauvegarder
```

#### `recalculate_team_stats`

Identique à `recalculate_user_stats` mais pour les équipes : recalcule `total_games`, `total_wins`, `total_points` en agrégeant les stats des membres.

```bash
python manage.py recalculate_team_stats
```

---

## 2. `authentication`

### Rôle

Gère toute l'authentification de la plateforme :
- **JWT** via `djangorestframework-simplejwt` (access token 24h, refresh 30 jours, rotation + blacklist)
- **Google OAuth 2.0** via `django-allauth`
- **Middleware WebSocket JWT** pour les connexions Django Channels

### Configuration JWT

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,       # Nouveau refresh à chaque renouvellement
    "BLACKLIST_AFTER_ROTATION": True,    # Ancien refresh blacklisté
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),    # Authorization: Bearer <token>
}
```

#### Cycle de vie des tokens

```
POST /api/auth/login/
    │
    ▼
{ "access": "eyJ...", "refresh": "eyJ..." }
    │
    ├── access token (24h) ──→ Authorization: Bearer eyJ...
    │                              │
    │                              ▼ Expiration
    │                    POST /api/auth/token/refresh/
    │                         { "refresh": "eyJ..." }
    │                              │
    │                              ▼
    │                   Ancien refresh → blacklist
    │                   Nouveau refresh → retourné
    │
    └── POST /api/auth/logout/
            { "refresh": "eyJ..." }
                 │
                 ▼ Token blacklisté → invalide
```

### Google OAuth 2.0

Le flux d'authentification Google utilise `django-allauth` :

```
Navigateur → POST /api/auth/google/
                  { "code": "<authorization_code>" }
                       │
                       ▼
              allauth échange le code avec Google
                       │
                       ▼
              Récupération du profil Google
              (email, nom, avatar, google_id)
                       │
                       ├── Utilisateur existant (email_hash match) → connexion
                       │
                       └── Nouvel utilisateur → création automatique du compte
                                │
                                ▼
                        Retour JWT pair (access + refresh)
```

### Middleware WebSocket JWT

```python
# apps/authentication/middleware.py

class JWTAuthMiddleware(BaseMiddleware):
    """
    Intercepte les connexions WebSocket et authentifie via JWT
    passé dans le query parameter ?token=<jwt>.
    """
    async def __call__(self, scope, receive, send):
        # Extraire le token du query string
        query_params = parse_qs(scope.get("query_string", b"").decode())
        token_key = query_params.get("token", [None])[0]

        scope["user"] = AnonymousUser()

        if token_key:
            try:
                access_token = AccessToken(token_key)
                user_id = access_token["user_id"]
                scope["user"] = await self.get_user(user_id)
            except (InvalidToken, TokenError, User.DoesNotExist):
                # Fermer la connexion WebSocket avec code 4003 (Unauthorized)
                await send({"type": "websocket.close", "code": 4003})
                return

        return await super().__call__(scope, receive, send)
```

### Endpoints API

| Méthode | URL                                 | Description                          | Auth                   |
| ------- | ----------------------------------- | ------------------------------------ | ---------------------- |
| `POST`  | `/api/auth/register/`               | Créer un compte + retourner JWT pair | Public                 |
| `POST`  | `/api/auth/login/`                  | Connexion + JWT pair                 | Public                 |
| `POST`  | `/api/auth/logout/`                 | Blacklister le refresh token         | JWT                    |
| `POST`  | `/api/auth/token/refresh/`          | Rafraîchir l'access token            | Public (refresh token) |
| `POST`  | `/api/auth/password/reset/`         | Envoyer email de reset               | Public                 |
| `POST`  | `/api/auth/password/reset/confirm/` | Confirmer le reset                   | Public (token email)   |
| `POST`  | `/api/auth/google/`                 | OAuth 2.0 Google                     | Public                 |

---

## 3. `games`

### Rôle

Application centrale du projet. Gère :
- La création et la gestion du cycle de vie des parties
- Le consumer WebSocket pour le jeu en temps réel
- La génération des questions selon le mode de jeu
- Le calcul des scores, streaks et bonus
- Les invitations entre joueurs

### Modes de jeu

| Mode         | Description                               | Type de question | Format réponse |
| ------------ | ----------------------------------------- | ---------------- | -------------- |
| `classique`  | Deviner le titre ou l'artiste             | QCM (4 options)  | Choix multiple |
| `rapide`     | Comme classique mais timer réduit         | QCM (4 options)  | Choix multiple |
| `generation` | Deviner l'année/décennie de sortie        | QCM (années)     | Choix multiple |
| `paroles`    | Compléter les paroles (fill-in-the-blank) | Texte à trous    | Saisie libre   |
| `karaoke`    | Paroles synchronisées avec la musique     | Paroles sync     | Affichage      |
| `mollo`      | Mode détendu, pas de score                | QCM              | Choix multiple |

### Modèles

| Modèle           | Description                                           |
| ---------------- | ----------------------------------------------------- |
| `Game`           | Partie avec configuration, statut, et lien playlist   |
| `GameRound`      | Un round : piste, question, options, réponse correcte |
| `GamePlayer`     | Participation d'un utilisateur à une partie           |
| `GameAnswer`     | Réponse soumise par un joueur à un round              |
| `GameInvitation` | Invitation envoyée par l'hôte à un ami                |
| `KaraokeSong`    | Chanson disponible en mode karaoké (YouTube + LRC)    |

### Consumer WebSocket — `GameConsumer`

Le `GameConsumer` est le cœur du jeu en temps réel. Il hérite de `AsyncJsonWebsocketConsumer` (Django Channels).

```python
# apps/games/consumers.py (structure)

class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer WebSocket pour /ws/game/<room_code>/
    Chaque instance représente la connexion d'un joueur à une partie.
    """

    async def connect(self):
        # 1. Vérifier l'authentification (via JWTAuthMiddleware)
        # 2. Récupérer ou créer le GamePlayer
        # 3. Rejoindre le channel group Redis "game_<room_code>"
        # 4. Broadcaster player_join à tous les joueurs

    async def disconnect(self, close_code):
        # Marquer le joueur comme déconnecté
        # Broadcaster player_leave

    async def receive_json(self, content):
        # Router les messages selon le type :
        # - "player_join" → handle_player_join
        # - "start_game" → handle_start_game (hôte uniquement)
        # - "player_answer" → handle_player_answer (avec rate limiting)

    # ─── Handlers entrants (client → serveur) ───────────────────

    async def handle_start_game(self, data):
        # Vérifier que l'appelant est l'hôte
        # Appeler GameService.generate_rounds()
        # Broadcaster "start_round" à tout le groupe

    async def handle_player_answer(self, data):
        # Rate limiting via script Lua Redis (max 1 réponse / 2s par joueur)
        # Enregistrer la réponse + calculer les points
        # Broadcaster mise à jour du score

    # ─── Handlers sortants (serveur → client) ────────────────────

    async def start_round(self, event):
        # Broadcaster start_round avec infos du round (sans réponse correcte)

    async def end_round(self, event):
        # Broadcaster fin de round + réponse correcte + classement

    async def next_round(self, event):
        # Broadcaster début du round suivant

    async def finish_game(self, event):
        # Broadcaster fin de partie + classement final
```

#### Protocole de messages WebSocket

```
CLIENT → SERVEUR                    SERVEUR → CLIENT
─────────────────                   ────────────────────────────────
player_join                         player_joined { user, players }
  { room_code }                     player_left { user, players }

start_game                          start_round {
  { room_code }  (hôte)               round_number, track_name,
                                       artist_name, preview_url,
                                       options [], question_text,
                                       duration
player_answer                       }
  { round_id,
    answer,                         end_round {
    response_time }                   correct_answer,
                                       player_answers [],
                                       leaderboard []
                                  }

                                    next_round { round_number }

                                    finish_game {
                                       final_leaderboard [],
                                       game_stats {}
                                    }

                                    error { code, message }
```

#### Rate limiting WebSocket (Lua + Redis)

Pour éviter le spam de réponses, un script Lua atomique est exécuté sur Redis avant d'enregistrer une réponse :

```lua
-- Rate limit : max 1 réponse par joueur par round
local key = KEYS[1]  -- "ratelimit:game:<room>:player:<id>:round:<num>"
local now = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

local existing = redis.call("GET", key)
if existing then
    return 0  -- Réponse déjà soumise
end

redis.call("SET", key, 1)
redis.call("EXPIRE", key, ttl)
return 1  -- Première réponse, autorisée
```

### Services

#### `GameService`

```python
# apps/games/services.py

class GameService:
    @staticmethod
    async def generate_rounds(game: Game) -> list[GameRound]:
        """
        Récupère les pistes depuis Deezer, génère les questions
        selon le mode de jeu et crée les GameRound en base.
        """

    @staticmethod
    async def calculate_score(
        answer: str,
        correct: str,
        response_time: float,
        streak: int,
        bonuses: list[str]
    ) -> dict:
        """
        Calcule les points gagnés pour une réponse.
        Formule : base_score * time_multiplier * streak_multiplier
        """

    @staticmethod
    async def get_final_leaderboard(game: Game) -> list[dict]:
        """
        Retourne le classement final avec rangs, scores et stats.
        """
```

#### `QuestionGeneratorService`

```python
class QuestionGeneratorService:
    """
    Génère les questions pour chaque mode de jeu.
    """

    @staticmethod
    def generate_mcq_question(track, all_tracks, guess_target) -> dict:
        """
        Mode classique/rapide : génère 4 options (1 correcte + 3 distracteurs).
        """

    @staticmethod
    def generate_year_question(track, all_tracks) -> dict:
        """
        Mode génération : propose des années proches de la date de sortie.
        """

    @staticmethod
    def generate_lyrics_question(track, lyrics) -> dict:
        """
        Mode paroles : extrait 3 mots consécutifs à compléter (fill-in-blank).
        """

    @staticmethod
    def generate_karaoke_question(karaoke_song) -> dict:
        """
        Mode karaoké : retourne les paroles synchronisées (LRC) + URL YouTube.
        """
```

### Broadcast Service

```python
class BroadcastService:
    """
    Service dédié à l'envoi de messages WebSocket via le channel layer Redis.
    Utilisé depuis les vues HTTP (ex: /start, /next-round) pour déclencher
    des événements WebSocket sans passer par le Consumer.
    """

    @staticmethod
    async def broadcast_to_game(room_code: str, event_type: str, data: dict):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"game_{room_code}",
            {"type": event_type, **data}
        )
```

### Calcul des scores

```
Score d'une réponse correcte :
─────────────────────────────
base_score = 1000

time_multiplier = 1 + (time_remaining / round_duration) * 0.5
  → Réponse instantanée : ×1.5
  → Réponse en fin de timer : ×1.0

streak_multiplier = 1 + (consecutive_correct * 0.1)
  → 1 bonne réponse : ×1.1
  → 3 bonnes réponses : ×1.3
  → Max : ×2.0 (10 bonnes réponses)

points_earned = round(base_score * time_multiplier * streak_multiplier)

streak_bonus = max(0, (consecutive_correct - 1) * 50)
```

### Endpoints API

| Méthode  | URL                                     | Description                             | Auth       |
| -------- | --------------------------------------- | --------------------------------------- | ---------- |
| `GET`    | `/api/games/`                           | Liste des parties                       | JWT        |
| `POST`   | `/api/games/`                           | Créer une partie (throttle 10/min)      | JWT        |
| `GET`    | `/api/games/{room_code}/`               | Détail d'une partie                     | JWT        |
| `PATCH`  | `/api/games/{room_code}/`               | Modifier la configuration               | JWT (hôte) |
| `DELETE` | `/api/games/{room_code}/`               | Supprimer                               | JWT (hôte) |
| `POST`   | `/api/games/{room_code}/join/`          | Rejoindre (throttle 20/min)             | JWT        |
| `POST`   | `/api/games/{room_code}/leave/`         | Quitter la partie                       | JWT        |
| `POST`   | `/api/games/{room_code}/start/`         | Démarrer + générer les rounds           | JWT (hôte) |
| `GET`    | `/api/games/{room_code}/current-round/` | Round en cours                          | JWT        |
| `POST`   | `/api/games/{room_code}/answer/`        | Soumettre une réponse                   | JWT        |
| `POST`   | `/api/games/{room_code}/end-round/`     | Forcer la fin d'un round                | JWT (hôte) |
| `POST`   | `/api/games/{room_code}/next-round/`    | Passer au round suivant                 | JWT (hôte) |
| `GET`    | `/api/games/{room_code}/results/`       | Résultats finaux + classement           | JWT        |
| `GET`    | `/api/games/{room_code}/results/pdf/`   | Télécharger résultats en PDF            | JWT        |
| `GET`    | `/api/games/available/`                 | Parties publiques en attente            | JWT        |
| `GET`    | `/api/games/public/`                    | Parties publiques (avec recherche)      | JWT        |
| `GET`    | `/api/games/history/`                   | Historique paginé des parties terminées | JWT        |
| `GET`    | `/api/games/leaderboard/`               | Classement global                       | JWT        |
| `POST`   | `/api/games/{room_code}/invite/`        | Inviter un ami                          | JWT (hôte) |
| `GET`    | `/api/games/my-invitations/`            | Invitations en attente                  | JWT        |
| `POST`   | `/api/games/invitations/{id}/accept/`   | Accepter une invitation                 | JWT        |
| `POST`   | `/api/games/invitations/{id}/decline/`  | Refuser une invitation                  | JWT        |
| `GET`    | `/api/games/karaoke-songs/`             | Liste des chansons karaoké              | JWT        |
| `GET`    | `/api/games/karaoke-songs/{id}/`        | Détail d'une chanson karaoké            | JWT        |

---

## 4. `playlists`

### Rôle

Fournit des services d'intégration avec les APIs externes de musique. **Aucun modèle de base de données** : les données sont récupérées à la volée et mises en cache dans Redis.

### `DeezerService`

```python
class DeezerService:
    """
    Client pour l'API publique Deezer.
    Cache Redis de 1 heure pour toutes les requêtes.
    Filtre les URLs de preview expirées (30 secondes d'extrait).
    """
    BASE_URL = "https://api.deezer.com"
    CACHE_TTL = 3600  # 1 heure

    @classmethod
    async def search_playlists(cls, query: str) -> list[dict]:
        """Recherche des playlists Deezer par mot-clé."""

    @classmethod
    async def get_playlist(cls, playlist_id: str) -> dict:
        """Récupère le détail d'une playlist avec ses pistes."""

    @classmethod
    async def get_tracks_with_preview(cls, playlist_id: str) -> list[dict]:
        """
        Récupère les pistes d'une playlist et filtre :
        - Les pistes sans URL de preview
        - Les URLs de preview expirées (détection par tentative HTTP HEAD)
        """
```

#### Filtrage des previews expirées

L'API Deezer retourne des URLs de preview de 30 secondes qui peuvent expirer. Le service effectue une vérification préalable :

```
GET https://cdns-preview-X.dzcdn.net/stream/c-xxx-64.mp3
    │
    ├── HTTP 200 → URL valide, incluse
    └── HTTP 403/404 → URL expirée, exclue de la liste
```

### `YouTubeService`

```python
class YouTubeService:
    """
    Client pour l'API YouTube Data v3.
    Utilisé principalement pour le mode karaoké.
    Nécessite YOUTUBE_API_KEY dans les variables d'environnement.
    """

    @classmethod
    async def get_video_info(cls, video_id: str) -> dict:
        """Récupère les métadonnées d'une vidéo YouTube."""

    @classmethod
    async def search_karaoke_video(cls, title: str, artist: str) -> str | None:
        """Recherche la meilleure vidéo karaoké pour une chanson."""
```

### Endpoints API

| Méthode | URL                    | Description                         | Auth |
| ------- | ---------------------- | ----------------------------------- | ---- |
| `GET`   | `/api/playlists/`      | Recherche/liste de playlists Deezer | JWT  |
| `GET`   | `/api/playlists/{id}/` | Détail d'une playlist Deezer        | JWT  |

---

## 5. `achievements`

### Rôle

Gère le système de récompenses (succès et badges). Les succès sont vérifiés de manière asynchrone via Celery après chaque partie pour ne pas bloquer la réponse HTTP.

### Modèles

| Modèle            | Description                                             |
| ----------------- | ------------------------------------------------------- |
| `Achievement`     | Définition d'un succès (condition, points, icône)       |
| `UserAchievement` | Association utilisateur ↔ succès avec date de déblocage |

### Types de conditions (`condition_type`)

| Type            | Description                           | Exemple                |
| --------------- | ------------------------------------- | ---------------------- |
| `games_played`  | Nombre de parties jouées              | 10 parties             |
| `wins`          | Nombre de victoires                   | 5 victoires            |
| `points`        | Points totaux accumulés               | 10 000 points          |
| `perfect_round` | Rounds parfaits (100% correct)        | 1 round parfait        |
| `streak`        | Série de bonnes réponses consécutives | 5 de suite             |
| `first_win`     | Première victoire                     | —                      |
| `daily_login`   | Connexion quotidienne consécutive     | 7 jours de suite       |
| `mode_specific` | Victoire dans un mode spécifique      | Gagner en mode karaoke |
| `speed`         | Réponse en moins de X secondes        | < 2 secondes           |
| `coins`         | Coins accumulés                       | 500 coins              |

### Tâche Celery : `check_achievements_async`

```python
# apps/achievements/tasks.py

@shared_task(bind=True, max_retries=3)
def check_achievements_async(self, user_id: str, game_id: str):
    """
    Vérifie et débloque les succès d'un utilisateur après une partie.
    Exécutée de manière asynchrone pour ne pas bloquer l'API.

    Flux :
    1. Récupérer l'utilisateur et la partie terminée
    2. Calculer les stats de la partie (streak, temps moyen, etc.)
    3. Pour chaque Achievement non encore débloqué :
       a. Évaluer la condition
       b. Si remplie → créer UserAchievement + créditer les points/coins
    4. Retourner la liste des succès débloqués
    """
```

### Commandes de gestion

#### `seed_achievements`

Peuple la base de données avec les 40+ succès prédéfinis du jeu.

```bash
python manage.py seed_achievements
# Option --reset : supprime tous les succès existants avant de recréer
```

#### `award_retroactive_achievements`

Attribue rétroactivement les succès aux utilisateurs existants qui remplissent déjà les conditions (à exécuter après ajout de nouveaux succès).

```bash
python manage.py award_retroactive_achievements
# Option --achievement-id <uuid> : traiter un seul succès
# Option --dry-run : simuler sans sauvegarder
```

#### `sync_coins_balance`

Recalcule le solde de coins de tous les utilisateurs en agrégeant :
- Coins gagnés via les succès
- Coins dépensés dans la boutique
- Bonus de connexion quotidienne

```bash
python manage.py sync_coins_balance
```

### Endpoints API

| Méthode | URL                              | Description                                | Auth |
| ------- | -------------------------------- | ------------------------------------------ | ---- |
| `GET`   | `/api/achievements/`             | Liste de tous les succès disponibles       | JWT  |
| `GET`   | `/api/achievements/mine/`        | Succès débloqués de l'utilisateur connecté | JWT  |
| `GET`   | `/api/achievements/user/{uuid}/` | Succès d'un utilisateur spécifique         | JWT  |

---

## 6. `administration`

### Rôle

Fournit les outils de gestion du site :
- **Mode maintenance** : désactive l'accès au site via un middleware (retourne HTTP 503)
- **Bannière d'information** : message configurable affiché sur l'interface
- **Pages légales** : politique de confidentialité et mentions légales
- **Tâches RGPD** : purge des données personnelles expirées

### Modèles

#### `SiteConfiguration` — Singleton

Ce modèle utilise le pattern **Singleton** : il ne peut exister qu'une seule instance en base de données. La sauvegarde est forcée sur l'id=1.

```python
class SiteConfiguration(models.Model):
    class Meta:
        verbose_name = "Configuration du site"

    def save(self, *args, **kwargs):
        self.pk = 1  # Forcer le singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
```

| Champ                 | Type           | Description                                    |
| --------------------- | -------------- | ---------------------------------------------- |
| `maintenance_mode`    | BooleanField   | Active/désactive le mode maintenance           |
| `maintenance_title`   | CharField      | Titre de la page de maintenance                |
| `maintenance_message` | TextField      | Message détaillé de maintenance                |
| `banner_enabled`      | BooleanField   | Afficher ou non la bannière                    |
| `banner_message`      | CharField(500) | Contenu de la bannière                         |
| `banner_color`        | CharField      | Style : `info`, `success`, `warning`, `danger` |
| `banner_dismissible`  | BooleanField   | L'utilisateur peut fermer la bannière          |

#### `LegalPage`

Stocke le contenu des pages légales éditables depuis l'admin.

| Champ       | Description                                                            |
| ----------- | ---------------------------------------------------------------------- |
| `page_type` | `privacy` (politique de confidentialité) ou `legal` (mentions légales) |
| `title`     | Titre de la page                                                       |
| `content`   | Contenu HTML/Markdown de la page                                       |

### Middleware : `MaintenanceMiddleware`

```python
class MaintenanceMiddleware(MiddlewareMixin):
    """
    Intercepte toutes les requêtes HTTP.
    Si maintenance_mode=True, retourne une réponse 503 à toutes les requêtes
    sauf :
    - Les requêtes vers /admin/ (pour que les admins puissent désactiver)
    - Les requêtes vers /api/administration/status/ (health check front)
    """

    EXEMPT_PATHS = ["/admin/", "/api/administration/status/"]

    def process_request(self, request):
        config = SiteConfiguration.get_instance()
        if config.maintenance_mode:
            if not any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
                return JsonResponse(
                    {"detail": config.maintenance_message},
                    status=503
                )
```

### Tâches Celery RGPD

#### `purge_expired_invitations`

```python
@shared_task
def purge_expired_invitations():
    """
    Supprime les invitations de partie expirées (>30 minutes) avec statut
    'pending'. Planifiée chaque nuit à 2h via Celery Beat.
    """
    cutoff = timezone.now() - timedelta(minutes=30)
    count, _ = GameInvitation.objects.filter(
        status="pending",
        created_at__lt=cutoff
    ).delete()
    return f"{count} invitations supprimées"
```

#### `anonymize_old_game_data`

```python
@shared_task
def anonymize_old_game_data():
    """
    Anonymise les données personnelles des parties terminées
    depuis plus de 2 ans (conformité RGPD).
    Les GameAnswer et GamePlayer sont conservés mais les références
    utilisateur sont remplacées par un utilisateur anonyme générique.
    Planifiée chaque dimanche à 3h.
    """
```

### Endpoints API

| Méthode | URL                                      | Description                          | Auth   |
| ------- | ---------------------------------------- | ------------------------------------ | ------ |
| `GET`   | `/api/administration/status/`            | Statut maintenance + config bannière | Public |
| `GET`   | `/api/administration/legal/{page_type}/` | Contenu d'une page légale            | Public |

---

## 7. `shop`

### Rôle

Gère la boutique virtuelle permettant aux joueurs d'acheter des bonus avec leurs coins, et l'utilisation de ces bonus pendant les parties.

### Modèles

| Modèle          | Description                                   |
| --------------- | --------------------------------------------- |
| `ShopItem`      | Article disponible à l'achat dans la boutique |
| `UserInventory` | Articles possédés par un utilisateur          |
| `GameBonus`     | Bonus activé par un joueur pendant une partie |

### Types de bonus

| Code            | Nom                  | Effet en jeu                                                |
| --------------- | -------------------- | ----------------------------------------------------------- |
| `double_points` | Points doublés       | Multiplie les points de ce round ×2                         |
| `max_points`    | Points max           | Attribue le score maximum quel que soit le temps de réponse |
| `time_bonus`    | Temps supplémentaire | Ajoute 10 secondes au timer du round                        |
| `fifty_fifty`   | 50/50                | Élimine 2 mauvaises options (mode QCM)                      |
| `steal`         | Vol                  | Vole les points d'un adversaire désigné                     |
| `shield`        | Bouclier             | Protège contre les effets négatifs adverses                 |
| `fog`           | Brouillard           | Masque les options des adversaires                          |
| `joker`         | Joker                | Passe un round sans pénalité                                |

### `BonusService`

```python
class BonusService:
    """
    Gère l'activation et les effets des bonus en jeu.
    Travaille en coordination avec le GameConsumer via le channel layer.
    """

    @staticmethod
    async def activate_bonus(
        game_id: str,
        player_id: str,
        bonus_type: str,
        round_number: int,
        target_player_id: str | None = None
    ) -> dict:
        """
        Active un bonus pour un joueur à un round donné.
        Vérifie que le joueur possède le bonus dans son inventaire.
        Crée le GameBonus et retourne les effets à appliquer.
        """

    @staticmethod
    def apply_bonus_to_score(base_score: int, bonuses: list[GameBonus]) -> int:
        """Applique les bonus actifs au calcul du score."""
```

### Endpoints API

| Méthode | URL                         | Description                          | Auth |
| ------- | --------------------------- | ------------------------------------ | ---- |
| `GET`   | `/api/shop/items/`          | Liste des articles disponibles       | JWT  |
| `GET`   | `/api/shop/items/{id}/`     | Détail d'un article                  | JWT  |
| `POST`  | `/api/shop/items/{id}/buy/` | Acheter un article                   | JWT  |
| `GET`   | `/api/shop/inventory/`      | Inventaire de l'utilisateur connecté | JWT  |

---

## 8. `stats`

### Rôle

Fournit des vues de statistiques calculées dynamiquement depuis les modèles existants (`Game`, `GamePlayer`, `GameAnswer`). **Aucun modèle de base de données dédié** : toutes les stats sont calculées par agrégation SQL via Django ORM.

### Vues de statistiques

#### Statistiques utilisateur (`/api/stats/me/`)

```python
# Agrégations calculées dynamiquement
{
    "total_games_played": 45,
    "total_wins": 12,
    "win_rate": 26.7,
    "total_points": 48250,
    "average_score_per_game": 1072,
    "best_score": 3200,
    "total_correct_answers": 387,
    "accuracy_rate": 78.4,       # % réponses correctes
    "average_response_time": 8.3, # secondes
    "best_streak": 9,
    "favorite_mode": "classique",
    "stats_by_mode": {
        "classique": { "games": 20, "wins": 8, "avg_score": 1150 },
        "rapide":    { "games": 10, "wins": 2, "avg_score": 980 },
        ...
    }
}
```

#### Classement global (`/api/stats/leaderboard/`)

Agrégation sur `GamePlayer` groupée par `user`, triée par score total décroissant. Paginé (20 par page).

#### Classement par mode (`/api/stats/leaderboard/{mode}/`)

Même logique mais filtrée sur `GamePlayer__game__mode = mode`.

### Endpoints API

| Méthode | URL                              | Description                                | Auth |
| ------- | -------------------------------- | ------------------------------------------ | ---- |
| `GET`   | `/api/stats/me/`                 | Stats détaillées de l'utilisateur connecté | JWT  |
| `GET`   | `/api/stats/leaderboard/`        | Classement global                          | JWT  |
| `GET`   | `/api/stats/leaderboard/teams/`  | Classement des équipes                     | JWT  |
| `GET`   | `/api/stats/leaderboard/{mode}/` | Classement par mode de jeu                 | JWT  |
| `GET`   | `/api/stats/my-rank/`            | Rang actuel + rangs par mode               | JWT  |
| `GET`   | `/api/stats/user/{user_id}/`     | Stats publiques d'un profil utilisateur    | JWT  |

---

## 9. `core`

### Rôle

Infrastructure transversale sans logique métier propre :
- **Health checks** : endpoints de vérification d'état pour Kubernetes/Docker
- **Métriques Prometheus** : 19+ métriques custom exposées sur `/metrics/`
- **Middleware de logging structuré** : journaux JSON enrichis
- **Middleware de métriques** : instrumente chaque requête HTTP

### Health Checks

Trois niveaux de vérification, compatibles avec les sondes Kubernetes :

```
GET /api/health/   ← Sonde de santé globale (DB + Redis + Celery)
GET /api/ready/    ← Readiness probe (prêt à recevoir du trafic)
GET /api/alive/    ← Liveness probe (processus vivant)
```

```python
# Exemple de réponse /api/health/
{
    "status": "healthy",
    "checks": {
        "database": { "status": "ok", "latency_ms": 2.3 },
        "redis":    { "status": "ok", "latency_ms": 0.8 },
        "celery":   { "status": "ok", "workers": 2 }
    },
    "version": "1.4.2",
    "timestamp": "2026-03-07T10:00:00Z"
}
```

### Métriques Prometheus

`PrometheusMetricsMiddleware` instrumente chaque requête HTTP et alimente 19+ métriques :

```
# Métriques HTTP
http_requests_total{method, path, status}       ← Compteur de requêtes
http_request_duration_seconds{method, path}     ← Histogramme de latence

# Métriques WebSocket
websocket_connections_active                    ← Jauge connexions actives
websocket_messages_total{direction, type}       ← Compteur messages WS

# Métriques métier
games_created_total{mode}                       ← Parties créées
games_completed_total{mode}                     ← Parties terminées
players_online_gauge                            ← Joueurs connectés
answers_submitted_total{is_correct}             ← Réponses soumises
achievements_unlocked_total{achievement_name}   ← Succès débloqués

# Métriques Celery
celery_tasks_total{task_name, status}           ← Tâches exécutées
celery_task_duration_seconds{task_name}         ← Durée des tâches

# Métriques cache
cache_hits_total{cache_name}                    ← Cache hits Redis
cache_misses_total{cache_name}                  ← Cache misses Redis
```

### Middleware de logging structuré

`StructuredLoggingMiddleware` émet des logs JSON enrichis pour chaque requête :

```json
{
    "timestamp": "2026-03-07T10:00:00.123Z",
    "level": "INFO",
    "method": "POST",
    "path": "/api/games/ABC123/answer/",
    "status_code": 200,
    "duration_ms": 45.2,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "req-abc123",
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
}
```

### Endpoints

| Méthode | URL            | Description                   | Auth         |
| ------- | -------------- | ----------------------------- | ------------ |
| `GET`   | `/api/health/` | Health check global           | Public       |
| `GET`   | `/api/ready/`  | Readiness probe               | Public       |
| `GET`   | `/api/alive/`  | Liveness probe                | Public       |
| `GET`   | `/metrics/`    | Métriques Prometheus (scrape) | IP whitelist |

---

> Voir aussi :
> - [01-structure.md](./01-structure.md) — Structure des dossiers et configuration
> - [03-models-mcd.md](./03-models-mcd.md) — MCD complet et documentation des modèles
> - [04-api-routes.md](./04-api-routes.md) — Référence complète des routes API
