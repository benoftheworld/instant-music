# ⚡ Quick Start - OAuth 2.0 Spotify

## 🎯 Setup Rapide (5 minutes)

### Étape 1: Configuration Spotify Dashboard

1. **Allez sur** https://developer.spotify.com/dashboard
2. **Connectez-vous** avec votre compte Spotify
3. **Cliquez** sur "Create an App"
4. **Remplissez:**
   - Name: `InstantMusic`
   - Description: `Application de quiz musical`
   - Redirect URI: `http://localhost:8000/api/playlists/spotify/callback/`
   - ✅ Cochez "Web API"
5. **Créez** l'application

### Étape 2: Variables d'Environnement

1. **Copiez** le Client ID et Client Secret
2. **Modifiez** `backend/.env`:

```bash
# Spotify OAuth 2.0
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/playlists/spotify/callback/
FRONTEND_URL=http://localhost:5173
```

### Étape 3: Redémarrer

```bash
cd /home/benoftheworld/instant-music
docker compose restart backend
```

### Étape 4: Tester !

1. **Ouvrez** http://localhost:5173
2. **Connectez-vous** à votre compte InstantMusic
3. **Allez** sur `/profile`
4. **Cliquez** sur "Connecter avec Spotify"
5. **Autorisez** dans la popup
6. **✅ C'est fait !** Badge vert "Actif" visible

---

## 🎮 Utilisation

### Accès Complet aux Playlists

Une fois connecté avec Spotify:

✅ **Toutes les playlists publiques** accessibles  
✅ **Vos playlists privées** accessibles  
✅ **Plus d'erreurs 403**  
✅ **Meilleure expérience de jeu**

### Flow Utilisateur

```
1. Profile Page
   ↓
2. Click "Connecter avec Spotify"
   ↓
3. Popup Spotify (login if needed)
   ↓
4. Authorize permissions
   ↓
5. ✅ Connected!
   ↓
6. Play games with ANY playlist
```

---

## 🧪 Test Rapide

### Backend OK?

```bash
# Test API endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/playlists/spotify/authorize/

# Should return: {"authorization_url": "https://...", "state": "..."}
```

### Frontend OK?

1. Ouvrir console navigateur (F12)
2. Aller sur `/profile`
3. Vérifier qu'il n'y a pas d'erreurs
4. Section "Spotify" devrait être visible

---

## ❌ Dépannage

### "Spotify not configured"

❌ **Problème:** Variables d'environnement manquantes  
✅ **Solution:** Vérifiez `backend/.env` et redémarrez

### "Invalid redirect URI"

❌ **Problème:** Redirect URI pas configuré dans Spotify Dashboard  
✅ **Solution:** Ajoutez `http://localhost:8000/api/playlists/spotify/callback/` dans Dashboard

### "Popup blocked"

❌ **Problème:** Bloqueur de popups actif  
✅ **Solution:** Autorisez les popups pour localhost:5173

### "User not authenticated in callback"

❌ **Problème:** Session expirée  
✅ **Solution:** Reconnectez-vous à InstantMusic avant de connecter Spotify

---

## 📚 Documentation Complète

Pour plus de détails, voir:
- **[OAUTH_IMPLEMENTATION.md](./OAUTH_IMPLEMENTATION.md)** - Guide complet
- **[README.md](./README.md)** - Vue d'ensemble du projet

---

## 🎉 Résultat

Après la configuration:

**Avant OAuth:**
```
GET /playlists/37i9dQZF1DX4o1oenSJRJd/tracks
→ 403 Forbidden ❌
```

**Avec OAuth:**
```
GET /playlists/37i9dQZF1DX4o1oenSJRJd/tracks
→ 200 OK ✅
→ 50 tracks returned
```

**Plus de limitations !** 🎊

---

## 💡 Tips

- **Production:** Changez les URLs en HTTPS
- **Sécurité:** Gardez le Client Secret privé
- **Multiple users:** Chaque utilisateur connecte son propre compte
- **Tokens:** Auto-refresh automatique, pas de maintenance

---

**Prêt à jouer sans restrictions ?** 🚀

Suivez les 4 étapes ci-dessus et profitez d'un accès complet à Spotify !
