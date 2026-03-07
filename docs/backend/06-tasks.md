# Tâches Celery

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Configuration Celery](#configuration-celery)
- [Architecture du flux de traitement](#architecture-du-flux-de-traitement)
- [Tâches disponibles](#tâches-disponibles)
  - [achievements.check\_and\_award](#achievementscheck_and_award)
  - [rgpd.purge\_expired\_invitations](#rgpdpurge_expired_invitations)
  - [rgpd.anonymize\_old\_game\_data](#rgpdanonymize_old_game_data)
  - [debug\_task](#debug_task)
- [Tâches périodiques (Celery Beat)](#tâches-périodiques-celery-beat)
- [Monitoring et observabilité](#monitoring-et-observabilité)
- [Bonnes pratiques](#bonnes-pratiques)

---

## Vue d'ensemble

Celery est le système de traitement de tâches asynchrones d'InstantMusic. Il permet d'**exécuter des opérations longues ou non critiques en dehors du cycle requête/réponse HTTP**, pour ne pas bloquer l'utilisateur.

### Quand utiliser Celery ?

| Situation                                     | Synchrone                                           | Asynchrone Celery    |
| --------------------------------------------- | --------------------------------------------------- | -------------------- |
| Calcul du score d'une réponse                 | Oui (< 5 ms)                                        | Non                  |
| Attribution des achievements après une partie | Non (peut prendre plusieurs secondes, non critique) | **Oui**              |
| Suppression de données RGPD                   | Non (tâche de maintenance)                          | **Oui (périodique)** |
| Envoi d'emails de notification                | Non (latence réseau)                                | **Oui**              |
| Enregistrement d'une GameAnswer               | Oui (doit être immédiat)                            | Non                  |

---

## Configuration Celery

Fichier : `backend/config/celery.py`

```python
from celery import Celery
from django.conf import settings

app = Celery("instantmusic")

# Charge la configuration depuis Django settings (préfixe CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découverte automatique des tâches dans toutes les apps Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
```

**Variables d'environnement nécessaires :**

```bash
CELERY_BROKER_URL=redis://redis:6379/0       # Canal de communication Worker ↔ App
CELERY_RESULT_BACKEND=redis://redis:6379/0   # Stockage des résultats de tâches
```

**Paramètres clés dans `settings/base.py` :**

```python
CELERY_TASK_SERIALIZER = "json"       # Format de sérialisation des tâches
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Europe/Paris"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

Le scheduler `DatabaseScheduler` stocke les planifications dans la base de données PostgreSQL, ce qui permet de les modifier depuis l'admin Django sans redémarrer les workers.

---

## Architecture du flux de traitement

### Flux complet : Application → Celery Beat → Worker → Résultat

```
                         DÉCLENCHEMENTS
                               │
           ┌───────────────────┼────────────────────┐
           │                   │                    │
    Code applicatif      Celery Beat          Admin Django
  (finish_game, etc.)  (tâches planifiées)  (déclenchement manuel)
           │                   │                    │
           └───────────────────┴────────────────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │  Application Django     │
                  │  .delay() / .apply_    │
                  │  async_with_retry()    │
                  └────────────┬───────────┘
                               │  Sérialise la tâche en JSON
                               │  et la place dans la queue
                               ▼
                  ┌────────────────────────┐
                  │       Redis             │
                  │  ┌──────────────────┐  │
                  │  │  Queue "celery"   │  │  ← Broker (file de messages)
                  │  │  [task1, task2,  │  │
                  │  │   task3, ...]    │  │
                  │  └──────────────────┘  │
                  │  ┌──────────────────┐  │
                  │  │  Result Backend  │  │  ← Stockage des résultats
                  │  │  {task_id: res} │  │
                  │  └──────────────────┘  │
                  └────────────┬───────────┘
                               │  Le worker poll la queue
                               ▼
                  ┌────────────────────────┐
                  │    Celery Worker        │
                  │  ┌──────────────────┐  │
                  │  │  Prefork pool    │  │  ← Processus worker
                  │  │  (N concurrents) │  │
                  │  └──────────────────┘  │
                  │  1. Désérialise tâche  │
                  │  2. Importe la func   │
                  │  3. Exécute           │
                  │  4. Retry si erreur   │
                  │  5. Stocke résultat   │
                  └────────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
             ✓ Succès                ✗ Échec (après retries)
                    │                     │
             Résultat stocké        Exception dans
             dans Redis             le résultat Redis
             (TTL 24h)              + log d'erreur
```

### Flux spécifique : Celery Beat (tâches planifiées)

```
PostgreSQL (PeriodicTask)
        │
        │  Lecture planification
        ▼
Celery Beat Process
  ┌─────────────────────────────┐
  │  Vérifie toutes les N sec   │
  │  si une tâche est due       │
  │  Comparaison avec last_run  │
  └─────────────┬───────────────┘
                │ Tâche due
                ▼
         Envoie dans Redis
         (comme .delay())
                │
                ▼
         Worker la traite
         (même flux qu'au-dessus)
```

---

## Tâches disponibles

### `achievements.check_and_award`

**Fichier :** `backend/apps/achievements/tasks.py`

```python
@shared_task(
    name="achievements.check_and_award",
    max_retries=3,
    default_retry_delay=10,
)
def check_and_award(user_id, game_id=None, round_data=None):
    ...
```

#### Rôle

Vérifie et attribue tous les achievements débloquables pour un utilisateur après qu'il ait participé à une partie.

#### Déclenchement

Appelée depuis `GameService.finish_game()` de manière asynchrone :

```python
# apps/games/services.py
def finish_game(self, game):
    # ... logique de fin de partie ...

    # Déclenche l'attribution d'achievements pour chaque joueur
    # sans bloquer la réponse WebSocket
    for player in game.players.all():
        check_and_award.delay(
            user_id=player.user_id,
            game_id=game.id,
            round_data=round_summary,
        )
```

#### Flux interne

```
check_and_award(user_id=42, game_id=7)
        │
        ▼
Charge User + UserStats depuis DB
        │
        ▼
Charge tous les AchievementDefinition
        │
        ▼
Pour chaque achievement :
  ┌─────────────────────────────┐
  │  L'utilisateur remplit les  │
  │  conditions (stats, jeux,   │──── Non → Passe au suivant
  │  victoires, streaks...) ?   │
  └─────────────────────────────┘
           │ Oui
           ▼
  UserAchievement.objects.get_or_create(
    user=user, achievement=achievement
  )
           │
  ┌────────┴────────┐
  │ Déjà débloqué ? │──── Oui → Passe au suivant
  └────────┬────────┘
           │ Non
           ▼
  Crée UserAchievement
  Ajoute coins à l'utilisateur
  Envoie notification WebSocket
  (NotificationConsumer)
```

#### Retry strategy

```
Tentative 1 ──→ Erreur DB temporaire
                      │
                      ▼ attente 10s
Tentative 2 ──→ Erreur DB temporaire
                      │
                      ▼ attente 10s
Tentative 3 ──→ Succès ✓
```

Si les 3 tentatives échouent, l'exception est enregistrée dans les logs. Les achievements ne sont pas attribués (perte acceptable pour une fonctionnalité non critique).

---

### `rgpd.purge_expired_invitations`

**Fichier :** `backend/apps/games/tasks.py` (ou `apps/administration/tasks.py`)

```python
@shared_task(name="rgpd.purge_expired_invitations")
def purge_expired_invitations():
    ...
```

#### Rôle

Supprime les `GameInvitation` expirées depuis plus de 7 jours de la base de données.

#### Contexte RGPD

Conformément au [RGPD (Règlement Général sur la Protection des Données)](https://www.cnil.fr/fr/rgpd-de-quoi-parle-t-on), les données personnelles ne doivent pas être conservées au-delà de leur durée d'utilité. Une invitation de jeu expirée n'a plus d'utilité après 7 jours et peut contenir des données d'identification (adresse email de l'invité).

#### Déclenchement (Celery Beat)

Planification recommandée : **quotidienne à 3h00** (faible charge serveur).

```
Tous les jours à 03:00
        │
        ▼
SELECT * FROM game_invitations
WHERE expires_at < NOW() - INTERVAL '7 days'
        │
        ▼
DELETE en batch (évite les locks longs)
        │
        ▼
Log du nombre d'enregistrements supprimés
```

---

### `rgpd.anonymize_old_game_data`

**Fichier :** `backend/apps/games/tasks.py`

```python
@shared_task(
    name="rgpd.anonymize_old_game_data",
)
def anonymize_old_game_data(retention_days=365):
    ...
```

#### Rôle

Supprime les données de jeu anciennes pour respecter la politique de rétention des données :
- Supprime les `GameAnswer` de plus de `retention_days` jours (défaut : 365 jours)
- Supprime les parties (`Game`) en statut `"cancelled"` de plus de `retention_days` jours

#### Paramètre `retention_days`

Le paramètre peut être surchargé lors de l'appel depuis Beat :

```python
# Configuration dans l'admin Django (PeriodicTask args)
{"retention_days": 365}
```

#### Déclenchement (Celery Beat)

Planification recommandée : **hebdomadaire le dimanche à 02:00**.

```
GameAnswer.objects.filter(
    created_at__lt=now() - timedelta(days=retention_days)
).delete()

Game.objects.filter(
    status="cancelled",
    created_at__lt=now() - timedelta(days=retention_days)
).delete()
```

---

### `debug_task`

**Fichier :** `backend/config/celery.py`

```python
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
```

#### Rôle

Tâche de test pour vérifier que la connexion entre l'application Django et le worker Celery fonctionne correctement.

#### Utilisation

```bash
# Depuis un shell Django (make dev-shell)
from config.celery import debug_task
result = debug_task.delay()
print(result.status)  # "SUCCESS"
```

---

## Tâches périodiques (Celery Beat)

### Configuration via l'admin Django

Grâce au `DatabaseScheduler` de `django-celery-beat`, toutes les tâches périodiques sont configurables depuis l'interface d'administration Django sans redémarrage.

**Accès :** `http://localhost:8000/admin/` → section **Periodic Tasks**

#### Créer une tâche périodique

1. Créer d'abord une **Interval** ou **Crontab** schedule
2. Créer ensuite la **Periodic Task** en référençant ce schedule

**Exemple de crontab pour `purge_expired_invitations` :**

```
┌─────────────── Minute  : 0
│ ┌───────────── Heure   : 3
│ │ ┌─────────── Jour/mois: * (tous)
│ │ │ ┌───────── Mois     : * (tous)
│ │ │ │ ┌─────── Jour/sem  : * (tous)
│ │ │ │ │
0 3 * * *   → Exécution tous les jours à 03:00
```

#### Récapitulatif des tâches périodiques recommandées

| Tâche                            | Schedule                | Description                    |
| -------------------------------- | ----------------------- | ------------------------------ |
| `rgpd.purge_expired_invitations` | Quotidien à 03:00       | Nettoyage invitations expirées |
| `rgpd.anonymize_old_game_data`   | Hebdomadaire dim. 02:00 | Anonymisation données > 1 an   |

#### Paramètres d'une PeriodicTask

```
Nom                : "RGPD - Purge invitations expirées"
Task               : rgpd.purge_expired_invitations
Schedule           : Crontab (0 3 * * *)
Arguments (JSON)   : []
Keyword arguments  : {}
Enabled            : ✓
One-off            : ☐ (si coché, s'exécute une seule fois puis se désactive)
```

### Lancer manuellement une tâche périodique

```bash
# Depuis un shell Django
from apps.games.tasks import purge_expired_invitations
result = purge_expired_invitations.delay()

# Ou depuis la CLI Celery
celery -A config.celery call rgpd.purge_expired_invitations
```

### Démarrage des services en développement

```bash
# Le Makefile lance automatiquement Beat et Worker :
make deploy-dev

# Logs des workers :
make logs-dev
# Filtrer les logs Celery :
docker compose logs -f celery celery-beat
```

---

## Monitoring et observabilité

### Logs des tâches

Chaque exécution de tâche génère des logs structurés :

```json
{
  "level": "INFO",
  "task_name": "achievements.check_and_award",
  "task_id": "b2c3d4e5-...",
  "user_id": 42,
  "status": "started",
  "timestamp": "2026-03-07T14:32:11Z"
}
```

### Flower (dashboard Celery)

En développement, Flower est accessible pour monitorer les workers :

```bash
# Démarrer Flower manuellement
celery -A config.celery flower --port=5555
# Accès : http://localhost:5555
```

Le dashboard affiche :
- Workers actifs et leur statut
- Tâches en cours d'exécution
- Historique des tâches (succès, échecs, retries)
- Statistiques de performance (tâches/minute, latence moyenne)

### Métriques Prometheus

Les métriques Celery sont exposées via `celery-prometheus-exporter` :
- `celery_tasks_total{task, state}` — compteur par état (SUCCESS, FAILURE, RETRY)
- `celery_task_duration_seconds` — histogramme des durées d'exécution

---

## Bonnes pratiques

### Idempotence

Les tâches Celery peuvent être exécutées **plusieurs fois** en cas de retry ou de déduplication. Elles doivent être **idempotentes** :

```python
# Bon : get_or_create est idempotent
UserAchievement.objects.get_or_create(user=user, achievement=ach)

# Mauvais : create() échouera ou dupliquera si appelé deux fois
UserAchievement.objects.create(user=user, achievement=ach)
```

### Paramètres simples

Les paramètres des tâches doivent être sérialisables en JSON. Passer des **IDs** plutôt que des objets Django :

```python
# Bon
check_and_award.delay(user_id=user.id, game_id=game.id)

# Mauvais (ne peut pas être sérialisé en JSON)
check_and_award.delay(user=user, game=game)
```

### Transactions et tâches

Ne pas lancer une tâche Celery dans une transaction Django avant le commit — la tâche pourrait s'exécuter avant que les données soient visibles :

```python
from django.db import transaction

# Bon : on_commit garantit que la tâche s'exécute après le commit
with transaction.atomic():
    game.status = "finished"
    game.save()
    transaction.on_commit(
        lambda: check_and_award.delay(user_id=user.id)
    )
```
