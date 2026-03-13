# InstantMusic

> Quiz musical multijoueur en temps reel

---

## Presentation du projet

**InstantMusic** est une application web de quiz musical multijoueur. Des joueurs se retrouvent dans une salle virtuelle, ecoutent des extraits musicaux et doivent repondre le plus rapidement possible aux questions posees : quel est le titre ? L'artiste ? L'annee de sortie ? Les paroles ?

Le jeu se joue en temps reel : quand un joueur repond, tous les autres voient sa reponse instantanement. Le systeme de bonus permet de voler des points, de se proteger, ou de doubler son score — rendant chaque partie impredictible.

### Modes de jeu disponibles

| Mode           | Description                           |
| -------------- | ------------------------------------- |
| **Classique**  | QCM : deviner le titre ou l'artiste   |
| **Rapide**     | QCM a tempo accelere                  |
| **Generation** | Deviner l'annee de sortie du morceau  |
| **Paroles**    | Completer les paroles (texte a trou)  |
| **Karaoke**    | Paroles synchronisees + video YouTube |
| **Mollo**      | Audio ralenti et pitch-shifte         |

---

## Stack technique

### Backend

| Technologie           | Role                         | Version |
| --------------------- | ---------------------------- | ------- |
| Django                | Framework web Python         | 5.1     |
| Django REST Framework | API REST                     | 3.15+   |
| Django Channels       | WebSocket / temps reel       | 4.x     |
| Celery                | Taches asynchrones           | 5.x     |
| Redis                 | Cache, broker, channel layer | 7.x     |
| PostgreSQL            | Base de donnees principale   | 15      |
| Gunicorn + Uvicorn    | Serveur ASGI (prod)          | -       |

### Frontend

| Technologie    | Role                         | Version |
| -------------- | ---------------------------- | ------- |
| React          | Framework UI                 | 18      |
| TypeScript     | Typage statique              | 5       |
| Vite           | Bundler / serveur dev        | 5.x     |
| Zustand        | Gestion d'etat global        | 4.x     |
| TanStack Query | Fetching et cache de donnees | 5.x     |
| Tailwind CSS   | Framework CSS utilitaire     | 3.x     |

### Infra

| Technologie             | Role                                  |
| ----------------------- | ------------------------------------- |
| Docker + Docker Compose | Conteneurisation de tous les services |
| Nginx                   | Reverse proxy, SSL, routage           |
| Let's Encrypt / Certbot | Certificats SSL automatiques (prod)   |

---

## Prerequis

Avant de commencer, vous devez avoir installe sur votre machine :

- **Docker** (version 24+ recommandee) — [Installer Docker](https://docs.docker.com/get-docker/)
- **Docker Compose v2** (integre a Docker Desktop) — verifier avec `docker compose version`
- **Git** pour cloner le depot

> Docker permet d'executer tous les services (base de donnees, serveur web, Redis...) dans des conteneurs isoles, sans avoir a les installer manuellement sur votre systeme.

---

## Installation rapide

```bash
# 1. Cloner le depot
git clone <url-du-repo> instant-music
cd instant-music

# 2. Copier les variables d'environnement
cp .env.example .env
# Editer .env avec vos valeurs (voir docs/deployment/01-developpement.md)

# 3. Lancer tout l'environnement local
make deploy-dev

# 4. Appliquer les migrations de base de donnees
make dev-migrate

# 5. (Optionnel) Creer un compte administrateur
make dev-createsuperuser
```

L'application est accessible sur **http://localhost:3000** apres quelques secondes.

---

## Acces locaux

| Service                     | URL                                          |
| --------------------------- | -------------------------------------------- |
| Application (Frontend)      | http://localhost:3000                        |
| API Backend                 | http://localhost:8000                        |
| Interface d'administration  | http://localhost:8000/admin                  |
| Documentation API (Swagger) | http://localhost:8000/api/schema/swagger-ui/ |
| Documentation API (ReDoc)   | http://localhost:8000/api/schema/redoc/      |

---

## Commandes essentielles

### Environnement de developpement

| Commande                   | Description                                                         |
| -------------------------- | ------------------------------------------------------------------- |
| `make deploy-dev`          | Demarrer tous les conteneurs (DB, Redis, Backend, Frontend, Celery) |
| `make logs-dev`            | Afficher les logs en temps reel de tous les services                |
| `make dev-shell`           | Ouvrir un shell dans le conteneur backend                           |
| `make dev-migrate`         | Appliquer les migrations Django                                     |
| `make dev-makemigrations`  | Creer de nouvelles migrations Django                                |
| `make dev-createsuperuser` | Creer un compte administrateur                                      |

### Tests

| Commande             | Description                                |
| -------------------- | ------------------------------------------ |
| `make test`          | Lancer tous les tests (backend + frontend) |
| `make test-backend`  | Tests Python uniquement (pytest)           |
| `make test-frontend` | Tests JavaScript uniquement (vitest)       |
| `make test-coverage` | Generer les rapports de couverture HTML    |

### Qualite du code

| Commande         | Description                                  |
| ---------------- | -------------------------------------------- |
| `make lint`      | Verifier le style : ruff + bandit + yamllint |
| `make format`    | Formater automatiquement le code Python      |
| `make typecheck` | Verifier les types Python avec mypy          |

---

## Structure du projet

```
instant-music/
├── backend/                      # Application Django
│   ├── apps/
│   │   ├── users/                # Utilisateurs, equipes, amities
│   │   ├── authentication/       # JWT + Google OAuth 2.0
│   │   ├── games/                # Logique de jeu, WebSocket consumer
│   │   ├── playlists/            # Integration Deezer + YouTube
│   │   ├── achievements/         # Succes / badges
│   │   ├── shop/                 # Boutique, bonus achetables
│   │   ├── stats/                # Statistiques joueurs
│   │   ├── administration/       # Mode maintenance, pages legales
│   │   └── core/                 # Health check, metriques Prometheus
│   └── config/
│       ├── settings/             # Parametres Django (base/dev/prod)
│       ├── asgi.py               # Point d'entree ASGI (WebSocket)
│       ├── celery.py             # Configuration Celery
│       └── urls.py               # Routage HTTP principal
│
├── frontend/                     # Application React
│   └── src/
│       ├── components/           # Composants UI reutilisables
│       ├── pages/                # Pages de l'application
│       ├── stores/               # Etats globaux Zustand
│       ├── hooks/                # Hooks personnalises
│       └── services/             # Appels API et WebSocket
│
├── _devops/                      # Configuration infrastructure
│   ├── docker/
│   │   ├── docker-compose.yml          # Compose developpement
│   │   ├── docker-compose.prod.yml     # Compose production
│   │   └── docker-compose.monitoring.yml # Monitoring optionnel
│   ├── nginx/
│   │   └── nginx.conf            # Configuration Nginx production
│   └── linter/                   # Configurations ruff, bandit, yamllint
│
├── docs/                         # Documentation (vous etes ici)
│   ├── INDEX.md                  # Sommaire general
│   ├── README.md                 # Ce fichier
│   ├── CHANGELOG.md              # Historique des versions
│   ├── architecture/             # Documentation de l'architecture
│   ├── backend/                  # Documentation backend Django
│   ├── frontend/                 # Documentation frontend React
│   ├── game/                     # Documentation du systeme de jeu
│   └── deployment/               # Documentation du deploiement
│
├── Makefile                      # Toutes les commandes DevOps
├── pyproject.toml                # Configuration Python (ruff, mypy, pytest)
└── CLAUDE.md                     # Instructions pour Claude Code
```

---

## Conventions

### Langue

Tout le projet est en **francais** : documentation, commentaires de code, messages de commit, noms de branches.

### Format des commits Git

```
type(scope): description courte en francais

Exemples :
feat(games): ajouter le mode karaoke
fix(auth): corriger la validation du token JWT
docs(architecture): mettre a jour le schema Redis
refactor(games): extraire la logique de scoring dans un service
test(playlists): ajouter les tests d'integration Deezer
```

Types valides : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branches Git

```
feature/<description>   # Nouvelle fonctionnalite
fix/<description>       # Correction de bug
hotfix/<description>    # Correction urgente (depuis main)
docs/<description>      # Documentation uniquement
```

Toujours partir de la branche `develop` (sauf hotfix depuis `main`).

### Python

- Formateur : **ruff** (longueur de ligne 88 caracteres, double guillemets, Python 3.11)
- Securite : **bandit**
- Typage : **mypy** (mode strict recommande)

### TypeScript

- Formateur : **Prettier** (100 caracteres, guillemets simples, trailing commas ES5)
- Linter : **ESLint**

---

## Documentation complete

La documentation complete est organisee dans le dossier `docs/`.

Commencer par le [sommaire general (INDEX.md)](./INDEX.md) pour naviguer.

Pour une plongee technique :
- [Architecture globale](./architecture/01-vue-ensemble.md)
- [Comment fonctionne le temps reel](./architecture/06-websockets.md)
- [Deploiement en production](./deployment/02-production.md)

---

## License

Ce projet est distribue sous licence MIT. Voir le fichier [LICENSE](../LICENSE) pour plus de details.
