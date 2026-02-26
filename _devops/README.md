# 🛠️ DevOps – InstantMusic

Ce dossier regroupe tous les fichiers d'infrastructure et d'automatisation du projet.

## 📁 Structure

```
_devops/
├── docker/              # Docker Compose files
│   ├── docker-compose.yml              # Dev : tous les services
│   ├── docker-compose.prod.yml         # Production
│   ├── docker-compose.monitoring.yml   # Stack monitoring (ELK + Prometheus + Grafana)
│   └── docker-compose.override.yml.example
├── linter/              # Configuration des linters
│   └── .yamllint.yml   # Règles yamllint (utilisé par le CI)
└── script/              # Scripts de déploiement
    ├── deploy.sh        # Déploiement automatique (dev ou prod)
    └── backup.sh        # Sauvegarde PostgreSQL
```

> Les workflows GitHub Actions restent dans `.github/workflows/` conformément aux conventions GitHub.

---

## 🐳 Docker Compose

### Développement

```bash
# Démarrer tous les services
docker compose -f _devops/docker/docker-compose.yml up -d

# Voir les logs
docker compose -f _devops/docker/docker-compose.yml logs -f

# Arrêter
docker compose -f _devops/docker/docker-compose.yml down
```

### Production

```bash
# Déployer via le script (recommandé)
./_devops/script/deploy.sh production

# Ou manuellement
docker compose -f _devops/docker/docker-compose.prod.yml up -d
```

### Monitoring (optionnel)

```bash
docker compose \
  -f _devops/docker/docker-compose.yml \
  -f _devops/docker/docker-compose.monitoring.yml \
  up -d
```

Services exposés :

| Service       | URL                        | Identifiants   |
|---------------|----------------------------|----------------|
| Kibana        | http://localhost:5601       | —              |
| Grafana       | http://localhost:3001       | admin / admin  |
| Prometheus    | http://localhost:9090       | —              |
| Elasticsearch | http://localhost:9200       | —              |

---

## 📜 Scripts

### `deploy.sh`

```bash
# Déploiement en développement
./_devops/script/deploy.sh development

# Déploiement en production
./_devops/script/deploy.sh production
```

Le script effectue dans l'ordre : `git pull` → build des images → `down` → `up` → migrations → `collectstatic`.

En mode production : seed des achievements et recalcul des statistiques.

### `backup.sh`

```bash
./_devops/script/backup.sh
```

Crée un dump compressé de la base PostgreSQL dans `./backups/` et purge les fichiers de plus de 30 jours.

---

## 🔍 Linters

| Outil       | Fichier de config                     | Cible              |
|-------------|---------------------------------------|--------------------|
| ruff        | `pyproject.toml` (racine)             | `backend/`         |
| bandit      | —                                     | `backend/`         |
| yamllint    | `_devops/linter/.yamllint.yml`        | tous les fichiers  |
| hadolint    | —                                     | Dockerfiles        |
| shellcheck  | —                                     | scripts shell      |
| prettier    | `.pre-commit-config.yaml` (racine)    | `frontend/`        |
| black       | `backend/pyproject.toml`              | `backend/`         |

> Le fichier `.pre-commit-config.yaml` reste à la racine du dépôt — c'est requis par l'outil `pre-commit`.
