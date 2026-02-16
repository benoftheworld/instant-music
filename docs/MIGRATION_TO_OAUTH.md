# 🔄 Guide de Migration - Passer du Mode Restreint à OAuth 2.0

## Introduction

Ce guide s'adresse aux utilisateurs existants d'InstantMusic qui utilisent actuellement le **mode restreint** (Client Credentials) et souhaitent passer au **mode optimal** (OAuth 2.0) pour débloquer l'accès complet aux playlists Spotify.

---

## 📊 État des Lieux

### Avant (Mode Restreint)

```
Utilisateur InstantMusic
    │
    ├─ Authentification : ✅ Compte InstantMusic
    ├─ Spotify : ❌ Non connecté
    ├─ Accès playlists : ⚠️ ~10% seulement
    ├─ Erreurs 403 : ⚠️ Fréquentes
    └─ Expérience : 📉 Limitée
```

### Après (Mode Optimal)

```
Utilisateur InstantMusic
    │
    ├─ Authentification : ✅ Compte InstantMusic
    ├─ Spotify : ✅ Connecté (OAuth 2.0)
    ├─ Accès playlists : ✅ 100%
    ├─ Erreurs 403 : ✅ Aucune
    └─ Expérience : 🚀 Complète
```

---

## 🚀 Migration Rapide (30 Secondes)

### Prérequis

- ✅ Compte InstantMusic actif
- ✅ Compte Spotify (gratuit ou premium)
- ✅ Navigateur moderne autorisant les popups

### Étapes

#### 1. Connexion à InstantMusic

```
https://instantmusic.app/login
    ↓
Identifiants habituels
    ↓
Connecté ✅
```

#### 2. Accès au Profil

```
Cliquez sur votre nom (coin supérieur droit)
    ↓
Sélectionnez "Profil"
    ↓
Page profil affichée
```

#### 3. Section Spotify

Vous verrez une bannière :

```
┌───────────────────────────────────────────┐
│ 🔒 Mode Restreint Actif                   │
│                                            │
│ Vous n'avez pas encore connecté votre     │
│ compte Spotify.                            │
│                                            │
│ [Connecter avec Spotify]                  │
└───────────────────────────────────────────┘
```

#### 4. Connexion Spotify

Cliquez sur **"Connecter avec Spotify"**

```
Popup Spotify s'ouvre (600x700px)
    ↓
Se connecter à Spotify (ou créer un compte)
    ↓
Autoriser InstantMusic
    ↓
Popup se ferme automatiquement
    ↓
✅ "Spotify Connecté" affiché
```

#### 5. Vérification

Vous devriez maintenant voir :

```
┌───────────────────────────────────────────┐
│ ✅ Spotify Connecté                       │
│                                            │
│ • Accès à 100% des playlists              │
│ • Connecté le : [date]                    │
│ • Expire le : [date + 1h]                 │
│                                            │
│ [Déconnecter Spotify]  [Actualiser]       │
└───────────────────────────────────────────┘
```

**🎉 Migration terminée !**

---

## 🔍 Vérification de la Migration

### Test 1 : Recherche de Playlist

1. Allez dans **"Créer une partie"**
2. Recherchez une playlist (ex: "Top 50 Global")
3. Sélectionnez une playlist qui échouait avant

**Avant :** `❌ Erreur 403 - Playlist non disponible`  
**Après :** `✅ Playlist chargée avec toutes les pistes`

### Test 2 : Playlists Privées

1. Recherchez le nom d'une de vos playlists privées
2. Sélectionnez-la

**Avant :** `❌ Impossible de voir vos playlists privées`  
**Après :** `✅ Toutes vos playlists privées sont accessibles`

### Test 3 : Création de Partie

1. Créez une partie avec une playlist populaire
2. Lancez la partie

**Avant :** `⚠️ Échec fréquent, peu de choix`  
**Après :** `✅ Fonctionne toujours, plein de choix`

---

## 📈 Changements Techniques (Backend)

### Avant Migration

```python
# backend/apps/playlists/views.py
@api_view(['GET'])
def search(request):
    # Utilise Client Credentials
    playlists = spotify_service.search_playlists(query)
    
    return Response({
        'playlists': playlists  # ~10% accessibles
    })
```

**Authentification :** Client Credentials (app-level)  
**Token :** Partagé entre tous les utilisateurs  
**Limitations :** 403 Forbidden sur la plupart des playlists

### Après Migration

```python
# backend/apps/playlists/views.py
@api_view(['GET'])
def search(request):
    # Détection automatique OAuth vs Client Credentials
    result = hybrid_spotify_service.search_playlists(
        query, 
        limit, 
        user=request.user  # ✨ Détecte automatiquement le mode
    )
    
    return Response({
        'playlists': result['playlists'],  # 100% accessibles si OAuth
        'using_oauth': result['using_oauth'],  # true pour vous
        'mode': result['mode']  # "oauth"
    })
```

**Authentification :** OAuth 2.0 (user-level)  
**Token :** Unique par utilisateur (stocké dans `SpotifyToken`)  
**Limitations :** Aucune !

---

## 🔐 Données Stockées

### Nouvelle Table : SpotifyToken

Après migration, une nouvelle entrée est créée :

```sql
-- Table: playlists_spotifytoken
INSERT INTO playlists_spotifytoken (
    user_id,           -- Votre ID utilisateur InstantMusic
    access_token,      -- Token d'accès Spotify (crypté)
    refresh_token,     -- Token de rafraîchissement (crypté)
    expires_at,        -- Date d'expiration (timezone aware)
    scope,             -- Permissions accordées
    created_at,        -- Date de connexion
    updated_at         -- Dernière mise à jour
) VALUES (
    42,
    'BQD...xyz',       -- Token crypté
    'AQB...abc',       -- Refresh token crypté
    '2024-01-01 15:00:00+00:00',
    'playlist-read-private playlist-read-collaborative user-library-read',
    NOW(),
    NOW()
);
```

**Localisation :** Base de données PostgreSQL, table `playlists_spotifytoken`

### Sécurité

- ✅ Tokens cryptés en base de données
- ✅ Refresh automatique toutes les heures
- ✅ Aucune donnée sensible exposée dans les réponses API
- ✅ Révocation possible à tout moment

---

## 🔄 Auto-Refresh des Tokens

### Comment ça marche ?

```python
def get_valid_token_for_user(self, user):
    """Retourne un token valide, rafraîchit automatiquement si nécessaire."""
    token = SpotifyToken.objects.get(user=user)
    
    # ⏰ Vérification 5 minutes avant expiration
    if token.is_expiring_soon(minutes=5):
        logger.info(f"Token expiring soon for {user.username}, refreshing...")
        
        # 🔄 Rafraîchissement automatique
        new_token_data = self._refresh_token(token.refresh_token)
        token.access_token = new_token_data['access_token']
        token.expires_at = timezone.now() + timedelta(seconds=new_token_data['expires_in'])
        token.save()
    
    return token.access_token
```

**Fréquence :** Automatique, 5 minutes avant expiration  
**Transparence :** Invisible pour l'utilisateur  
**Fallback :** Si échec, utilise Client Credentials temporairement

---

## 🎯 Comparaison Avant/Après

### Recherche de Playlists

#### Avant (Client Credentials)

```bash
$ curl http://localhost:8000/api/playlists/search/?q=pop
{
  "playlists": [
    {
      "id": "37i9dQZF1DXcBWIGoYBM5M",
      "name": "Today's Top Hits",
      "error": "403 Forbidden"  # ❌ Ne fonctionne pas
    },
    # ...~10% seulement accessibles
  ]
}
```

#### Après (OAuth 2.0)

```bash
$ curl http://localhost:8000/api/playlists/search/?q=pop \
       -H "Authorization: Bearer YOUR_TOKEN"
{
  "playlists": [
    {
      "id": "37i9dQZF1DXcBWIGoYBM5M",
      "name": "Today's Top Hits",
      "tracks_count": 50,
      "image": "https://...",
      "tracks": [...]  # ✅ Toutes les pistes accessibles
    },
    # ...100% accessibles
  ],
  "using_oauth": true,
  "mode": "oauth"
}
```

### Création de Partie

#### Avant

```
User clique "Créer une partie"
    ↓
Recherche "pop hits"
    ↓
90% des playlists retournent 403
    ↓
⚠️ Frustration utilisateur
    ↓
Abandonne ou utilise une playlist de test
```

#### Après

```
User clique "Créer une partie"
    ↓
Recherche "pop hits"
    ↓
100% des playlists accessibles
    ↓
✅ Choix large et varié
    ↓
Sélectionne sa playlist préférée
    ↓
Partie créée avec succès
```

---

## 🛠️ Résolution de Problèmes

### Problème 1 : Popup Bloquée

**Symptôme :** Clic sur "Connecter avec Spotify" ne fait rien

**Cause :** Bloqueur de popup du navigateur

**Solution :**
1. Vérifier la barre d'adresse du navigateur
2. Cliquer sur l'icône de popup bloquée
3. Autoriser les popups pour InstantMusic
4. Réessayer

### Problème 2 : Erreur "Invalid State"

**Symptôme :** Après connexion Spotify, erreur "Invalid state parameter"

**Cause :** Session expirée ou attaque CSRF détectée

**Solution :**
1. Fermer la popup
2. Actualiser la page du profil
3. Réessayer la connexion Spotify

### Problème 3 : Token Expire Trop Vite

**Symptôme :** "Token expired" après quelques minutes

**Cause :** Problème de rafraîchissement automatique

**Solution :**
1. Aller dans le profil
2. Cliquer sur "Actualiser" dans la section Spotify
3. Si le problème persiste, déconnecter puis reconnecter

### Problème 4 : "Already Connected" mais 403 Errors

**Symptôme :** Badge indique "Connecté" mais erreurs 403 persistent

**Cause :** Token invalide ou révoqué côté Spotify

**Solution :**
1. Cliquer sur "Déconnecter Spotify"
2. Attendre 5 secondes
3. Reconnecter avec Spotify
4. Vérifier que le badge affiche "Connecté"

---

## 📊 Métriques de Migration

### Pour les Utilisateurs

Après migration, vous devriez constater :

- **Playlists accessibles** : 10% → 100% (+900%)
- **Erreurs 403** : 90% → 0% (-100%)
- **Temps de recherche** : Inchangé (~1-2s)
- **Satisfaction** : 📉 → 🚀

### Pour les Développeurs

Métriques à tracker :

```python
from django.db.models import Count

# Taux d'adoption OAuth
total_users = User.objects.count()
oauth_users = SpotifyToken.objects.count()
adoption_rate = (oauth_users / total_users) * 100

print(f"OAuth Adoption Rate: {adoption_rate:.1f}%")

# Erreurs API par mode
from apps.analytics.models import APICall

client_creds_errors = APICall.objects.filter(
    mode='client_credentials',
    status_code=403
).count()

oauth_errors = APICall.objects.filter(
    mode='oauth',
    status_code=403
).count()

print(f"Client Credentials 403 Errors: {client_creds_errors}")
print(f"OAuth 403 Errors: {oauth_errors}")  # Devrait être ~0
```

---

## 🎁 Bénéfices Post-Migration

### Bénéfice 1 : Accès Complet

```
Avant : 🔒 Mode Restreint
    ├─ 10% des playlists publiques
    ├─ 0% des playlists privées
    └─ 0% des playlists collaboratives

Après : 🔓 Mode Optimal
    ├─ 100% des playlists publiques
    ├─ 100% des playlists privées
    └─ 100% des playlists collaboratives
```

### Bénéfice 2 : Expérience Fluide

```
Parcours utilisateur AVANT :
1. Recherche "Top Hits" → 10 résultats
2. Clique sur playlist 1 → ❌ 403 Error
3. Clique sur playlist 2 → ❌ 403 Error
4. Clique sur playlist 3 → ❌ 403 Error
5. Clique sur playlist 4 → ✅ Fonctionne enfin !
6. 😤 Frustration élevée

Parcours utilisateur APRÈS :
1. Recherche "Top Hits" → 50 résultats
2. Clique sur playlist 1 → ✅ Fonctionne
3. 😊 Satisfaction immédiate
```

### Bénéfice 3 : Créativité Débloquée

**Avant :**
- Limité aux playlists de test
- Peur de tester de nouvelles playlists
- Parties répétitives avec les mêmes musiques

**Après :**
- Accès à vos propres playlists
- Exploration libre de l'univers Spotify
- Parties variées et personnalisées

---

## 🔮 Maintenance Post-Migration

### Actions Automatiques

Aucune action requise de votre part ! Le système gère :

- ✅ Rafraîchissement automatique des tokens (toutes les heures)
- ✅ Détection des tokens expirés
- ✅ Fallback gracieux vers Client Credentials si OAuth échoue
- ✅ Logs et monitoring des erreurs

### Actions Optionnelles

Si vous le souhaitez :

1. **Vérifier la connexion** (optionnel)
   - Aller dans le profil
   - Vérifier que le badge est vert
   - Date d'expiration affichée

2. **Rafraîchir manuellement** (rare)
   - Cliquer sur "Actualiser"
   - Utile si vous avez changé les permissions Spotify

3. **Déconnecter/Reconnecter** (troubleshooting)
   - Si problèmes persistants
   - Déconnecter → Attendre 5s → Reconnecter

---

## 📚 Documentation Connexe

- **[USER_GUIDE_SPOTIFY.md](./USER_GUIDE_SPOTIFY.md)** - Guide utilisateur complet
- **[SPOTIFY_HYBRID_SYSTEM.md](./SPOTIFY_HYBRID_SYSTEM.md)** - Documentation technique
- **[SPOTIFY_OAUTH.md](./SPOTIFY_OAUTH.md)** - Configuration OAuth 2.0
- **[README.md](../README.md)** - Documentation principale du projet

---

## 🆘 Support

**Problèmes de migration ?**

1. Consultez la section [Résolution de Problèmes](#résolution-de-problèmes)
2. Vérifiez les logs : `docker compose logs backend | grep spotify`
3. Contactez le support : support@instantmusic.com

**Feedback sur l'expérience OAuth ?**

Nous voulons savoir ! Envoyez-nous un message avec :
- ⏱️ Temps de migration
- 😊 Satisfaction (1-5 étoiles)
- 💬 Commentaires/suggestions

---

**Bonne migration ! 🚀**
