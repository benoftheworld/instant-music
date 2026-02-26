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
- Google Cloud Console (OAuth)
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

### 2.5 Achievements (initialisation et rétroactivité)

Les achievements (succès) sont définis dans le code et doivent être initialisés en base.
Après un déploiement initial ou si vous ajoutez/modifiez des achievements, exécutez :

```bash
# Seed des achievements (crée les définitions si elles n'existent pas)
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py seed_achievements

# Optionnel : attribuer rétroactivement les achievements aux utilisateurs
# (vérifie l'historique des parties et peut prendre du temps selon le nombre d'utilisateurs)
docker compose -f _devops/docker/docker-compose.prod.yml exec backend python manage.py award_retroactive_achievements
```

Le script de déploiement `./_devops/script/deploy.sh` exécute désormais automatiquement
`seed_achievements` et `award_retroactive_achievements` lors d'un déploiement en production.
Si vous préférez contrôler ces commandes manuellement (par exemple en raison du temps d'exécution),
éditez le script de déploiement ou exécutez les commandes séparément depuis le serveur.

```

---

## 🔒 Étape 3: Configuration SSL (HTTPS)

Les certificats sont gérés automatiquement par un service `certbot` Docker intégré.
Le renouvellement se fait toutes les 12h sans intervention manuelle.

### 3.1 Obtenir le certificat initial (première installation)

```bash
# S'assurer que le port 80 est libre et accessible depuis Internet (DNS configuré)
make ssl-init DOMAIN=benoftheworld.fr EMAIL=admin@benoftheworld.fr
```

Cette commande :
1. Démarre nginx en mode HTTP-only (pas de SSL requis)
2. Exécute certbot qui complète le challenge ACME via webroot
3. Stocke les certs dans un volume Docker `instantmusic_letsencrypt`
4. Redémarre nginx avec la config SSL complète

### 3.2 Vérifier l'état du certificat

```bash
make ssl-status
```

### 3.3 Renouvellement (normalement automatique)

Le service `certbot` tourne en arrière-plan et renouvelle automatiquement.
Pour forcer un renouvellement manuel :

```bash
make ssl-renew
```

### 3.4 Redémarrer nginx après modification de la config

```bash
docker compose -f _devops/docker/docker-compose.prod.yml restart nginx
```

> **Note** : La section SSL dans `_devops/nginx/nginx.conf` référence
> `/etc/letsencrypt/live/benoftheworld.fr/fullchain.pem` qui est monté
> depuis le volume Docker `instantmusic_letsencrypt`.


---

## 🔍 Étape 4: Configuration des APIs

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
