# Configuration Spotify API

Ce guide explique comment configurer l'intégration Spotify pour InstantMusic.

## Obtenir les credentials Spotify

1. **Créer un compte développeur Spotify**
   - Allez sur [Spotify for Developers](https://developer.spotify.com/)
   - Connectez-vous avec votre compte Spotify (ou créez-en un)

2. **Créer une application**
   - Accédez au [Dashboard](https://developer.spotify.com/dashboard)
   - Cliquez sur "Create app"
   - Remplissez les informations :
     - **App name**: InstantMusic
     - **App description**: Application de jeux musicaux multijoueurs
     - **Redirect URIs**: `http://localhost:3000/callback` (pour le développement)
     - **APIs used**: Web API
   - Acceptez les conditions et créez l'app

3. **Récupérer les credentials**
   - Dans le dashboard de votre app, cliquez sur "Settings"
   - Vous verrez :
     - **Client ID**: Copiez cette valeur
     - **Client Secret**: Cliquez sur "View client secret" et copiez

## Configuration de l'application

### Backend

1. Créez un fichier `.env` à partir de `.env.example` :
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **IMPORTANT** : Ouvrez `backend/.env` et **remplacez les valeurs par défaut** par vos **VRAIS** credentials Spotify :
   
   ```env
   # ❌ NE LAISSEZ PAS les valeurs par défaut !
   # SPOTIFY_CLIENT_ID=your-client-id
   # SPOTIFY_CLIENT_SECRET=your-client-secret
   
   # ✅ Remplacez par vos credentials depuis le dashboard Spotify
   SPOTIFY_CLIENT_ID=abc123def456ghi789...  # Votre vrai Client ID (32 caractères)
   SPOTIFY_CLIENT_SECRET=xyz987uvw654rst321...  # Votre vrai Client Secret (32 caractères)
   ```
   
   **Comment obtenir ces valeurs ?**
   - Allez sur votre [Spotify Dashboard](https://developer.spotify.com/dashboard)
   - Cliquez sur votre app
   - Cliquez sur **"Settings"**
   - Copiez le **Client ID**
   - Cliquez sur **"View client secret"** et copiez le **Client Secret**

3. Redémarrez le backend :
   ```bash
   docker-compose restart backend
   ```

### Frontend

Le frontend utilise déjà l'API backend, donc aucune configuration supplémentaire n'est nécessaire côté frontend.

## Test de l'intégration

1. **Démarrez les services** :
   ```bash
   docker-compose up -d
   ```

2. **Accédez à l'application** :
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api

3. **Testez la recherche de playlists** :
   - Connectez-vous à l'application
   - Cliquez sur "Créer une partie"
   - Cliquez sur "Sélectionner" sous la section Playlist
   - Recherchez une playlist (ex: "Top Hits")
   - Les résultats devraient s'afficher

## API Endpoints Disponibles

### Rechercher des playlists
```http
GET /api/playlists/playlists/search/?query=rock&limit=20
Authorization: Bearer {access_token}
```

### Obtenir une playlist
```http
GET /api/playlists/playlists/spotify/{spotify_id}/
Authorization: Bearer {access_token}
```

### Obtenir les morceaux d'une playlist
```http
GET /api/playlists/playlists/spotify/{spotify_id}/tracks/?limit=50
Authorization: Bearer {access_token}
```

### Obtenir un morceau
```http
GET /api/playlists/tracks/spotify/{spotify_id}/
Authorization: Bearer {access_token}
```

## Limites et Quotas

- **Client Credentials Flow**: Utilisé par l'application (pas de token utilisateur requis)
- **Rate Limiting**: Spotify limite les appels API
- **Cache Redis**: Implémenté pour réduire les appels API
  - Playlists: 30 minutes de cache
  - Tracks: 1 heure de cache
  - Token d'accès: 1 heure de cache

## Dépannage

### ❌ Erreur: "400 Bad Request" lors de l'authentification

**Symptôme** :
```
Failed to get Spotify access token: 400 Client Error: Bad Request
```

**Cause** : Vous avez laissé les valeurs par défaut dans `.env` au lieu de mettre vos vrais credentials.

**Solution** :
1. Vérifiez votre fichier `backend/.env` :
   ```bash
   cat backend/.env | grep SPOTIFY
   ```
2. Si vous voyez `your-client-id` ou `your-client-secret`, c'est le problème !
3. Remplacez-les par vos **VRAIS** credentials depuis le [Spotify Dashboard](https://developer.spotify.com/dashboard)
4. Redémarrez : `docker-compose restart backend`

**Note** : Les credentials doivent être des chaînes de ~32 caractères alphanumériques, pas les valeurs textuelles "your-client-id" !

### Erreur: "Spotify credentials not configured"
- Vérifiez que `SPOTIFY_CLIENT_ID` et `SPOTIFY_CLIENT_SECRET` sont définis dans `.env`
- Redémarrez le backend après modification du `.env`

### Erreur: "Failed to authenticate with Spotify"
- Vérifiez que vos credentials sont corrects (depuis le dashboard Spotify)
- Assurez-vous que votre app Spotify est en statut "Development" ou "Extended Quota Mode"
- Testez vos credentials manuellement avec curl (voir section Développement)

### Pas de résultats de recherche
- Vérifiez que Redis fonctionne : `docker-compose ps redis`
- Consultez les logs backend : `docker-compose logs backend`

### Preview audio non disponible
- Certains morceaux n'ont pas de preview (30 sec) disponible
- C'est une limitation de Spotify, pas de l'application

## Développement

### Tester l'API Spotify directement

**Dans le shell Django** :
```bash
# Dans le container backend
docker-compose exec backend python manage.py shell

# Testez le service
from apps.playlists.services import spotify_service
playlists = spotify_service.search_playlists('rock', limit=5)
print(f"Trouvé {len(playlists)} playlists!")
for p in playlists[:3]:
    print(f"- {p['name']}")
```

**Avec curl (test manuel des credentials)** :
```bash
# Remplacez YOUR_CLIENT_ID et YOUR_CLIENT_SECRET par vos vraies valeurs
CLIENT_ID="votre_client_id"
CLIENT_SECRET="votre_client_secret"

# Testez l'authentification
curl -X POST "https://accounts.spotify.com/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=client_credentials"

# Si ça fonctionne, vous obtiendrez un JSON avec "access_token"
# Si erreur 400, vos credentials sont incorrects
```

## Production

Pour la production, n'oubliez pas de :
1. Modifier les "Redirect URIs" dans le dashboard Spotify avec votre domaine
2. Utiliser des variables d'environnement sécurisées
3. Activer le rate limiting côté Django
4. Monitorer les appels API Spotify

## Ressources

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Client Credentials Flow](https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/)
- [API Reference](https://developer.spotify.com/documentation/web-api/reference/)
