# Architecture — Celery

> Ce document explique ce qu'est Celery, pourquoi on l'utilise, et comment il est configure dans InstantMusic.

---

## Sommaire

- [Qu'est-ce que Celery ?](#quest-ce-que-celery-)
- [Pourquoi les taches asynchrones ?](#pourquoi-les-taches-asynchrones-)
- [Celery Worker vs Celery Beat](#celery-worker-vs-celery-beat)
- [Schema du flux Celery](#schema-du-flux-celery)
- [Taches du projet](#taches-du-projet)
- [Configuration](#configuration)
- [Monitoring des taches](#monitoring-des-taches)
- [Troubleshooting](#troubleshooting)

---

## Qu'est-ce que Celery ?

**Celery** est un systeme de file de taches pour Python. Il permet d'executer des operations en **arriere-plan**, separement du serveur web.

### L'analogie du restaurant

Imaginez un restaurant :
- Le **serveur** (notre backend Django) prend les commandes et les transmet en cuisine. Il ne reste pas en cuisine a attendre que le plat soit pret : il va servir d'autres clients.
- La **cuisine** (Celery Worker) prepare les plats tranquillement, a son rythme.
- Le **ticket de commande** (Redis broker) est le bout de papier que le serveur depose en cuisine.
- Le **chef de rang** (Celery Beat) passe automatiquement certaines commandes a heures fixes (ex: "le plat du jour a 12h tous les jours").

Sans ce systeme, le serveur resterait bloque en cuisine pendant toute la preparation. Les autres clients attendraient indefiniment.

---

## Pourquoi les taches asynchrones ?

### Le probleme : le serveur web ne doit pas bloquer

Quand un utilisateur fait une requete HTTP a Django, Django doit repondre rapidement (idealement en moins de 100ms). Si Django doit faire quelque chose de long (calculer des statistiques, envoyer un email, verifier des succes...), cela bloque toute la requete.

```
SANS CELERY (bloquant)

Requete HTTP
    │
    ▼
Django traite la requete
    │
    │  Calcul des succes... (500ms)
    │  Envoi d'email... (1200ms)
    │  Mise a jour des statistiques... (800ms)
    │
    ▼  (2500ms plus tard)
Reponse HTTP
    │
    ▼
Utilisateur (a attendu 2,5 secondes !)
```

```
AVEC CELERY (non-bloquant)

Requete HTTP
    │
    ▼
Django traite la requete (10ms)
    │
    │  Enfile les taches dans Redis (1ms)
    │  check_and_award.delay(game_id)  ← retourne immediatement
    │  send_email.delay(user_id)       ← retourne immediatement
    │
    ▼  (11ms total !)
Reponse HTTP
    │
    ▼
Utilisateur (reponse immediate)

    ... (en arriere-plan, Celery Worker execute les taches) ...
```

### Autres avantages de Celery

- **Retry automatique** : si une tache echoue (ex: API Deezer indisponible), Celery peut la reessayer automatiquement apres un delai.
- **Priorites** : certaines taches peuvent etre marquees prioritaires.
- **Concurrence** : plusieurs workers peuvent executer des taches en parallele.
- **Planification** : Celery Beat permet de lancer des taches a des horaires precis.

---

## Celery Worker vs Celery Beat

Le projet utilise deux conteneurs Celery distincts, chacun avec un role different.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CELERY WORKER                                      │
│                                                                       │
│  Surveille la file Redis en permanence.                              │
│  Des qu'une tache arrive, il l'execute.                              │
│                                                                       │
│  Mode de fonctionnement : "reactif"                                  │
│  "Je travaille quand on me demande de travailler."                   │
│                                                                       │
│  Commande de demarrage :                                             │
│  celery -A config.celery worker --loglevel=info                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Planificateur)                        │
│                                                                       │
│  Consulte un planning et enfile des taches dans Redis                │
│  a des moments precis (toutes les heures, tous les jours...).        │
│                                                                       │
│  Mode de fonctionnement : "proactif / cron"                          │
│  "A 2h du matin chaque nuit, j'enfile la tache de nettoyage."       │
│                                                                       │
│  Commande de demarrage :                                             │
│  celery -A config.celery beat --scheduler=django_celery_beat.schedulers.DatabaseScheduler
│                                                                       │
│  Le planning est stocke dans PostgreSQL (DatabaseScheduler)          │
│  et est modifiable via l'interface Django Admin.                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Important :** Celery Beat ne fait que **planifier** les taches (les mettre dans la file Redis). C'est toujours le **Celery Worker** qui les execute.

---

## Schema du flux Celery

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           FLUX COMPLET D'UNE TACHE CELERY                         │
└──────────────────────────────────────────────────────────────────────────────────┘

  1. DECLENCHEMENT
  ─────────────────

  A) Depuis le backend Django (tache immediate) :

     # Dans GameConsumer.finish_game()
     from apps.achievements.tasks import check_and_award
     check_and_award.delay(game_id=42)
                     │
                     └── .delay() place la tache dans Redis et retourne immediatement
                         un objet AsyncResult (pour consulter le resultat plus tard)

  B) Depuis Celery Beat (tache planifiee) :

     # Celery Beat lit le planning depuis PostgreSQL
     # "Tous les jours a 2h : lancer rgpd.purge_expired_invitations"
     # Il appelle automatiquement purge_expired_invitations.delay()


  2. FILE D'ATTENTE (Redis - DB 0)
  ─────────────────────────────────

     ┌──────────────────────────────────────────────────────────┐
     │  REDIS LIST "celery"                                      │
     │                                                            │
     │  ← BLPOP (worker depile)        RPUSH (Django empile) ←  │
     │                                                            │
     │  [tache3, tache2, tache1 (premiere arrivee)]             │
     └──────────────────────────────────────────────────────────┘


  3. EXECUTION (Celery Worker)
  ─────────────────────────────

     Celery Worker
          │
          │  BLPOP sur la file (bloquant : attend si vide)
          │
          ▼
     Recoit la tache :
     {
       "task": "apps.achievements.tasks.check_and_award",
       "id": "d3b07384-d3fa-4c23-a765-abc123",
       "kwargs": {"game_id": 42},
       "retries": 0
     }
          │
          ▼
     Execute check_and_award(game_id=42)
          │
          ├── Lit PostgreSQL (Game, GamePlayer, GameAnswer)
          ├── Calcule les succes debloques
          ├── Ecrit dans PostgreSQL (Achievement)
          └── (optionnel) Envoie une notification via Redis channel layer


  4. RESULTAT
  ────────────

     Redis DB 0 :
     SET "celery-task-meta-d3b07384-..." →
     {
       "status": "SUCCESS",
       "result": {"awarded": ["premier_quiz", "score_parfait"]},
       "date_done": "2026-03-07T14:30:00Z"
     }

     En cas d'echec :
     {
       "status": "FAILURE",
       "result": "ConnectionError: ...",
       "traceback": "...",
       "date_done": "..."
     }
     → Celery retente automatiquement (max_retries=3, countdown=60)
```

---

## Taches du projet

### `achievements.check_and_award`

**Declenchement :** apres la fin d'une partie (tache immediate)
**Declencheur :** `GameConsumer.finish_game()`

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_and_award(self, game_id: int) -> dict:
    """
    Verifie quels succes chaque joueur a debloque a l'issue de la partie.
    Ecrit les nouveaux succes en base et notifie les joueurs via WebSocket.

    Args:
        game_id: L'identifiant de la partie qui vient de se terminer.

    Returns:
        Dict avec la liste des succes attribues par joueur.
    """
```

**Ce que fait cette tache :**
1. Recupere la partie et tous ses joueurs depuis PostgreSQL
2. Pour chaque joueur, calcule ses statistiques de la partie (score, bonnes reponses, temps...)
3. Verifie chaque critere de succes (ex: "Score parfait : 10/10 bonnes reponses")
4. Cree les enregistrements `Achievement` en base pour les nouveaux succes
5. Envoie une notification temps reel via le channel layer Redis

**Pourquoi en async ?** La verification peut necessiter plusieurs requetes SQL et des calculs : on ne veut pas bloquer la reponse WebSocket `finish_game` pour ca.

---

### `rgpd.purge_expired_invitations`

**Declenchement :** planifie (toutes les nuits)
**Declencheur :** Celery Beat

```python
@shared_task
def purge_expired_invitations() -> dict:
    """
    Supprime les invitations de jeu expirées (creées il y a plus de 7 jours).
    Respect du RGPD : on ne conserve pas les invitations indefiniment.

    Returns:
        Dict avec le nombre d'invitations supprimees.
    """
```

**Ce que fait cette tache :**
1. Recherche toutes les invitations creees il y a plus de 7 jours
2. Les supprime de la base de donnees
3. Retourne un compte pour les logs

**Pourquoi planifiee ?** Ce nettoyage n'a pas besoin de se faire en temps reel. Une fois par nuit suffit.

---

### `rgpd.anonymize_old_game_data`

**Declenchement :** planifie (une fois par semaine)
**Declencheur :** Celery Beat

```python
@shared_task
def anonymize_old_game_data() -> dict:
    """
    Anonymise ou supprime les donnees de parties de plus de 365 jours.
    Conformite RGPD : droit a l'oubli, minimisation des donnees.

    Returns:
        Dict avec le nombre de parties anonymisees/supprimees.
    """
```

**Ce que fait cette tache :**
1. Recherche les parties terminees il y a plus de 365 jours
2. Pour les parties concernees :
   - Supprime les reponses detaillees (`GameAnswer`)
   - Anonymise les donnees joueurs (remplace les references utilisateur par NULL)
   - Garde les scores aggreges (statistiques globales sans info personnelle)
3. Retourne un rapport pour les logs

**Pourquoi en async ?** Cette operation peut toucher des milliers de lignes en base. L'executer en arriere-plan evite tout impact sur les performances de l'application.

---

### `debug_task`

**Declenchement :** manuel (tests et verification)
**Declencheur :** Developer / admin

```python
@shared_task(bind=True)
def debug_task(self) -> str:
    """
    Tache de test pour verifier que Celery fonctionne correctement.
    Affiche les informations de la requete en cours dans les logs.

    Returns:
        Message de confirmation.
    """
    print(f"Request: {self.request!r}")
    return "Celery fonctionne correctement !"
```

**Usage :**
```python
# Dans le shell Django (make dev-shell)
from config.celery import debug_task
result = debug_task.delay()
result.get(timeout=10)  # → "Celery fonctionne correctement !"
```

---

## Configuration

### `backend/config/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("instantmusic")

# Charge la configuration depuis les settings Django
# (tous les parametres prefixes CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-decouvre les taches dans tous les fichiers tasks.py des apps
app.autodiscover_tasks()
```

### Settings Django

```python
# backend/config/settings/base.py

# Broker : Redis DB 0 (file d'attente des taches)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")

# Result backend : Redis DB 0 (stockage des resultats)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")

# Format de serialisation des messages
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Fuseau horaire
CELERY_TIMEZONE = "Europe/Paris"
CELERY_ENABLE_UTC = True

# Expiration des resultats (1 journee)
CELERY_RESULT_EXPIRES = 86400

# DatabaseScheduler : le planning Celery Beat est stocke en base PostgreSQL
# Cela permet de modifier le planning via l'interface Django Admin
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Planning des taches periodiques (initial, modifiable en admin)
CELERY_BEAT_SCHEDULE = {
    "purge-expired-invitations": {
        "task": "apps.administration.tasks.purge_expired_invitations",
        "schedule": crontab(hour=2, minute=0),  # Tous les jours a 2h du matin
    },
    "anonymize-old-game-data": {
        "task": "apps.administration.tasks.anonymize_old_game_data",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Dimanche a 3h
    },
}

# Apps necessaires pour Celery Beat (gestion du planning en base)
INSTALLED_APPS = [
    ...
    "django_celery_beat",
    "django_celery_results",
    ...
]
```

---

## Monitoring des taches

### Flower (interface web Celery)

Flower est une interface web pour monitorer Celery en temps reel. En developpement, on peut le lancer ainsi :

```bash
# Dans le shell du conteneur backend
make dev-shell
celery -A config.celery flower --port=5555
```

Interface accessible sur : http://localhost:5555

Flower affiche :
- Les workers actifs et leur etat
- Les taches en cours, en attente, terminees
- Les statistiques d'execution (temps moyen, taux d'echec)
- Les files d'attente et leur longueur

### Via les logs

```bash
# Voir les logs du worker en temps reel
make logs-dev

# Ou directement
docker compose logs -f celery

# Sortie typique du worker
[2026-03-07 14:30:00] INFO celery.worker: Received task:
    apps.achievements.tasks.check_and_award[d3b07384-...]
[2026-03-07 14:30:00] INFO celery.task: Task
    apps.achievements.tasks.check_and_award[d3b07384-...]
    succeeded in 0.234s: {'awarded': ['premier_quiz']}
```

### Via Django Admin

Les resultats des taches sont visibles dans l'admin Django si `django_celery_results` est installe :

`http://localhost:8000/admin/django_celery_results/taskresult/`

---

## Troubleshooting

### Les taches ne s'executent pas

```bash
# 1. Verifier que le worker est en marche
docker compose ps celery
# → doit etre "Up"

# 2. Verifier que Redis est accessible depuis le worker
docker compose exec celery redis-cli -h redis ping
# → doit repondre "PONG"

# 3. Verifier les logs du worker
docker compose logs celery
# → chercher des erreurs de connexion

# 4. Tester avec la debug_task
docker compose exec backend python manage.py shell -c "
from config.celery import debug_task
r = debug_task.delay()
print(r.get(timeout=10))
"
```

### Celery Beat ne lance pas les taches planifiees

```bash
# 1. Verifier que le beat est en marche
docker compose ps celery-beat

# 2. Verifier les logs du beat
docker compose logs celery-beat

# 3. Verifier que les migrations django_celery_beat sont appliquees
docker compose exec backend python manage.py showmigrations django_celery_beat

# 4. Verifier le planning dans l'admin
# http://localhost:8000/admin/django_celery_beat/periodictask/
```

### Une tache est bloquee dans la file

```bash
# Voir les taches en attente
docker compose exec redis redis-cli -n 0 LLEN celery
# → nombre de taches en attente

# Purger la file (ATTENTION : supprime toutes les taches en attente)
docker compose exec redis redis-cli -n 0 DEL celery
```
