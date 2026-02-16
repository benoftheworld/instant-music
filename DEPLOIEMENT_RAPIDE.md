# 🚀 Déploiement Rapide - InstantMusic

## TL;DR - Commandes Essentielles

```bash
# 1. Cloner et configurer
git clone <votre-repo>
cd instant-music
cp .env.prod.example .env.prod
nano .env.prod  # Configurer vos variables

# 2. Déployer
./deploy.sh production

# 3. Créer un admin
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 4. Voir les logs
docker compose -f docker-compose.prod.yml logs -f
```

## 📁 Fichiers de Configuration Créés

### Production
- `docker-compose.prod.yml` - Configuration Docker pour production
- `backend/Dockerfile.prod` - Image Docker optimisée backend
- `frontend/Dockerfile.prod` - Image Docker optimisée frontend  
- `nginx/nginx.conf` - Serveur web Nginx
- `.env.prod.example` - Template variables d'environnement

### Scripts Utiles
- `deploy.sh` - Script de déploiement automatique
- `backup.sh` - Script de sauvegarde DB

### Documentation
- `docs/PRODUCTION_DEPLOYMENT.md` - **Guide complet étape par étape**

## 🎯 Guide Complet

**👉 Consultez [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) pour le guide détaillé avec:**

- Configuration serveur complet
- Installation Docker
- Configuration SSL/HTTPS
- Configuration APIs (YouTube, OAuth)
- Monitoring et maintenance
- Dépannage
- Optimisations

## 📋 Checklist Rapide

### Avant le Déploiement

- [ ] Serveur avec Docker installé
- [ ] Nom de domaine configuré (DNS)
- [ ] YouTube API Key obtenue
- [ ] Google OAuth configuré
- [ ] Variables dans `.env.prod` remplies
- [ ] Certificat SSL obtenu (Let's Encrypt)

### Configuration Minimale `.env.prod`

```bash
# Essentiels à configurer
SECRET_KEY=<générer-avec-python>
ALLOWED_HOSTS=votredomaine.com
POSTGRES_PASSWORD=<mot-de-passe-fort>
YOUTUBE_API_KEY=<votre-clé>
GOOGLE_OAUTH_CLIENT_ID=<votre-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<votre-secret>
VITE_API_URL=https://votredomaine.com/api
VITE_WS_URL=wss://votredomaine.com/ws
```

## 🔧 Commandes Utiles

### Déploiement
```bash
# Production
./deploy.sh production

# Development
./deploy.sh development
```

### Maintenance
```bash
# Voir les logs
docker compose -f docker-compose.prod.yml logs -f [service]

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart [service]

# Backup DB
./backup.sh

# Accéder au shell Django
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# Migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Monitoring
```bash
# Status des containers
docker compose -f docker-compose.prod.yml ps

# Stats ressources
docker stats

# Health check
curl https://votredomaine.com/api/health/
```

## 🌐 Hébergeurs Recommandés

| Hébergeur | Prix/mois | Complexité | Recommandé pour |
|-----------|-----------|------------|-----------------|
| **Hetzner** | 5-20€ | Moyen | Meilleur rapport qualité/prix |
| **DigitalOcean** | 12-24$ | Moyen | Documentation excellente |
| **OVH** | 5-20€ | Moyen | Support français |
| **Railway** | 5-20$ | Facile | Déploiement rapide |
| **Render** | 7-25$ | Facile | CI/CD intégré |

## ⚡ Déploiement 1-Click (Railway/Render)

Pour un déploiement ultra-rapide sans serveur:

1. Fork le projet sur GitHub
2. Connectez Railway/Render à votre repo
3. Configurez les variables d'environnement
4. Deploy automatique à chaque push

## 🆘 Problèmes Fréquents

### "Cannot connect to database"
```bash
docker compose -f docker-compose.prod.yml restart db backend
```

### "502 Bad Gateway"
```bash
# Vérifier que le backend est démarré
docker compose -f docker-compose.prod.yml logs backend
```

### "Static files not found"
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## 📞 Support

Pour plus d'aide, consultez:
- Le guide complet: `docs/PRODUCTION_DEPLOYMENT.md`
- Les logs: `docker compose -f docker-compose.prod.yml logs`
- Documentation Django: https://docs.djangoproject.com
- Documentation Docker: https://docs.docker.com

---

**Bonne chance pour votre déploiement ! 🎉**
