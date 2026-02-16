# 🎵 InstantMusic

Une application web interactive de jeux musicaux multijoueurs en temps réel.

## Fonctionnalités (MVP)
- Authentification (username/password + Google OAuth)
- Profil utilisateur (avatar, mot de passe, statistiques)
- Créer / rejoindre parties en ligne (lobby, WebSocket)
- Quiz musical (mode 4 réponses, rapide)
- Intégration Spotify (extraits 30s)
- Backoffice administration
- Docker pour dev & prod

## ❓ Compte Spotify Obligatoire ?

### ❌ NON - Le compte Spotify est OPTIONNEL

InstantMusic utilise un **système hybride intelligent** qui s'adapte automatiquement :

| Mode | Compte Spotify | Accès Playlists | Expérience |
|------|----------------|-----------------|------------|
| **Mode Restreint** | ❌ Non requis | ⚠️ ~10% seulement | Basique mais fonctionnel |
| **Mode Optimal** | ✅ Connecté (gratuit/premium) | ✅ 100% complètes | Expérience complète |

**Recommandation** : Connectez votre compte Spotify (30 secondes) pour une expérience optimale.

📖 **[Guide utilisateur complet](./docs/USER_GUIDE_SPOTIFY.md)** - Avec ou sans Spotify ?

---

## 🎵 Système d'Authentification Spotify

### ✅ OAuth 2.0 (Mode Optimal - RECOMMANDÉ)

**L'authentification OAuth 2.0 est maintenant disponible !** Les utilisateurs peuvent connecter leur compte Spotify pour accéder à **toutes les playlists** sans restrictions.

**Comment utiliser:**
1. Connectez-vous à InstantMusic
2. Allez sur votre profil (`/profile`)
3. Cliquez sur "Connecter avec Spotify"
4. ✅ Accès complet à toutes les playlists !

**Configuration développeur:** Voir [docs/SPOTIFY_OAUTH.md](./docs/SPOTIFY_OAUTH.md)

### ⚙️ Client Credentials (Mode Restreint - Fallback Automatique)

L'application bascule automatiquement sur **Client Credentials Flow** pour les utilisateurs sans compte Spotify :
- ⚠️ ~90% des playlists publiques retournent une erreur 403 (Forbidden)
- ❌ Pas d'accès aux playlists privées
- ✅ Messages d'erreur clairs en cas de restriction
- ✅ Application reste utilisable

### 🧪 Comment tester une playlist ?

**Méthode rapide** - Utilisez le script de test :
```bash
# Tester une seule playlist
docker compose exec backend python test_playlist_access.py <PLAYLIST_ID>

# Tester plusieurs playlists automatiquement
./test_playlists.sh
```

**Guides disponibles :**
- 📘 **[docs/USER_GUIDE_SPOTIFY.md](./docs/USER_GUIDE_SPOTIFY.md)** - Guide utilisateur simple (RECOMMANDÉ)
- 🔧 **[docs/SPOTIFY_HYBRID_SYSTEM.md](./docs/SPOTIFY_HYBRID_SYSTEM.md)** - Documentation technique complète
- 🔑 **[docs/SPOTIFY_OAUTH.md](./docs/SPOTIFY_OAUTH.md)** - Configuration OAuth 2.0
- 🧪 **[docs/SPOTIFY_PLAYLIST_TESTING.md](./docs/SPOTIFY_PLAYLIST_TESTING.md)** - Tests et validation
- 📋 **[docs/SPOTIFY_API_LIMITATIONS.md](./docs/SPOTIFY_API_LIMITATIONS.md)** - Limitations API Spotify

**Test du système** : Toutes les fonctionnalités du jeu ont été testées et fonctionnent parfaitement avec des données de test.

Voir la documentation du projet pour la suite (configuration, tests, déploiement).