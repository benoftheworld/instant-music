# Déploiement local — Guide complet

## Vue d'ensemble

Ce guide explique comment lancer l'environnement de développement InstantMusic sur votre machine locale. Tout l'environnement tourne dans des conteneurs Docker, ce qui garantit que chaque développeur travaille dans un environnement identique.

```
┌──────────────────────────────────────────────────────────────────────┐
│                   ENVIRONNEMENT LOCAL                                │
│                                                                      │
│   Votre machine                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Docker Compose (docker-compose.yml)                        │   │
│   │                                                             │   │
│   │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────────────┐ │   │
│   │  │ frontend │ │ backend  │ │ celery │ │ nginx            │ │   │
│   │  │ React    │ │ Django   │ │ worker │ │ (reverse proxy)  │ │   │
│   │  │ :3000    │ │ :8000    │ │        │ │ :80              │ │   │
│   │  └──────────┘ └──────────┘ └────────┘ └──────────────────┘ │   │
│   │                                                             │   │
│   │  ┌──────────┐ ┌──────────┐                                 │   │
│   │  │ postgres │ │  redis   │                                 │   │
│   │  │ :5432    │ │  :6379   │                                 │   │
│   │  └──────────┘ └──────────┘                                 │   │
│   └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :

### 1. Docker Desktop

Docker est le système de conteneurisation. Il permet d'exécuter des applications dans des environnements isolés (conteneurs).

- **macOS** : https://docs.docker.com/desktop/install/mac-install/
- **Windows** : https://docs.docker.com/desktop/install/windows-install/ (WSL2 requis)
- **Linux** : https://docs.docker.com/engine/install/ubuntu/

```bash
# Vérifier l'installation
docker --version
# Docker version 26.0.0 (ou supérieur)
```

### 2. Docker Compose v2

Docker Compose permet de définir et gérer plusieurs conteneurs comme une seule application. La v2 est intégrée à Docker Desktop récent (commande `docker compose` sans tiret).

```bash
# Vérifier Docker Compose v2
docker compose version
# Docker Compose version v2.x.x
```

> Si vous avez encore `docker-compose` (avec tiret), c'est la v1 qui est dépréciée. Mettez à jour Docker Desktop.

### 3. Git

```bash
git --version
# git version 2.x.x
```

### 4. Make

Make est utilisé pour lancer les commandes définies dans le `Makefile`.

```bash
# macOS (via Xcode Command Line Tools)
xcode-select --install

# Linux
sudo apt-get install make

# Windows (via Chocolatey)
choco install make

# Vérifier
make --version
```

---

## Installation pas à pas

### Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/votre-org/instant-music.git
cd instant-music
```

### Étape 2 — Configurer les variables d'environnement

Le fichier `.env` contient les configurations sensibles (mots de passe, clés API). Il n'est jamais commité dans Git. Copiez le fichier d'exemple :

```bash
cp .env.example .env
```

Ouvrez `.env` et remplissez les variables :

```bash
# ─── Base de données ────────────────────────────────────────
POSTGRES_DB=instantmusic
POSTGRES_USER=instantmusic
POSTGRES_PASSWORD=changeme123          # ← Choisir un mot de passe fort
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ─── Redis ──────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ─── Django ─────────────────────────────────────────────────
DJANGO_SECRET_KEY=your-secret-key-here   # ← Générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ─── JWT ────────────────────────────────────────────────────
JWT_ACCESS_TOKEN_LIFETIME=15             # minutes
JWT_REFRESH_TOKEN_LIFETIME=7             # jours

# ─── APIs externes ──────────────────────────────────────────
# Deezer (pas de clé requise pour l'API publique)
# DEEZER_API_KEY=                        # optionnel si plan premium

# Google OAuth (optionnel)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# ─── Frontend ───────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# ─── Email (optionnel en dev) ───────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

> **Astuce** : En développement, vous n'avez pas besoin de configurer les APIs externes pour démarrer. Les fonctionnalités nécessitant Deezer ou Google OAuth seront simplement indisponibles.

### Étape 3 — Lancer l'environnement

```bash
make deploy-dev
```

Cette commande :
1. Build les images Docker (backend, frontend)
2. Démarre tous les conteneurs
3. Attend que la base de données soit prête
4. L'application sera disponible après ~30-60 secondes

```
$ make deploy-dev
[+] Building 45.2s (24/24) FINISHED
[+] Running 6/6
 ✔ Container db        Started
 ✔ Container redis     Started
 ✔ Container backend   Started
 ✔ Container celery    Started
 ✔ Container frontend  Started
 ✔ Container nginx     Started
```

### Étape 4 — Appliquer les migrations

Les migrations créent les tables en base de données. À faire la première fois, et après chaque `make dev-makemigrations` :

```bash
make dev-migrate
```

```
$ make dev-migrate
Running migrations...
  Applying users.0001_initial... OK
  Applying games.0001_initial... OK
  Applying playlists.0001_initial... OK
  Applying achievements.0001_initial... OK
  ...
```

### Étape 5 — Créer un compte administrateur

```bash
make dev-createsuperuser
```

Suivez les instructions interactives :
```
Username (leave blank to use 'root'): admin
Email address: admin@localhost.com
Password: ********
Password (again): ********
Superuser created successfully.
```

### Étape 6 — Charger les données initiales (seed)

```bash
# Charger les achievements prédéfinis
make dev-shell
# Dans le shell :
python manage.py seed_achievements

# Charger les items de la boutique
python manage.py seed_shop

# Optionnel : charger des playlists de démo
python manage.py seed_playlists

exit
```

---

## Accès aux services

Après `make deploy-dev` et les migrations, voici les URLs disponibles :

| Service          | URL                                          | Description                              |
| ---------------- | -------------------------------------------- | ---------------------------------------- |
| **Frontend**     | http://localhost:3000                        | Application React (interface principale) |
| **Backend API**  | http://localhost:8000/api/                   | API REST Django                          |
| **Admin Django** | http://localhost:8000/admin/                 | Interface d'administration               |
| **Swagger UI**   | http://localhost:8000/api/schema/swagger-ui/ | Documentation API interactive            |
| **ReDoc**        | http://localhost:8000/api/schema/redoc/      | Documentation API alternative            |

---

## Commandes utiles du Makefile

### Développement quotidien

```bash
# Démarrer l'environnement (ou redémarrer après arrêt)
make deploy-dev

# Voir les logs en temps réel de tous les services
make logs-dev

# Voir les logs d'un service spécifique
docker compose -f _devops/docker/docker-compose.yml logs -f backend
docker compose -f _devops/docker/docker-compose.yml logs -f frontend

# Ouvrir un shell dans le container backend
make dev-shell

# Dans le shell Django, exemples :
python manage.py shell          # Shell Python Django
python manage.py dbshell        # Shell PostgreSQL
python manage.py showmigrations # Voir l'état des migrations
```

### Gestion des migrations

```bash
# Créer de nouvelles migrations après modification d'un modèle
make dev-makemigrations

# Appliquer les migrations
make dev-migrate

# Annuler jusqu'à une migration spécifique
docker compose exec backend python manage.py migrate games 0001
```

### Tests

```bash
# Lancer tous les tests (backend + frontend)
make test

# Tests backend uniquement (pytest)
make test-backend

# Tests frontend uniquement (vitest)
make test-frontend

# Avec rapport de couverture HTML
make test-coverage
# → Rapports dans backend/htmlcov/ et frontend/coverage/
```

### Linting et formatage

```bash
# Vérifier le code (lint)
make lint

# Formater automatiquement le code Python
make format

# Vérification des types Python (mypy)
make typecheck

# Linting frontend
cd frontend && npm run lint
```

---

## Structure des volumes Docker

En développement, le code source est **monté en volume** dans les conteneurs. Toute modification du code est donc immédiatement reflétée sans rebuild :

```yaml
# docker-compose.yml (simplifié)
services:
  backend:
    volumes:
      - ./backend:/app  # Mount du code Python
    # → modifications dans backend/ = effet immédiat

  frontend:
    volumes:
      - ./frontend:/app # Mount du code React
    # → Vite Hot Module Replacement actif
```

---

## Débogage courant

### Le backend ne démarre pas

```bash
# Vérifier les logs d'erreur
docker compose -f _devops/docker/docker-compose.yml logs backend

# Problèmes courants :
# 1. Variables d'environnement manquantes → vérifier .env
# 2. Port 8000 déjà utilisé
#    → lsof -i :8000 (Linux/Mac)
#    → netstat -ano | findstr :8000 (Windows)
# 3. Dépendances Python non installées
#    → docker compose build backend
```

### Le frontend ne démarre pas

```bash
docker compose -f _devops/docker/docker-compose.yml logs frontend

# Problèmes courants :
# 1. Port 3000 déjà utilisé (par une autre appli React ?)
# 2. node_modules manquant → docker compose build frontend
```

### Erreur de connexion à la base de données

```bash
# Vérifier que PostgreSQL est bien lancé
docker compose -f _devops/docker/docker-compose.yml ps db

# Se connecter manuellement à la DB
docker compose -f _devops/docker/docker-compose.yml exec db psql -U instantmusic -d instantmusic
```

### Réinitialiser complètement l'environnement

```bash
# Arrêter et supprimer les conteneurs + volumes
docker compose -f _devops/docker/docker-compose.yml down -v

# Recommencer depuis l'étape 3
make deploy-dev
make dev-migrate
make dev-createsuperuser
```

### Les migrations échouent

```bash
# Voir l'état actuel des migrations
docker compose exec backend python manage.py showmigrations

# Vérifier s'il y a des conflits
docker compose exec backend python manage.py migrate --check

# En dernier recours (données perdues !)
docker compose down -v  # Supprime le volume PostgreSQL
make deploy-dev
make dev-migrate
```

### Les WebSockets ne fonctionnent pas

Les WebSockets passent par nginx en développement. Vérifier :

```bash
# 1. Nginx configuré pour les WS
grep -i websocket _devops/nginx/nginx.dev.conf

# 2. Django Channels configuré (ASGI, pas WSGI)
cat backend/config/asgi.py

# 3. Redis est bien accessible
docker compose exec backend python -c "
import django; django.setup()
from channels.layers import get_channel_layer
import asyncio
layer = get_channel_layer()
print(asyncio.run(layer.send('test', {'type': 'test'})))
print('Redis OK')
"
```

---

## Workflow de développement recommandé

```
1. git pull origin develop    ← Récupérer les dernières modifications
2. make deploy-dev            ← Démarrer l'environnement
3. make dev-migrate           ← Appliquer éventuelles nouvelles migrations
4. [coder...]                 ← Le hot reload est actif
5. make test                  ← Lancer les tests
6. make lint                  ← Vérifier le code
7. git add / commit / push    ← Soumettre les changements
```
