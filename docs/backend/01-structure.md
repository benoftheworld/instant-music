# Structure du Backend — InstantMusic

> Documentation de l'organisation du dossier `backend/`, de l'architecture Django en environnements séparés et des fichiers de configuration clés.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Arborescence complète](#arborescence-complète)
3. [Fichiers racine](#fichiers-racine)
4. [Dépendances (`requirements/`)](#dépendances-requirements)
5. [Configuration (`config/`)](#configuration-config)
   - [Split settings par environnement](#split-settings-par-environnement)
   - [ASGI et WebSocket](#asgi-et-websocket)
   - [Celery](#celery)
   - [URLs HTTP](#urls-http)
6. [Applications (`apps/`)](#applications-apps)
7. [Statiques et templates admin](#statiques-et-templates-admin)

---

## Vue d'ensemble

Le backend est une application **Django 5.1** organisée selon le pattern **"config as a package"** : les paramètres sont divisés en trois fichiers (`base`, `development`, `production`) pour isoler les surcharges d'environnement. Le projet utilise **Django Channels** pour les WebSockets, **Celery** pour les tâches asynchrones, et **DRF** (Django REST Framework) pour l'API REST.

```
┌─────────────────────────────────────────────────────────┐
│                        BACKEND                           │
│                                                          │
│   manage.py  ←  point d'entrée CLI Django                │
│   config/    ←  ASGI, Celery, URLs, Settings             │
│   apps/      ←  9 applications métier                    │
│   requirements/ ← dépendances par env                    │
└─────────────────────────────────────────────────────────┘
```

---

## Arborescence complète

```
backend/
├── Dockerfile                   ← Image Docker pour le développement
├── Dockerfile.prod              ← Image Docker multi-stage pour la production
├── .dockerignore                ← Exclusions de l'image Docker
├── manage.py                    ← CLI Django (migrations, shell, commandes custom)
│
├── pyproject.toml               ← Configuration ruff + mypy + pytest (backend)
├── ruff.toml                    ← Surcharges ruff spécifiques backend
├── pytest.ini                   ← Configuration pytest (markers, paths)
├── conftest.py                  ← Fixtures pytest partagées
│
├── .env.example                 ← Template des variables d'environnement
│
├── requirements/
│   ├── base.txt                 ← Dépendances communes (Django, DRF, Channels…)
│   ├── development.txt          ← Extras dev (debug-toolbar, factory-boy…)
│   └── production.txt           ← Extras prod (gunicorn, sentry-sdk…)
│
├── config/
│   ├── __init__.py
│   ├── asgi.py                  ← Routing ASGI HTTP + WebSocket
│   ├── celery.py                ← Instance Celery + auto-découverte des tâches
│   ├── wsgi.py                  ← Fallback WSGI (non utilisé en prod)
│   ├── urls.py                  ← Routing HTTP principal (inclut toutes les apps)
│   ├── db_router.py             ← Router de base de données (optionnel)
│   ├── otel.py                  ← Instrumentation OpenTelemetry
│   └── settings/
│       ├── __init__.py
│       ├── base.py              ← Paramètres communs à tous les environnements
│       ├── development.py       ← Surcharges pour le développement local
│       └── production.py        ← Surcharges pour la production (HTTPS, S3…)
│
├── apps/
│   ├── __init__.py
│   ├── achievements/            ← Succès et badges utilisateurs
│   ├── administration/          ← Mode maintenance, pages légales, RGPD
│   ├── authentication/          ← JWT + Google OAuth 2.0
│   ├── core/                    ← Health checks, métriques Prometheus, middleware
│   ├── games/                   ← Logique de jeu complète + WebSocket Consumer
│   ├── playlists/               ← Intégration API Deezer + YouTube
│   ├── shop/                    ← Boutique virtuelle, bonus de partie
│   ├── stats/                   ← Statistiques joueurs et classements
│   └── users/                   ← Utilisateurs, équipes, amitiés
│
├── static/
│   └── admin/
│       └── js/                  ← JavaScript custom pour l'interface Jazzmin
│
└── templates/
    └── admin/                   ← Templates HTML custom pour l'admin Django
```

---

## Fichiers racine

### `manage.py`

Point d'entrée standard Django. Configure la variable d'environnement `DJANGO_SETTINGS_MODULE` pour pointer vers le bon fichier de settings selon l'environnement. Utilisé pour toutes les commandes de gestion (`migrate`, `shell`, `createsuperuser`, etc.).

### `Dockerfile` et `Dockerfile.prod`

| Fichier           | Usage               | Particularités                                                                           |
| ----------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| `Dockerfile`      | Développement local | Image unique, `requirements/development.txt`, rechargement automatique                   |
| `Dockerfile.prod` | Production          | Multi-stage build, `requirements/production.txt`, utilisateur non-root, assets collectés |

Le build multi-stage de `Dockerfile.prod` comprend deux étapes :
1. **Builder** : installation des dépendances Python dans un virtualenv isolé
2. **Runner** : copie uniquement le virtualenv et le code source (image finale allégée)

### `pyproject.toml` et `ruff.toml`

Configuration centralisée des outils de qualité de code :

```toml
# pyproject.toml (extrait)
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"
strict = true
```

### `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
markers =
    django_db: tests requiring database access
    slow: tests marked as slow
```

### `.env.example`

Template exhaustif listant toutes les variables d'environnement requises. Toute nouvelle variable d'environnement ajoutée au projet **doit** être documentée dans ce fichier.

---

## Dépendances (`requirements/`)

La stratégie de split des requirements permet de garder les images de production légères et de n'installer les outils de développement que localement.

### `base.txt` — Dépendances communes

```
Django==5.1.*
djangorestframework==3.15.*
djangorestframework-simplejwt==5.3.*
django-allauth==65.*           # OAuth 2.0
channels==4.1.*                # WebSocket (ASGI)
channels-redis==4.2.*          # Channel layer Redis
celery==5.4.*                  # Tâches asynchrones
redis==5.0.*                   # Client Redis
psycopg[binary]==3.2.*         # Driver PostgreSQL
cryptography==43.*             # Chiffrement AES Fernet (emails)
Pillow==11.*                   # Traitement images (avatars)
drf-spectacular==0.27.*        # OpenAPI / Swagger
django-jazzmin==3.*            # Interface admin moderne
reportlab==4.*                 # Génération PDF (résultats)
prometheus-client==0.21.*      # Métriques Prometheus
```

### `development.txt`

```
-r base.txt
django-debug-toolbar==4.*      # Debug SQL, cache, requêtes
factory-boy==3.*               # Factories pour les tests
faker==30.*                    # Génération de données fictives
pytest-django==4.*             # Plugin pytest pour Django
pytest-asyncio==0.24.*         # Tests async (Channels)
```

### `production.txt`

```
-r base.txt
gunicorn==23.*                 # Serveur WSGI/ASGI
uvicorn[standard]==0.32.*      # Worker ASGI pour Channels
sentry-sdk[django]==2.*        # Monitoring des erreurs
django-storages[s3]==1.14.*    # Stockage S3 (avatars prod)
boto3==1.35.*                  # AWS SDK
```

---

## Configuration (`config/`)

### Split settings par environnement

Le pattern "split settings" divise la configuration en trois niveaux d'héritage :

```
config/settings/base.py          ← Paramètres communs (70% de la config)
       ├── development.py         ← Hérite de base, surcharges dev
       └── production.py          ← Hérite de base, surcharges prod
```

La variable d'environnement `DJANGO_SETTINGS_MODULE` détermine quel fichier est chargé :

```bash
# Développement
DJANGO_SETTINGS_MODULE=config.settings.development

# Production
DJANGO_SETTINGS_MODULE=config.settings.production
```

#### `settings/base.py` — Paramètres communs

Ce fichier contient tout ce qui est partagé entre les environnements :

```python
# Extrait représentatif de base.py

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Applications installées
DJANGO_APPS = [
    "jazzmin",                        # Admin moderne (doit être en premier)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "channels",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "drf_spectacular",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.users",
    "apps.authentication",
    "apps.games",
    "apps.playlists",
    "apps.achievements",
    "apps.stats",
    "apps.administration",
    "apps.shop",
    "apps.core",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Modèle utilisateur custom
AUTH_USER_MODEL = "users.User"

# Configuration JWT (simplejwt)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
}

# Configuration DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Channels (WebSocket)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")],
        },
    }
}

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
```

#### `settings/development.py` — Surcharges développement

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Base de données locale
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "instantmusic"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# Email en console pour le développement
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS permissif en dev
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]
```

#### `settings/production.py` — Surcharges production

```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Stockage S3 (avatars, médias)
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-west-3")

# Sentry
import sentry_sdk
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    traces_sample_rate=0.1,
)

# Email SMTP
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
```

---

### ASGI et WebSocket

Le fichier `config/asgi.py` est le point d'entrée du serveur ASGI. Il gère à la fois les requêtes HTTP classiques et les connexions WebSocket via Django Channels.

```python
# config/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Application ASGI Django standard (HTTP)
django_asgi_app = get_asgi_application()

from apps.games.routing import websocket_urlpatterns
from apps.authentication.middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    # Requêtes HTTP classiques → Django views
    "http": django_asgi_app,

    # Connexions WebSocket → Django Channels
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

#### Flux de traitement des requêtes

```
Client
  │
  ▼
Nginx (reverse proxy)
  ├── /          → React SPA (nginx:alpine)
  ├── /api/      → gunicorn (WSGI) → Django HTTP
  ├── /ws/       → uvicorn (ASGI) → Django Channels
  └── /admin/    → gunicorn → Django Admin (Jazzmin)
       │
       ▼
ProtocolTypeRouter
  ├── "http"      → get_asgi_application() → URLs HTTP
  └── "websocket" → AllowedHostsOriginValidator
                      └── JWTAuthMiddlewareStack
                            └── URLRouter
                                  └── /ws/game/<room_code>/
                                        └── GameConsumer
```

#### Pattern `JWTAuthMiddlewareStack`

Le middleware WebSocket (`apps/authentication/middleware.py`) intercepte les connexions WebSocket pour authentifier l'utilisateur via un JWT passé en query parameter :

```
ws://localhost:8000/ws/game/ABC123/?token=eyJhbGciOiJIUzI1NiJ9...
                                           ↑
                                    Extrait par JWTAuthMiddleware
                                    Vérifié → user injecté dans scope
                                    Invalide → fermeture avec code 4003
```

```python
# Comportement du middleware WebSocket JWT
class JWTAuthMiddleware:
    async def __call__(self, scope, receive, send):
        # 1. Extraire le token du query string
        token = parse_qs(scope["query_string"]).get(b"token", [None])[0]

        if token:
            try:
                # 2. Valider le JWT et récupérer l'utilisateur
                validated_token = AccessToken(token.decode())
                user = await get_user(validated_token["user_id"])
                scope["user"] = user
            except (InvalidToken, TokenError):
                # 3. Token invalide → fermer la connexion avec code 4003
                await send({"type": "websocket.close", "code": 4003})
                return

        await self.inner(scope, receive, send)
```

---

### Celery

Le fichier `config/celery.py` configure l'instance Celery utilisée pour les tâches asynchrones (vérification des succès, purge des données RGPD, etc.).

```python
# config/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("instantmusic")

# Lire la configuration depuis les settings Django (préfixe CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-découverte des tâches dans chaque app Django
# Cherche un fichier tasks.py dans chaque app de INSTALLED_APPS
app.autodiscover_tasks()
```

#### Architecture Celery

```
Django App
    │
    │  .delay() / .apply_async()
    ▼
Redis (broker)
    │
    ▼
Celery Worker (container séparé)
    │
    ├── check_achievements_async     (apps.achievements)
    ├── purge_expired_invitations    (apps.administration)
    └── anonymize_old_game_data      (apps.administration)
    │
    ▼
Redis (result backend)
    │
    ▼
Django (récupération du résultat si nécessaire)
```

#### Configuration des queues

```python
# Dans base.py
CELERY_TASK_ROUTES = {
    "apps.achievements.tasks.*": {"queue": "achievements"},
    "apps.administration.tasks.*": {"queue": "maintenance"},
}

CELERY_BEAT_SCHEDULE = {
    "purge-expired-invitations": {
        "task": "apps.administration.tasks.purge_expired_invitations",
        "schedule": crontab(hour=2, minute=0),   # Chaque nuit à 2h
    },
    "anonymize-old-game-data": {
        "task": "apps.administration.tasks.anonymize_old_game_data",
        "schedule": crontab(day_of_week=0, hour=3),  # Dimanche 3h
    },
}
```

---

### URLs HTTP

Le fichier `config/urls.py` est le routeur HTTP principal. Il inclut les URLs de chaque application Django.

```python
# config/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Interface d'administration Django (Jazzmin)
    path("admin/", admin.site.urls),

    # API REST — chaque app gère ses propres URLs
    path("api/auth/", include("apps.authentication.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/games/", include("apps.games.urls")),
    path("api/playlists/", include("apps.playlists.urls")),
    path("api/achievements/", include("apps.achievements.urls")),
    path("api/stats/", include("apps.stats.urls")),
    path("api/administration/", include("apps.administration.urls")),
    path("api/shop/", include("apps.shop.urls")),

    # Health checks et métriques
    path("api/", include("apps.core.urls")),
    path("metrics/", include("apps.core.metrics_urls")),

    # Documentation OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Médias en développement
    # (en production, servis par S3/nginx)
]
```

---

## Applications (`apps/`)

Chaque application Django suit une structure interne standardisée :

```
apps/<nom_app>/
├── __init__.py
├── admin.py          ← Enregistrement des modèles dans l'interface admin
├── apps.py           ← Configuration AppConfig (label, verbose_name)
├── consumers.py      ← Consumers WebSocket (uniquement apps/games/)
├── migrations/       ← Migrations de base de données
│   ├── __init__.py
│   └── 0001_initial.py
├── models.py         ← Modèles Django (ou models/ package)
├── routing.py        ← Routes WebSocket (uniquement apps/games/)
├── serializers.py    ← Sérialiseurs DRF
├── services.py       ← Logique métier (ou services/ package)
├── tasks.py          ← Tâches Celery
├── tests.py          ← Tests unitaires et d'intégration
├── urls.py           ← Routes HTTP de l'application
└── views.py          ← Vues DRF (ViewSets, APIViews)
```

| Application      | Rôle principal                 | Modèles DB | WebSocket  | Celery |
| ---------------- | ------------------------------ | ---------- | ---------- | ------ |
| `users`          | Utilisateurs, équipes, amitiés | Oui        | Non        | Non    |
| `authentication` | JWT + OAuth 2.0                | Non        | Middleware | Non    |
| `games`          | Logique de jeu complète        | Oui        | Consumer   | Non    |
| `playlists`      | API Deezer + YouTube           | Non        | Non        | Non    |
| `achievements`   | Succès et badges               | Oui        | Non        | Oui    |
| `administration` | Maintenance, RGPD              | Oui        | Non        | Oui    |
| `shop`           | Boutique, bonus                | Oui        | Non        | Non    |
| `stats`          | Statistiques dynamiques        | Non        | Non        | Non    |
| `core`           | Health checks, métriques       | Non        | Non        | Non    |

Pour la documentation détaillée de chaque application, voir [02-apps.md](./02-apps.md).

---

## Statiques et templates admin

### `static/admin/js/`

Fichiers JavaScript personnalisés chargés dans l'interface Jazzmin. Ces fichiers étendent ou surchargent le comportement de l'admin Django pour des fonctionnalités spécifiques (ex. : affichage en temps réel du statut des parties, actions bulk, etc.).

### `templates/admin/`

Templates HTML qui surchargent les templates par défaut de Django Admin. Suivent la convention Django de surcharge par chemin relatif :

```
templates/admin/
├── base_site.html          ← Template de base (branding, logo)
├── apps/
│   └── games/
│       └── game/
│           └── change_list.html  ← Vue liste des parties customisée
└── ...
```

---

> Voir aussi :
> - [02-apps.md](./02-apps.md) — Rôle détaillé de chaque application Django
> - [03-models-mcd.md](./03-models-mcd.md) — MCD complet et documentation des modèles
> - [04-api-routes.md](./04-api-routes.md) — Référence complète des routes API
