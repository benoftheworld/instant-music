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

## ⚠️ Important - Limitations Spotify

L'application utilise le **Client Credentials Flow** de Spotify, qui a des restrictions importantes :
- ❌ La plupart des playlists publiques retournent une erreur 403 (Forbidden)
- ❌ Pas d'accès aux playlists utilisateur privées
- ✅ L'application affiche des messages d'erreur clairs en cas de restriction

**Solutions :**
1. **Pour le développement** : Voir [SPOTIFY_PLAYLISTS.md](./SPOTIFY_PLAYLISTS.md) pour les solutions de contournement
2. **Pour la production** : Il est recommandé d'implémenter OAuth 2.0 Authorization Code Flow pour un accès complet

**Test du système** : Toutes les fonctionnalités du jeu ont été testées et fonctionnent parfaitement avec des données de test.

Voir la documentation du projet pour la suite (configuration, tests, déploiement).