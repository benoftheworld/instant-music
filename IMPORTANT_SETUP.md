# ⚠️ IMPORTANT - Configuration Requise

## 🔑 Credentials Spotify Obligatoires

Pour que l'application fonctionne correctement, vous **DEVEZ** configurer vos credentials Spotify :

### 1. Obtenir les Credentials

Suivez le guide détaillé dans [SPOTIFY_SETUP.md](./SPOTIFY_SETUP.md) pour :
- Créer un compte développeur Spotify
- Créer une application Spotify
- Obtenir votre `Client ID` et `Client Secret`

### 2. Configuration

**Créez un fichier `.env`** dans le dossier `backend/` :

```bash
cp backend/.env.example backend/.env
```

**Modifiez** `backend/.env` et ajoutez vos credentials :

```env
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

### 3. Redémarrage

Après avoir configuré les credentials, redémarrez les services :

```bash
docker-compose restart backend
```

## 🧪 Tester l'Intégration

### Méthode 1 : Via l'Interface Web

1. Accédez à http://localhost:3000
2. Connectez-vous
3. Cliquez sur "Créer une partie"
4. Essayez de chercher une playlist (ex: "Top Hits")
5. Les résultats devraient s'afficher

### Méthode 2 : Via l'API

```bash
# Obtenez un token JWT
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Utilisez le token pour rechercher des playlists
curl -X GET "http://localhost:8000/api/playlists/playlists/search/?query=rock" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## ❌ Erreurs Courantes

### "Spotify credentials not configured"
**Solution** : Vérifiez que `SPOTIFY_CLIENT_ID` et `SPOTIFY_CLIENT_SECRET` sont bien définis dans `backend/.env`

### "Failed to authenticate with Spotify"
**Causes possibles** :
- Credentials incorrects → Vérifiez sur le dashboard Spotify
- Problème réseau → Vérifiez votre connexion internet
- App Spotify non activée → Assurez-vous que l'app est en statut "Development"

### Pas de résultats de recherche
**Solutions** :
- Vérifiez que Redis fonctionne : `docker-compose ps redis`
- Consultez les logs : `docker-compose logs backend`
- Vérifiez les credentials Spotify

## 📝 Notes Importantes

### Limitations Spotify API
- **Mode gratuit** : 30 secondes de preview audio uniquement
- **Rate limiting** : Spotify limite le nombre d'appels
- **Cache** : Implémenté pour réduire la charge API

### Sécurité
- **NE JAMAIS** commiter le fichier `.env` avec vos credentials
- Le `.gitignore` est configuré pour l'exclure automatiquement
- En production, utilisez des variables d'environnement sécurisées

### Redis
Redis est utilisé pour :
- Cache des appels Spotify (performances)
- WebSocket (Django Channels)
- Celery (tâches asynchrones)

Si Redis ne fonctionne pas, l'application ne pourra pas :
- Mettre en cache les playlists
- Gérer le temps réel (WebSocket)

## 🚀 Workflow de Développement

### Démarrer l'application
```bash
docker-compose up -d
```

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Backend uniquement
docker-compose logs -f backend

# Frontend uniquement  
docker-compose logs -f frontend
```

### Arrêter l'application
```bash
docker-compose down
```

### Rebuild après modifications
```bash
docker-compose up -d --build
```

## 📚 Ressources

- [SPOTIFY_SETUP.md](./SPOTIFY_SETUP.md) - Guide complet de configuration Spotify
- [SPRINT5_RECAP.md](./SPRINT5_RECAP.md) - Récapitulatif de l'implémentation
- [README.md](./README.md) - Documentation générale du projet

## ✅ Checklist Avant de Continuer

- [ ] Credentials Spotify configurés dans `.env`
- [ ] Services démarrés : `docker-compose ps` (tous "Up")
- [ ] Backend accessible : http://localhost:8000/api
- [ ] Frontend accessible : http://localhost:3000
- [ ] Recherche de playlists fonctionnelle
- [ ] Redis opérationnel
- [ ] Migrations appliquées

## 🎯 Prochaine Étape

Une fois la configuration Spotify validée, vous pouvez passer au **Sprint 6-7 : Quiz Musical** pour implémenter la logique de jeu !

---

**Besoin d'aide ?** Consultez les logs avec `docker-compose logs` ou référez-vous aux guides détaillés.
