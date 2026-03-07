# Système d'Achievements — InstantMusic

## Vue d'ensemble

Les achievements (succès/badges) récompensent les joueurs pour leurs accomplissements dans InstantMusic. Il existe **40+ achievements** organisés par catégories. Chaque achievement débloqué attribue des **coins** qui peuvent être dépensés dans la boutique.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SYSTÈME D'ACHIEVEMENTS                           │
│                                                                     │
│   Fin de partie ──► Celery task ──► Vérification conditions         │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │  check_achievements_async(user_id, game_id)              │     │
│   │                                                          │     │
│   │  Pour chaque Achievement en DB :                         │     │
│   │    1. condition_type == 'games_played' ?                 │     │
│   │       → user.games_played >= achievement.threshold ?    │     │
│   │    2. Déjà débloqué ? → passer                          │     │
│   │    3. Non débloqué + condition remplie → débloquer       │     │
│   └──────────────────────────────────────────────────────────┘     │
│                  │                                                  │
│                  ▼                                                  │
│   UserAchievement créé ──► coins_balance += achievement.points      │
│                  │                                                  │
│                  ▼                                                  │
│   NotificationConsumer.notify() ──► WS push ──► Toast frontend      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Catégories d'achievements

### 1. Parties jouées (`games_played`)

| Achievement     | Seuil | Coins | Description              |
| --------------- | ----- | ----- | ------------------------ |
| Première partie | 1     | 50    | Jouer sa première partie |
| Habitué         | 5     | 100   | Jouer 5 parties          |
| Joueur régulier | 25    | 250   | Jouer 25 parties         |
| Vétéran         | 100   | 500   | Jouer 100 parties        |
| Légende         | 500   | 1000  | Jouer 500 parties        |

### 2. Victoires (`wins`)

| Achievement       | Seuil | Coins | Description               |
| ----------------- | ----- | ----- | ------------------------- |
| Première victoire | 1     | 100   | Gagner sa première partie |
| Gagnant           | 5     | 200   | Gagner 5 parties          |
| Champion          | 25    | 500   | Gagner 25 parties         |
| Imbattable        | 100   | 1000  | Gagner 100 parties        |

### 3. Points accumulés (`points`)

| Achievement | Seuil   | Coins | Description                     |
| ----------- | ------- | ----- | ------------------------------- |
| Bon début   | 1 000   | 50    | Accumuler 1 000 points au total |
| Pointeur    | 10 000  | 150   | Accumuler 10 000 points         |
| Expert      | 50 000  | 400   | Accumuler 50 000 points         |
| Maître      | 250 000 | 800   | Accumuler 250 000 points        |

### 4. Rounds parfaits (`perfect_round`)

| Achievement     | Seuil | Coins | Description                          |
| --------------- | ----- | ----- | ------------------------------------ |
| Premier parfait | 1     | 75    | Répondre correctement en moins de 5s |
| Serial parfait  | 10    | 200   | 10 rounds parfaits au total          |
| Ultrasson       | 50    | 600   | 50 rounds parfaits                   |

### 5. Streaks (`streak`)

| Achievement  | Seuil | Coins | Description                     |
| ------------ | ----- | ----- | ------------------------------- |
| En rythme    | 3     | 100   | 3 bonnes réponses consécutives  |
| Dans la zone | 5     | 200   | 5 bonnes réponses consécutives  |
| Inarrêtable  | 10    | 500   | 10 bonnes réponses consécutives |
| Dieu du quiz | 15    | 1000  | 15 bonnes réponses consécutives |

### 6. Spécifiques aux modes de jeu

| Achievement        | Condition             | Coins | Description                         |
| ------------------ | --------------------- | ----- | ----------------------------------- |
| Mélomane classique | 10 parties classique  | 150   | Jouer 10 parties en mode Classique  |
| Speedrunner        | 10 parties rapide     | 200   | Jouer 10 parties en mode Rapide     |
| Historien          | 10 parties génération | 200   | Jouer 10 parties en mode Génération |
| Poète              | 10 parties paroles    | 200   | Jouer 10 parties en mode Paroles    |
| Star du karaoké    | 10 parties karaoké    | 300   | Jouer 10 parties en mode Karaoké    |
| Tortue musicale    | 10 parties mollo      | 200   | Jouer 10 parties en mode Mollo      |

### 7. Social (`social`)

| Achievement         | Condition         | Coins | Description                      |
| ------------------- | ----------------- | ----- | -------------------------------- |
| Premier ami         | 1 ami             | 100   | Ajouter un premier ami           |
| Bien entouré        | 10 amis           | 250   | Avoir 10 amis                    |
| Créateur d'équipe   | 1 équipe créée    | 150   | Créer une équipe                 |
| Chef de bande       | 10 membres équipe | 300   | Avoir 10 membres dans son équipe |
| Invitation acceptée | 1                 | 75    | Inviter un ami en partie         |

---

## Modèles de données

### Modèle `Achievement`

```python
# backend/apps/achievements/models.py

class Achievement(models.Model):
    CONDITION_TYPES = [
        ('games_played', 'Parties jouées'),
        ('wins', 'Victoires'),
        ('points', 'Points accumulés'),
        ('perfect_round', 'Rounds parfaits'),
        ('streak', 'Streak'),
        ('mode_games', 'Parties par mode'),
        ('social', 'Social'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    condition_type = models.CharField(max_length=30, choices=CONDITION_TYPES)
    condition_threshold = models.IntegerField()  # Ex: 5 pour "5 victoires"
    condition_game_mode = models.CharField(max_length=20, blank=True)  # Pour mode_games
    points = models.IntegerField()  # Coins attribués
    icon = models.CharField(max_length=100)  # Chemin vers l'icône
    is_secret = models.BooleanField(default=False)  # Caché jusqu'au débloquage

    class Meta:
        ordering = ['condition_type', 'condition_threshold']
```

### Modèle `UserAchievement`

```python
class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(Game, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ['user', 'achievement']  # Un achievement max par user
```

---

## Flux de déclenchement

### Étape 1 — Fin de partie

```python
# backend/apps/games/services.py

class GameService:
    @staticmethod
    async def finish_game(game: Game):
        # Terminer la partie
        game.status = 'finished'
        game.finished_at = timezone.now()
        await game.asave()

        # Pour chaque joueur, vérifier les achievements en arrière-plan
        async for game_player in game.players.all():
            # Celery .delay() = exécution asynchrone (non bloquant)
            check_achievements_async.delay(
                user_id=game_player.user.id,
                game_id=game.id
            )

        # Mettre à jour les statistiques
        update_player_stats_async.delay(game_id=game.id)
```

### Étape 2 — Tâche Celery

```python
# backend/apps/achievements/tasks.py
from celery import shared_task

@shared_task
def check_achievements_async(user_id: int, game_id: int):
    """
    Tâche asynchrone exécutée par un worker Celery.
    Vérifie toutes les conditions d'achievements pour l'utilisateur.
    """
    user = User.objects.get(id=user_id)
    game = Game.objects.get(id=game_id)

    # Récupérer les achievements déjà débloqués
    already_unlocked = set(
        UserAchievement.objects.filter(user=user)
        .values_list('achievement_id', flat=True)
    )

    # Vérifier tous les achievements disponibles
    achievements = Achievement.objects.exclude(id__in=already_unlocked)

    newly_unlocked = []
    for achievement in achievements:
        if check_achievement_condition(user, game, achievement):
            # Débloquer l'achievement
            user_ach = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                game=game
            )
            newly_unlocked.append(user_ach)

            # Attribuer les coins
            User.objects.filter(id=user_id).update(
                coins_balance=F('coins_balance') + achievement.points
            )

    # Notifier le client pour chaque nouvel achievement
    for user_ach in newly_unlocked:
        notify_achievement_unlocked.delay(
            user_id=user_id,
            achievement_id=user_ach.achievement.id
        )

    return len(newly_unlocked)
```

### Étape 3 — Vérification des conditions

```python
def check_achievement_condition(
    user: User,
    game: Game,
    achievement: Achievement
) -> bool:
    """Vérifie si la condition de l'achievement est remplie."""

    match achievement.condition_type:

        case 'games_played':
            count = UserAchievement.objects.filter(
                user=user
            ).count()  # Ou stats.total_games
            total = user.stats.total_games
            return total >= achievement.condition_threshold

        case 'wins':
            return user.stats.total_wins >= achievement.condition_threshold

        case 'points':
            return user.stats.total_points >= achievement.condition_threshold

        case 'perfect_round':
            # Round parfait = réponse correcte en < 5s
            perfect_count = GameAnswer.objects.filter(
                player__user=user,
                is_correct=True,
                response_time__lte=5.0
            ).count()
            return perfect_count >= achievement.condition_threshold

        case 'streak':
            # Vérifier les réponses de cette partie
            max_streak = get_max_streak_in_game(user, game)
            return max_streak >= achievement.condition_threshold

        case 'mode_games':
            count = Game.objects.filter(
                players__user=user,
                game_mode=achievement.condition_game_mode,
                status='finished'
            ).count()
            return count >= achievement.condition_threshold

        case 'social':
            return check_social_condition(user, achievement)

        case _:
            return False
```

### Étape 4 — Notification WebSocket

```python
# backend/apps/achievements/tasks.py

@shared_task
def notify_achievement_unlocked(user_id: int, achievement_id: int):
    """Envoie une notification WebSocket au client."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    achievement = Achievement.objects.get(id=achievement_id)

    # Envoyer au channel personnel de l'utilisateur
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}_notifications",  # Channel du NotificationConsumer
        {
            "type": "achievement_unlocked",
            "data": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon,
                "points": achievement.points,
            }
        }
    )
```

### Étape 5 — Réception côté frontend

```typescript
// services/notificationWebSocket.ts

onmessage: (event) => {
  const message = JSON.parse(event.data)

  if (message.type === 'achievement_unlocked') {
    // Ajouter le toast dans le store
    useNotificationStore.getState().addAchievementToast({
      id: crypto.randomUUID(),
      achievement: message.data,
      points_earned: message.data.points,
    })
  }
}
```

```typescript
// Composant AchievementToast.tsx (dans le layout global)

function AchievementToastContainer() {
  const { achievementToasts, dismissAchievementToast } = useNotificationStore()

  return (
    <div className="fixed bottom-4 right-4 space-y-2">
      {achievementToasts.map(toast => (
        <motion.div
          key={toast.id}
          initial={{ x: 300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 300, opacity: 0 }}
          className="bg-yellow-400 rounded-lg p-4 shadow-lg"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">{toast.achievement.icon}</span>
            <div>
              <p className="font-bold">Achievement débloqué !</p>
              <p>{toast.achievement.name}</p>
              <p className="text-sm">+{toast.points_earned} coins</p>
            </div>
            <button onClick={() => dismissAchievementToast(toast.id)}>
              ×
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
```

---

## Diagramme de flux complet

```
Fin de partie (game_finished)
        │
        ▼
GameService.finish_game(game)
        │
        ├── game.status = 'finished'
        ├── game.save()
        │
        └── Pour chaque joueur :
                │
                ▼
        check_achievements_async.delay(user_id, game_id)
                │   [Celery worker]
                │
                ▼
        Pour chaque Achievement non débloqué :
                │
                ├── check_achievement_condition(user, game, achievement)
                │          │
                │     Condition remplie ?
                │          │
                │    Oui ──┘
                │          │
                ▼          ▼
         Passer      UserAchievement.objects.create(...)
                          │
                          ├── coins_balance += achievement.points
                          │
                          └── notify_achievement_unlocked.delay(user_id, ach_id)
                                        │  [Celery worker]
                                        │
                                        ▼
                               channel_layer.group_send(
                                 "user_{id}_notifications",
                                 { type: "achievement_unlocked", ... }
                               )
                                        │  [WebSocket]
                                        │
                                        ▼
                               Frontend NotificationConsumer
                                        │
                                        ▼
                               notificationStore.addAchievementToast()
                                        │
                                        ▼
                               <AchievementToast /> animé
```

---

## Importance de l'asynchronisme (Celery)

La vérification des achievements est délibérément **asynchrone** pour plusieurs raisons :

```
SYNCHRONE (mauvaise approche)           ASYNCHRONE avec Celery (bonne approche)
──────────────────────────────          ─────────────────────────────────────────
GameConsumer.finish_game()              GameConsumer.finish_game()
  │                                       │
  ├── check achievements (sync)           ├── game.status = 'finished'
  │   (bloque le WS 500-2000ms)           ├── group_send(game_finished)  ← rapide
  │                                       └── delay(check_achievements)  ← async
  └── group_send(game_finished)
      (retardé de 500-2000ms)           Worker Celery (autre process) :
                                          check_achievements_async()
                                          → peut prendre 1-5 secondes
                                          → n'impacte pas l'UX
```

Les joueurs reçoivent immédiatement le message `game_finished` et sont redirigés vers la page résultats. Quelques secondes plus tard, les toasts d'achievements arrivent via le WebSocket de notifications persistant.

---

## Page achievements — Interface

```
┌────────────────────────────────────────────────────────────────────┐
│  MES ACHIEVEMENTS                                                  │
│                                                                    │
│  Débloqués : 12 / 43          Coins gagnés : 3 250                │
│                                                                    │
│  ── PARTIES JOUÉES ────────────────────────────────────────────   │
│                                                                    │
│  [🎵] Première partie   ✓ DÉBLOQUÉ  +50 coins                     │
│       "Jouer sa première partie"                                   │
│                                                                    │
│  [🎮] Habitué           ✓ DÉBLOQUÉ  +100 coins                    │
│       "Jouer 5 parties"                                            │
│                                                                    │
│  [⭐] Joueur régulier    ░░░░████ 18/25      +250 coins            │
│       "Jouer 25 parties"                                           │
│                                                                    │
│  [👑] Vétéran            ░░░░░░░░ 18/100     +500 coins            │
│       "Jouer 100 parties"                                          │
│                                                                    │
│  ── VICTOIRES ─────────────────────────────────────────────────   │
│  [🏆] Première victoire  ✓ DÉBLOQUÉ  +100 coins                   │
│  [🥇] Gagnant            ░░████░░░░ 3/5       +200 coins           │
│                                                                    │
│  ── ACHIEVEMENTS SECRETS ──────────────────────────────────────   │
│  [?]  ???               ─ Non débloqué                            │
└────────────────────────────────────────────────────────────────────┘
```

### Barre de progression

Les achievements avec un seuil affichent une barre de progression pour motiver les joueurs à continuer :

```typescript
// Dans ProfilePage ou AchievementsPage
const AchievementItem = ({ achievement, userProgress }) => {
  const progress = userProgress / achievement.condition_threshold
  const isUnlocked = progress >= 1.0

  return (
    <div className={`achievement ${isUnlocked ? 'unlocked' : 'locked'}`}>
      <span className="icon">{achievement.icon}</span>
      <div>
        <h3>{achievement.name}</h3>
        <p>{achievement.description}</p>
        {!isUnlocked && (
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(progress * 100, 100)}%` }}
            />
            <span>{userProgress} / {achievement.condition_threshold}</span>
          </div>
        )}
        {isUnlocked && <span className="coins">+{achievement.points} coins</span>}
      </div>
    </div>
  )
}
```
