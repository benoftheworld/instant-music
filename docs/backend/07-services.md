# Services — Couche métier

## Table des matières

- [Vue d'ensemble de l'architecture](#vue-densemble-de-larchitecture)
- [Services d'intégration externe](#services-dintégration-externe)
  - [DeezerService](#deezerservice)
  - [YouTubeService](#youtubeservice)
  - [LyricsService](#lyricsservice)
- [Services de jeu](#services-de-jeu)
  - [GameService](#gameservice)
  - [QuestionGeneratorService](#questiongeneratorservice)
- [Services applicatifs](#services-applicatifs)
  - [BonusService](#bonusservice)
  - [BroadcastService](#broadcastservice)
  - [PDFService](#pdfservice)
- [Interactions entre services](#interactions-entre-services)
- [Patterns communs](#patterns-communs)

---

## Vue d'ensemble de l'architecture

Les services constituent la couche métier d'InstantMusic. Ils sont appelés depuis les vues DRF et les consumers WebSocket. Ils ne doivent jamais être appelés directement depuis les modèles.

```
                    SOURCES DE DONNÉES EXTERNES
                              │
         ┌────────────────────┼────────────────────┐
         │                   │                    │
   ┌─────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
   │  Deezer API │    │ YouTube API  │    │  LRCLib API  │
   │  (publique) │    │ (API Key)    │    │  (publique)  │
   └─────┬──────┘    └───────┬──────┘    └───────┬──────┘
         │                   │                    │
   ┌─────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
   │DeezerService│    │YouTubeService│    │LyricsService │
   │  + cache    │    │  + cache     │    │  + cache     │
   │  Redis 1h   │    │  Redis 1h    │    │  Redis 1h    │
   └─────┬──────┘    └───────┬──────┘    └───────┬──────┘
         │                   │                    │
         └──────────┬─────────┘                   │
                    │                             │
             ┌──────▼──────┐                      │
             │QuestionGener│◄─────────────────────┘
             │atorService  │
             └──────┬──────┘
                    │
             ┌──────▼──────┐        ┌─────────────┐
             │ GameService  │◄───────│ BonusService │
             └──────┬──────┘        └─────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
   ┌─────▼────┐ ┌───▼────┐ ┌──▼──────────┐
   │Broadcast │ │  PDF   │ │   Celery     │
   │ Service  │ │Service │ │(achievements)│
   └──────────┘ └────────┘ └─────────────┘
         │
   ┌─────▼─────────────────────────┐
   │  Django Channels Layer (Redis) │
   │  → Tous les clients WebSocket  │
   └───────────────────────────────┘
```

---

## Services d'intégration externe

### DeezerService

**Fichier :** `backend/apps/playlists/deezer_service.py`

Service d'accès à l'[API publique Deezer](https://developers.deezer.com/api). Aucune clé API n'est requise.

#### Initialisation (Singleton)

```python
class DeezerService:
    BASE_URL = "https://api.deezer.com"

    def __init__(self):
        self.session = requests.Session()
        self.redis = get_redis_connection("default")

# Instance unique partagée dans toute l'application
deezer_service = DeezerService()
```

#### Méthodes

| Méthode                                   | Cache Redis | Description                                          |
| ----------------------------------------- | ----------- | ---------------------------------------------------- |
| `search_playlists(query, limit)`          | 1 heure     | Recherche des playlists par mot-clé                  |
| `get_playlist(playlist_id)`               | 1 heure     | Métadonnées d'une playlist (titre, image, nb pistes) |
| `get_playlist_tracks(playlist_id, limit)` | 30 min      | Pistes avec pagination, filtre sans preview          |
| `search_tracks(query, limit)`             | 1 heure     | Recherche de pistes par mot-clé                      |
| `get_track_details(track_id)`             | 1 heure     | Détails d'une piste (inclut `release_date`)          |
| `clean_track_title(title)`                | N/A         | Nettoyage du titre (supprime suffixes)               |

#### Stratégie de cache Redis

```
search_playlists("rock 80s", limit=10)
        │
        ▼
┌───────────────────────────────────────┐
│  Clé Redis :                          │
│  "deezer:search_playlists:           │
│   rock 80s:10"                        │
│                                       │
│  Cache HIT ?                          │──── Oui → Retourne JSON désérialisé
│  (TTL restant > 0)                    │
└───────────────────────────────────────┘
           │ Non (MISS)
           ▼
   GET https://api.deezer.com/search/playlist
   ?q=rock+80s&limit=10
           │
           ▼
   Stocke résultat dans Redis
   SET "deezer:search_playlists:rock 80s:10"
   EX 3600 (1 heure)
           │
           ▼
   Retourne les données
```

#### Filtrage des pistes sans preview

L'API Deezer ne fournit pas toujours une URL de preview audio (30 secondes). Les pistes sans `preview` URL sont automatiquement filtrées dans `get_playlist_tracks()` car elles ne peuvent pas être utilisées dans le quiz.

```python
tracks = [t for t in raw_tracks if t.get("preview")]
```

#### Nettoyage des titres (`clean_track_title`)

Supprime les suffixes marketing parasites qui empêcheraient la vérification de réponse :

```python
# Patterns supprimés via regex :
# - "Remastered 2024", "2011 Remaster"
# - "Deluxe Edition", "Deluxe Version"
# - "Live Version", "Live at ..."
# - "(feat. Artist)", "[Explicit]"

clean_track_title("Hotel California (2013 Remaster)")
# → "Hotel California"
```

---

### YouTubeService

**Fichier :** `backend/apps/playlists/youtube_service.py`

Service d'accès à l'[API YouTube Data v3](https://developers.google.com/youtube/v3).

**Prérequis :** Variable d'environnement `YOUTUBE_API_KEY` obligatoire.

#### Initialisation (Singleton)

```python
class YouTubeService:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.session = requests.Session()
        self.redis = get_redis_connection("default")

youtube_service = YouTubeService()
```

#### Méthodes

| Méthode                                   | Cache Redis | Description                                   |
| ----------------------------------------- | ----------- | --------------------------------------------- |
| `search_playlists(query, limit)`          | 1 heure     | Recherche playlists YouTube                   |
| `get_playlist(playlist_id)`               | 1 heure     | Métadonnées playlist YouTube                  |
| `get_playlist_tracks(playlist_id, limit)` | 1 heure     | Items + détails vidéo, filtre non-intégrables |
| `search_music_videos(query, limit)`       | 1 heure     | Recherche vidéos (catégorie musique = 10)     |
| `_parse_video_title(title)`               | N/A         | Extraction (artiste, titre) depuis le titre   |
| `_parse_iso_duration(duration)`           | N/A         | Conversion ISO 8601 → millisecondes           |

#### Filtrage des vidéos non-intégrables

YouTube impose des restrictions d'intégration sur certaines vidéos. Les vidéos avec `embeddable: false` sont filtrées :

```
get_playlist_tracks("PLxxx")
        │
        ▼
  API: playlistItems.list
  → Liste des video_id
        │
        ▼
  API: videos.list (batch)
  → contentDetails + status
        │
        ▼
  Filtre: status.embeddable == True
         ET status.privacyStatus == "public"
```

#### Parsing des titres vidéo (`_parse_video_title`)

Les vidéos musicales YouTube n'ont pas de métadonnées structurées artiste/titre. Une heuristique parse le titre :

```
"The Beatles - Hey Jude (Official Audio)"
         │
         ▼
Séparateurs testés dans l'ordre :
  " - " → trouvé
         │
    ┌────┴────────────────────────────┐
    │ Artiste : "The Beatles"         │
    │ Titre   : "Hey Jude (Official   │
    │            Audio)"              │
    └────┬────────────────────────────┘
         │
         ▼
Nettoyage du titre :
  Supprime "(Official Audio)", "(Official Video)",
  "(Lyrics)", "[HD]", etc.
         │
         ▼
  Artiste : "The Beatles"
  Titre   : "Hey Jude"
```

#### Conversion de durée ISO 8601 (`_parse_iso_duration`)

```python
_parse_iso_duration("PT3M45S")  # → 225000 ms
_parse_iso_duration("PT1H2M3S") # → 3723000 ms
```

---

### LyricsService

**Fichier :** `backend/apps/games/lyrics_service.py`

Service d'accès aux paroles de chansons, utilisé pour les modes **Paroles** et **Karaoké**.

#### Sources de données

```
                  get_lyrics(artist, title)
                          │
            ┌─────────────┴──────────────┐
            │                            │
     Essai LRCLib               Fallback lyrics.ovh
     lrclib.net/api/get         api.lyrics.ovh/v1/
            │                            │
     ┌──────┴───────┐           ┌────────┴────────┐
     │ Paroles brutes│           │  Paroles brutes  │
     │ (+ LRC synch)│           │  (texte simple)  │
     └──────┬───────┘           └────────┬─────────┘
            └──────────┬─────────────────┘
                       │
                 Cache Redis 1h
                 "lyrics:{artist}:{title}"
```

#### Méthodes

| Méthode                                                            | Retour                               | Description                             |
| ------------------------------------------------------------------ | ------------------------------------ | --------------------------------------- |
| `get_lyrics(artist, title)`                                        | `str`                                | Paroles texte brut                      |
| `get_synced_lyrics(artist, title)`                                 | `(list[dict], lrclib_id)`            | Paroles synchronisées + ID LRCLib       |
| `get_synced_lyrics_by_lrclib_id(id)`                               | `list[dict]`                         | Lookup direct par ID (mode karaoké)     |
| `create_lyrics_question(lyrics, all_tracks_words, words_to_blank)` | `(snippet, correct_phrase, options)` | Génère une question lacunaire           |
| `parse_lrc(lrc_text)`                                              | `list[dict]`                         | Parse un fichier `.lrc` avec timestamps |

#### Résolution en 3 étapes pour `get_synced_lyrics`

```
get_synced_lyrics("The Beatles", "Hey Jude")
        │
        ▼
Étape 1 : Recherche exacte
  GET /api/get?artist_name=The+Beatles&track_name=Hey+Jude
        │
  ┌─────┴─────┐
  │  Trouvé ? │──── Oui → Retourne (paroles, id)
  └─────┬─────┘
        │ Non
        ▼
Étape 2 : Recherche par mots-clés
  GET /api/search?q=The+Beatles+Hey+Jude
  → Prend le premier résultat le plus proche
        │
  ┌─────┴─────┐
  │  Trouvé ? │──── Oui → Retourne (paroles, id)
  └─────┬─────┘
        │ Non
        ▼
Étape 3 : Recherche titre seul
  GET /api/search?q=Hey+Jude
  → Prend le résultat correspondant à l'artiste
        │
  ┌─────┴─────┐
  │  Trouvé ? │──── Oui → Retourne (paroles, id)
  └─────┬─────┘
        │ Non → Retourne ([], None)
```

#### Circuit breaker pour LRCLib

LRCLib est un service externe non garanti. Un circuit breaker évite de bloquer les requêtes si le service est indisponible :

```
Requête vers lrclib.net
        │
        ▼
┌───────────────────────────────┐
│  Circuit OUVERT ?             │──── Oui → Passe directement au fallback
│  (marqué "down" dans Redis)   │           lyrics.ovh
└───────────────────────────────┘
           │ Non (circuit fermé)
           ▼
   Tentative de connexion
           │
  ┌────────┴────────┐
  │ ConnectionError │──── Oui → Marque "down" dans Redis 90s
  └────────┬────────┘           → Passe au fallback
           │ Non
           ▼
   Retourne les paroles
```

#### Format des paroles synchronisées

```python
[
    {"time_ms": 0,     "text": ""},
    {"time_ms": 15400, "text": "Hey Jude, don't make it bad"},
    {"time_ms": 19200, "text": "Take a sad song and make it better"},
    {"time_ms": 23100, "text": "Remember to let her into your heart"},
    ...
]
```

#### Génération de question lacunaire (`create_lyrics_question`)

```
create_lyrics_question(
    lyrics="Hey Jude don't make it bad take a sad song",
    all_tracks_words=["Hotel", "California", "Jude", "Yesterday"],
    words_to_blank=1
)
        │
        ▼
Sélectionne un snippet de 2-4 lignes
Choisit 1 mot à masquer (mot significatif, > 3 lettres)
Génère 3 distracteurs depuis all_tracks_words
        │
        ▼
Retourne :
  snippet       = "Hey ___ don't make it bad"
  correct_phrase= "Jude"
  options       = ["Jude", "Hotel", "California", "Yesterday"]
                  (mélangés aléatoirement)
```

---

## Services de jeu

### GameService

**Fichier :** `backend/apps/games/services.py`

Service central de la logique de jeu. Gère le cycle de vie complet d'une partie.

#### Méthodes principales

##### `start_game(game)`

```
start_game(game)
        │
        ▼
┌───────────────────────────┐
│  game.game_mode ?         │
└───────────────────────────┘
    │           │           │
"karaoke"   "classique"  "paroles"
    │       "rapide"     "generation"
    ▼           └─────┬────┘
_start_karaoke_       │
game(game)            ▼
                QuestionGenerator
                Service.generate_
                rounds(game)
                      │
                      ▼
                Crée N GameRound
                (N = game.nb_rounds)
                      │
                      ▼
                game.status = "started"
                game.save()
```

##### `_start_karaoke_game(game)`

Mode karaoké spécifique : une seule piste YouTube avec paroles synchronisées.

```
_start_karaoke_game(game)
        │
        ▼
YouTubeService.get_playlist_tracks(
    game.playlist_id
)
        │
        ▼
Pour chaque piste :
  LyricsService.get_synced_lyrics(
      artist, title
  )
        │
        ▼
Sélectionne la piste avec le
meilleur score de paroles disponibles
        │
        ▼
Crée 1 GameRound avec :
  extra_data = {
      "synced_lyrics": [...],
      "lrclib_id": 12345,
      "youtube_video_id": "dQw4w9WgXcQ"
  }
```

##### `check_answer(game_mode, answer, correct_answer, extra_data)`

Vérifie la réponse selon la logique propre à chaque mode :

```
Mode "classique" / "rapide" :
  Comparaison textuelle insensible à la casse,
  normalisation des accents et de la ponctuation.
  Retourne (True/False, 1.0)

Mode "generation" :
  answer = année saisie (int)
  correct_answer = année de sortie
  delta = |answer - correct_answer|

  delta == 0 → (True,  1.0)   # Exact
  delta == 1 → (True,  0.8)   # ±1 an
  delta == 2 → (True,  0.6)   # ±2 ans
  delta >= 3 → (False, 0.0)   # Trop loin

Mode "paroles" :
  Comparaison du mot/phrase blanqué(e).
  Retourne (True/False, 1.0)
```

##### `submit_answer(player, round_obj, answer, response_time)`

```
submit_answer(player, round, "Beatles", 4.2)
        │
        ▼
check_answer(mode, "Beatles", "Beatles", extra)
→ (is_correct=True, accuracy_factor=1.0)
        │
        ▼
calculate_score(1.0, response_time=4.2, max_time=30)
→ base_points = max(MIN_SCORE, BASE_SCORE - 4.2 * TIME_PENALTY)
→ points = base_points * accuracy_factor
        │
        ▼
BonusService.apply_score_bonuses(
    player, round_number, points, is_correct, game
)
→ Applique les bonus actifs (double_points, etc.)
        │
        ▼
Crée GameAnswer(
    player=player,
    round=round,
    answer="Beatles",
    is_correct=True,
    points_earned=points_final,
    response_time=4.2
)
        │
        ▼
player.total_points += points_final
player.save()
```

##### Formule de calcul du score

```
points_base = max(MIN_SCORE, BASE_SCORE - response_time * TIME_PENALTY)
points_final = points_base * accuracy_factor

Exemple (mode classique, réponse correcte en 4.2s) :
  MIN_SCORE    = 100
  BASE_SCORE   = 1000
  TIME_PENALTY = 20
  accuracy_factor = 1.0

  points_base = max(100, 1000 - 4.2 * 20)
              = max(100, 916)
              = 916
  points_final = 916 * 1.0 = 916

Exemple (mode génération, ±1 an, réponse en 10s) :
  points_base = max(100, 1000 - 10 * 20) = max(100, 800) = 800
  points_final = 800 * 0.8 = 640
```

##### `finish_game(game)`

```
finish_game(game)
        │
        ▼
Trie les joueurs par total_points
Attribue les rangs (1er, 2ème, 3ème...)
        │
        ▼
Pour chaque joueur :
  Attribue des pièces (coins)
  selon le rang (1er = plus de pièces)
        │
        ▼
game.status = "finished"
game.finished_at = now()
game.save()
        │
        ▼
Pour chaque joueur :
  check_and_award.delay(user_id, game_id)
  (Celery async, ne bloque pas)
        │
        ▼
Incrémente métriques Prometheus :
  games_completed_total{mode}
  game_duration_seconds
```

---

### QuestionGeneratorService

**Fichier :** `backend/apps/games/services.py`

Génère les questions de chaque round selon le mode de jeu.

#### Modes et stratégies

```
┌──────────────┬────────────────────────────────────────────┐
│ Mode         │ Type de question                           │
├──────────────┼────────────────────────────────────────────┤
│ classique    │ MCQ : deviner le titre OU l'artiste        │
│ rapide       │ MCQ : même logique, temps réduit           │
│ generation   │ MCQ : deviner l'année de sortie            │
│ paroles      │ Fill-in-blank depuis LRCLib                │
│ karaoke      │ Round unique, paroles sync + vidéo YouTube │
└──────────────┴────────────────────────────────────────────┘
```

#### Génération des distracteurs (MCQ)

```
Piste correcte : "Hey Jude" - The Beatles

Génération des 3 options incorrectes :
  Stratégie 1 : Piocher dans les autres pistes de la même playlist
    → "Let It Be", "Come Together", "Yesterday"

  Stratégie 2 : Si la playlist est trop petite (<4 pistes),
    compléter avec des artistes/titres de playlists similaires
    (résultats Deezer pour la même recherche)

Résultat final (mélangé) :
  ["Yesterday", "Hey Jude", "Come Together", "Let It Be"]
         ↑ correct (à l'index aléatoire)
```

---

## Services applicatifs

### BonusService

**Fichier :** `backend/apps/shop/services.py`

Gère l'activation et l'application des bonus achetés dans la boutique.

#### Types de bonus

| Bonus           | Effet                                          |
| --------------- | ---------------------------------------------- |
| `double_points` | Double les points du round                     |
| `max_points`    | Donne le score maximum indépendamment du temps |
| `steal`         | Vole des points au joueur en tête              |
| `shield`        | Bloque un vol de points                        |
| `fog`           | Masque les scores des autres joueurs           |
| `time_freeze`   | Arrête le chronomètre                          |
| `hint`          | Révèle un indice (première lettre, etc.)       |
| `skip`          | Passe le round sans pénalité                   |

#### Flux d'activation

```
activate_bonus(user, game, "double_points", round_number=3)
        │
        ▼
Vérifie UserInventory : user possède "double_points" ?
        │
  ┌─────┴─────┐
  │  Non       │──── Lance ItemNotAvailableError
  └─────┬─────┘
        │ Oui
        ▼
Vérifie GameBonus : bonus déjà actif ce round ?
        │
  ┌─────┴─────┐
  │  Oui       │──── Lance BonusAlreadyActiveError
  └─────┬─────┘
        │ Non
        ▼
Décrémente UserInventory.quantity -= 1
Crée GameBonus(user, game, "double_points", round=3)
Retourne GameBonus
```

#### Application des bonus au scoring

```
apply_score_bonuses(player, round=3, base_points=800, is_correct=True, game)
        │
        ▼
Charge GameBonus actifs pour (player, round, game)
        │
        ▼
Pour chaque bonus :
  "double_points" → points *= 2   → 1600
  "max_points"    → points = MAX_SCORE → 1000 (si > double_points)
  "steal"         → points += steal_from_leader(game, player)
  "shield"        → bloque tout steal sur ce joueur
        │
        ▼
Retourne points_final = 1600
```

---

### BroadcastService

**Fichier :** `backend/apps/games/broadcast_service.py`

Fournit des wrappers **synchrones** autour de l'API asynchrone de Django Channels. Permet aux vues HTTP DRF d'envoyer des messages WebSocket sans être elles-mêmes des coroutines.

#### Problème résolu

```python
# Dans une vue DRF synchrone, on ne peut pas faire :
await channel_layer.group_send(...)  # SyntaxError (pas dans async)

# BroadcastService utilise async_to_sync :
from asgiref.sync import async_to_sync

class BroadcastService:
    def broadcast_player_join(self, room_code, player_data):
        async_to_sync(channel_layer.group_send)(
            f"game_{room_code}",
            {"type": "player_joined", "player": player_data}
        )
```

#### Méthodes disponibles

| Méthode                  | Message envoyé  | Contexte d'utilisation           |
| ------------------------ | --------------- | -------------------------------- |
| `broadcast_player_join`  | `player_joined` | Quand un joueur rejoint via HTTP |
| `broadcast_player_leave` | `player_leave`  | Déconnexion détectée             |
| `broadcast_game_update`  | `game_updated`  | Mise à jour des paramètres       |
| `broadcast_round_start`  | `round_started` | Démarrage d'un round             |
| `broadcast_round_end`    | `round_ended`   | Fin d'un round                   |
| `broadcast_next_round`   | `next_round`    | Passage au round suivant         |
| `broadcast_game_finish`  | `game_finished` | Fin de partie                    |

---

### PDFService

**Fichier :** `backend/apps/games/pdf_service.py`

Génère un récapitulatif PDF des résultats d'une partie via la bibliothèque [ReportLab](https://www.reportlab.com/).

#### Signature

```python
def generate_results_pdf(
    game_data: dict,
    rankings: list[dict],
    rounds_detail: list[dict]
) -> bytes:
    ...
```

#### Structure du PDF généré

```
┌─────────────────────────────────────────────┐
│           INSTANT MUSIC                     │
│        Résultats de la partie               │
│                                             │
│  Salle : ABCD1234     Mode : Classique      │
│  Date  : 07/03/2026   Durée : 12 min        │
│  Playlist : Rock des années 80              │
├─────────────────────────────────────────────┤
│  CLASSEMENT FINAL                           │
│  ┌──────┬───────────────────┬───────────┐  │
│  │ Rang │ Joueur            │ Points    │  │
│  ├──────┼───────────────────┼───────────┤  │
│  │  🥇  │ Alice             │ 8 420 pts │  │
│  │  🥈  │ Bob               │ 7 180 pts │  │
│  │  🥉  │ Charlie           │ 6 950 pts │  │
│  └──────┴───────────────────┴───────────┘  │
├─────────────────────────────────────────────┤
│  DÉTAIL DES ROUNDS                          │
│  Round 1 : "Hotel California" - Eagles      │
│    Alice : ✓ 950 pts (2.3s)                │
│    Bob   : ✓ 820 pts (4.1s)                │
│  ...                                        │
└─────────────────────────────────────────────┘
```

#### Endpoint

```
GET /api/games/{room_code}/results/pdf/
Authorization: Bearer <token>
→ Response: application/pdf
```

---

## Interactions entre services

### Flux complet : Démarrage d'une partie classique

```
Frontend                 GameConsumer           GameService
   │                          │                     │
   │  WS: start_game          │                     │
   │─────────────────────────►│                     │
   │                          │ start_game(game)    │
   │                          │────────────────────►│
   │                          │                     │ get_playlist_tracks()
   │                          │                     │────────────────────►DeezerService
   │                          │                     │◄────────────────────
   │                          │                     │ generate_rounds()
   │                          │                     │────────────────────►QuestionGeneratorService
   │                          │                     │◄────────────────────
   │                          │                     │ Crée N GameRound
   │                          │◄────────────────────│
   │                          │ broadcast_round_start│
   │                          │────────────────────►BroadcastService
   │  WS: round_started       │                     │
   │◄─────────────────────────│                     │
```

### Flux complet : Soumission d'une réponse avec bonus

```
Frontend                 GameConsumer      GameService      BonusService
   │                          │                │                │
   │  WS: player_answer       │                │                │
   │─────────────────────────►│                │                │
   │                          │ submit_answer()│                │
   │                          │───────────────►│                │
   │                          │                │ check_answer() │
   │                          │                │ (is_correct)   │
   │                          │                │                │
   │                          │                │ apply_score_bonuses()
   │                          │                │───────────────►│
   │                          │                │◄───────────────│
   │                          │                │ points_final   │
   │                          │                │ Crée GameAnswer│
   │                          │◄───────────────│                │
   │  WS: player_answered     │                │                │
   │◄─────────────────────────│                │                │
```

---

## Patterns communs

### Pattern Singleton

Tous les services sont instanciés une seule fois au niveau du module. Cela évite de recréer les connexions Redis et les sessions HTTP à chaque requête :

```python
# En bas de chaque fichier service :
deezer_service = DeezerService()
youtube_service = YouTubeService()
# etc.

# Dans les vues :
from apps.playlists.deezer_service import deezer_service
results = deezer_service.search_playlists("rock")
```

### Gestion des erreurs

Les services d'intégration externe utilisent des exceptions spécifiques :

```python
class DeezerAPIError(Exception):
    """Erreur de communication avec l'API Deezer"""

class YouTubeAPIError(Exception):
    """Erreur de communication avec l'API YouTube"""

class LyricsNotFoundError(Exception):
    """Paroles introuvables pour la piste"""
```

Les consommateurs de ces services (GameService, QuestionGeneratorService) attrapent ces exceptions et fournissent des comportements de fallback (ex. : passer la piste sans paroles, utiliser un autre fournisseur).

### Cache Redis — conventions de nommage des clés

```
deezer:search_playlists:{query}:{limit}    TTL 3600s
deezer:playlist:{playlist_id}              TTL 3600s
deezer:playlist_tracks:{id}:{limit}        TTL 1800s
deezer:track:{track_id}                    TTL 3600s
youtube:search_playlists:{query}:{limit}   TTL 3600s
youtube:playlist:{playlist_id}             TTL 3600s
lyrics:{artist}:{title}                    TTL 3600s
lyrics:synced:{artist}:{title}             TTL 3600s
lyrics:lrclib_id:{id}                      TTL 3600s
lrclib:circuit_breaker                     TTL 90s
```
