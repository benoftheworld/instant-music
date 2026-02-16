# 📋 Liste de Playlists à Tester

Cette liste contient des IDs de playlists Spotify à tester avec l'application. Certaines peuvent fonctionner, d'autres peuvent être bloquées (403/404).

## ⚡ Comment Tester

```bash
# Tester UNE playlist
docker compose exec backend python test_playlist_access.py <ID_DE_LA_LISTE>

# Tester TOUTES les playlists automatiquement
./test_playlists.sh
```

## 📝 Format des URLs Spotify

```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
                                  ^^^^^^^^^^^^^^^^^^^^^^^^
                                  ↑ C'est l'ID à copier
```

---

## 🎵 Playlists Spotify Editorial à Tester

### Top Hits & Populaires

| Nom | ID | Commande de Test |
|-----|----|--------------------|
| Today's Top Hits | `37i9dQZF1DXcBWIGoYBM5M` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXcBWIGoYBM5M` |
| Global Top 50 | `37i9dQZF1DXcBWIGoYBM5M` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXcBWIGoYBM5M` |
| Hot Hits France | `37i9dQZF1DX0yTZbKXT492` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX0yTZbKXT492` |
| Viral 50 Global | `37i9dQZEVXbLiRSasKsNU9` | `docker compose exec backend python test_playlist_access.py 37i9dQZEVXbLiRSasKsNU9` |

### Par Décennie

| Nom | ID | Commande de Test |
|-----|----|--------------------|
| All Out 2010s | `37i9dQZF1DX5Ejj0EkURtP` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX5Ejj0EkURtP` |
| All Out 2000s | `37i9dQZF1DX4o1oenSJRJd` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX4o1oenSJRJd` |
| All Out 90s | `37i9dQZF1DXbTxeAdrVG2l` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXbTxeAdrVG2l` |
| All Out 80s | `37i9dQZF1DX4UtSsGT1Sbe` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX4UtSsGT1Sbe` |

### Par Genre

| Nom | ID | Commande de Test |
|-----|----|--------------------|
| RapCaviar | `37i9dQZF1DX0XUsuxWHRQd` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX0XUsuxWHRQd` |
| Rock Classics | `37i9dQZF1DWXRqgorJj26U` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DWXRqgorJj26U` |
| Jazz Vibes | `37i9dQZF1DXbITWG1ZJKYt` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXbITWG1ZJKYt` |
| Electronic Party | `37i9dQZF1DX4eRPd9frC1m` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX4eRPd9frC1m` |
| Country Hits | `37i9dQZF1DX1lVhptIYRda` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX1lVhptIYRda` |

### Ambiance

| Nom | ID | Commande de Test |
|-----|----|--------------------|
| Chill Hits | `37i9dQZF1DX4WYpdgoIcn6` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DX4WYpdgoIcn6` |
| Workout Motivation | `37i9dQZF1DXdxcBWuJkbcy` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXdxcBWuJkbcy` |
| Focus Flow | `37i9dQZF1DWZeKCadgRdKQ` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DWZeKCadgRdKQ` |
| Party Time | `37i9dQZF1DXaXB8fQg7xif` | `docker compose exec backend python test_playlist_access.py 37i9dQZF1DXaXB8fQg7xif` |

---

## 🔍 Comment Trouver Plus de Playlists

### Méthode 1: Spotify Web Player

1. Allez sur https://open.spotify.com/
2. Parcourez les sections:
   - "Parcourir" → "Playlists éditoriales"
   - "Rechercher" → cherchez un genre
3. Cliquez sur une playlist qui vous intéresse
4. Copiez l'URL depuis la barre d'adresse
5. Extrayez l'ID (partie après `/playlist/`)
6. Testez-la !

### Méthode 2: Spotify Desktop App

1. Ouvrez l'app Spotify
2. Trouvez une playlist intéressante
3. Clic droit → "Partager" → "Copier le lien de la playlist"
4. Format: `https://open.spotify.com/playlist/ID?si=...`
5. Gardez seulement l'ID (entre `/playlist/` et `?`)
6. Testez-la !

### Méthode 3: Recherche via l'API (dans l'app)

```bash
docker compose exec backend python manage.py shell
```

Puis:

```python
from apps.playlists.services import spotify_service

# Rechercher des playlists
results = spotify_service.search_playlists("rock", limit=10)

# Afficher les IDs
for playlist in results:
    print(f"{playlist['name']}: {playlist['id']}")
```

---

## ✍️ Créer Votre Propre Playlist de Test

**La méthode la plus fiable :**

### Étapes:

1. **Créez une playlist sur Spotify:**
   - Cliquez sur "Créer une playlist"
   - Nom: "InstantMusic Test"

2. **Ajoutez des morceaux variés:**
   - Minimum: 10 morceaux
   - Recommandé: 20+ morceaux
   - Variez artistes et styles

3. **Rendez-la publique:**
   - Cliquez sur "..." de la playlist
   - "Rendre publique"

4. **Récupérez l'ID:**
   - Partagez → Copier le lien
   - Extrayez l'ID

5. **Testez:**
   ```bash
   docker compose exec backend python test_playlist_access.py VOTRE_ID
   ```

### 📝 Suggestions de Morceaux Populaires

Pour votre playlist de test, ajoutez des morceaux connus :

- **Rock**: Bohemian Rhapsody (Queen), Hotel California (Eagles)
- **Pop**: Shape of You (Ed Sheeran), Blinding Lights (The Weeknd)
- **Hip-Hop**: Lose Yourself (Eminem), HUMBLE. (Kendrick Lamar)
- **Électro**: Titanium (David Guetta), Wake Me Up (Avicii)
- **Classic**: Stairway to Heaven (Led Zeppelin), Sweet Child O' Mine (Guns N' Roses)

**⚠️ Important:** Même vos propres playlists publiques peuvent être bloquées avec Client Credentials Flow. C'est une limitation de Spotify, pas de votre configuration.

---

## 📊 Résultats des Tests

### ✅ Playlists qui ont Fonctionné

Notez ici les playlists qui ont passé le test:

```
ID: _________________  Nom: _______________________
ID: _________________  Nom: _______________________
ID: _________________  Nom: _______________________
```

### ❌ Playlists Bloquées

La majorité des playlists seront probablement bloquées. C'est normal avec Client Credentials Flow.

---

## 🚀 Alternative: Tracks par Défaut

Si AUCUNE playlist ne fonctionne, utilisez les morceaux par défaut:

**Fichier:** `backend/apps/games/fixtures/fallback_tracks.json`

**Contenu:** 15 morceaux populaires prêts à l'emploi (Queen, The Weeknd, Ed Sheeran, etc.)

**À implémenter:** Fonction pour charger ces tracks au lieu d'une playlist Spotify.

---

## 💡 Conseils

1. **Testez plusieurs playlists** : Utilisez `./test_playlists.sh` pour en tester plusieurs d'un coup

2. **Gardez une liste de celles qui fonctionnent** : Notez les IDs accessibles pour référence future

3. **Variété** : Si vous créez votre playlist, mettez des artistes et genres variés pour le jeu

4. **Nombre de morceaux** : Minimum 10, idéal 20-30 pour éviter les répétitions

5. **OAuth pour la production** : Pour une vraie app en prod, implémentez OAuth 2.0 pour accès complet

---

## 🔗 Ressources

- **Test rapide**: `./test_playlists.sh`
- **Test manuel**: `docker compose exec backend python test_playlist_access.py <ID>`
- **Documentation**: [SELECTING_PLAYLISTS.md](./SELECTING_PLAYLISTS.md)
- **Guide OAuth**: [SPOTIFY_PLAYLISTS.md](./SPOTIFY_PLAYLISTS.md)

---

**Bonne chance dans la recherche de playlists accessibles ! 🎵**

N'oubliez pas: la limitation vient de Spotify, pas de votre code. Le système de jeu fonctionne parfaitement, comme le prouvent les tests avec données mockées. ✅
