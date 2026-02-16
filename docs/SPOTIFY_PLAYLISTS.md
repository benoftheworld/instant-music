# Guide des Playlists Spotify

## Problème d'accès aux playlists

L'application utilise le **Client Credentials Flow** de Spotify, qui a des limitations importantes :
- ❌ Pas d'accès aux playlists utilisateur privées
- ❌ Pas d'accès à la plupart des playlists publiques populaires
- ✅ Accès uniquement aux playlists créées par l'application ou certaines playlists éditoriales

## Message d'erreur

Si vous voyez ce message :
```
Accès refusé à cette playlist Spotify. Les playlists privées ou protégées ne sont pas accessibles avec l'authentification actuelle. Veuillez sélectionner une playlist publique différente.
```

Cela signifie que la playlist sélectionnée n'est pas accessible avec le mode d'authentification actuel.

## Solutions

### Solution 1 : Créer vos propres playlists (Recommandé pour développement)

1. Créez une playlist publique dans Spotify
2. Ajoutez au moins 10-15 morceaux
3. Rendez-la **publique** et **collaborative**
4. Utilisez son ID dans l'application

**Note:** Même les playlists publiques peuvent avoir des restrictions selon leur propriétaire.

### Solution 2 : Utiliser des playlists pré-définies (À implémenter)

Créer une bibliothèque de morceaux dans la base de données :

```python
# backend/apps/games/fixtures/default_tracks.json
[
  {
    "spotify_id": "track_id_1",
    "name": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "preview_url": "https://..."
  },
  ...
]
```

### Solution 3 : Passer à OAuth 2.0 (Recommandé pour production)

Pour un accès complet aux playlists Spotify :

1. **Modifier l'authentification Spotify** :
   - Utiliser Authorization Code Flow au lieu de Client Credentials
   - Demander les permissions : `user-read-private`, `playlist-read-private`, `playlist-read-collaborative`

2. **Avantages** :
   - Accès à toutes les playlists de l'utilisateur
   - Accès aux playlists privées
   - Expérience utilisateur améliorée

3. **Inconvénients** :
   - Nécessite une authentification utilisateur
   - Plus complexe à implémenter
   - Gestion des tokens de rafraîchissement

## Implémentation temporaire

En attendant une solution permanente, l'application :
- ✅ Affiche un message d'erreur clair à l'utilisateur
- ✅ Permet de sélectionner une autre playlist
- ✅ Log les erreurs pour le debugging

## Test avec playlists accessibles

Pour tester localement, créez une playlist sur votre compte Spotify avec :
- Minimum 10 morceaux variés
- Statut : Public
- Pas de restrictions géographiques

**Important:** Même avec ces paramètres, l'accès n'est pas garanti avec Client Credentials Flow.

## Recommandation pour la production

Pour une application en production, il est **fortement recommandé** d'implémenter :
1. OAuth 2.0 Authorization Code Flow pour accès complet aux playlists
2. Une bibliothèque de morceaux par défaut dans la base de données
3. Un système de cache pour les playlists fréquemment utilisées
