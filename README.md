# 🎵 InstantMusic

Une application web interactive de jeux musicaux multijoueurs en temps réel.

## Fonctionnalités (MVP)
- Authentification (username/password + Google OAuth)
- Profil utilisateur (avatar, mot de passe, statistiques)
- Créer / rejoindre parties en ligne (lobby, WebSocket)
- Quiz musical (mode 4 réponses, rapide)
- Intégration Spotify (extraits 30s)
- Backoffice administration
- Docker pour dev & prod

Voir la documentation du projet pour la suite (configuration, tests, déploiement).

## 🚀 Démarrage rapide

```bash
# Application principale (dev)
docker compose up -d

# Stack de monitoring (ELK + Prometheus + Grafana)
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 📊 Monitoring

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