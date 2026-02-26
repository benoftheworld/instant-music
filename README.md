# 🎵 InstantMusic

Une application web interactive de quiz musical multijoueur en temps réel.

## 🎮 Fonctionnalités

- **Quiz musical multijoueur** - Affrontez vos amis en temps réel
- **Authentification complète** - Inscription/connexion classique + Google OAuth
- **Profils personnalisables** - Avatar, statistiques, historique
- **Système de jeu avancé** - Timer, scoring dynamique, classement en direct
- **Intégration musicale** - Morceaux via Deezer (extraits 30s gratuits)
- **Communication temps réel** - WebSocket pour synchronisation instantanée
- **Interface moderne** - React + TypeScript + Tailwind CSS
- **Administration** - Backoffice Django pour gestion complète

## 🏗️ Architecture

### Stack Technique

**Backend:**
- Django 5.1 + Django REST Framework
- WebSocket (Django Channels + Daphne)
- PostgreSQL (base de données)
- Redis (cache + broker WebSocket)
- Celery (tâches asynchrones)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Query (gestion API)
- Zustand (state management)
- Tailwind CSS (styling)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (reverse proxy en production)

### Structure DevOps

Les fichiers de configuration DevOps sont organisés dans le dossier `_devops/` :

```
_devops/
├── docker/              # Docker Compose files
├── script/              # Scripts de déploiement
└── linter/              # Configuration des linters
```

Les workflows CI/CD restent dans `.github/workflows/` (convention GitHub).

📖 Voir [_devops/README.md](_devops/README.md) pour plus de détails.

### APIs Externes

- **Deezer API** - Recherche de playlists et morceaux (gratuit, pas de clé requise)
- **Google OAuth 2.0** - Authentification sociale (optionnel)

## 🚀 Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Git

### Installation

1. **Cloner le repository**
```bash
git clone <votre-repo>
cd instant-music
```

2. **Configurer l'environnement**
```bash
# Copier le fichier d'exemple
cp backend/.env.example backend/.env

# Éditer backend/.env et configurer au minimum :
# - SECRET_KEY (générer avec: python -c "import secrets; print(secrets.token_urlsafe(50))")
# - GOOGLE_OAUTH_CLIENT_ID (optionnel - voir section OAuth)
# - GOOGLE_OAUTH_CLIENT_SECRET (optionnel)
```

3. **Démarrer l'application**
```bash
# Depuis la racine du projet
./_devops/script/deploy.sh development

# Ou directement
cd _devops/docker && docker compose up -d
```

4. **Initialiser la base de données**
```bash
# Appliquer les migrations
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py migrate

# Créer un superutilisateur
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py createsuperuser
```

5. **Accéder à l'application**
- Frontend: http://localhost:3000
- API Backend: http://localhost:8000/api
- Admin Django: http://localhost:8000/admin

## 🎯 Configuration Google OAuth (Optionnel)

L'authentification Google OAuth est optionnelle. Sans elle, les utilisateurs peuvent toujours :
- S'inscrire avec email/mot de passe
- Se connecter normalement
- Utiliser toutes les fonctionnalités

### Pour activer Google OAuth :

1. **Créer un projet Google Cloud**
   - Accédez à https://console.cloud.google.com
   - Créez un nouveau projet

2. **Configurer OAuth 2.0**
   - APIs & Services → Identifiants
   - Créer des identifiants → ID client OAuth 2.0
   - Type : Application Web
   - Origines JavaScript autorisées : `http://localhost:3000`
   - URI de redirection : `http://localhost:3000/auth/google/callback`

3. **Ajouter les credentials**
```bash
# Dans backend/.env
GOOGLE_OAUTH_CLIENT_ID=votre_client_id
GOOGLE_OAUTH_CLIENT_SECRET=votre_client_secret
```

4. **Redémarrer les services**
```bash
docker compose -f _devops/docker/docker-compose.yml restart backend
```

## 📖 Documentation

- **[QUICK_START.md](docs/QUICK_START.md)** - Guide de démarrage ultra-rapide
- **[GAMEPLAY_SYSTEM.md](docs/GAMEPLAY_SYSTEM.md)** - Système de jeu détaillé
- **[PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)** - Guide de déploiement en production
- **[SECURITY.md](docs/SECURITY.md)** - Bonnes pratiques de sécurité
- **[_devops/README.md](_devops/README.md)** - Documentation DevOps et CI/CD

## 🔧 Commandes Utiles

### Développement

```bash
# Voir les logs
docker compose -f _devops/docker/docker-compose.yml logs -f [service]

# Redémarrer un service
docker compose -f _devops/docker/docker-compose.yml restart [service]

# Arrêter l'application
docker compose -f _devops/docker/docker-compose.yml down

# Arrêter et supprimer les volumes
docker compose -f _devops/docker/docker-compose.yml down -v

# Shell Django
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py shell

# Créer une migration
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py makemigrations

# Appliquer les migrations
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py migrate

# Collecter les fichiers statiques
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py collectstatic --noinput

# Lancer les tests
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py test
```

### Production

Consultez [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) pour le guide complet.

```bash
# Déployer en production
./_devops/script/deploy.sh production

# Créer un backup de la base de données
./_devops/script/backup.sh
```

## 🎮 Comment Jouer

1. **Créer un compte** ou se connecter
2. **Créer une partie** et choisir une playlist Deezer
3. **Partager le code** de la salle avec vos amis
4. **Lancer la partie** une fois que tout le monde est prêt
5. **Répondre aux questions** le plus vite possible
6. **Consulter le classement** et la victoire ! 🏆

## 📊 Système de Scoring

- **Points de base** : jusqu'à 100 points (réduit avec le temps)
- **Formule de base** : `points = max(10, 100 - (temps_reponse * 3))`
- **Tolérance année** : facteur d'exactitude (1.0, 0.6, 0.3) applique sur les points
- **Bonus de rang** : +10 (1er), +5 (2e), +2 (3e) si bonne réponse
- **Mauvaise réponse** : 0 point

Exemple : 3 secondes = 91 points (hors bonus de rang)

## 🛠️ Services Docker

| Service     | Port | Description                    |
| ----------- | ---- | ------------------------------ |
| frontend    | 3000 | Interface React                |
| backend     | 8000 | API Django + WebSocket         |
| db          | 5432 | PostgreSQL                     |
| redis       | 6379 | Cache & Message Broker         |
| celery      | -    | Worker pour tâches asynchrones |
| celery-beat | -    | Planificateur de tâches        |

## 🧪 Tests

```bash
# Tests backend
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py test

# Tests avec couverture
docker compose -f _devops/docker/docker-compose.yml exec backend pytest --cov=apps --cov-report=html

# Tests frontend
docker compose -f _devops/docker/docker-compose.yml exec frontend npm test
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer de nouvelles fonctionnalités
- Soumettre des pull requests

## 📝 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 🔗 Liens Utiles

- [Documentation Django](https://docs.djangoproject.com/)
- [Documentation React](https://react.dev/)
- [API Deezer](https://developers.deezer.com/api)
- [Django Channels](https://channels.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)

---

**Développé avec ❤️ pour les amateurs de musique et de jeux**

## 📊 Monitoring

```bash
# Démarrer la stack monitoring (ELK + Prometheus + Grafana)
docker compose \
  -f _devops/docker/docker-compose.yml \
  -f _devops/docker/docker-compose.monitoring.yml \
  up -d
```

| Service       | URL                        | Identifiants   |
|---------------|----------------------------|----------------|
| Kibana        | http://localhost:5601       | —              |
| Grafana       | http://localhost:3001       | admin / admin  |
| Prometheus    | http://localhost:9090       | —              |
| Elasticsearch | http://localhost:9200       | —              |

La datasource **Prometheus** est provisionnée automatiquement dans Grafana.
Les logs applicatifs sont collectés via **Logstash** et indexés dans **Elasticsearch**.

## 🔍 CI/CD – GitHub Actions

Le pipeline `.github/workflows/ci.yml` exécute les jobs suivants sur chaque push/PR :

| Job             | Outil          | Description                              |
|-----------------|----------------|------------------------------------------|
| lint-python     | ruff + bandit  | Style PEP8, imports, sécurité Python     |
| lint-docker     | hadolint       | Bonnes pratiques Dockerfile              |
| lint-shell      | shellcheck     | Vérification des scripts shell           |
| lint-yaml       | yamllint       | Validation des fichiers YAML             |
| trivy-scan      | trivy          | Analyse de vulnérabilités des images     |
| sbom            | syft           | Génération de la SBOM (SPDX JSON)        |
| backend-tests   | pytest         | Tests unitaires Django                   |
| frontend-tests  | vitest         | Tests unitaires React                    |
