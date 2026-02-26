# DevOps — InstantMusic

Ce dossier regroupe tous les fichiers d'infrastructure, de déploiement et d'automatisation.

> Les workflows GitHub Actions restent dans `.github/workflows/` — requis par GitHub.

---

## Structure

```
_devops/
├── docker/
│   ├── docker-compose.yml              # Développement local
│   ├── docker-compose.prod.yml         # Production
│   ├── docker-compose.monitoring.yml   # Stack ELK + Prometheus + Grafana
│   └── docker-compose.override.yml.example
├── nginx/
│   ├── nginx.conf                      # Config Nginx production (HTTPS, rate-limit, proxy)
│   ├── instantmusic.conf.example       # Config hors Docker (installation système)
│   └── ssl/                            # Certificats SSL (non versionnés — gitignore)
├── monitoring/
│   ├── grafana/provisioning/           # Dashboards et datasources auto-provisionnés
│   ├── logstash/config/ + pipeline/    # Config et pipeline Logstash
│   └── prometheus/prometheus.yml       # Targets Prometheus
├── script/
│   ├── deploy.sh                       # Script de déploiement (dev/prod + options)
│   └── backup.sh                       # Sauvegarde PostgreSQL
└── linter/
    ├── .bandit.yml                     # Config Bandit (sécurité Python)
    ├── .hadolint.yaml                  # Config Hadolint (Dockerfiles)
    └── .yamllint.yml                   # Config Yamllint (fichiers YAML)
```

---

## Déploiement

### Commande unique (recommandée via Makefile)

```bash
# Production
make deploy-prod

# Développement
make deploy-dev

# État des services
make status

# Logs
make logs
make logs-backend

# Rollback
make rollback
```

### Script direct

```bash
# Production
./_devops/script/deploy.sh production

# Développement
./_devops/script/deploy.sh development

# Options
./_devops/script/deploy.sh production --no-pull    # Saute git pull
./_devops/script/deploy.sh production --no-cache   # Force rebuild sans cache
./_devops/script/deploy.sh production --status     # Affiche l'état des services
./_devops/script/deploy.sh production --logs       # Tous les logs
./_devops/script/deploy.sh production --logs backend  # Logs d'un service
./_devops/script/deploy.sh production --rollback   # Revient à l'image "previous"
```

Le script effectue dans l'ordre :
1. Tag des images actuelles comme `previous` (rollback safety)
2. `git pull`
3. Build des images Docker
4. `docker compose down --remove-orphans`
5. `docker compose up -d`
6. Attente de la santé du backend
7. `python manage.py migrate`
8. `python manage.py collectstatic`
9. En production : `seed_achievements`, `award_retroactive_achievements`, `recalculate_user_stats`
10. `docker image prune`

---

## Docker Compose

### Développement

```bash
docker compose -f _devops/docker/docker-compose.yml up -d
docker compose -f _devops/docker/docker-compose.yml logs -f
docker compose -f _devops/docker/docker-compose.yml down
```

Services : `db` (PostgreSQL :5433), `redis` (:6379), `backend` (:8000), `celery`, `celery-beat`, `frontend` (:3000)

### Production

```bash
# Déploiement via Makefile (recommandé)
make deploy-prod

# Ou manuellement
docker compose -f _devops/docker/docker-compose.prod.yml up -d
```

Services : identiques + `nginx` (:80/:443)

### Monitoring (optionnel)

```bash
make monitoring-up
```

| Service       | URL                         | Identifiants  |
|---------------|-----------------------------|---------------|
| Prometheus    | http://localhost:9090        | —             |
| Grafana       | http://localhost:3001        | admin / admin |
| Kibana        | http://localhost:5601        | —             |
| Elasticsearch | http://localhost:9200        | —             |

---

## Scripts

### `deploy.sh`

Voir section Déploiement ci-dessus. Supporte les options `--status`, `--logs`, `--rollback`, `--no-pull`, `--no-cache`.

### `backup.sh`

```bash
./_devops/script/backup.sh
# ou
make backup
```

Crée un dump `.sql.gz` de la base PostgreSQL dans `./backups/` avec horodatage.
Purge automatiquement les sauvegardes de plus de 30 jours.

---

## Linters

| Outil       | Config                               | Cible              |
|-------------|--------------------------------------|--------------------|
| ruff        | `pyproject.toml` (racine)            | `backend/`         |
| bandit      | `pyproject.toml` + `_devops/linter/.bandit.yml` | `backend/` |
| mypy        | `backend/pyproject.toml`             | `backend/`         |
| yamllint    | `_devops/linter/.yamllint.yml`       | tous les YAML      |
| hadolint    | `_devops/linter/.hadolint.yaml`      | Dockerfiles        |
| shellcheck  | (inline CI)                          | scripts `.sh`      |
| eslint      | `frontend/.eslintrc.json`            | `frontend/src/`    |
| prettier    | `frontend/.prettierrc`               | `frontend/src/`    |

Voir [docs/LINTERS.md](../docs/LINTERS.md) pour la documentation complète.
