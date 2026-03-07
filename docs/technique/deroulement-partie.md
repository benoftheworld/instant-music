# Déroulement technique d'une partie — Documentation technique

## Vue d'ensemble

Une partie InstantMusic suit un cycle de vie en 5 phases. Ce document détaille le fonctionnement technique de chaque phase, les interactions entre frontend, backend, WebSocket et base de données.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Création │───►│  Lobby   │───►│  Rounds  │───►│  Score   │───►│ Résultat │
│          │    │ (attente)│    │ (en jeu) │    │ (calcul) │    │ (final)  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
  status:         status:         status:         status:         status:
  waiting         waiting       in_progress     in_progress      finished
```

---

## Phase 1 : Création de la partie

### Acteur : Hôte (joueur créateur)

**Frontend** → `CreateGamePage.tsx`

1. L'hôte configure la partie :
   - Mode de jeu (`classique`, `rapide`, `generation`, `paroles`, `karaoke`)
   - Playlist Deezer (recherche via API)
   - Options : nombre de rounds, durée, mode de réponse (QCM/texte), cible (artiste/titre)

2. Envoi de la requête :
   ```
   POST /api/games/
   Body: { mode, playlist_id, max_players, num_rounds, round_duration, ... }
   ```

**Backend** → `GameViewSet.create()`

3. Génération d'un `room_code` unique (6 caractères alphanumériques)
4. Création du modèle `Game` (UUID comme clé primaire)
5. Création automatique d'un `GamePlayer` pour l'hôte
6. Retour du `room_code` au frontend

**Modèle Game créé** :
```
Game(
  id=UUID,
  room_code="ABC123",
  host=user,
  mode="classique",
  status="waiting",
  playlist_id="123456789",
  num_rounds=10,
  round_duration=30,
  ...
)
```

---

## Phase 2 : Lobby (salle d'attente)

### Acteurs : Hôte + Joueurs

**Frontend** → `GameLobbyPage.tsx`

1. Le joueur arrive sur `/game/{room_code}/lobby`
2. Connexion WebSocket :
   ```typescript
   wsService.connect(roomCode)  // → ws://host/ws/game/{roomCode}/
   ```

**Backend** → `GameConsumer.connect()`

3. Le consumer :
   - Rejoint le group Redis `game_{room_code}`
   - Accepte la connexion WebSocket
   - Marque `GamePlayer.is_connected = True`
   - Broadcast `player_joined` à tout le group avec le `game_data` complet

**Rejoindre la partie** :

4. Requête API REST :
   ```
   POST /api/games/{room_code}/join/
   ```
5. Création d'un `GamePlayer(game=game, user=user, score=0)`
6. Le broadcast service notifie tous les clients via WebSocket

**Diagramme de séquence** :

```
Joueur B         Frontend B        Backend API      Consumer       Redis Group
   │                 │                  │                │               │
   │ Clic Rejoindre  │                  │                │               │
   ├────────────────►│                  │                │               │
   │                 │ POST /join/      │                │               │
   │                 ├─────────────────►│                │               │
   │                 │                  │ GamePlayer.create()            │
   │                 │   200 OK         │                │               │
   │                 │◄─────────────────┤                │               │
   │                 │                  │ broadcast_     │               │
   │                 │                  │ player_join()  │               │
   │                 │                  ├───────────────►│               │
   │                 │                  │                │ group_send()  │
   │                 │                  │                ├──────────────►│
   │                 │                  │                │               │
   │                 │◄────WS: player_joined─────────────┤◄──────────────┤
   │ UI: nouveau     │                  │                │               │
   │ joueur affiché   │                  │                │               │
   │◄────────────────┤                  │                │               │
```

---

## Phase 3 : Lancement et rounds

### Acteur : Hôte (déclenche le démarrage)

**Étape 3.1 — Démarrage de la partie**

1. L'hôte clique « Démarrer » → appel API :
   ```
   POST /api/games/{room_code}/start/
   ```

2. **Backend** → `GameService.start_game(game)` :
   - Vérifie que `status == "waiting"`
   - Appelle `QuestionGeneratorService.generate_questions()` :
     - Récupère les morceaux depuis l'API Deezer
     - Génère les questions selon le mode (voir section Modes)
   - Crée les objets `GameRound` en base
   - Passe `status` à `"in_progress"`, enregistre `started_at`
   - Démarre le premier round (`rounds[0].started_at = now`)

3. **Broadcast** → `broadcast_round_start(room_code, first_round)`
   - Tous les clients reçoivent `{"type": "round_started", "round_data": {...}}`

**Étape 3.2 — Déroulement d'un round**

```
┌──────────────────────────────────────────────────────┐
│                    Un round (30 sec)                   │
│                                                       │
│  ┌─────────┐  ┌───────────────┐  ┌────────────────┐ │
│  │ Timer    │  │ Écoute audio  │  │ Soumission     │ │
│  │ décompte │  │ + affichage   │  │ réponse        │ │
│  │ (5 sec)  │→ │ question      │→ │ (avant timer)  │ │
│  └─────────┘  └───────────────┘  └────────────────┘ │
│                                                       │
│  timer_start_round   round_duration    player_answer  │
└──────────────────────────────────────────────────────┘
```

**Frontend** → `GamePlayPage.tsx` :

1. Réception de `round_started` → affichage du décompte (`timer_start_round` secondes)
2. Lecture de l'extrait audio (30 sec d'un morceau Deezer via `preview_url`)
3. Affichage de la question (QCM 4 choix ou saisie libre selon `answer_mode`)
4. Le joueur soumet sa réponse :
   ```
   POST /api/games/{room_code}/answer/
   Body: { answer: "Titre du morceau", response_time: 12.5 }
   ```

**Étape 3.3 — Soumission et scoring**

**Backend** → `GameService.submit_answer()` :

```python
# 1. Vérification de la réponse
is_correct, accuracy_factor = self.check_answer(game_mode, answer, correct_answer, extra_data)

# 2. Calcul du score
points = self.calculate_score(accuracy_factor, response_time, round_duration)

# 3. Bonus de rapidité (les 3 premiers corrects)
rank_bonus = RANK_BONUS.get(correct_before, 0)  # {0: +10, 1: +5, 2: +2}

# 4. Enregistrement
GameAnswer.objects.create(round=round_obj, player=player, ...)
player.score += points
```

**Algorithme de scoring** :

```
score = max(10, (100 - response_time × 3)) × accuracy_factor
+ bonus de rang (10/5/2 pour les 3 premiers corrects)
```

| Paramètre            | Valeur    |
| -------------------- | --------- |
| Points de base       | 100       |
| Pénalité par seconde | -3 points |
| Minimum si correct   | 10 points |
| Bonus 1er correct    | +10       |
| Bonus 2ème correct   | +5        |
| Bonus 3ème correct   | +2        |

**Étape 3.4 — Fin de round**

1. L'hôte (ou un timer) déclenche :
   ```
   POST /api/games/{room_code}/end-round/
   ```
2. `GameService.end_round()` : enregistre `ended_at` sur le round
3. **Broadcast** → `broadcast_round_end()` envoie :
   ```json
   {
     "type": "round_ended",
     "results": {
       "correct_answer": "Bohemian Rhapsody",
       "round_data": { ... },
       "player_scores": {
         "alice": { "points_earned": 95, "is_correct": true, "response_time": 4.2 },
         "bob":   { "points_earned": 0,  "is_correct": false, "response_time": 28.1 }
       },
       "updated_players": [
         { "username": "alice", "score": 285, "rank": 1 },
         { "username": "bob",   "score": 190, "rank": 2 }
       ]
     }
   }
   ```
4. Frontend affiche l'écran de résultats du round (`RoundResultsScreen.tsx`)

**Étape 3.5 — Passage au round suivant**

1. Après `score_display_duration` secondes, l'hôte déclenche :
   ```
   POST /api/games/{room_code}/next-round/
   ```
2. `GameService.start_round(next_round)` : enregistre `started_at`
3. **Broadcast** → `broadcast_next_round()` avec les données du nouveau round + scores mis à jour
4. Retour à l'étape 3.2

---

## Phase 4 : Fin de partie

Quand le dernier round est terminé :

1. Appel API :
   ```
   POST /api/games/{room_code}/finish/
   ```

2. **Backend** → `GameService.finish_game()` :
   ```python
   game.status = GameStatus.FINISHED
   game.finished_at = timezone.now()

   # Classement final par score décroissant
   for rank, player in enumerate(players.order_by("-score"), start=1):
       player.rank = rank
       player.save()

       # Vérification des succès (perfect game, etc.)
       achievement_service.check_and_award(player.user, game=game, ...)

   game.save()  # Déclenche le signal pour maj des stats utilisateur
   ```

3. **Signal Django** (`update_player_stats_on_game_finish`) :
   - Met à jour `user.total_games_played`, `user.total_wins`, `user.total_points`

4. **Broadcast** → `broadcast_game_finish()` envoie les résultats finaux sérialisés

---

## Phase 5 : Résultats

**Frontend** → `GameResultsPage.tsx`

- Affichage du classement final (podium)
- Statistiques par joueur (score, réponses correctes, temps moyen)
- Succès débloqués pendant la partie
- Option de rejouer ou retourner à l'accueil

---

## Modes de jeu

### Classique / Rapide

| Aspect        | Classique                         | Rapide          |
| ------------- | --------------------------------- | --------------- |
| Extrait audio | 30 sec                            | **3 sec**       |
| Question      | QCM 4 choix (titre ou artiste)    | QCM 4 choix     |
| Mode texte    | Saisie libre avec fuzzy matching  | Saisie libre    |
| Double points | Artiste + Titre corrects en texte | Artiste + Titre |

**Fuzzy matching** (mode texte) :
- Normalisation : minuscules, suppression accents, articles (le/la/the)
- Comparaison : distance de Levenshtein pour chaînes ≤ 30 caractères
- Seuil de similarité : **80%**
- Bonus double points si artiste ET titre corrects (accuracy_factor = 2.0)

### Génération (année de sortie)

- Question : « En quelle année est sorti "Titre" de Artiste ? »
- QCM : 4 années plausibles (l'année correcte ± offsets aléatoires)
- Scoring avec tolérance :
  - Exact : 100% des points
  - ± 2 ans : 75%
  - ± 5 ans : 40%
  - Au-delà : 0 point

### Paroles

- Récupération des paroles via LRCLib
- Extraction d'un extrait avec mots à deviner (blancs)
- QCM : le(s) mot(s) correct(s) + 3 mauvaises réponses (tirées d'autres titres)
- Configurable : nombre de mots à deviner (2-10)

### Karaoké

- Morceau pré-sélectionné depuis le catalogue admin (`KaraokeSong`)
- Lecture via YouTube (vidéo complète, pas un extrait de 30 sec)
- Paroles synchronisées depuis LRCLib (format LRC avec timestamps)
- Pas de scoring (mode présentation/fun)
- Durée de round = durée de la vidéo (max 300 sec)

---

## Modèles de données

```
Game (UUID pk)
 ├── room_code (unique, 6 chars)
 ├── host → User
 ├── mode, status, answer_mode, guess_target
 ├── playlist_id, num_rounds, round_duration
 ├── created_at, started_at, finished_at
 │
 ├── GamePlayer (1:N)
 │    ├── user → User
 │    ├── score, rank, is_connected
 │    └── joined_at
 │
 └── GameRound (1:N, ordonné par round_number)
      ├── round_number, track_id, track_name, artist_name
      ├── correct_answer, options (JSON), question_type
      ├── preview_url, extra_data (JSON), duration
      ├── started_at, ended_at
      │
      └── GameAnswer (1:N)
           ├── player → GamePlayer
           ├── answer, is_correct, points_earned
           ├── response_time, answered_at
           └── unique_together: [round, player]
```

---

## Métriques Prometheus associées

| Métrique                                                   | Phase       |
| ---------------------------------------------------------- | ----------- |
| `instantmusic_games_created_total{mode}`                   | Création    |
| `instantmusic_games_active`                                | Lobby → Fin |
| `instantmusic_ws_connections_active`                       | Lobby → Fin |
| `instantmusic_answers_total{is_correct, game_mode}`        | Rounds      |
| `instantmusic_answer_response_time_seconds{game_mode}`     | Rounds      |
| `instantmusic_scores_earned{game_mode}`                    | Rounds      |
| `instantmusic_games_finished_total{mode}`                  | Fin         |
| `instantmusic_external_api_requests_total{service=deezer}` | Lancement   |
