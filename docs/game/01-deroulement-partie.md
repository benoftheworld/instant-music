# Déroulement d'une partie — InstantMusic

## Vue d'ensemble

Une partie InstantMusic passe par **5 étapes principales** depuis la création jusqu'aux résultats finaux. Chaque étape implique des interactions entre le frontend (React), le backend (Django), la base de données (PostgreSQL) et le broker de messages (Redis/Channels).

```
┌─────────────────────────────────────────────────────────────────┐
│               CYCLE DE VIE D'UNE PARTIE                         │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │Création  │→ │  Lobby   │→ │  Jeu     │→ │  Résultats   │   │
│  │          │  │(attente) │  │(boucle)  │  │              │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│                                                                 │
│  Base de données :                                              │
│  waiting  ─────────────────────────►  in_progress  ──► finished│
└─────────────────────────────────────────────────────────────────┘
```

---

## Étape 1 — Création de partie (`CreateGamePage`)

### Ce que fait le joueur

L'hôte configure sa partie via un formulaire :

```
┌────────────────────────────────────────────────┐
│              CRÉER UNE PARTIE                   │
│                                                │
│  Mode de jeu :   [Classique ▼]                 │
│                                                │
│  Playlist :      [Hits 2024 ▼]                 │
│                  ○ Sélectionner une playlist   │
│                  ○ Entrer une URL Deezer        │
│                                                │
│  Nombre de rounds :  [10 ──────── 30]          │
│  Durée par round :   [20s ─────── 60s]         │
│  Mode de réponse :   ● QCM  ○ Texte libre      │
│  Deviner :           ● Titre  ○ Artiste        │
│                                                │
│            [Créer la partie]                   │
└────────────────────────────────────────────────┘
```

### Ce qui se passe côté backend

```
POST /api/games/
{
  "game_mode": "classique",
  "playlist_id": 42,
  "total_rounds": 15,
  "round_duration": 30,
  "answer_mode": "mcq",
  "guess_target": "title"
}

← 201 Created
{
  "id": 123,
  "room_code": "AZERTY",   ← Code unique généré automatiquement
  "status": "waiting",
  "host": { "id": 1, ... }
}
```

Un **code de salle** unique (6 caractères alphanumériques) est généré. Les autres joueurs l'utilisent pour rejoindre.

---

## Étape 2 — Lobby (`GameLobbyPage`)

### Connexion WebSocket

Dès que le lobby est affiché, une connexion WebSocket est établie.

```
GET /game/lobby/AZERTY
        │
        ▼
useGameWebSocket("AZERTY")
        │
        ▼  Connexion
ws://backend:8000/ws/game/AZERTY/?token=eyJ...
        │
        ▼  Serveur
GameConsumer.connect()
  → Vérifie le token JWT
  → Ajoute le joueur au group Redis "game_AZERTY"
  → Broadcast player_join à tous les membres du group
```

### Interface du lobby

```
┌────────────────────────────────────────────────┐
│         SALLE AZERTY  ─  Mode Classique        │
│                                                │
│  Joueurs connectés (3/8) :                     │
│  ✓ Alice (hôte)          ● connecté            │
│  ✓ Bob                   ● connecté            │
│  ✓ Charlie               ● connecté            │
│  ○ En attente...                               │
│                                                │
│  Partager le code : AZERTY                     │
│  [Copier le lien]  [Inviter des amis]           │
│                                                │
│  ───────────────────────────────────────────   │
│  [Démarrer la partie]   ← visible pour l'hôte  │
└────────────────────────────────────────────────┘
```

### Messages WebSocket échangés dans le lobby

```
Quand Bob rejoint :
  Bob → WS : { type: "player_join" }
  Serveur → Tous : { type: "player_joined", data: { user: {Bob}, players: [...] } }

Quand Charlie rejoint :
  Charlie → WS : { type: "player_join" }
  Serveur → Tous : { type: "player_joined", data: { user: {Charlie}, players: [...] } }

Quand Bob se déconnecte :
  Serveur → Tous : { type: "player_left", data: { user_id: 2, players: [...] } }
```

---

## Étape 3 — Démarrage de la partie

### Ce que fait l'hôte

L'hôte clique "Démarrer la partie". Le client envoie un message WebSocket.

```
Alice → WS : { type: "start_game" }
```

### Ce que fait le serveur

```python
# backend/apps/games/consumers.py (GameConsumer)
async def start_game(self, data):
    # 1. Vérifier que c'est bien l'hôte
    if self.user.id != game.host_id:
        await self.send_error("Seul l'hôte peut démarrer")
        return

    # 2. Vérifier qu'il y a au moins 2 joueurs
    if game.players.count() < 2:
        await self.send_error("Il faut au moins 2 joueurs")
        return

    # 3. Générer tous les rounds depuis Deezer
    await GameService.generate_rounds(game)

    # 4. Passer la partie en "in_progress"
    game.status = 'in_progress'
    await game.asave()

    # 5. Broadcast à tous les joueurs
    await self.channel_layer.group_send(
        f"game_{self.room_code}",
        {
            "type": "game_started",
            "data": {
                "total_rounds": game.total_rounds,
                "players": [...],
            }
        }
    )

    # 6. Démarrer le premier round
    await self.start_next_round()
```

### Génération des rounds depuis Deezer

```
GameService.generate_rounds(game)
        │
        ▼
Récupère la playlist Deezer via API :
GET https://api.deezer.com/playlist/{playlist_id}/tracks
        │
        ▼
Sélectionne aléatoirement `total_rounds` pistes
        │
        ▼
Pour chaque piste → crée un GameRound en DB :
  GameRound(
    game=game,
    round_number=1,
    track_title="Shape of You",
    track_artist="Ed Sheeran",
    audio_preview_url="https://cdns-preview-d.dzcdn.net/...",
    correct_answer="Shape of You",   # ou nom artiste selon guess_target
    choices=["Shape of You", "Blinding Lights", "Bad Guy", "Levitating"]
  )
```

---

## Étape 4 — Boucle de jeu

### Vue d'ensemble de la boucle

```
┌─────────────────────────────────────────────────────────────────┐
│                    BOUCLE D'UN ROUND                            │
│                                                                 │
│  ┌──────────────────┐                                           │
│  │  Serveur envoie  │ → round_started (question, audio, timer)  │
│  │  round_started   │                                           │
│  └──────────────────┘                                           │
│          │ timer_start_round secondes                           │
│          ▼                                                      │
│  ┌──────────────────┐                                           │
│  │  Joueurs lisent  │  ← Audio Deezer démarre                   │
│  │  la question     │  ← Timer affiché                          │
│  └──────────────────┘                                           │
│          │                                                      │
│          ▼ (joueur répond)                                      │
│  ┌──────────────────┐                                           │
│  │  player_answer   │ → Serveur valide + calcule score          │
│  └──────────────────┘    → Broadcast player_answered           │
│          │                                                      │
│          ▼ (tous ont répondu OU timer expiré)                   │
│  ┌──────────────────┐                                           │
│  │  round_ended     │ ← Serveur broadcast (scores, bonne rép.)  │
│  └──────────────────┘                                           │
│          │ score_display_duration secondes                      │
│          ▼                                                      │
│  ┌──────────────────┐                                           │
│  │  next_round      │ → Hôte envoie (ou auto-avance)            │
│  └──────────────────┘                                           │
│          │                                                      │
│   [round suivant] ──── ou ──── [game_finished]                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4a. Démarrage d'un round (`round_started`)

```
Serveur → Tous :
{
  "type": "round_started",
  "data": {
    "round_number": 1,
    "question": {
      "audio_url": "https://cdns-preview-d.dzcdn.net/...",
      "choices": ["Shape of You", "Blinding Lights", "Bad Guy", "Levitating"],
      "question_text": "Quel est le titre de cette chanson ?"
    },
    "timer_duration": 30,
    "timer_start_round": 3
  }
}
```

Le frontend :
1. Met à jour l'état → `phase: 'playing'`
2. Affiche un compte à rebours de `timer_start_round` secondes
3. Lance ensuite la lecture audio (Howler.js) de l'extrait Deezer
4. Affiche les choix de réponse

### 4b. Réponse d'un joueur (`player_answer`)

```
Joueur → Serveur :
{ "type": "player_answer", "answer": "Shape of You" }

        │
        ▼  Serveur :
GameConsumer.player_answer()
        │
        ▼
GameService.submit_answer(player, round, answer, response_time)
        │
        ├── Vérifier si correct
        ├── Calculer les points (voir modes de jeu)
        ├── Appliquer les bonus actifs
        └── Sauvegarder GameAnswer en DB

        │
        ▼  Broadcast à tous :
{
  "type": "player_answered",
  "data": {
    "player_id": 42,
    "response_time": 12.4   // secondes (sans révéler si correct)
  }
}
```

> Note : Le serveur ne révèle PAS si la réponse est correcte avant la fin du round. Cela évite que les joueurs lents ne copient.

### 4c. Fin d'un round (`round_ended`)

Le round se termine quand :
- Tous les joueurs ont répondu, **ou**
- Le timer expire (géré par une tâche Celery)

```
Serveur → Tous :
{
  "type": "round_ended",
  "data": {
    "correct_answer": "Shape of You",
    "scores": [
      {
        "player_id": 1,
        "player_name": "Alice",
        "points_earned": 850,
        "is_correct": true,
        "response_time": 8.2
      },
      {
        "player_id": 2,
        "player_name": "Bob",
        "points_earned": 0,
        "is_correct": false,
        "response_time": null
      }
    ],
    "rankings": [
      { "player_id": 1, "total_score": 850, "rank": 1 },
      { "player_id": 2, "total_score": 0, "rank": 2 }
    ]
  }
}
```

### 4d. Affichage des résultats et round suivant

```
Frontend :
  Phase → 'showing_results'
  Affiche : bonne réponse + scores de chaque joueur + classement
  Timer : score_display_duration secondes (ex: 5s)
         ↓
  Hôte voit : bouton "Round suivant"
  Auto-avance si timer expiré

Hôte → Serveur :
{ "type": "next_round" }

Serveur :
  Si dernier round → game_finished
  Sinon → start_next_round() → broadcast round_started
```

---

## Étape 5 — Fin de partie (`game_finished`)

### Message serveur

```
Serveur → Tous :
{
  "type": "game_finished",
  "data": {
    "final_rankings": [
      {
        "rank": 1,
        "player_id": 1,
        "player_name": "Alice",
        "total_score": 8450,
        "correct_answers": 12,
        "accuracy": 0.8
      },
      {
        "rank": 2,
        "player_id": 3,
        "player_name": "Charlie",
        "total_score": 7200,
        "correct_answers": 10,
        "accuracy": 0.67
      }
    ]
  }
}
```

### Ce qui se passe en base de données

```python
# GameService.finish_game()
game.status = 'finished'
game.finished_at = timezone.now()
await game.asave()

# Calcul du gagnant
winner = max(players, key=lambda p: p.score)
game.winner = winner.user
await game.asave()

# Trigger async : vérification des achievements
check_achievements_async.delay(user_id, game_id)

# Mise à jour des statistiques joueurs
update_player_stats.delay(game_id)
```

### Redirection vers les résultats

```
Frontend :
  gameState.phase = 'game_over'
        │
        ▼
  <Navigate to="/game/AZERTY/results" />
        │
        ▼
  GameResultsPage
        │
        ▼
  GET /api/games/AZERTY/results/
  → Affiche classement final, stats, achievements débloqués
```

---

## Diagramme de séquence complet

```
Alice (Hôte)       Bob              Serveur            Base de données
     │               │                  │                    │
     │── POST /api/games/ ─────────────►│                    │
     │                                  │── INSERT Game ────►│
     │◄── 201 { room_code: "AZERTY" } ──│◄─ Game{id:123} ────│
     │                                  │                    │
     │── WS: connect /ws/game/AZERTY/ ─►│                    │
     │◄── { type: player_joined } ──────│                    │
     │               │                  │                    │
     │               │── WS: connect ──►│                    │
     │               │◄── joined ───────│                    │
     │◄── { type: player_joined, Bob } ─│                    │
     │               │                  │                    │
     │── { type: "start_game" } ────────►│                    │
     │                                  │── generate_rounds ►│
     │                                  │◄── rounds créés ───│
     │                                  │── UPDATE status ──►│
     │◄── { type: "game_started" } ─────│                    │
     │               │◄── game_started ─│                    │
     │                                  │                    │
     │                                  │── start_round(1) ──│
     │◄── { type: "round_started",      │                    │
     │      round:1, audio_url, choices }│                   │
     │               │◄── round_started ─│                   │
     │               │                  │                    │
     │  [joue audio, affiche choix]      │                    │
     │               │ [joue audio]      │                    │
     │               │                  │                    │
     │── { type: "player_answer",        │                    │
     │     answer: "Shape of You" } ────►│                    │
     │                                  │── submit_answer ──►│
     │                                  │◄── GameAnswer ─────│
     │◄── { type: "player_answered",    │                    │
     │      player_id: 1 } ─────────────│                    │
     │               │◄── player_answered│                   │
     │               │                  │                    │
     │               │── { type: "player_answer",            │
     │               │   answer: "Bad Guy" } ───────────────►│
     │                                  │── submit_answer ──►│
     │◄── { type: "player_answered",    │◄── GameAnswer ─────│
     │      player_id: 2 } ─────────────│                    │
     │               │◄── player_answered│                   │
     │                                  │                    │
     │    [tous ont répondu]            │                    │
     │◄── { type: "round_ended",        │                    │
     │      correct_answer: "Shape of You",                   │
     │      scores: [...] } ────────────│                    │
     │               │◄── round_ended ──│                    │
     │               │                  │                    │
     │  [affiche résultats 5s]          │                    │
     │── { type: "next_round" } ────────►│                    │
     │                                  │                    │
     │  ... [répéter pour rounds 2..N] ...                    │
     │                                  │                    │
     │◄── { type: "game_finished",      │                    │
     │      final_rankings: [...] } ────│                    │
     │               │◄── game_finished ─│                   │
     │                                  │── UPDATE finished ►│
     │  [→ /game/AZERTY/results]        │── check_achievements│
     │               │  [→ results]     │   (Celery async)   │
```

---

## États de la partie en base de données

```
          ┌──────────┐
   Création│          │
  ─────────►  waiting  │
           │          │
           └────┬─────┘
                │ start_game
                ▼
           ┌────────────┐
           │ in_progress │
           └────┬───────┘
                │
        ┌───────┴───────┐
        │               │
   finish_game      cancel_game
        │               │
        ▼               ▼
   ┌──────────┐  ┌──────────────┐
   │ finished  │  │  cancelled   │
   └──────────┘  └──────────────┘
```

### Modèle Django `Game`

```python
class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('in_progress', 'En cours'),
        ('finished', 'Terminée'),
        ('cancelled', 'Annulée'),
    ]

    room_code = models.CharField(max_length=6, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    game_mode = models.CharField(max_length=20)
    answer_mode = models.CharField(max_length=10, default='mcq')
    guess_target = models.CharField(max_length=10, default='title')
    total_rounds = models.IntegerField(default=10)
    current_round = models.IntegerField(default=0)
    round_duration = models.IntegerField(default=30)  # secondes
    timer_start_round = models.IntegerField(default=3)
    score_display_duration = models.IntegerField(default=5)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_games')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    winner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
```

---

## Configuration de la partie

| Paramètre                | Valeur par défaut | Description                              |
| ------------------------ | ----------------- | ---------------------------------------- |
| `total_rounds`           | 10                | Nombre de questions                      |
| `round_duration`         | 30                | Secondes pour répondre                   |
| `timer_start_round`      | 3                 | Secondes d'attente avant audio           |
| `score_display_duration` | 5                 | Secondes d'affichage des scores          |
| `answer_mode`            | `mcq`             | `mcq` (4 choix) ou `text` (saisie libre) |
| `guess_target`           | `title`           | `title` (titre) ou `artist` (artiste)    |
| `max_players`            | 8                 | Joueurs maximum par salle                |
