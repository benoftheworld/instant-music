# 🎵 Guide: Comment Sélectionner une Playlist qui Fonctionne

## Problème

Avec le **Client Credentials Flow** de Spotify, la majorité des playlists retournent une erreur 403 (Forbidden). Voici comment trouver des playlists accessibles.

## ⚡ Solution Rapide: Script de Test

J'ai créé un script pour tester rapidement si une playlist est accessible :

```bash
docker compose exec backend python test_playlist_access.py <playlist_id>
```

### Exemples d'utilisation

**Avec un ID de playlist:**
```bash
docker compose exec backend python test_playlist_access.py 37i9dQZF1DXcBWIGoYBM5M
```

**Avec une URL complète:**
```bash
docker compose exec backend python test_playlist_access.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
```

### Résultat

Le script vous dira:
- ✅ Si la playlist est accessible
- 📊 Combien de morceaux sont disponibles
- 🎵 Des exemples de morceaux
- ❌ Ou si elle est bloquée (403)

---

## 🔍 Méthode 1: Créer Votre Propre Playlist (Recommandé)

### Étapes:

1. **Ouvrez Spotify** (Desktop ou Web)

2. **Créez une nouvelle playlist:**
   - Cliquez sur "Créer une playlist"
   - Nommez-la (ex: "InstantMusic Test")

3. **Ajoutez des morceaux:**
   - Minimum: 10 morceaux
   - Recommandé: 20+ morceaux pour plus de variété

4. **Rendez-la publique:**
   - Cliquez sur les "..." de la playlist
   - Menu → "Rendre publique"

5. **Récupérez l'ID:**
   - Cliquez sur "Partager" → "Copier le lien de la playlist"
   - URL format: `https://open.spotify.com/playlist/ABC123XYZ`
   - L'ID est: `ABC123XYZ`

6. **Testez l'accessibilité:**
   ```bash
   docker compose exec backend python test_playlist_access.py ABC123XYZ
   ```

### ⚠️ Attention

Même vos propres playlists publiques peuvent être bloquées avec Client Credentials Flow. C'est une limitation de Spotify, pas de votre configuration.

---

## 🔍 Méthode 2: Tester des Playlists Existantes

### Où chercher des playlists:

1. **Playlists Spotify Featured** (certaines peuvent fonctionner):
   - Allez sur https://open.spotify.com
   - Section "Parcourir" → "Playlists éditoriales"
   - Copiez l'ID et testez

2. **Playlists de labels/artistes:**
   - Certaines playlists officielles peuvent être accessibles
   - Recherchez des labels de musique
   - Testez leurs playlists

3. **Playlists anciennes/rares:**
   - Les playlists moins populaires ont parfois moins de restrictions

### Commande de recherche et test

```bash
# 1. Recherchez des playlists dans l'app
# 2. Pour chaque playlist trouvée, testez:
docker compose exec backend python test_playlist_access.py <ID_PLAYLIST>
```

---

## 🔍 Méthode 3: Tester via l'Interface de l'Application

### Depuis le Frontend

1. **Lancez l'application:**
   ```bash
   # Services déjà lancés normalement
   ```

2. **Dans la page de création de partie:**
   - Entrez un ID de playlist à tester
   - Cliquez sur "Démarrer la partie"

3. **Résultat:**
   - ✅ Si ça fonctionne: la partie démarre
   - ❌ Si erreur: message d'explication clair

---

## 📝 Format des IDs Spotify

### Exemples d'URLs Spotify:

**Playlist:**
```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
                                  ^^^^^^^^^^^^^^^^^^^^^^^^
                                  C'est l'ID
```

**Avec paramètres:**
```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123
                                  ^^^^^^^^^^^^^^^^^^^^^^^^
                                  ID (ignorez le ?si=...)
```

---

## 🎯 Stratégie de Test Recommandée

### Script de test automatique

Créez un fichier avec plusieurs IDs à tester:

```bash
# test_multiple.sh
#!/bin/bash

PLAYLISTS=(
    "37i9dQZF1DXcBWIGoYBM5M"
    "37i9dQZF1DX0XUsuxWHRQd"
    "37i9dQZF1DX4o1oenSJRJd"
    # Ajoutez vos IDs ici
)

for id in "${PLAYLISTS[@]}"; do
    echo "Testing: $id"
    docker compose exec backend python test_playlist_access.py "$id"
    echo ""
done
```

Rendez-le exécutable et lancez:
```bash
chmod +x test_multiple.sh
./test_multiple.sh
```

---

## 🌟 Alternative: Utiliser les Tracks par Défaut

Si vous ne trouvez aucune playlist accessible, vous pouvez utiliser les morceaux de test:

### Fichier créé: `backend/apps/games/fixtures/fallback_tracks.json`

Ce fichier contient 15 morceaux populaires prêts à l'emploi.

### Pour l'utiliser (à implémenter):

1. Créez une fonction dans `GameService`:
   ```python
   def start_game_with_default_tracks(room_code):
       # Charge fallback_tracks.json
       # Génère les questions
       # Démarre la partie
   ```

2. Dans le frontend, ajoutez un bouton:
   - "Utiliser les morceaux par défaut"
   - Appelle l'endpoint spécial
   - Démarre sans playlist Spotify

---

## 🚀 Solution Définitive: OAuth 2.0

Pour éliminer complètement les restrictions:

### Avantages:
- ✅ Accès à TOUTES les playlists publiques
- ✅ Accès aux playlists privées de l'utilisateur
- ✅ Pas de 403 Forbidden
- ✅ Meilleure expérience utilisateur

### Inconvénients:
- ⏱️ Plus complexe à implémenter
- 🔐 Nécessite authentification utilisateur
- 🔄 Gestion des tokens de rafraîchissement

**Voir:** [SPOTIFY_PLAYLISTS.md](./SPOTIFY_PLAYLISTS.md) pour les détails d'implémentation

---

## 📊 Résumé des Options

| Option | Difficulté | Fiabilité | Recommandé pour |
|--------|-----------|-----------|-----------------|
| Script de test | ⭐ Facile | ✅ Excellent | Développement |
| Créer ses playlists | ⭐⭐ Moyen | ⚠️ Variable | Tests |
| Tracks par défaut | ⭐ Facile | ✅ 100% | Demo/MVP |
| OAuth 2.0 | ⭐⭐⭐ Difficile | ✅ 100% | Production |

---

## 🎮 Pour Démarrer Maintenant

**Option la plus simple pour tester le jeu:**

1. **Utilisez le script de test:**
   ```bash
   docker compose exec backend python test_playlist_access.py 37i9dQZF1DXcBWIGoYBM5M
   ```

2. **Si bloqué, cherchez-en une autre:**
   - Parcourez Spotify
   - Copiez des IDs
   - Testez-les un par un

3. **Dès qu'une fonctionne:**
   - Notez l'ID
   - Utilisez-la dans votre partie
   - Profitez du jeu! 🎉

---

## ❓ Questions Fréquentes

**Q: Pourquoi ma playlist publique est bloquée?**  
R: C'est une limitation de Spotify avec Client Credentials Flow. Spotify restreint l'accès même aux playlists publiques avec ce type d'authentification.

**Q: Combien de morceaux minimum?**  
R: 4 minimum absolu, 10+ recommandé pour une bonne expérience.

**Q: Puis-je utiliser des playlists privées?**  
R: Non, Client Credentials ne peut pas accéder aux playlists privées. Il faut OAuth 2.0.

**Q: Le script de test est-il sûr?**  
R: Oui, il utilise uniquement l'API Spotify en lecture seule.

**Q: Et si AUCUNE playlist ne fonctionne?**  
R: Utilisez les tracks par défaut (fallback_tracks.json) ou implémentez OAuth 2.0.

---

**Besoin d'aide?** Consultez [SPOTIFY_PLAYLISTS.md](./SPOTIFY_PLAYLISTS.md) pour plus de détails techniques.
