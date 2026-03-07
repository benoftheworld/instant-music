# Modes de jeu — InstantMusic

## Vue d'ensemble

InstantMusic propose **6 modes de jeu** distincts, chacun offrant une expérience différente autour de la musique. Tous les modes partagent la même infrastructure (WebSocket, timer, scores) mais diffèrent dans la source du contenu, le type de question et les mécaniques de gameplay.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        6 MODES DE JEU                               │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │ Classique  │  │   Rapide   │  │ Génération │                     │
│  │            │  │            │  │            │                     │
│  │ Titre ou   │  │ Titre ou   │  │  Année de  │                     │
│  │ artiste ?  │  │ artiste ?  │  │  sortie ?  │                     │
│  │ (30s)      │  │ (15s)      │  │            │                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │  Paroles   │  │  Karaoké   │  │   Mollo    │                     │
│  │            │  │            │  │            │                     │
│  │ Compléter  │  │ Paroles    │  │ Audio      │                     │
│  │ les paroles│  │ synchro.   │  │ ralenti    │                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tableau comparatif

| Mode       | Code         | Source audio             | Type question  | `answer_mode`   | `guess_target`      | Durée       |
| ---------- | ------------ | ------------------------ | -------------- | --------------- | ------------------- | ----------- |
| Classique  | `classique`  | Deezer preview 30s       | MCQ ou texte   | `mcq` ou `text` | `title` ou `artist` | 30s         |
| Rapide     | `rapide`     | Deezer preview 30s       | MCQ ou texte   | `mcq` ou `text` | `title` ou `artist` | 15s         |
| Génération | `generation` | Deezer preview 30s       | MCQ années     | `mcq`           | `year`              | 30s         |
| Paroles    | `paroles`    | Deezer preview 30s       | Fill-in-blank  | `mcq` ou `text` | `lyrics`            | 30s         |
| Karaoké    | `karaoke`    | YouTube embed            | Karaoké scroll | `text`          | `lyrics`            | durée vidéo |
| Mollo      | `mollo`      | Deezer preview (ralenti) | MCQ ou texte   | `mcq` ou `text` | `title` ou `artist` | 45s         |

---

## Mode 1 — Classique

### Description

Le mode de base. Un extrait musical Deezer de 30 secondes est joué, et les joueurs doivent identifier soit le **titre** soit l'**artiste** selon la configuration choisie.

### Interface

```
┌──────────────────────────────────────────────────────┐
│  ♫  Shape of You — Ed Sheeran                        │
│  ████████████████░░░░░░░░░░░░  0:18 restante          │
│                                                      │
│  Quel est le titre de cette chanson ?               │
│                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │  ✓ Shape of You     │  │    Blinding Lights   │   │
│  └─────────────────────┘  └─────────────────────┘   │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │       Bad Guy       │  │     Levitating       │   │
│  └─────────────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Génération des questions

```python
# Génération des distracteurs (fausses réponses)
def generate_mcq_choices(correct_answer: str, game_mode: str, playlist: Playlist) -> list[str]:
    """
    Génère 3 distracteurs plausibles en piochant dans la playlist
    ou dans la base Deezer, puis mélange avec la bonne réponse.
    """
    all_tracks = playlist.tracks.exclude(title=correct_answer)

    if game_mode == 'classique' and guess_target == 'title':
        distractors = random.sample(
            [t.title for t in all_tracks], 3
        )
    elif guess_target == 'artist':
        distractors = random.sample(
            list(set([t.artist for t in all_tracks])), 3
        )

    choices = [correct_answer] + distractors
    random.shuffle(choices)
    return choices
```

### Paramètres spécifiques

| Paramètre           | Valeur                             |
| ------------------- | ---------------------------------- |
| `round_duration`    | 30 secondes                        |
| Nombre de choix MCQ | 4                                  |
| `guess_target`      | `title` ou `artist` (configurable) |
| Source audio        | Deezer preview (30s max)           |

---

## Mode 2 — Rapide

### Description

Version accélérée du mode Classique. La durée de réponse est réduite de moitié (15s), ce qui augmente la pression et favorise les joueurs qui ont une bonne mémoire musicale immédiate. Les points sont identiques mais la fenêtre de temps est plus courte, donc les bonus de vitesse sont plus difficiles à obtenir.

### Différences avec Classique

```
Classique                    Rapide
──────────                   ──────
round_duration = 30s    vs   round_duration = 15s
score max à 0s          vs   score max à 0s
TIME_PENALTY par seconde     TIME_PENALTY par seconde (x2 effet)
```

### Stratégie de score

La rapidité est encore plus déterminante dans ce mode. Répondre dans les 3 premières secondes rapporte le score maximal, alors qu'attendre 14 secondes donne presque le score minimum.

---

## Mode 3 — Génération

### Description

Les joueurs doivent deviner l'**année de sortie** de la chanson. Les 4 choix proposent des années proches, ce qui demande une bonne connaissance de la chronologie musicale.

### Interface

```
┌──────────────────────────────────────────────────────┐
│  ♫  Don't Stop Me Now — Queen                        │
│  ████████████████░░░░░░░░░░░░  0:15 restante          │
│                                                      │
│  En quelle année est sortie cette chanson ?         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   1975   │  │   1978   │  │   1981   │  │   1984   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────────────────────────────────────────┘
```

### Génération des choix d'années

```python
def generate_year_choices(correct_year: int) -> list[int]:
    """
    Génère 3 années proches pour rendre le quiz difficile.
    Les années sont espacées de 2 à 5 ans maximum.
    """
    offsets = random.sample([-5, -4, -3, -2, 2, 3, 4, 5], 3)
    distractors = [correct_year + offset for offset in offsets]
    choices = [correct_year] + distractors
    choices.sort()  # Les années sont toujours triées chronologiquement
    return choices
```

### Source de la donnée

La propriété `release_date` de l'API Deezer fournit la date de sortie au format `YYYY-MM-DD`. On extrait l'année :

```python
track_data = deezer_api.get_track(track_id)
correct_year = int(track_data['release_date'][:4])  # "1978-10-13" → 1978
```

### Spécificité de scoring

Le scoring utilise la **proximité** en mode texte ou est binaire en MCQ. En MCQ, il n'y a que correct (100%) ou incorrect (0%).

---

## Mode 4 — Paroles

### Description

Un extrait de paroles est affiché avec un ou plusieurs **mots masqués**. Les joueurs doivent trouver les mots manquants. Ce mode combine l'écoute musicale et la mémorisation des paroles.

### Interface

```
┌──────────────────────────────────────────────────────┐
│  ♫  Bohemian Rhapsody — Queen                        │
│                                                      │
│  Complète les paroles :                              │
│                                                      │
│  "Is this the real life ?                            │
│   Is this just ________ ?                            │
│   Caught in a landslide,                             │
│   No escape from ________"                           │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │  fantasy    │  │   reality   │                   │
│  └─────────────┘  └─────────────┘                   │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │   memory    │  │   misery    │                   │
│  └─────────────┘  └─────────────┘                   │
└──────────────────────────────────────────────────────┘
```

### Sources des paroles

Le backend utilise **deux sources** pour récupérer les paroles :

1. **LRCLib** (prioritaire) : base de données de paroles avec timestamps LRC pour la synchronisation
2. **lyrics.ovh** (fallback) : API gratuite de paroles sans timestamps

```python
# backend/apps/playlists/lyrics_service.py
async def get_lyrics(artist: str, title: str) -> LyricsResult | None:
    # 1. Essayer LRCLib
    result = await lrclib_client.get_lyrics(artist, title)
    if result:
        return LyricsResult(
            lyrics=result.plain_lyrics,
            synced_lyrics=result.synced_lyrics,  # Format LRC
            source='lrclib'
        )

    # 2. Fallback sur lyrics.ovh
    result = await lyrics_ovh_client.get_lyrics(artist, title)
    if result:
        return LyricsResult(
            lyrics=result.lyrics,
            synced_lyrics=None,
            source='lyrics_ovh'
        )

    return None
```

### Génération du fill-in-blank

```python
def generate_lyrics_question(lyrics: str) -> LyricsQuestion:
    """
    Sélectionne un extrait de 4 lignes et masque 1-2 mots clés.
    """
    lines = lyrics.strip().split('\n')
    # Choisir 4 lignes consécutives
    start = random.randint(0, len(lines) - 4)
    excerpt = lines[start:start + 4]

    # Trouver les mots "intéressants" (longueur > 4, non communs)
    candidates = find_interesting_words(excerpt)

    # Masquer 1 mot dans la dernière ligne
    masked_word = random.choice(candidates)
    masked_excerpt = mask_word(excerpt, masked_word)

    return LyricsQuestion(
        masked_text=masked_excerpt,
        correct_answer=masked_word,
        choices=generate_word_distractors(masked_word)
    )
```

---

## Mode 5 — Karaoké

### Description

Le mode le plus immersif. Une vidéo YouTube de la chanson est embarquée, et les paroles défilent en **synchronisation** avec la musique (format karaoké). Les joueurs doivent trouver le mot manquant en regardant les paroles défiler.

### Architecture technique

```
┌───────────────────────────────────────────────────────────────────┐
│                      MODE KARAOKÉ                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  YouTube IFrame                            │  │
│  │         (vidéo officielle de la chanson)                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │            Paroles synchronisées (LRC)                     │  │
│  │                                                            │  │
│  │  [00:42.50] Is this the real life?                         │  │
│  │  [00:46.10] Is this just ████████?      ← mot masqué      │  │
│  │  [00:50.32] Caught in a landslide...                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### Prérequis des données

Pour qu'une chanson soit disponible en mode Karaoké, elle doit avoir :
- Un champ `lrclib_id` : identifiant LRCLib pour les paroles synchronisées
- Un champ `youtube_id` : identifiant de la vidéo YouTube

```python
class Track(models.Model):
    # ... autres champs
    lrclib_id = models.IntegerField(null=True, blank=True)
    youtube_id = models.CharField(max_length=20, null=True, blank=True)

    @property
    def is_karaoke_compatible(self) -> bool:
        return bool(self.lrclib_id and self.youtube_id)
```

### Format LRC (paroles synchronisées)

Le format LRC est un fichier texte avec des timestamps au format `[mm:ss.xx]` :

```
[00:42.50] Is this the real life?
[00:46.10] Is this just fantasy?
[00:50.32] Caught in a landslide,
[00:54.41] No escape from reality
[00:58.60] Open your eyes,
[01:02.71] Look up to the skies and see
```

### Composant `KaraokeQuestion.tsx`

```typescript
// La logique de synchronisation utilise l'API YouTube IFrame
// pour connaître le temps courant et surligner la ligne active

const KaraokeQuestion = ({ lrcContent, videoId, maskedWord }) => {
  const [currentTime, setCurrentTime] = useState(0)
  const parsedLyrics = useMemo(() => parseLRC(lrcContent), [lrcContent])

  // Mise à jour du temps toutes les 100ms
  useEffect(() => {
    const interval = setInterval(() => {
      const time = youtubePlayer.getCurrentTime()
      setCurrentTime(time)
    }, 100)
    return () => clearInterval(interval)
  }, [])

  // Trouver la ligne active
  const activeLine = parsedLyrics.findLast(
    line => line.timestamp <= currentTime
  )

  return (
    <div className="karaoke-container">
      <div id="youtube-player" />
      <div className="lyrics-scroll">
        {parsedLyrics.map((line, i) => (
          <p
            key={i}
            className={line === activeLine ? 'active' : ''}
          >
            {line.text.replace(maskedWord, '______')}
          </p>
        ))}
      </div>
    </div>
  )
}
```

---

## Mode 6 — Mollo

### Description

L'audio Deezer est joué à **vitesse réduite** (ex: 75% de la vitesse normale), ce qui déforme le pitch et rend la chanson plus difficile à reconnaître. Ce mode teste les connaisseurs qui connaissent les chansons "dans leur os".

### Implémentation du ralentissement

Le ralentissement est réalisé côté frontend via l'API Web Audio :

```typescript
// services/soundEffects.ts — Mode Mollo
const createSlowedPlayer = (audioUrl: string, speed: number = 0.75) => {
  const sound = new Howl({
    src: [audioUrl],
    rate: speed,         // 0.75 = 75% de la vitesse normale
    // Note: Howler ajuste automatiquement le pitch
  })
  return sound
}
```

Alternativement, côté serveur avec `librosa` ou `pydub` pour un traitement audio plus avancé (pitch-shift sans modification de tempo).

### Interface

Identique au mode Classique, avec un indicateur visuel "RALENTI" et une icône tortue pour signaler le mode spécial.

```
┌──────────────────────────────────────────────────────┐
│  🐢 MODE MOLLO — Audio ralenti à 75%                 │
│  ♫  ~~~ (extrait déformé) ~~~                        │
│  ████████████░░░░░░░░░░░░░░░  0:30 restante           │
│                                                      │
│  Quel est le titre de cette chanson ?               │
│  ┌────────────┐  ┌────────────┐                      │
│  │ Titre A    │  │ Titre B    │                      │
│  └────────────┘  └────────────┘                      │
└──────────────────────────────────────────────────────┘
```

### Durée étendue

La durée est augmentée à 45 secondes pour compenser la difficulté accrue.

---

## Calcul du score

### Formule principale

```python
# backend/apps/games/services.py

BASE_POINTS = 1000       # Points maximum pour une réponse parfaite
MIN_POINTS = 100         # Points minimum si réponse correcte très lente
TIME_PENALTY = 20        # Points perdus par seconde

def calculate_score(
    is_correct: bool,
    response_time: float,
    round_duration: float,
    accuracy_factor: float = 1.0
) -> int:
    if not is_correct:
        return 0

    # Décrément linéaire selon le temps de réponse
    time_based_points = max(MIN_POINTS, BASE_POINTS - response_time * TIME_PENALTY)

    # Facteur de précision (1.0 pour MCQ correct, 0.0-1.0 pour texte libre)
    points = round(time_based_points * accuracy_factor)

    return points
```

### Visualisation du score selon le temps de réponse

```
Points
 1000 ┤●
  900 ┤ ╲
  800 ┤  ╲
  700 ┤   ╲
  600 ┤    ╲
  500 ┤     ╲
  400 ┤      ╲
  300 ┤       ╲
  200 ┤        ╲
  100 ┤─────────●────────────●
      └──────────────────────────► Temps (secondes)
      0    5    10   15   20   25   30

  Répondre en 0s = 1000 pts
  Répondre en 5s = 900 pts
  Répondre en 45s = 100 pts (minimum)
```

### Mode texte — `accuracy_factor`

En mode texte libre, la réponse est comparée à la bonne réponse via un algorithme de similarité (distance de Levenshtein normalisée).

```python
from difflib import SequenceMatcher

def calculate_text_accuracy(user_answer: str, correct_answer: str) -> float:
    """
    Retourne un score entre 0.0 et 1.0 selon la similarité.
    0.0 = rien en commun
    1.0 = correspondance exacte
    """
    normalized_user = normalize_text(user_answer)
    normalized_correct = normalize_text(correct_answer)

    ratio = SequenceMatcher(None, normalized_user, normalized_correct).ratio()

    # Seuil minimal : en dessous de 0.6, on considère la réponse comme fausse
    return ratio if ratio >= 0.6 else 0.0


def normalize_text(text: str) -> str:
    """Supprime accents, articles, ponctuation, met en minuscules."""
    import unicodedata
    # Supprimer accents
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    # Minuscules
    text = text.lower()
    # Supprimer articles communs
    for article in ['the ', 'le ', 'la ', 'les ', "l'", 'a ', 'an ']:
        text = text.replace(article, '')
    # Supprimer ponctuation
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()
```

### Bonus de streak (enchaînement)

Si un joueur répond correctement à plusieurs rounds consécutifs, il reçoit des points bonus.

```python
STREAK_BONUS = {
    2: 50,    # 2 bonnes réponses consécutives = +50 pts
    3: 100,   # 3 = +100 pts
    4: 150,   # 4 = +150 pts
    5: 200,   # 5+ = +200 pts (plafonné)
}

def apply_streak_bonus(player: GamePlayer, base_points: int) -> int:
    streak = player.consecutive_correct
    bonus = STREAK_BONUS.get(min(streak, 5), 0)
    return base_points + bonus
```

### Comparaison des modes — Difficulté et temps

| Mode       | Durée    | Difficulté  | Spécificité                  |
| ---------- | -------- | ----------- | ---------------------------- |
| Classique  | 30s      | Moyen       | Standard, bonne introduction |
| Rapide     | 15s      | Élevé       | Stress et réflexes requis    |
| Génération | 30s      | Moyen-élevé | Connaissances culturelles    |
| Paroles    | 30s      | Moyen       | Mémorisation des paroles     |
| Karaoké    | Variable | Moyen       | Expérience immersive         |
| Mollo      | 45s      | Très élevé  | Audio déformé = déduction    |
