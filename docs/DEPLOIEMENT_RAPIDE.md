# Déploiement Rapide — InstantMusic

> Pour le guide complet : [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

---

## TL;DR — Depuis votre VPS

```bash
# 1. Cloner
git clone https://github.com/benoftheworld/instant-music.git
cd instant-music

# 2. Configurer
cp .env.prod.example .env.prod
nano .env.prod  # Renseigner les variables déployement

# 3. Déployer (une seule commande)
make deploy-prod
```

---

## Checklist pré-déploiement

- [ ] Serveur Ubuntu 20.04+ avec Docker 24+ et Docker Compose v2
- [ ] Nom de domaine pointant vers le serveur (enregistrement A/AAAA)
- [ ] Port 80 et 443 ouverts dans le pare-feu
- [ ] Certificat SSL Let's Encrypt configuré (voir guide complet)
- [ ] Fichier `.env.prod` rempli

### Variables minimales dans `.env.prod`

```bash
SECRET_KEY=<générer: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ALLOWED_HOSTS=votredomaine.com
POSTGRES_PASSWORD=<mot-de-passe-fort>
VITE_API_URL=https://votredomaine.com/api
VITE_WS_URL=wss://votredomaine.com/ws
```

---

## Commandes utiles (Makefile)

```bash
make deploy-prod          # Déployer / mettre à jour
make status               # État des services
make logs                 # Logs en temps réel
make logs-backend         # Logs backend uniquement
make rollback             # Revenir à la version précédente
make backup               # Sauvegarder la base de données
make prod-createsuperuser # Créer un compte admin
```

## Script direct (sans Makefile)

```bash
# Déploiement production
./_devops/script/deploy.sh production

# Développement local
./_devops/script/deploy.sh development

# Options disponibles
./_devops/script/deploy.sh production --no-pull   # Sans git pull
./_devops/script/deploy.sh production --status    # État des services
./_devops/script/deploy.sh production --logs      # Tous les logs
./_devops/script/deploy.sh production --logs backend  # Logs d'un service
./_devops/script/deploy.sh production --rollback  # Rollback
```

---

## Fichiers de configuration clés

| Fichier                                  | Usage                              |
|------------------------------------------|------------------------------------|
| `_devops/docker/docker-compose.prod.yml` | Orchestration production           |
| `_devops/docker/docker-compose.yml`      | Orchestration développement        |
| `_devops/nginx/nginx.conf`               | Reverse proxy Nginx                |
| `_devops/nginx/ssl/`                     | Certificats SSL (non versionnés)   |
| `_devops/script/deploy.sh`               | Script de déploiement              |
| `.env.prod`                              | Variables d'environnement prod     |
