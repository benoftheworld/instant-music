# 🔧 FIX : Erreur 400 Spotify Authentication

## ❌ Problème Identifié

Vos credentials Spotify dans `backend/.env` sont encore les valeurs par défaut :
- `SPOTIFY_CLIENT_ID=your-client-id` ❌
- `SPOTIFY_CLIENT_SECRET=your-client-secret` ❌

C'est pour ça que Spotify retourne une erreur **400 Bad Request**.

## ✅ Solution en 3 Étapes

### 1. Récupérez vos VRAIS credentials Spotify

1. Allez sur votre [Spotify Dashboard](https://developer.spotify.com/dashboard)
2. Cliquez sur votre application
3. Cliquez sur **"Settings"** (en haut à droite)
4. Vous verrez :
   - **Client ID** : `abc123...` (chaîne de ~32 caractères)
   - **Client secret** : Cliquez sur "View client secret" pour l'afficher

**COPIEZ ces deux valeurs !**

### 2. Modifiez le fichier `.env`

```bash
# Ouvrez le fichier avec nano ou votre éditeur
nano backend/.env
```

Remplacez les lignes :
```env
# AVANT (INCORRECT) ❌
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret

# APRÈS (CORRECT) ✅
SPOTIFY_CLIENT_ID=votre_vrai_client_id_depuis_spotify
SPOTIFY_CLIENT_SECRET=votre_vrai_client_secret_depuis_spotify
```

**Exemple avec de vraies valeurs** :
```env
SPOTIFY_CLIENT_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
SPOTIFY_CLIENT_SECRET=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4
```

Sauvegardez : `Ctrl+O` puis `Enter`, puis `Ctrl+X` pour quitter nano.

### 3. Redémarrez le backend

```bash
docker-compose restart backend
```

Attendez 5 secondes que le service redémarre.

## 🧪 Test

Après le redémarrage, testez à nouveau :

```bash
docker-compose exec backend python manage.py shell
```

Dans le shell Python :
```python
from apps.playlists.services import spotify_service
playlists = spotify_service.search_playlists('rock', limit=5)
print(f"Trouvé {len(playlists)} playlists!")
for p in playlists[:3]:
    print(f"- {p['name']} ({p['total_tracks']} morceaux)")
```

Si ça fonctionne, vous devriez voir :
```
Trouvé 5 playlists!
- Rock Classics (50 morceaux)
- Rock Hits (100 morceaux)
...
```

## 📝 Notes Importantes

### ⚠️ À propos des Redirect URIs

Vous avez configuré `http://127.0.0.1:3000/callback` dans les Redirect URIs de votre app Spotify. 

**C'est OK mais non nécessaire** pour notre cas ! Voici pourquoi :

- **Notre application** utilise le **Client Credentials Flow** (authentification d'application)
- Ce flow **ne nécessite PAS** de Redirect URI
- Les Redirect URIs sont utilisés pour le **Authorization Code Flow** (authentification utilisateur)

Donc pas besoin de toucher aux Redirect URIs, laissez-les comme ils sont.

### 🔑 API configurées

Vous avez sélectionné :
- ✅ Web API (nécessaire)
- ✅ Web Playback SDK (optionnel pour nous)

C'est parfait ! Web API est suffisant.

## 🚨 Sécurité

**NE JAMAIS** :
- Commiter le fichier `.env` avec vos credentials
- Partager vos credentials publiquement
- Les copier dans du code source

Le `.gitignore` est configuré pour exclure `.env` automatiquement.

## 📚 Ressources

- [Spotify Client Credentials Flow](https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/)
- [Spotify Dashboard](https://developer.spotify.com/dashboard)

---

Après avoir suivi ces étapes, l'intégration Spotify devrait fonctionner ! 🎉
