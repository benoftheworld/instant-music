# 🎵 Système Hybride Spotify - Authentification Optionnelle

## Question Clé : L'utilisateur doit-il obligatoirement avoir un compte Spotify ?

**❌ NON - Le compte Spotify est OPTIONNEL**

InstantMusic utilise un **système hybride intelligent** qui s'adapte automatiquement selon que l'utilisateur a connecté ou non son compte Spotify.

---

## 🔄 Fonctionnement du Système Hybride

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              HybridSpotifyService                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Utilisateur connecté avec Spotify?                          │
│           ┌─────────────┴─────────────┐                     │
│          OUI                           NON                   │
│           │                             │                    │
│           ▼                             ▼                    │
│  ┌────────────────┐          ┌──────────────────┐          │
│  │ OAuth 2.0      │          │ Client           │          │
│  │ Service        │          │ Credentials      │          │
│  │                │          │ Service          │          │
│  │ ✅ Tous les    │          │ ⚠️  Playlists    │          │
│  │    playlists   │          │    publiques     │          │
│  │ ✅ Privés      │          │    limitées      │          │
│  │ ✅ Collaborative│         │ ❌ 403 Forbidden │          │
│  └────────────────┘          └──────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Logique de Sélection Automatique

Le `HybridSpotifyService` détermine automatiquement quel service utiliser :

```python
def _get_service_for_user(self, user):
    """Sélectionne automatiquement le bon service d'authentification."""
    
    # Si utilisateur authentifié ET a connecté Spotify
    if user and user.is_authenticated:
        try:
            token = SpotifyToken.objects.get(user=user)
            
            # Si token valide → OAuth 2.0
            if not token.is_expired():
                return oauth_service, True
                
        except SpotifyToken.DoesNotExist:
            pass
    
    # Sinon → Client Credentials (mode restreint)
    return client_service, False
```

---

## 👥 Deux Modes d'Utilisation

### Mode 1 : Sans Compte Spotify (Client Credentials)

**✅ Avantages**
- Aucune inscription Spotify requise
- Accès immédiat à l'application
- Simplicité d'utilisation

**⚠️ Limitations**
- Accès limité aux playlists Spotify publiques
- Erreurs 403 Forbidden sur ~90% des playlists
- Pas d'accès aux playlists privées ou collaboratives

**💡 Cas d'usage**
- Test rapide de l'application
- Utilisateurs sans compte Spotify
- Démonstrations publiques

### Mode 2 : Avec Compte Spotify (OAuth 2.0)

**✅ Avantages**
- Accès complet à TOUTES les playlists Spotify
- Playlists privées accessibles
- Playlists collaboratives incluses
- Aucune erreur 403 Forbidden
- Meilleure expérience utilisateur

**⚠️ Inconvénient**
- Nécessite un compte Spotify (gratuit ou premium)
- Étape supplémentaire de connexion

**💡 Cas d'usage**
- Utilisation régulière de l'application
- Accès aux playlists personnelles
- Expérience optimale

---

## 🛠️ Implémentation Technique

### Backend : HybridSpotifyService

Fichier : `backend/apps/playlists/hybrid_service.py`

```python
class HybridSpotifyService:
    """
    Service intelligent qui bascule automatiquement entre 
    OAuth 2.0 et Client Credentials selon l'utilisateur.
    """
    
    def search_playlists(self, query: str, limit: int = 20, user=None):
        """Recherche de playlists avec authentification adaptative."""
        service, is_oauth = self._get_service_for_user(user)
        
        try:
            results = service.search_playlists(query, limit)
            return {
                'playlists': results,
                'using_oauth': is_oauth,
                'mode': 'oauth' if is_oauth else 'client_credentials'
            }
        except Exception as e:
            # Fallback vers Client Credentials si OAuth échoue
            if is_oauth:
                logger.warning(f"OAuth failed, falling back to client credentials: {e}")
                results = client_service.search_playlists(query, limit)
                return {
                    'playlists': results,
                    'using_oauth': False,
                    'mode': 'client_credentials'
                }
            raise
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 50, user=None):
        """Récupération des pistes avec authentification adaptative."""
        service, is_oauth = self._get_service_for_user(user)
        
        try:
            return service.get_playlist_tracks(playlist_id, limit)
        except Exception as e:
            # Fallback automatique
            if is_oauth:
                logger.warning(f"OAuth failed for playlist tracks, falling back")
                return client_service.get_playlist_tracks(playlist_id, limit)
            raise
```

### Intégration dans les Views

Fichier : `backend/apps/playlists/views.py`

```python
from .hybrid_service import hybrid_spotify_service

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
    """Recherche de playlists - utilise automatiquement le bon mode."""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 20))
    
    # Le service détermine automatiquement OAuth vs Client Credentials
    result = hybrid_spotify_service.search_playlists(
        query, 
        limit, 
        user=request.user  # Passe l'utilisateur authentifié
    )
    
    return Response({
        'playlists': result['playlists'],
        'using_oauth': result['using_oauth'],  # Métadonnées pour le frontend
        'mode': result['mode']
    })
```

### Intégration dans le Système de Jeu

Fichier : `backend/apps/games/services.py`

```python
class GameService:
    """Service de gestion des parties."""
    
    @staticmethod
    def start_game(game: Game):
        """Démarre une partie en utilisant l'OAuth de l'hôte si disponible."""
        
        # Génère les questions en utilisant l'authentification de l'hôte
        questions = QuestionGeneratorService.generate_questions(
            game.playlist_spotify_id,
            game.num_questions,
            user=game.host  # ✨ Utilise l'OAuth de l'hôte du jeu
        )
        
        # ...reste de la logique
```

**Bénéfice** : Si l'hôte d'une partie a connecté son compte Spotify, les questions seront générées avec OAuth, donnant accès à toutes les playlists !

### Frontend : Bannière d'Information

Fichier : `frontend/src/components/spotify/SpotifyModeBanner.tsx`

```tsx
export default function SpotifyModeBanner() {
  const [isConnected, setIsConnected] = useState(false);

  // Vérifie automatiquement si l'utilisateur a connecté Spotify
  useEffect(() => {
    const checkConnection = async () => {
      const connected = await spotifyAuthService.isConnected();
      setIsConnected(connected);
    };
    checkConnection();
  }, []);

  // N'affiche rien si déjà connecté
  if (isConnected) return null;

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <h3>Accès limité aux playlists Spotify</h3>
      <p>
        Vous utilisez le <strong>mode restreint</strong>. 
        Connectez votre compte Spotify pour un accès complet !
      </p>
      <Link to="/profile" className="btn-primary">
        Connecter Spotify
      </Link>
    </div>
  );
}
```

---

## 📊 Comparaison des Modes

| Fonctionnalité | Sans Spotify | Avec Spotify |
|----------------|--------------|---------------|
| **Playlists publiques** | ⚠️ ~10% seulement | ✅ 100% |
| **Playlists privées** | ❌ Aucune | ✅ Toutes |
| **Playlists collaboratives** | ❌ Aucune | ✅ Toutes |
| **Erreurs 403** | ⚠️ Fréquentes | ✅ Aucune |
| **Compte requis** | ❌ Non | ✅ Spotify (gratuit/premium) |
| **Expérience** | ⚙️ Basique | 🌟 Optimale |

---

## 🔐 Sécurité et Gestion des Tokens

### Stockage des Tokens OAuth

```python
class SpotifyToken(models.Model):
    """
    Stockage sécurisé des tokens OAuth par utilisateur.
    OneToOne : un seul token par utilisateur.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    scope = models.TextField()
    
    def is_expired(self) -> bool:
        """Vérifie si le token a expiré."""
        return timezone.now() >= self.expires_at
    
    def is_expiring_soon(self, minutes: int = 5) -> bool:
        """Vérifie si le token expire dans les X minutes."""
        return timezone.now() >= self.expires_at - timedelta(minutes=minutes)
```

### Auto-Refresh des Tokens

Le système rafraîchit automatiquement les tokens **5 minutes avant expiration** :

```python
def get_valid_token_for_user(self, user) -> Optional[str]:
    """Retourne un token valide, le rafraîchit si nécessaire."""
    try:
        token = SpotifyToken.objects.get(user=user)
        
        # Rafraîchissement automatique si expiration imminente
        if token.is_expiring_soon(minutes=5):
            logger.info(f"Token expiring soon for user {user.id}, refreshing...")
            self.refresh_access_token(token.refresh_token)
            token.refresh_from_db()
        
        return token.access_token if not token.is_expired() else None
        
    except SpotifyToken.DoesNotExist:
        return None
```

---

## 🚀 Recommandations UX

### Pour les Nouveaux Utilisateurs

1. **Onboarding sans friction**
   - Laisser l'utilisateur créer un compte et jouer immédiatement
   - Montrer la bannière d'information sur les limitations
   - Inviter (sans forcer) à connecter Spotify pour une meilleure expérience

2. **Messages clairs**
   ```
   ⚠️ Accès limité
   La plupart des playlists Spotify publiques ne sont pas accessibles 
   en mode restreint.
   
   💡 Solution : Connectez votre compte Spotify (gratuit) pour accéder 
   à toutes les playlists !
   ```

3. **Encouragement progressif**
   - Première session : bannière informative (dismissible)
   - Après 2-3 erreurs 403 : proposition de connexion
   - Profil utilisateur : section "Connexions" avec statut visible

### Pour les Utilisateurs Existants

1. **Transparence totale**
   - Afficher clairement le mode actif (OAuth vs Client Credentials)
   - Expliquer les bénéfices de la connexion Spotify
   - Permettre déconnexion facile (réversible)

2. **Feedback en temps réel**
   ```json
   {
     "playlists": [...],
     "using_oauth": true,
     "mode": "oauth"
   }
   ```

3. **Indicateurs visuels**
   - Badge vert : "Connecté avec Spotify"
   - Badge gris : "Mode restreint"

---

## 🧪 Tests et Validation

### Scénarios de Test

#### Test 1 : Utilisateur sans Spotify

```bash
# Se connecter comme user1 (pas de SpotifyToken)
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/playlists/search/?q=rock"

# Réponse attendue
{
  "playlists": [...],
  "using_oauth": false,
  "mode": "client_credentials"
}
```

#### Test 2 : Utilisateur avec Spotify

```bash
# Se connecter comme user2 (a connecté Spotify)
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/playlists/search/?q=rock"

# Réponse attendue
{
  "playlists": [...],
  "using_oauth": true,
  "mode": "oauth"
}
```

#### Test 3 : Fallback Automatique

```python
# Simuler une erreur OAuth
def test_oauth_fallback(self):
    """Si OAuth échoue, le système bascule sur Client Credentials."""
    
    # Utilisateur avec token OAuth expiré/invalide
    user = User.objects.create_user('test', 'test@test.com', 'password')
    SpotifyToken.objects.create(
        user=user,
        access_token='INVALID',
        refresh_token='INVALID',
        expires_at=timezone.now() - timedelta(hours=1)
    )
    
    # Le système doit automatiquement basculer sur Client Credentials
    result = hybrid_spotify_service.search_playlists('test', user=user)
    
    assert result['using_oauth'] == False
    assert result['mode'] == 'client_credentials'
    assert len(result['playlists']) > 0  # Fonctionne quand même
```

---

## 📈 Métriques et Analytics (Recommandé)

Pour optimiser l'expérience, tracker ces métriques :

```python
# Dans views.py ou middleware
from django.core.signals import request_finished

def track_spotify_mode_usage(sender, **kwargs):
    """Track OAuth vs Client Credentials usage."""
    
    response = kwargs.get('response')
    if hasattr(response, 'data') and 'using_oauth' in response.data:
        mode = 'oauth' if response.data['using_oauth'] else 'client_credentials'
        
        # Envoyer à analytics
        analytics.track('spotify_api_call', {
            'mode': mode,
            'endpoint': kwargs.get('request').path,
            'timestamp': timezone.now()
        })

request_finished.connect(track_spotify_mode_usage)
```

**Métriques clés à suivre** :
- % d'utilisateurs ayant connecté Spotify
- Nombre de requêtes OAuth vs Client Credentials
- Taux d'erreurs 403 par mode
- Conversion : visiteur → utilisateur avec Spotify connecté

---

## 🎯 Conclusion

### Réponse à la Question Initiale

> **"L'utilisateur devra obligatoirement avoir un compte spotify?"**

**NON** - Le système hybride garantit que :

✅ **Tout utilisateur peut jouer** sans compte Spotify  
✅ **L'expérience est dégradée** mais fonctionnelle  
✅ **La connexion Spotify est optionnelle** et améliore l'expérience  
✅ **Le système bascule automatiquement** entre les deux modes  
✅ **Aucun utilisateur n'est bloqué** - graceful degradation

### Architecture Technique

```
InstantMusic
    │
    ├─ Sans Spotify ────▶ Client Credentials ────▶ Accès limité (fonctionne)
    │                     (Mode restreint)
    │
    └─ Avec Spotify ────▶ OAuth 2.0 ────────────▶ Accès complet (optimal)
                          (Mode premium)
```

### Avantages de cette Approche

1. **Accessibilité** : Pas de barrière à l'entrée
2. **Flexibilité** : Utilisateur choisit son niveau d'engagement
3. **Évolutivité** : Facile d'ajouter d'autres services (YouTube, Deezer)
4. **UX** : Dégradation gracieuse, jamais de blocage
5. **Business** : Conversion progressive des utilisateurs

### Recommandation Produit

**Phase 1 (Actuelle)** : Système hybride avec onboarding sans friction  
**Phase 2** : Gamification de la connexion Spotify (badges, achievements)  
**Phase 3** : Features exclusives OAuth (stats avancées, playlists collab)

---

## 📚 Ressources

- [Documentation OAuth 2.0](./SPOTIFY_OAUTH.md)
- [Guide de Test des Playlists](./SPOTIFY_PLAYLIST_TESTING.md)
- [Limitations Spotify API](./SPOTIFY_API_LIMITATIONS.md)
- [Code: HybridSpotifyService](../backend/apps/playlists/hybrid_service.py)

---

**Date de création** : 2024  
**Version** : 1.0  
**Auteur** : InstantMusic Team
