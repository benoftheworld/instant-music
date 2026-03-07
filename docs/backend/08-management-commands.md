# Commandes de gestion Django (Management Commands)

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Utilisation en développement](#utilisation-en-développement)
- [Commandes par application](#commandes-par-application)
  - [apps.achievements](#appsachievements)
    - [seed\_achievements](#seed_achievements)
    - [award\_retroactive\_achievements](#award_retroactive_achievements)
    - [sync\_coins\_balance](#sync_coins_balance)
  - [apps.shop](#appsshop)
    - [seed\_shop](#seed_shop)
  - [apps.users](#appsusers)
    - [recalculate\_user\_stats](#recalculate_user_stats)
    - [recalculate\_team\_stats](#recalculate_team_stats)
- [Ordre d'exécution au premier déploiement](#ordre-dexécution-au-premier-déploiement)
- [Intégration CI/CD](#intégration-cicd)

---

## Vue d'ensemble

Les commandes de gestion Django (`manage.py`) sont des scripts d'administration qui s'exécutent en dehors du contexte HTTP. Elles sont utilisées pour :
- Initialiser les données de référence (seeding)
- Réparer des incohérences de données (recalcul)
- Effectuer des opérations de maintenance planifiées

Toutes les commandes sont localisées dans `backend/apps/<app>/management/commands/<commande>.py`.

**Structure d'une commande Django :**

```
backend/
└── apps/
    └── achievements/
        └── management/
            ├── __init__.py
            └── commands/
                ├── __init__.py
                ├── seed_achievements.py
                ├── award_retroactive_achievements.py
                └── sync_coins_balance.py
```

---

## Utilisation en développement

```bash
# Via le Makefile (recommandé)
make dev-shell
# Puis dans le shell Docker :
python manage.py <commande> [options]

# Ou directement via Docker Compose :
docker compose exec backend python manage.py <commande>

# En production :
docker compose -f docker-compose.prod.yml exec backend python manage.py <commande>
```

---

## Commandes par application

### `apps.achievements`

#### `seed_achievements`

**Fichier :** `backend/apps/achievements/management/commands/seed_achievements.py`

##### Usage

```bash
python manage.py seed_achievements [--reset] [--force]
```

##### Options

| Option    | Type | Description                                                       |
| --------- | ---- | ----------------------------------------------------------------- |
| `--reset` | flag | Supprime **tous** les achievements existants avant l'import       |
| `--force` | flag | Met à jour les achievements existants même s'ils n'ont pas changé |

##### Rôle

Initialise les 40+ achievements par défaut dans la base de données. Les achievements sont définis comme des données de référence dans le code source (non modifiables par les utilisateurs).

##### Comportement détaillé

```
python manage.py seed_achievements
        │
        ▼
Charge les définitions d'achievements depuis le code
(liste de dicts : name, description, condition, coins_reward, icon)
        │
        ▼
┌───────────────────────────────┐
│  Option --reset ?             │──── Oui → Achievement.objects.all().delete()
└───────────────────────────────┘
           │ Non
           ▼
Pour chaque achievement défini :
  ┌───────────────────────────────────────┐
  │  Achievement.objects.get_or_create(   │
  │      name=achievement["name"],        │
  │      defaults={...}                   │
  │  )                                    │
  └───────────────────────────────────────┘
           │
  ┌────────┴───────────────┐
  │ Existait déjà (created=False) ?      │
  └────────┬───────────────┘
           │ Oui ET --force activé
           ▼
  Met à jour tous les champs
  (description, coins_reward, icon, etc.)
           │
           ▼
Affiche un résumé :
  "40 achievements créés, 0 mis à jour"
```

##### Exemples d'achievements seedés

```
┌─────────────────────────────┬──────────────────────────────────┬──────────┐
│ Nom                         │ Condition                        │ Pièces   │
├─────────────────────────────┼──────────────────────────────────┼──────────┤
│ Premier pas                 │ Jouer 1 partie                   │ 10       │
│ Mélomane                    │ Jouer 10 parties                 │ 50       │
│ Virtuose                    │ Jouer 100 parties                │ 500      │
│ Première victoire           │ Gagner 1 partie                  │ 25       │
│ Champion                    │ Gagner 10 parties                │ 200      │
│ Réponse parfaite            │ Répondre en < 1s                 │ 30       │
│ Série de feu                │ 5 bonnes réponses d'affilée      │ 75       │
│ Maître des paroles          │ Mode paroles, score > 8000       │ 100      │
│ Nostalgique                 │ Mode génération, 5 années exactes│ 150      │
└─────────────────────────────┴──────────────────────────────────┴──────────┘
```

##### Quand l'utiliser

- **Premier déploiement** : obligatoire pour que les achievements soient disponibles
- **Ajout de nouveaux achievements** : `python manage.py seed_achievements --force`
- **Réinitialisation complète** : `python manage.py seed_achievements --reset --force`

> **Attention avec `--reset` :** Supprime également tous les `UserAchievement` via la contrainte `CASCADE`. À n'utiliser qu'en développement ou après une migration majeure.

---

#### `award_retroactive_achievements`

**Fichier :** `backend/apps/achievements/management/commands/award_retroactive_achievements.py`

##### Usage

```bash
python manage.py award_retroactive_achievements
```

##### Rôle

Attribue rétroactivement les achievements aux utilisateurs existants en fonction de leurs statistiques actuelles. Cette commande est nécessaire quand de nouveaux achievements sont ajoutés alors que des utilisateurs ont déjà joué.

##### Comportement détaillé

```
award_retroactive_achievements
        │
        ▼
Charge tous les AchievementDefinition
        │
        ▼
Pour chaque User actif :
        │
        ▼
  Charge UserStats
        │
        ▼
  Pour chaque AchievementDefinition :
    ┌────────────────────────────────────┐
    │  L'utilisateur a déjà cet         │
    │  achievement (UserAchievement) ?  │──── Oui → Passe au suivant
    └────────────────────────────────────┘
               │ Non
               ▼
    Évalue la condition de l'achievement
    (stats.total_games >= achievement.threshold, etc.)
               │
      ┌────────┴────────┐
      │  Condition OK ? │──── Non → Passe au suivant
      └────────┬────────┘
               │ Oui
               ▼
    UserAchievement.objects.create(
        user=user,
        achievement=achievement,
        awarded_retroactively=True
    )
    user.coins_balance += achievement.coins_reward
    user.save()
        │
        ▼
Affiche un résumé :
  "127 achievements attribués à 45 utilisateurs"
```

##### Quand l'utiliser

- Après l'ajout de nouveaux achievements (`seed_achievements --force`) pour récompenser les joueurs existants
- Après une migration de données importants

> Cette commande peut être longue si la base d'utilisateurs est grande. Elle est conçue pour être exécutée une seule fois après chaque ajout de nouveaux achievements.

---

#### `sync_coins_balance`

**Fichier :** `backend/apps/achievements/management/commands/sync_coins_balance.py`

##### Usage

```bash
python manage.py sync_coins_balance
```

##### Rôle

Recalcule le solde de pièces (`coins_balance`) de chaque utilisateur en additionnant les `coins_reward` de tous leurs `UserAchievement` actifs, puis en soustrayant les achats en boutique.

##### Pourquoi cette commande est nécessaire

Le `coins_balance` est un champ dénormalisé sur le modèle `User` pour des raisons de performance (éviter un `SUM()` à chaque affichage). Il peut devenir incohérent si :
- Une migration de données a modifié les `coins_reward` des achievements
- Un bug a causé des doubles attributions
- Une tâche Celery a échoué silencieusement

##### Comportement détaillé

```
sync_coins_balance
        │
        ▼
Pour chaque User :
        │
        ▼
  coins_earned = UserAchievement.objects
      .filter(user=user)
      .aggregate(total=Sum("achievement__coins_reward"))
      ["total"] or 0
        │
        ▼
  coins_spent = ShopPurchase.objects
      .filter(user=user)
      .aggregate(total=Sum("item__cost"))
      ["total"] or 0
        │
        ▼
  new_balance = coins_earned - coins_spent
        │
  ┌─────┴──────────────────────────────┐
  │  new_balance != user.coins_balance  │──── Non → Pas de modification
  └─────┬──────────────────────────────┘
        │ Oui
        ▼
  user.coins_balance = new_balance
  user.save(update_fields=["coins_balance"])
  Log : "User 42: 850 → 920 coins (corrigé)"
        │
        ▼
Affiche un résumé :
  "12 soldes corrigés sur 450 utilisateurs"
```

---

### `apps.shop`

#### `seed_shop`

**Fichier :** `backend/apps/shop/management/commands/seed_shop.py`

##### Usage

```bash
python manage.py seed_shop
```

##### Rôle

Initialise les 8 articles de la boutique dans la base de données (un article par type de bonus).

##### Articles créés

```
┌─────────────────┬────────────────────────────────────────────┬──────────┐
│ Type de bonus   │ Description                                │ Prix     │
├─────────────────┼────────────────────────────────────────────┼──────────┤
│ double_points   │ Double les points du prochain round        │ 200 pcs  │
│ max_points      │ Garantit le score max pour 1 round         │ 350 pcs  │
│ steal           │ Vole 200 pts au joueur en tête             │ 300 pcs  │
│ shield          │ Bloque le prochain vol de points           │ 150 pcs  │
│ fog             │ Masque les scores 1 round                  │ 100 pcs  │
│ time_freeze     │ Gèle le chrono pour 1 round                │ 250 pcs  │
│ hint            │ Révèle un indice (1ère lettre)             │ 75 pcs   │
│ skip            │ Passe 1 round sans pénalité                │ 125 pcs  │
└─────────────────┴────────────────────────────────────────────┴──────────┘
```

##### Comportement

```
python manage.py seed_shop
        │
        ▼
Pour chaque article défini :
  ShopItem.objects.get_or_create(
      bonus_type=item["bonus_type"],
      defaults={
          "name": item["name"],
          "description": item["description"],
          "cost": item["cost"],
          "icon": item["icon"],
          "is_available": True,
      }
  )
        │
        ▼
"8 articles créés, 0 déjà existants"
```

##### Quand l'utiliser

- **Premier déploiement** : obligatoire avant que les joueurs puissent acheter des bonus

---

### `apps.users`

#### `recalculate_user_stats`

**Fichier :** `backend/apps/users/management/commands/recalculate_user_stats.py`

##### Usage

```bash
python manage.py recalculate_user_stats
```

##### Rôle

Recalcule les statistiques dénormalisées pour **tous les utilisateurs** à partir des données brutes en base :
- `total_games_played` : nombre de parties jouées (statut `finished`)
- `total_wins` : nombre de victoires (rang final = 1)
- `total_points` : somme de tous les points gagnés

##### Pourquoi ces stats sont dénormalisées

Ces champs sont lus très fréquemment (leaderboard, profil utilisateur) mais changent rarement (seulement après une partie). La dénormalisation évite des `COUNT()` et `SUM()` coûteux à chaque lecture.

##### Comportement détaillé

```
recalculate_user_stats
        │
        ▼
Pour chaque User :
        │
        ▼
  total_games = GamePlayer.objects
      .filter(
          user=user,
          game__status="finished"
      ).count()
        │
        ▼
  total_wins = GamePlayer.objects
      .filter(
          user=user,
          game__status="finished",
          final_rank=1
      ).count()
        │
        ▼
  total_points = GameAnswer.objects
      .filter(
          player__user=user,
          player__game__status="finished"
      ).aggregate(total=Sum("points_earned"))["total"] or 0
        │
        ▼
  UserStats.objects.update_or_create(
      user=user,
      defaults={
          "total_games_played": total_games,
          "total_wins": total_wins,
          "total_points": total_points,
      }
  )
        │
        ▼
"450 utilisateurs recalculés"
```

##### Quand l'utiliser

- Après une migration de données
- Si des incohérences sont détectées dans le leaderboard
- Après un import de données depuis un autre système
- En cas de correction de bug sur le système de scoring

---

#### `recalculate_team_stats`

**Fichier :** `backend/apps/users/management/commands/recalculate_team_stats.py`

##### Usage

```bash
python manage.py recalculate_team_stats
```

##### Rôle

Recalcule les statistiques agrégées des équipes (teams) en se basant sur les parties de leurs membres :
- `total_games` : parties jouées par au moins un membre de l'équipe
- `total_wins` : victoires collectives
- `total_points` : somme des points de tous les membres

##### Comportement

```
recalculate_team_stats
        │
        ▼
Pour chaque Team :
        │
        ▼
  members = TeamMember.objects.filter(team=team)
  member_ids = members.values_list("user_id", flat=True)
        │
        ▼
  Agrège les stats depuis GamePlayer
  pour tous les membres de l'équipe
        │
        ▼
  TeamStats.objects.update_or_create(
      team=team,
      defaults={...stats agrégées...}
  )
        │
        ▼
"85 équipes recalculées"
```

---

## Ordre d'exécution au premier déploiement

Lors du **premier déploiement** (ou d'une réinstallation complète), les commandes doivent être exécutées dans cet ordre précis :

```
1. python manage.py migrate
   │  Applique toutes les migrations Django
   │  (crée les tables en base de données)
   │
   ▼
2. python manage.py seed_achievements
   │  Initialise les achievements de référence
   │  (doit précéder seed_shop car des achievements
   │   peuvent référencer des types de bonus)
   │
   ▼
3. python manage.py seed_shop
   │  Initialise les articles de la boutique
   │
   ▼
4. python manage.py createsuperuser
      Crée le compte administrateur
      (ou via: make dev-createsuperuser)
```

En développement, le Makefile automatise ces étapes :

```bash
make deploy-dev   # Lance l'environnement complet
make dev-migrate  # Applique les migrations
# Puis manuellement :
make dev-shell
python manage.py seed_achievements
python manage.py seed_shop
```

---

## Intégration CI/CD

Dans le pipeline CI/CD (`.github/workflows/ci.yml`), certaines commandes sont exécutées automatiquement :

```yaml
# Extrait du workflow CI
- name: Appliquer les migrations
  run: python manage.py migrate --no-input

- name: Initialiser les données de référence
  run: |
    python manage.py seed_achievements
    python manage.py seed_shop
```

Les commandes de **recalcul** (`recalculate_*`, `sync_coins_balance`, `award_retroactive_achievements`) ne sont **pas** exécutées en CI car elles sont des outils de maintenance, pas d'initialisation.

### Commandes à exécuter après une mise en production

Si une mise en production contient de nouveaux achievements ou de nouveaux articles de boutique :

```bash
# 1. Appliquer les migrations
python manage.py migrate

# 2. Mettre à jour les achievements (si nouveaux ajoutés)
python manage.py seed_achievements --force

# 3. Attribuer rétroactivement aux utilisateurs existants
python manage.py award_retroactive_achievements

# 4. Mettre à jour la boutique (si nouveaux articles)
python manage.py seed_shop
```
