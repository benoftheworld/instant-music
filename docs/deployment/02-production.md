# Déploiement en production — Guide complet

## Vue d'ensemble

En production, l'architecture est renforcée pour la performance, la sécurité et la haute disponibilité. Les différences principales par rapport au développement :

| Aspect          | Développement   | Production                  |
| --------------- | --------------- | --------------------------- |
| HTTPS           | Non             | Oui (Certbot/Let's Encrypt) |
| Build frontend  | Vite dev server | Nginx statique              |
| Backend         | runserver (dev) | Gunicorn + uvicorn workers  |
| DEBUG           | True            | False                       |
| Base de données | Volume Docker   | Volume persistant + backups |
| Variables d'env | .env (local)    | .env.prod (serveur)         |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE PRODUCTION                            │
│                                                                         │
│   Internet                                                              │
│      │ :443 HTTPS                                                       │
│      ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  Nginx (reverse proxy + SSL termination)                        │  │
│   │                                                                 │  │
│   │  /              → Frontend (SPA statique, nginx:alpine)         │  │
│   │  /api/          → Backend (Gunicorn :8000)                      │  │
│   │  /ws/           → Backend (uvicorn ASGI WebSocket)              │  │
│   │  /admin/        → Backend (Django Admin)                        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  Backend (Gunicorn + uvicorn)    Celery Workers                 │   │
│   └───────────────────┬──────────────────────────────────────────┘    │
│                        │                                               │
│   ┌────────────────────┼──────────────────────────────────────────┐   │
│   │  PostgreSQL 15     │  Redis                                    │   │
│   └────────────────────┴──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prérequis serveur

### Configuration recommandée

- **OS** : Ubuntu 22.04 LTS
- **RAM** : 4 GB minimum (8 GB recommandé)
- **CPU** : 2 vCPUs minimum
- **Disque** : 50 GB SSD
- **Réseau** : IP fixe ou domaine configuré

### Logiciels à installer

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER  # Ajouter l'utilisateur au groupe docker
newgrp docker  # Recharger le groupe

# Vérifier
docker --version
docker compose version

# Make
sudo apt install make -y

# Git
sudo apt install git -y
```

### Configuration DNS

Avant de déployer, configurez votre domaine :

```
Type A :  instantmusic.example.com  →  IP_DE_VOTRE_SERVEUR
```

Vérifiez la propagation DNS :
```bash
nslookup instantmusic.example.com
dig instantmusic.example.com A
```

---

## Configuration des variables d'environnement production

Créez le fichier `.env.prod` sur le serveur (ne jamais le committer dans Git !) :

```bash
# ─── Django ─────────────────────────────────────────────────────────
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<clé-secrète-longue-et-aléatoire>   # 50+ caractères
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=instantmusic.example.com,www.instantmusic.example.com

# ─── Base de données ────────────────────────────────────────────────
POSTGRES_DB=instantmusic_prod
POSTGRES_USER=instantmusic_prod
POSTGRES_PASSWORD=<mot-de-passe-très-fort>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ─── Redis ──────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ─── CORS ───────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=https://instantmusic.example.com

# ─── JWT ────────────────────────────────────────────────────────────
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7

# ─── Email (prod) ───────────────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@instantmusic.example.com
EMAIL_HOST_PASSWORD=<mot-de-passe-app-gmail>

# ─── APIs externes ──────────────────────────────────────────────────
DEEZER_API_KEY=<votre-clé-deezer>
GOOGLE_CLIENT_ID=<votre-client-id-google>
GOOGLE_CLIENT_SECRET=<votre-secret-google>

# ─── Monitoring (optionnel) ─────────────────────────────────────────
SENTRY_DSN=https://xxx@sentry.io/xxx

# ─── SSL ────────────────────────────────────────────────────────────
DOMAIN=instantmusic.example.com
LETSENCRYPT_EMAIL=admin@instantmusic.example.com
```

### Générer une clé secrète Django

```bash
python3 -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
"
```

---

## Configuration SSL avec Certbot

InstantMusic utilise Let's Encrypt pour les certificats SSL gratuits.

### Initialisation SSL (première fois)

```bash
# Si make ssl-init est disponible :
make ssl-init

# Sinon, manuellement :
docker compose -f _devops/docker/docker-compose.ssl-init.yml up
```

Ce processus :
1. Lance un conteneur Certbot temporaire
2. Défie Let's Encrypt via HTTP (port 80)
3. Télécharge et stocke les certificats dans `_devops/certbot/`
4. Configure Nginx pour HTTPS

```
_devops/certbot/
├── conf/
│   └── live/
│       └── instantmusic.example.com/
│           ├── cert.pem       ← Certificat
│           ├── privkey.pem    ← Clé privée
│           └── fullchain.pem  ← Chaîne complète
└── www/                       ← Challenge HTTP
```

### Renouvellement automatique des certificats

Let's Encrypt expire après 90 jours. Configurez un cron pour le renouvellement :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (renouvellement tous les dimanches à 3h)
0 3 * * 0 cd /path/to/instant-music && docker compose -f _devops/docker/docker-compose.ssl-renew.yml up >> /var/log/certbot-renew.log 2>&1
```

---

## Déploiement

### Premier déploiement

```bash
# 1. Cloner le repo sur le serveur
git clone https://github.com/votre-org/instant-music.git
cd instant-music

# 2. Créer le fichier .env.prod (voir section précédente)
nano .env.prod

# 3. Initialiser SSL
make ssl-init

# 4. Lancer l'environnement de production
docker compose -f _devops/docker/docker-compose.prod.yml up -d

# 5. Appliquer les migrations
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py migrate

# 6. Collecter les fichiers statiques
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py collectstatic --noinput

# 7. Créer le superutilisateur
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py createsuperuser

# 8. Charger les données initiales
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py seed_achievements
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py seed_shop
```

### Configuration Nginx en production

```nginx
# _devops/nginx/nginx.conf (structure simplifiée)
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name instantmusic.example.com;

    # Redirection HTTP → HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name instantmusic.example.com;

    # Certificats SSL
    ssl_certificate     /etc/letsencrypt/live/instantmusic.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/instantmusic.example.com/privkey.pem;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;

    # Frontend (SPA statique)
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;  # Gère les routes SPA
    }

    # API REST
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;  # Essentiel pour WS
        proxy_set_header Connection "upgrade";
    }

    # Admin
    location /admin/ {
        proxy_pass http://backend;
    }
}
```

---

## Mise à jour de l'application

### Workflow de mise à jour standard

```bash
# 1. Récupérer le code le plus récent
git pull origin main

# 2. Rebuilder les images si nécessaire
docker compose -f _devops/docker/docker-compose.prod.yml build

# 3. Redémarrer les services (rolling restart)
docker compose -f _devops/docker/docker-compose.prod.yml up -d --no-deps backend
docker compose -f _devops/docker/docker-compose.prod.yml up -d --no-deps frontend

# 4. Appliquer les migrations
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py migrate

# 5. Collecter les fichiers statiques (si frontend a changé)
docker compose -f _devops/docker/docker-compose.prod.yml exec backend \
  python manage.py collectstatic --noinput

# 6. Vérifier que tout tourne
docker compose -f _devops/docker/docker-compose.prod.yml ps
```

---

## Sauvegarde de la base de données

### Script de backup (`_devops/script/backup.sh`)

```bash
#!/bin/bash
# _devops/script/backup.sh

# Configuration
BACKUP_DIR="/var/backups/instantmusic"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="_devops/docker/docker-compose.prod.yml"

# Créer le répertoire de backup
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U instantmusic_prod instantmusic_prod | \
  gzip > "$BACKUP_DIR/db_backup_${DATE}.sql.gz"

echo "Backup créé : $BACKUP_DIR/db_backup_${DATE}.sql.gz"

# Supprimer les backups de plus de 30 jours
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
echo "Anciens backups nettoyés."
```

### Automatiser les backups

```bash
# Crontab : backup tous les jours à 2h
crontab -e
0 2 * * * /path/to/instant-music/_devops/script/backup.sh >> /var/log/instantmusic-backup.log 2>&1
```

### Restaurer un backup

```bash
# Arrêter le backend pour éviter les écritures pendant la restauration
docker compose -f _devops/docker/docker-compose.prod.yml stop backend celery

# Restaurer
gunzip -c /var/backups/instantmusic/db_backup_20260307_020000.sql.gz | \
  docker compose -f _devops/docker/docker-compose.prod.yml exec -T db \
  psql -U instantmusic_prod instantmusic_prod

# Redémarrer
docker compose -f _devops/docker/docker-compose.prod.yml start backend celery
```

---

## Monitoring optionnel en production

```bash
# Lancer le monitoring en plus de l'application
docker compose \
  -f _devops/docker/docker-compose.prod.yml \
  -f _devops/docker/docker-compose.monitoring.yml \
  up -d

# Accès Grafana (accessible uniquement via VPN ou SSH tunnel en prod)
# ssh -L 3001:localhost:3001 user@serveur
# → http://localhost:3001 sur votre machine locale
```

---

## Vérifications post-déploiement

```bash
# 1. Tous les services tournent
docker compose -f _devops/docker/docker-compose.prod.yml ps

# 2. L'API répond
curl -s https://instantmusic.example.com/api/health/ | python3 -m json.tool

# 3. Le frontend est accessible
curl -s -o /dev/null -w "%{http_code}" https://instantmusic.example.com/

# 4. L'admin est accessible
curl -s -o /dev/null -w "%{http_code}" https://instantmusic.example.com/admin/

# 5. Vérifier les logs d'erreur
docker compose -f _devops/docker/docker-compose.prod.yml logs --tail=100 backend | grep ERROR
```

---

## Sécurité — Checklist production

```
Avant de mettre en production :

[ ] DJANGO_DEBUG = False
[ ] DJANGO_SECRET_KEY unique et forte (50+ caractères)
[ ] ALLOWED_HOSTS configuré avec votre domaine uniquement
[ ] HTTPS activé et certificats valides
[ ] Headers de sécurité HTTP configurés dans Nginx
[ ] Mot de passe PostgreSQL fort et unique
[ ] Backups automatisés et testés
[ ] Firewall configuré (ports 80 et 443 uniquement exposés)
[ ] Accès SSH par clé uniquement (désactiver mot de passe)
[ ] Monitoring des erreurs activé (Sentry ou ELK)
[ ] Rate limiting sur l'API (Nginx ou Django)
[ ] CORS configuré pour votre domaine uniquement
```
