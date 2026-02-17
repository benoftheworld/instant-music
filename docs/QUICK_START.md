# 🚀 Guide de Démarrage Rapide

Guide ultra-rapide pour lancer InstantMusic en moins de 5 minutes.

## 📋 Prérequis

- Docker et Docker Compose installés
- Git

## ⚡ Installation Express (3 étapes)

### 1. Cloner et configurer

```bash
git clone https://github.com/benoftheworld/instant-music.git
cd instant-music
cp backend/.env.example backend/.env
```

### 2. Générer la clé secrète

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"
```
Copiez le résultat dans `backend/.env`.

### 3. Démarrer l'application

```bash
# Déployer en mode développement (build, up, migrations, static)
./_devops/script/deploy.sh development

# Pour déployer en production (si configuré) :
# ./_devops/script/deploy.sh production
```

✅ **C'est tout !** Accédez à http://localhost:3000

## 🎮 Premier Test

1. Créez un compte utilisateur sur http://localhost:3000
2. Cliquez sur "Créer une partie"
3. Recherchez une playlist (ex: "Top 50")
4. Sélectionnez une playlist Deezer
5. Copiez le code de la salle
6. Lancez la partie !

## 🔍 Vérification

### Services actifs

Le script `deploy.sh` affiche l'état des services à la fin du déploiement. Pour vérifier manuellement :

```bash
docker compose -f _devops/docker/docker-compose.yml ps
```

Tous les services doivent être "Up" :
- frontend (port 3000)
- backend (port 8000)
- db (PostgreSQL)
- redis
- celery
- celery-beat

### Logs en temps réel

```bash
# Tous les services
docker compose -f _devops/docker/docker-compose.yml logs -f

# Un service spécifique
docker compose -f _devops/docker/docker-compose.yml logs -f backend
```

### Tester l'API

```bash
# Health check
curl http://localhost:8000/api/health/

# Recherche de playlists (sans authentification)
curl http://localhost:8000/api/playlists/playlists/search/?q=rock
```

## ⚙️ Configuration Optionnelle

### Google OAuth (Connexion avec Google)

Si vous voulez activer la connexion via Google :

1. Créez un projet sur https://console.cloud.google.com
2. Configurez OAuth 2.0 (voir README principal)
3. Ajoutez dans `backend/.env` :
   ```
   GOOGLE_OAUTH_CLIENT_ID=votre_id
   GOOGLE_OAUTH_CLIENT_SECRET=votre_secret
   ```
4. Redémarrez : `docker compose -f _devops/docker/docker-compose.yml restart backend`

## 🛠️ Commandes Essentielles

```bash
# Arrêter l'application
docker compose -f _devops/docker/docker-compose.yml down

# Redémarrer un service
docker compose -f _devops/docker/docker-compose.yml restart backend

# Voir les logs
docker compose -f _devops/docker/docker-compose.yml logs -f backend

# Shell Django
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py shell

# Créer des données de test
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py loaddata fixtures/games.json
```

## ❗ Problèmes Courants

### Les migrations ne s'appliquent pas

La manière la plus simple est de relancer le déploiement (le script exécute les migrations) :

```bash
./_devops/script/deploy.sh development
```

Si vous devez forcer la réinitialisation des volumes puis redéployer (opération destructive) :

```bash
docker compose -f _devops/docker/docker-compose.yml down -v
./_devops/script/deploy.sh development
```

### Le frontend ne démarre pas

Relancer le déploiement (rebuild + up) règle souvent le problème :

```bash
./_devops/script/deploy.sh development
```

Pour voir les logs du frontend :

```bash
docker compose -f _devops/docker/docker-compose.yml logs -f frontend
```

### Problème de connexion à la base de données

Attendez que PostgreSQL soit complètement démarré :
```bash
docker compose -f _devops/docker/docker-compose.yml logs db | grep "ready to accept connections"
```

### Port déjà utilisé

Vérifiez qu'aucun service n'utilise les ports 3000, 8000, 5432, 6379 :
```bash
lsof -i :3000
lsof -i :8000
```

## 🔄 Réinitialisation Complète

Pour repartir de zéro :

```bash
# Tout supprimer (services + volumes)
docker compose -f _devops/docker/docker-compose.yml down -v

# Supprimer les images
docker compose -f _devops/docker/docker-compose.yml down --rmi all

# Redémarrer proprement
./_devops/script/deploy.sh development
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py migrate
docker compose -f _devops/docker/docker-compose.yml exec backend python manage.py createsuperuser
```

## 📚 Documentation Complète

Pour aller plus loin :
- **[README.md](../README.md)** - Documentation principale
- **[GAMEPLAY_SYSTEM.md](GAMEPLAY_SYSTEM.md)** - Système de jeu
- **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** - Déploiement production

## 🎯 Prochaines Étapes

1. ✅ Application lancée
2. 📝 Créer un compte admin
3. 👤 Créer des utilisateurs test
4. 🎮 Tester une partie complète
5. 🚀 Personnaliser et déployer !

---

**Besoin d'aide ?** Consultez les logs avec `docker compose -f _devops/docker/docker-compose.yml logs -f`
