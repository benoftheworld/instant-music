# Système de Bonus — InstantMusic

## Vue d'ensemble

Le système de bonus ajoute une couche stratégique au quiz musical. Les joueurs gagnent des **pièces (coins)** via les achievements, puis les dépensent dans la **boutique** pour acheter des bonus utilisables pendant les parties.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CYCLE DE VIE DES BONUS                           │
│                                                                     │
│  Jouer & gagner          Acheter                  Utiliser          │
│  achievements            en boutique              en partie         │
│                                                                     │
│  ┌──────────┐  coins  ┌──────────┐  inventaire  ┌──────────────┐  │
│  │Achievement│ ──────► │ Boutique │ ───────────► │ Partie       │  │
│  │           │         │  /shop/  │              │ (WebSocket)  │  │
│  └──────────┘          └──────────┘              └──────────────┘  │
│                                                                     │
│  Achievements → coins_balance += points                            │
│  Achat        → coins_balance -= prix                              │
│  Activation   → UserInventory.quantity -= 1                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Les 8 types de bonus

### Tableau récapitulatif

| Bonus         | Code            | Prix      | Effet                            | Timing            |
| ------------- | --------------- | --------- | -------------------------------- | ----------------- |
| Double Points | `double_points` | 200 coins | ×2 sur les points gagnés         | Avant de répondre |
| Score Max     | `max_points`    | 350 coins | Garantit 1000 points             | Avant de répondre |
| Temps Bonus   | `time_bonus`    | 150 coins | +10s au timer                    | Pendant le round  |
| 50/50         | `fifty_fifty`   | 100 coins | Élimine 2 mauvaises réponses     | Avant de répondre |
| Vol de Points | `steal`         | 400 coins | Vole des points au leader        | Après la réponse  |
| Bouclier      | `shield`        | 250 coins | Bloque un steal adverse          | Avant le round    |
| Brouillard    | `fog`           | 300 coins | Cache les scores aux autres      | Pendant le round  |
| Joker         | `joker`         | 500 coins | Réponse automatiquement correcte | Avant de répondre |

---

### Bonus 1 — Double Points (`double_points`)

**Description** : Multiplie par 2 les points gagnés pour ce round, quelle que soit la vitesse de réponse.

**Exemple** :
```
Sans bonus : réponse en 10s → 800 pts
Avec bonus : réponse en 10s → 1600 pts (×2)
```

**Application dans le code** :
```python
# backend/apps/games/services.py
def apply_score_bonuses(base_points: int, active_bonuses: list[str]) -> int:
    points = base_points

    if 'double_points' in active_bonuses:
        points *= 2

    return points
```

**Interface frontend** :
```
┌─────────────────────────────────────────────┐
│  BonusActivator.tsx                         │
│                                             │
│  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │  ×2    │  │  MAX   │  │  +10s  │  ...   │
│  │        │  │        │  │        │        │
│  │  x1    │  │  x2    │  │  x1    │        │
│  └────────┘  └────────┘  └────────┘        │
│  (double pts)(max pts) (temps bonus)        │
└─────────────────────────────────────────────┘
```

---

### Bonus 2 — Score Max (`max_points`)

**Description** : Garantit d'obtenir le score maximum (BASE_POINTS = 1000) quel que soit le temps de réponse. Idéal si vous connaissez la réponse mais prenez du temps à cliquer.

**Exemple** :
```
Sans bonus : réponse en 25s → 500 pts
Avec bonus : réponse en 25s → 1000 pts (max garanti)
```

**Application** :
```python
if 'max_points' in active_bonuses:
    points = BASE_POINTS  # Ignore le time_based_points
```

---

### Bonus 3 — Temps Bonus (`time_bonus`)

**Description** : Ajoute 10 secondes supplémentaires au timer du round. Le timer affiché augmente instantanément.

**Exemple** :
```
Timer à 5s restantes → activation → Timer passe à 15s
```

**Implémentation WebSocket** :
```python
# GameConsumer.activate_bonus()
async def activate_bonus_time(self, player: GamePlayer, game_round: GameRound):
    game_round.extended_duration += 10  # Ajoute 10 secondes
    await game_round.asave()

    # Broadcast à tous pour mettre à jour le timer affiché
    await self.channel_layer.group_send(
        f"game_{self.room_code}",
        {
            "type": "bonus_activated",
            "data": {
                "bonus_type": "time_bonus",
                "player_id": player.user.id,
                "new_timer_duration": game_round.extended_duration,
                "time_added": 10
            }
        }
    )
```

---

### Bonus 4 — 50/50 (`fifty_fifty`)

**Description** : Élimine 2 des 3 mauvaises réponses en MCQ, ne laissant que 2 choix (la bonne réponse + 1 distracteur).

**Exemple** :
```
Avant 50/50 :              Après 50/50 :
┌──────────────┐           ┌──────────────┐
│ Shape of You │           │ Shape of You │  ← bonne réponse
├──────────────┤           ├──────────────┤
│ Blinding Lts │  ──────►  │              │  (masqué)
├──────────────┤           ├──────────────┤
│ Bad Guy      │           │ Bad Guy      │  ← 1 distracteur
├──────────────┤           ├──────────────┤
│ Levitating   │           │              │  (masqué)
└──────────────┘           └──────────────┘
```

**Application** :
```python
def apply_fifty_fifty(choices: list[str], correct_answer: str) -> list[str]:
    """Garde la bonne réponse + 1 distracteur aléatoire."""
    wrong_choices = [c for c in choices if c != correct_answer]
    kept_wrong = random.choice(wrong_choices)
    result = [correct_answer, kept_wrong]
    random.shuffle(result)
    return result
```

**Frontend** (dans le reducer) :
```typescript
case 'BONUS_ACTIVATED':
  if (action.payload.bonus_type === 'fifty_fifty') {
    return {
      ...state,
      currentQuestion: {
        ...state.currentQuestion,
        choices: removeTwoWrongAnswers(
          state.currentQuestion.choices,
          state.currentQuestion.correct_answer
        )
      }
    }
  }
```

---

### Bonus 5 — Vol de Points (`steal`)

**Description** : Vole un pourcentage des points du joueur en première position au classement. Bonus offensif idéal pour rattraper un retard.

**Règles** :
- Vol = 10% des points du leader (arrondi)
- Ne peut pas voler plus de 500 points en une fois
- Si le bouclier (`shield`) du leader est actif, le vol est bloqué

**Exemple** :
```
Bob est 1er avec 5000 pts
Alice active steal
  → Bob perd 500 pts (10%)
  → Alice gagne 500 pts
```

**Application** :
```python
async def apply_steal_bonus(
    thief: GamePlayer,
    game: Game
) -> dict:
    # Trouver le joueur en tête
    leader = await game.players.order_by('-score').afirst()

    if leader.user.id == thief.user.id:
        return {"error": "Vous ne pouvez pas vous voler vous-même"}

    # Vérifier si le leader a un bouclier actif
    if await BonusService.has_active_shield(leader, game):
        return {
            "blocked": True,
            "message": f"{leader.user.username} est protégé par un bouclier !"
        }

    # Calculer le montant volé
    stolen = min(round(leader.score * 0.10), 500)

    # Appliquer
    leader.score -= stolen
    thief.score += stolen
    await leader.asave()
    await thief.asave()

    return {
        "stolen": stolen,
        "from_player": leader.user.username,
        "to_player": thief.user.username
    }
```

---

### Bonus 6 — Bouclier (`shield`)

**Description** : Protège contre un vol de points. Se déclenche automatiquement si quelqu'un tente un `steal`. Une fois déclenché, le bouclier est consommé.

**Fonctionnement** :
```
Alice active shield  →  GameBonus{type: 'shield', is_active: True} créé

Bob active steal sur Alice
  →  BonusService détecte shield actif sur Alice
  →  Vol bloqué
  →  shield marqué is_active: False (consommé)
  →  Message broadcast: "Le vol a été bloqué !"
```

**Modèle de données** :
```python
class GameBonus(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE)
    bonus_type = models.CharField(max_length=30)
    round_number = models.IntegerField()
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
```

---

### Bonus 7 — Brouillard (`fog`)

**Description** : Cache le tableau des scores à tous les autres joueurs pendant ce round. Ainsi, personne ne peut voir votre score ni votre classement momentanément.

**Effet** :
```
Alice active fog
  →  Pour Bob et Charlie : LiveScoreboard affiche "???"
  →  Pour Alice : son score est toujours visible
  →  Dure jusqu'à la fin du round
```

**Broadcast** :
```python
await self.channel_layer.group_send(
    f"game_{self.room_code}",
    {
        "type": "bonus_activated",
        "data": {
            "bonus_type": "fog",
            "player_id": player.user.id,
            "fog_player_name": player.user.username
        }
    }
)
```

**Frontend** (LiveScoreboard) :
```typescript
// Si fog actif pour un joueur, masquer son score
const displayScore = (player: GamePlayer) => {
  if (foggedPlayerIds.includes(player.user.id)) {
    return '???'
  }
  return player.score.toLocaleString()
}
```

---

### Bonus 8 — Joker (`joker`)

**Description** : Le bonus le plus puissant (et le plus cher). La réponse est validée comme correcte peu importe ce qui est soumis. Idéal pour un round où vous n'avez aucune idée de la réponse.

**Comportement** :
- Le joueur peut cliquer n'importe quelle réponse (ou rien)
- Le serveur force `is_correct = True` et calcule le score comme si la réponse était juste
- Le joueur reçoit les points calculés normalement (selon la vitesse)

**Application** :
```python
async def submit_answer(self, player, game_round, answer, response_time):
    # Vérifier si le joker est actif
    has_joker = await BonusService.has_active_joker(player, game_round)

    if has_joker:
        is_correct = True  # Force la correction
        accuracy_factor = 1.0
    else:
        is_correct = (normalize_text(answer) == normalize_text(game_round.correct_answer))
        accuracy_factor = calculate_text_accuracy(answer, game_round.correct_answer)

    points = calculate_score(is_correct, response_time, accuracy_factor)
    points = apply_score_bonuses(points, active_bonuses)

    # Créer la réponse en base
    await GameAnswer.objects.acreate(
        game_round=game_round,
        player=player,
        answer=answer,
        is_correct=is_correct,
        points_earned=points,
        response_time=response_time,
        bonus_used='joker' if has_joker else None
    )
```

---

## Flux d'achat en boutique

### Endpoint REST

```
POST /api/shop/items/{item_id}/buy/

Headers: Authorization: Bearer {jwt}

Response 200:
{
  "success": true,
  "item": {
    "bonus_type": "double_points",
    "name": "Double Points",
    "quantity": 3  // Nouveau total en inventaire
  },
  "coins_remaining": 800  // Coins restants après achat
}

Response 402 (insufficient funds):
{
  "error": "Solde insuffisant",
  "required": 200,
  "current_balance": 150
}
```

### Service backend

```python
# backend/apps/shop/services.py

class ShopService:
    @staticmethod
    def buy_item(user: User, item_id: int) -> dict:
        item = get_object_or_404(ShopItem, id=item_id, is_available=True)

        # Vérifier le solde
        if user.coins_balance < item.price:
            raise InsufficientFundsError(
                required=item.price,
                current=user.coins_balance
            )

        with transaction.atomic():
            # Débiter les coins
            user.coins_balance -= item.price
            user.save(update_fields=['coins_balance'])

            # Ajouter à l'inventaire
            inventory_item, created = UserInventory.objects.get_or_create(
                user=user,
                bonus_type=item.bonus_type,
                defaults={'quantity': 0}
            )
            inventory_item.quantity += 1
            inventory_item.save(update_fields=['quantity'])

            return {
                'success': True,
                'item': item,
                'new_quantity': inventory_item.quantity,
                'coins_remaining': user.coins_balance
            }
```

---

## Flux d'activation en partie

### Diagramme de séquence

```
Joueur (frontend)          WebSocket             GameConsumer           BonusService
       │                       │                       │                      │
       │── activate_bonus ────►│                       │                      │
       │   { bonus_type:       │──── dispatch ────────►│                      │
       │     "double_points" } │                       │── activate_bonus ───►│
       │                       │                       │                      │── Vérif. inventaire
       │                       │                       │                      │── Décrémente qty
       │                       │                       │◄─ GameBonus créé ────│
       │                       │◄─── group_send ───────│                      │
       │◄── bonus_activated ───│                       │                      │
       │    (broadcast tous)   │                       │                      │
```

### Message WebSocket

```javascript
// Client → Serveur
{
  "type": "activate_bonus",
  "bonus_type": "double_points"
}

// Serveur → Tous (broadcast)
{
  "type": "bonus_activated",
  "data": {
    "player_id": 42,
    "player_name": "Alice",
    "bonus_type": "double_points",
    "round_number": 5
  }
}
```

### Consumer Django Channels

```python
# backend/apps/games/consumers.py

async def receive_json(self, content):
    message_type = content.get('type')

    match message_type:
        case 'activate_bonus':
            await self.activate_bonus(content)
        # ... autres types

async def activate_bonus(self, data):
    bonus_type = data.get('bonus_type')

    # Vérifier que l'inventaire contient ce bonus
    inventory = await UserInventory.objects.filter(
        user=self.user,
        bonus_type=bonus_type,
        quantity__gt=0
    ).afirst()

    if not inventory:
        await self.send_json({
            "type": "error",
            "message": f"Bonus '{bonus_type}' non disponible dans l'inventaire"
        })
        return

    # Décrémenter l'inventaire
    inventory.quantity -= 1
    await inventory.asave(update_fields=['quantity'])

    # Créer l'enregistrement GameBonus
    game_round = await self.get_current_round()
    await GameBonus.objects.acreate(
        game=self.game,
        player=self.game_player,
        bonus_type=bonus_type,
        round_number=game_round.round_number,
        is_active=True
    )

    # Appliquer les effets immédiats (time_bonus, fifty_fifty, fog)
    effect_data = await BonusService.apply_immediate_effect(
        bonus_type, self.game_player, game_round, self.game
    )

    # Broadcast à tous les joueurs
    await self.channel_layer.group_send(
        f"game_{self.room_code}",
        {
            "type": "bonus_activated",
            "data": {
                "player_id": self.user.id,
                "player_name": self.user.username,
                "bonus_type": bonus_type,
                "round_number": game_round.round_number,
                **effect_data  # Données spécifiques au bonus (ex: new_timer pour time_bonus)
            }
        }
    )
```

---

## Application lors du scoring

La fonction `apply_score_bonuses` est appelée dans `GameService.submit_answer()` après le calcul du score de base.

```
GameService.submit_answer()
        │
        ├── calculate_score(is_correct, response_time, accuracy_factor)
        │          → base_points = 800
        │
        ├── BonusService.get_active_bonuses(player, round)
        │          → ['double_points', 'max_points']
        │
        ├── BonusService.apply_score_bonuses(base_points, active_bonuses)
        │     ├── max_points actif → points = 1000
        │     └── double_points actif → points = 2000
        │
        └── GameAnswer.points_earned = 2000
```

### Ordre d'application des bonus de score

L'ordre est important quand plusieurs bonus de score sont actifs simultanément :

```python
def apply_score_bonuses(base_points: int, active_bonuses: list[str]) -> int:
    points = base_points

    # 1. max_points d'abord (remplace le calcul temps)
    if 'max_points' in active_bonuses:
        points = BASE_POINTS

    # 2. Ensuite double_points (s'applique sur le résultat de max)
    if 'double_points' in active_bonuses:
        points *= 2

    return points

# Exemple : max_points + double_points
# → 1000 (max) → 2000 (double) = 2000 pts total
```

---

## Modèles de données

```python
# Modèle boutique
class ShopItem(models.Model):
    bonus_type = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()  # En coins
    icon = models.CharField(max_length=50)  # Emoji ou chemin icône
    is_available = models.BooleanField(default=True)

# Inventaire utilisateur
class UserInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bonus_type = models.CharField(max_length=30)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'bonus_type']

# Bonus utilisé en partie
class GameBonus(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE)
    bonus_type = models.CharField(max_length=30)
    round_number = models.IntegerField()
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
```

---

## Interface frontend — Boutique (`ShopPage`)

```
┌────────────────────────────────────────────────────────────┐
│  BOUTIQUE                          Votre solde : 850 coins │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Double Points              ×2   200 coins         │   │
│  │  Multiplie vos points par 2      [Acheter]         │   │
│  │  En stock : 1                                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Score Max                  MAX   350 coins        │   │
│  │  Garantit 1000 points             [Acheter]        │   │
│  │  En stock : 0                                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Joker                      JKR   500 coins        │   │
│  │  Réponse automatiquement correcte  [Acheter]       │   │
│  │  En stock : 2                                      │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```
