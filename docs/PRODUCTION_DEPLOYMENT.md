# 🚀 Guide de Déploiement en Production - InstantMusic

Ce guide détaille les étapes pour déployer InstantMusic en production sur un serveur.

## 📋 Prérequis

### Serveur
- **OS**: Ubuntu 20.04+ / Debian 11+ (recommandé)
- **RAM**: Minimum 2GB, recommandé 4GB+
- **CPU**: 2 cores minimum
- **Stockage**: 20GB minimum
- **Accès**: SSH avec droits sudo

### Logiciels requis
- Docker 24.0+
- Docker Compose v2.20+
- Git
- Un nom de domaine (pour SSL/HTTPS)

### Comptes/API
- Google Cloud Console (YouTube API + OAuth)
- Serveur SMTP ou Gmail pour les emails
- (Optionnel) Sentry pour le monitoring

---

## 🔧 Étape 1: Préparation du Serveur

### 1.1 Connexion et mise à jour

```bash
ssh user@your-server-ip

# Mise à jour du système
sudo apt update && sudo apt upgrade -y
```

### 1.2 Installation de Docker

```bash
# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Installation de Docker Compose
sudo apt install docker-compose-plugin -y

# Vérification
docker --version
docker compose version
```

### 1.3 Configuration du Firewall

```bash
# Autoriser SSH, HTTP et HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📦 Étape 2: Déploiement de l'Application

### 2.1 Cloner le projet

```bash
# Créer un dossier pour l'application
mkdir -p ~/apps
cd ~/apps

# Cloner le repository (remplacer par votre URL)
git clone https://github.com/votre-username/instant-music.git
cd instant-music
```

### 2.2 Configuration des variables d'environnement

```bash
# Copier le fichier exemple
cp .env.prod.example .env.prod

# Éditer avec vos valeurs
nano .env.prod
```

**Valeurs importantes à configurer:**

```bash
# Générer une SECRET_KEY sécurisée
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Remplir dans .env.prod:
SECRET_KEY=<la-clé-générée>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_PASSWORD=<mot-de-passe-fort>
GOOGLE_OAUTH_CLIENT_ID=<votre-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<votre-client-secret>
VITE_API_URL=https://yourdomain.com/api
VITE_WS_URL=wss://yourdomain.com/ws
```

### 2.3 Build et lancement

```bash
# Build des images Docker
docker compose -f _devops/docker/docker-compose.prod.yml build

# Lancement des containers
docker compose -f _devops/docker/docker-compose.prod.yml up -d

# Vérifier que tout fonctionne
docker compose -f _devops/docker/docker-compose.prod.yml ps
```

### 2.4 Migrations et superuser

```bash
# Appliquer les migrations
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py migrate

# Créer un superutilisateur
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py createsuperuser

# Collecter les fichiers statiques
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 🔒 Étape 3: Configuration SSL (HTTPS)

### Option A: Let's Encrypt avec Certbot (Recommandé)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx -y

# Créer le dossier SSL
mkdir -p nginx/ssl

# Obtenir un certificat SSL
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copier les certificats dans le dossier nginx
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chmod 644 nginx/ssl/*.pem

# Renouvellement automatique
sudo crontab -e
# Ajouter: 0 0 1 * * certbot renew --quiet && docker compose -f /root/apps/instant-music/_devops/docker/docker-compose.prod.yml restart nginx
```

### Option B: Cloudflare (Alternative)

Si vous utilisez Cloudflare, activez:
- SSL/TLS → Full (strict)
- Automatic HTTPS Rewrites
- Always Use HTTPS

### 3.1 Activer HTTPS dans Nginx

Éditez `nginx/nginx.conf` et décommentez la section HTTPS:

```bash
nano nginx/nginx.conf

# Décommenter le bloc:
# server {
#     listen 443 ssl http2;
#     ...
# }

# Et activer la redirection HTTP → HTTPS dans le bloc server listen 80
```

Redémarrez Nginx:

```bash
docker compose -f _devops/docker/docker-compose.prod.yml restart nginx
```

---

## 🔍 Étape 4: Configuration des APIs

### 4.1 YouTube Data API

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer **YouTube Data API v3**
4. Créer des identifiants (Clé API)
5. Copier la clé dans `.env.prod` → `YOUTUBE_API_KEY`

### 4.2 Google OAuth

1. Toujours dans Google Cloud Console
2. Aller dans **APIs & Services** → **OAuth consent screen**
3. Configurer l'écran de consentement
4. Aller dans **Credentials** → **Create OAuth 2.0 Client ID**
5. Type: **Web application**
6. Authorized redirect URIs:
   - `https://yourdomain.com/api/auth/google/callback`
   - `http://localhost:3000/api/auth/google/callback` (dev)
7. Copier Client ID et Secret dans `.env.prod`

---

## 📧 Étape 5: Configuration Email (Gmail)

```bash
# Si vous utilisez Gmail:
# 1. Activer l'authentification à 2 facteurs
# 2. Générer un mot de passe d'application
# 3. Configurer dans .env.prod:

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

---

## 🔄 Étape 6: Mises à jour

### Déployer une nouvelle version

```bash
cd ~/apps/instant-music

# Pull les dernières modifications
git pull origin main

# Rebuild et redémarrer
docker compose -f _devops/docker/docker-compose.prod.yml build
docker compose -f _devops/docker/docker-compose.prod.yml up -d

# Appliquer les migrations si nécessaire
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py migrate

# Collecter les nouveaux fichiers statiques
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 📊 Étape 7: Monitoring et Maintenance

### Logs

```bash
# Voir tous les logs
docker compose -f _devops/docker/docker-compose.prod.yml logs -f

# Logs d'un service spécifique
docker compose -f _devops/docker/docker-compose.prod.yml logs -f backend
docker compose -f _devops/docker/docker-compose.prod.yml logs -f nginx

# Logs avec limite
docker compose -f _devops/docker/docker-compose.prod.yml logs --tail=100 backend
```

### Backup de la base de données

```bash
# Créer un backup
docker compose -f _devops/docker/docker-compose.prod.yml exec db pg_dump -U instantmusic_user instantmusic_prod > backup_$(date +%Y%m%d).sql

# Restaurer un backup
cat backup_20260216.sql | docker compose -f _devops/docker/docker-compose.prod.yml exec -T db psql -U instantmusic_user instantmusic_prod
```

### Nettoyage Docker

```bash
# Supprimer les images inutilisées
docker system prune -a

# Voir l'utilisation disque
docker system df
```

---

## 🔐 Étape 8: Sécurité

### 8.1 Sécuriser PostgreSQL

```bash
# Changer le mot de passe par défaut dans .env.prod
POSTGRES_PASSWORD=<très-fort-mot-de-passe>
```

### 8.2 Limiter l'accès SSH

```bash
# Désactiver login root
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Utiliser des clés SSH au lieu de mots de passe
# PasswordAuthentication no

sudo systemctl restart ssh
```

### 8.3 Fail2Ban (protection brute force)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## ⚡ Optimisations de Performance

### 1. Activer Redis Cache

Déjà configuré dans le projet avec Celery et channels.

### 2. CDN pour les fichiers statiques (Optionnel)

Configurez un CDN comme Cloudflare ou AWS CloudFront pour servir:
- `/static/`
- `/media/`
- Assets du frontend

### 3. Augmenter les workers

Éditez `docker-compose.prod.yml` pour augmenter les replicas Celery:

```yaml
celery:
  deploy:
    replicas: 2  # Ajuster selon votre charge
```

---

## 🐛 Dépannage

### Le site ne charge pas

```bash
# Vérifier les containers
docker compose -f _devops/docker/docker-compose.prod.yml ps

# Vérifier les logs
docker compose -f _devops/docker/docker-compose.prod.yml logs nginx
docker compose -f _devops/docker/docker-compose.prod.yml logs backend
```

### Erreur 502 Bad Gateway

```bash
# Le backend n'est probablement pas démarré
docker compose -f _devops/docker/docker-compose.prod.yml restart backend

# Vérifier la santé du backend
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py check
```

### WebSocket ne fonctionne pas

```bash
# Vérifier la configuration Nginx (section /ws/)
# Vérifier Redis
docker compose -f _devops/docker/docker-compose.prod.yml exec redis redis-cli ping
```

---

## 📱 Étape 9: Configuration du Domaine

### Configuration DNS

Chez votre registrar (Namecheap, OVH, etc.):

```
Type    Name    Value           TTL
A       @       <IP-SERVER>     3600
A       www     <IP-SERVER>     3600
CNAME   *       yourdomain.com  3600
```

Attendez la propagation DNS (peut prendre jusqu'à 48h).

---

## ✅ Checklist Finale

- [ ] Docker et Docker Compose installés
- [ ] Variables d'environnement configurées dans `.env.prod`
- [ ] HTTPS/SSL configuré avec certificat valide
- [ ] YouTube API activée et clé configurée
- [ ] Google OAuth configuré avec redirect URIs corrects
- [ ] Email SMTP configuré
- [ ] Migrations appliquées
- [ ] Superuser créé
- [ ] Firewall configuré (ports 80, 443, 22)
- [ ] Backup automatique de la base de données
- [ ] Monitoring des logs en place
- [ ] DNS configuré et propagé

---

## 🎯 URLs Finales

Une fois déployé:

- **Frontend**: https://yourdomain.com
- **API**: https://yourdomain.com/api
- **Admin Django**: https://yourdomain.com/admin
- **WebSocket**: wss://yourdomain.com/ws

---

## 📞 Support

Si vous rencontrez des problèmes:
1. Consultez les logs: `docker compose -f _devops/docker/docker-compose.prod.yml logs`
2. Vérifiez la documentation Django et React
3. Testez en développement d'abord

---

## 🚀 Hébergeurs Recommandés

### Option 1: VPS Traditionnels
- **DigitalOcean**: $12-24/mois (Droplet)
- **Hetzner**: €4-16/mois (Cloud Server)
- **OVH**: €5-20/mois (VPS)
- **Linode**: $12-24/mois

### Option 2: Cloud Platform
- **AWS**: EC2 + RDS
- **Google Cloud**: Compute Engine + Cloud SQL
- **Azure**: Virtual Machines + Database

### Option 3: Platform as a Service (plus simple)
- **Railway**: Deploy in 1 click
- **Render**: Support Docker Compose
- **Fly.io**: Edge computing

---

**Félicitations ! Votre application InstantMusic est maintenant en production ! 🎉**
