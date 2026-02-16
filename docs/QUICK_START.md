# ⚡ Quick Start - Tester InstantMusic MAINTENANT

Vous voulez tester le jeu immédiatement ? Voici comment procéder :

## 🎯 Étape 1: Lancez l'Application

```bash
cd /home/benoftheworld/instant-music
docker compose up -d
```

Les 6 services doivent être démarrés (backend, frontend, db, redis, celery, celery_beat).

## 🎵 Étape 2: Trouvez une Playlist Accessible

### Option A - Script Automatique (Recommandé)

Testez plusieurs playlists d'un coup :

```bash
./test_playlists.sh
```

Le script testera automatiquement plusieurs playlists et vous dira lesquelles fonctionnent.

### Option B - Test Manuel

Testez une playlist spécifique :

```bash
# Format 1: Avec l'ID de playlist
docker compose exec backend python test_playlist_access.py 37i9dQZF1DX4UtSsGT1Sbe

# Format 2: Avec l'URL complète
docker compose exec backend python test_playlist_access.py "https://open.spotify.com/playlist/37i9dQZF1DX4UtSsGT1Sbe"
```

**Résultat du script :**
- ✅ Si accessible → Il affiche les morceaux et confirme que c'est utilisable
- ❌ Si bloqué (403/404) → Il vous indique d'en essayer une autre

## 🎮 Étape 3: Lancez une Partie de Test

Une fois que vous avez trouvé une playlist accessible :

### Dans le Backend (Terminal Docker)

```bash
docker compose exec backend python manage.py shell
```

Puis dans le shell Python :

```python
from apps.games.models import Game, Player
from apps.games.services import game_service

# 1. Créer une partie
game = Game.objects.create(
    room_code="TEST01",
    host_username="player1",
    playlist_id="VOTRE_ID_ICI",  # ← Remplacez par l'ID qui fonctionne
    status="waiting"
)

# 2. Ajouter des joueurs
player1 = Player.objects.create(
    game=game,
    username="player1",
    is_connected=True
)
player2 = Player.objects.create(
    game=game,
    username="player2",
    is_connected=True
)

# 3. Démarrer la partie
rounds_created = game_service.start_game("TEST01")
print(f"✅ {rounds_created} rounds créés!")

# 4. Vérifier le premier round
current_round = game_service.get_current_round("TEST01")
print(f"Question: {current_round.question['question']}")
print(f"Options: {current_round.question['options']}")

# 5. Soumettre une réponse
result = game_service.submit_answer(
    room_code="TEST01",
    player_username="player1",
    round_number=1,
    selected_option="A",  # Choisissez A, B, C ou D
    response_time=5.0     # Temps de réponse en secondes
)
print(f"Score obtenu: {result['points_earned']} points")
print(f"Réponse correcte: {result['is_correct']}")
```

### Dans le Frontend (Navigateur)

1. **Ouvrez** : http://localhost:5173

2. **Connectez-vous** ou créez un compte

3. **Créez une partie** :
   - Entrez l'ID de playlist qui fonctionne
   - Créez la room

4. **Invitez des joueurs** :
   - Partagez le code de la room
   - Ou ouvrez un autre navigateur en mode incognito

5. **Démarrez la partie** :
   - Le host clique sur "Démarrer"
   - Le jeu commence ! 🎉

## 🐛 Problèmes Courants

### "Playlist not accessible" ou erreur 403

**Cause** : La playlist est bloquée par Spotify avec Client Credentials Flow.

**Solution** :
1. Testez d'autres playlists avec le script
2. Créez votre propre playlist publique
3. Voir [SELECTING_PLAYLISTS.md](./SELECTING_PLAYLISTS.md) pour tous les détails

### "Not enough tracks" ou erreur 4 morceaux

**Cause** : La playlist n'a pas assez de morceaux accessibles.

**Solution** :
- Choisissez une playlist avec au moins 10 morceaux
- Vérifiez avec le script de test

### Services Docker pas démarrés

**Commande** :
```bash
docker compose ps  # Vérifier l'état
docker compose up -d  # Démarrer si nécessaire
docker compose logs backend  # Voir les logs en cas d'erreur
```

### "New Spotify token cached"

**C'est normal !** Le système récupère automatiquement un nouveau token d'accès Spotify. Cela ne prend que 1-2 secondes.

## 📚 Documentation Complète

- **[SELECTING_PLAYLISTS.md](./SELECTING_PLAYLISTS.md)** - Guide détaillé pour choisir des playlists
- **[SPOTIFY_PLAYLISTS.md](./SPOTIFY_PLAYLISTS.md)** - Limitations et solutions techniques
- **[GAMEPLAY_SYSTEM.md](./GAMEPLAY_SYSTEM.md)** - Documentation complète du système de jeu
- **[SPRINT_SUMMARY.md](./SPRINT_SUMMARY.md)** - Récapitulatif de tous les sprints

## 🎉 Succès !

Si vous arrivez à démarrer une partie et voir des questions s'afficher, **félicitations** ! Le système fonctionne parfaitement.

Le seul challenge est de trouver des playlists accessibles avec le Client Credentials Flow de Spotify. C'est une limitation de l'API, pas de votre code.

## 💡 Astuce Pro

**Créez votre propre "playlist de test"** :
1. Créez une playlist sur Spotify avec 15-20 morceaux variés
2. Rendez-la publique
3. Testez-la avec le script
4. Si elle fonctionne, gardez son ID pour tous vos tests !

Même si elle ne fonctionne pas à cause des restrictions Spotify, tous les tests avec des données mockées prouvent que le système de jeu fonctionne à 100%.

---

**Prêt à jouer ?** Lancez `./test_playlists.sh` et trouvez votre première playlist ! 🚀
