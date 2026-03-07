# Middleware — HTTP & WebSocket

## Table des matières

- [Concept de middleware](#concept-de-middleware)
- [Middleware HTTP](#middleware-http)
  - [Ordre de traitement](#ordre-de-traitement)
  - [Détail de chaque middleware](#détail-de-chaque-middleware)
- [Middleware WebSocket](#middleware-websocket)
  - [Pile ASGI](#pile-asgi)
  - [AllowedHostsOriginValidator](#allowedhostsoriginvalidator)
  - [JwtWebSocketMiddleware](#jwtwebsocketmiddleware)
- [Pourquoi l'ordre est critique](#pourquoi-lordre-est-critique)
- [Middlewares personnalisés](#middlewares-personnalisés)

---

## Concept de middleware

Un middleware Django est une couche de traitement intercalée entre le serveur HTTP et la vue. Chaque middleware peut modifier la **requête entrante** avant qu'elle atteigne la vue, et modifier la **réponse sortante** avant qu'elle soit envoyée au client.

Le modèle est celui des **couches d'oignon** : la requête traverse chaque couche de l'extérieur vers l'intérieur, et la réponse ressort de l'intérieur vers l'extérieur en repassant par les mêmes couches dans l'ordre inverse.

```
                        REQUÊTE HTTP ENTRANTE
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│  1. SecurityMiddleware                                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  2. CorsMiddleware                                  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  3. PrometheusMetricsMiddleware               │  │  │
│  │  │  ┌────────────────────────────────────────┐  │  │  │
│  │  │  │  4. StructuredLoggingMiddleware         │  │  │  │
│  │  │  │  ┌──────────────────────────────────┐  │  │  │  │
│  │  │  │  │  5. SessionMiddleware             │  │  │  │  │
│  │  │  │  │  ┌────────────────────────────┐  │  │  │  │  │
│  │  │  │  │  │  6. CommonMiddleware        │  │  │  │  │  │
│  │  │  │  │  │  ┌──────────────────────┐  │  │  │  │  │  │
│  │  │  │  │  │  │  7. CsrfViewMW       │  │  │  │  │  │  │
│  │  │  │  │  │  │  ┌────────────────┐  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  8. AuthMW     │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  ┌──────────┐  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  9. Msg  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  ┌────┐  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  │ 10 │  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  │ 11 │  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  │ 12 │  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  │    │  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  │ VUE│  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  │  └────┘  │  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  │  └──────────┘  │  │  │  │  │  │  │  │
│  │  │  │  │  │  │  └────────────────┘  │  │  │  │  │  │  │
│  │  │  │  │  │  └──────────────────────┘  │  │  │  │  │  │
│  │  │  │  │  └────────────────────────────┘  │  │  │  │  │
│  │  │  │  └──────────────────────────────────┘  │  │  │  │
│  │  │  └────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                               │
                       RÉPONSE HTTP SORTANTE
                   (traverse dans l'ordre inverse)
```

> **Lecture du schéma :** La requête entre par `SecurityMiddleware` (couche 1), traverse toutes les couches jusqu'à la vue au centre, puis la réponse remonte en sens inverse. Un middleware peut **court-circuiter** la chaîne en renvoyant une réponse directement (ex. : `MaintenanceMiddleware` renvoie un 503 sans jamais atteindre la vue).

---

## Middleware HTTP

### Ordre de traitement

La liste `MIDDLEWARE` dans `backend/config/settings/base.py` définit l'ordre. Les indices correspondent aux couches du schéma ci-dessus.

```python
MIDDLEWARE = [
    # 1
    "django.middleware.security.SecurityMiddleware",
    # 2
    "corsheaders.middleware.CorsMiddleware",
    # 3
    "apps.core.middleware.PrometheusMetricsMiddleware",
    # 4
    "apps.core.logging_middleware.StructuredLoggingMiddleware",
    # 5
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 6
    "django.middleware.common.CommonMiddleware",
    # 7
    "django.middleware.csrf.CsrfViewMiddleware",
    # 8
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 9
    "django.contrib.messages.middleware.MessageMiddleware",
    # 10
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 11
    "apps.administration.middleware.MaintenanceMiddleware",
    # 12
    "auditlog.middleware.AuditlogMiddleware",
]
```

---

### Détail de chaque middleware

#### 1. `SecurityMiddleware` — `django.middleware.security`

Couche de sécurité de base fournie par Django.

**Responsabilités :**
- Force la redirection HTTP → HTTPS (`SECURE_SSL_REDIRECT = True` en production)
- Ajoute le header `Strict-Transport-Security` (HSTS) pour indiquer aux navigateurs de toujours utiliser HTTPS
- Ajoute `X-Content-Type-Options: nosniff` pour empêcher le MIME sniffing
- Gère `SECURE_BROWSER_XSS_FILTER` (header `X-XSS-Protection` pour les vieux navigateurs)

**Configuration (production) :**
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000        # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Placé en premier** car la redirection HTTPS doit se produire avant tout autre traitement.

---

#### 2. `CorsMiddleware` — `corsheaders.middleware`

Gère les headers [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) (Cross-Origin Resource Sharing) pour les requêtes cross-origin provenant du frontend React.

**Responsabilités :**
- Répond aux requêtes `OPTIONS` preflight avec les headers CORS appropriés
- Ajoute `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers` aux réponses
- En développement, autorise `http://localhost:3000` (Vite dev server)

**Doit être placé avant `SessionMiddleware`** car Django `corsheaders` doit intercepter les requêtes preflight AVANT que `SessionMiddleware` tente d'accéder aux cookies.

**Configuration :**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # dev
    "https://instantmusic.app", # prod
]
CORS_ALLOW_CREDENTIALS = True  # nécessaire pour envoyer les cookies JWT
```

---

#### 3. `PrometheusMetricsMiddleware` — `apps.core.middleware`

Middleware personnalisé qui instrumente chaque requête HTTP pour Prometheus.

**Responsabilités :**
- Enregistre le timestamp de début de traitement (`time.monotonic()`)
- Après la réponse, incrémente les compteurs :
  - `http_requests_total{method, path, status_code}` — nombre total de requêtes
  - `http_request_duration_seconds{method, path}` — histogramme des latences

**Placé tôt (position 3)** pour mesurer la latence **totale**, incluant les traitements des middlewares suivants (authentification, CSRF, logique métier). Le placer après `AuthenticationMiddleware` aurait exclu le temps d'authentification des mesures.

```
Requête entre → [timestamp_début] → ... traitements ... → Réponse → [timestamp_fin]
                                                                    latence = fin - début
```

**Métriques exposées sur `/metrics/` (Prometheus scrape endpoint).**

---

#### 4. `StructuredLoggingMiddleware` — `apps.core.logging_middleware`

Génère un enregistrement de log JSON structuré pour chaque cycle requête/réponse.

**Responsabilités :**
- Génère un `request_id` UUID unique par requête (transmis via header `X-Request-ID`)
- Capture : méthode HTTP, chemin, `user_id` (si authentifié), IP client, User-Agent
- Mesure la durée de traitement complète
- Après la réponse : émet un log JSON avec `status_code`, durée en ms

**Exemple de log émis :**
```json
{
  "level": "INFO",
  "timestamp": "2026-03-07T14:32:11.456Z",
  "request_id": "a3f1b2c4-...",
  "method": "POST",
  "path": "/api/games/",
  "status_code": 201,
  "duration_ms": 47.3,
  "user_id": 42,
  "ip": "192.168.1.10"
}
```

Le `request_id` est propagé dans tous les logs émis pendant le traitement de cette requête, ce qui permet de **corréler** tous les logs d'une même requête dans Kibana / Grafana Loki.

---

#### 5. `SessionMiddleware` — `django.contrib.sessions`

Gère la persistance des sessions HTTP via cookies.

**Responsabilités :**
- Charge la session depuis le store (Redis ou base de données) en début de requête
- Sauvegarde les modifications de session en fin de requête
- Nécessaire pour que `AuthenticationMiddleware` puisse identifier l'utilisateur

> Dans InstantMusic, l'authentification principale se fait via JWT (Bearer token), mais les sessions restent nécessaires pour l'admin Django et le panneau Jazzmin.

---

#### 6. `CommonMiddleware` — `django.middleware.common`

Utilitaires HTTP génériques.

**Responsabilités :**
- Redirige les URLs sans slash final si `APPEND_SLASH = True` (ex. `/api/games` → `/api/games/`)
- Envoie le header `Content-Length` sur les réponses statiques
- Gère les `DISALLOWED_USER_AGENTS`

---

#### 7. `CsrfViewMiddleware` — `django.middleware.csrf`

Protection contre les attaques [CSRF](https://owasp.org/www-community/attacks/csrf) (Cross-Site Request Forgery).

**Responsabilités :**
- Vérifie la présence et la validité du token CSRF sur les requêtes `POST`, `PUT`, `PATCH`, `DELETE`
- Le token est transmis dans le cookie `csrftoken` et dans le header `X-CSRFToken`

> Les vues DRF utilisant l'authentification JWT (`SessionAuthentication` désactivée) sont exemptées via `@csrf_exempt` ou la configuration DRF. L'admin Django utilise la protection CSRF standard.

---

#### 8. `AuthenticationMiddleware` — `django.contrib.auth`

Peuple `request.user` à partir de la session HTTP active.

**Responsabilités :**
- Lit l'identifiant utilisateur stocké en session
- Charge l'objet `User` correspondant depuis la base de données
- Si aucune session valide : `request.user` = `AnonymousUser`

**Note :** Pour les API REST (JWT), l'authentification est gérée par DRF (`JWTAuthentication`) et non par ce middleware. Ce middleware sert principalement pour l'admin Django.

---

#### 9. `MessageMiddleware` — `django.contrib.messages`

Framework de messages flash (notifications one-shot entre requêtes).

**Responsabilités :**
- Fournit `request._messages` pour stocker des messages à afficher lors de la prochaine requête
- Utilisé par l'interface d'admin Django (Jazzmin) pour les notifications de succès/erreur

---

#### 10. `XFrameOptionsMiddleware` — `django.middleware.clickjacking`

Protège contre les attaques de [clickjacking](https://owasp.org/www-community/attacks/Clickjacking).

**Responsabilités :**
- Ajoute le header `X-Frame-Options: DENY` sur toutes les réponses
- Empêche l'intégration de l'application dans un `<iframe>` sur un site tiers

**Configuration :**
```python
X_FRAME_OPTIONS = "DENY"
```

---

#### 11. `MaintenanceMiddleware` — `apps.administration.middleware`

Middleware personnalisé qui active le mode maintenance de l'application.

**Comportement :**

```
Requête entrante
      │
      ▼
┌─────────────────────────────────┐
│  SiteConfiguration.maintenance  │──── False ──→ Passe la requête normalement
│  _mode actif ?                  │
└─────────────────────────────────┘
           │ True
           ▼
┌─────────────────────────────────┐
│  Chemin commence par /admin/ ?  │──── Oui ──→ Bypass (accès admin maintenu)
└─────────────────────────────────┘
           │ Non
           ▼
┌─────────────────────────────────────────────────────────┐
│  Retourne HttpResponse 503 avec message personnalisé     │
│  (lu depuis SiteConfiguration.maintenance_message)       │
└─────────────────────────────────────────────────────────┘
```

**Activation :** Via l'admin Django → `SiteConfiguration` → cocher `maintenance_mode`. Le changement est effectif immédiatement sans redémarrage du serveur.

**Placé tard dans la chaîne** (position 11) car il nécessite que `SessionMiddleware` et `AuthenticationMiddleware` aient été exécutés pour pouvoir détecter si la requête cible `/admin/`.

---

#### 12. `AuditlogMiddleware` — `auditlog.middleware`

Fourni par la bibliothèque [`django-auditlog`](https://django-auditlog.readthedocs.io/). Enregistre automatiquement l'auteur des modifications sur les modèles tracés.

**Responsabilités :**
- Associe `request.user` au thread local courant
- Permet à `auditlog` de savoir **qui** a effectué chaque modification (`LogEntry`)
- Tracé automatiquement sur tous les modèles décorés avec `@auditlog.register()`

**Placé en dernier** car il n'a besoin que de `request.user` (déjà peuplé par le middleware 8) et n'a pas d'impact sur la réponse.

---

## Middleware WebSocket

Le protocole WebSocket nécessite une pile de middleware distincte, définie dans `backend/config/asgi.py`. Django Channels gère la connexion ASGI et applique ses propres couches de middleware.

### Pile ASGI

```python
# backend/config/asgi.py

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JwtWebSocketMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

```
  Connexion WebSocket entrante (ws://host/ws/game/XXXX/)
                     │
                     ▼
    ┌────────────────────────────────────┐
    │  AllowedHostsOriginValidator        │
    │  Vérifie l'origine dans             │
    │  ALLOWED_HOSTS                      │
    │  ✗ Origine inconnue → Ferme (403)   │
    └────────────────────────────────────┘
                     │ ✓ Origine valide
                     ▼
    ┌────────────────────────────────────┐
    │  JwtWebSocketMiddleware             │
    │  Extrait ?token=<jwt>               │
    │  Valide avec simplejwt              │
    │  Injecte scope["user"]              │
    │  ✗ Token invalide → Ferme (4003)    │
    └────────────────────────────────────┘
                     │ ✓ Token valide
                     ▼
    ┌────────────────────────────────────┐
    │  URLRouter                          │
    │  ws/game/<room_code>/  → GameConsumer  │
    │  ws/notifications/     → NotificationConsumer │
    └────────────────────────────────────┘
                     │
                     ▼
              Consumer actif
         (connexion WebSocket établie)
```

---

### AllowedHostsOriginValidator

Fourni par Django Channels (`channels.security.websocket`).

**Comportement :**
- Récupère le header `Origin` de la requête HTTP d'upgrade WebSocket
- Vérifie que l'origine est dans la liste `ALLOWED_HOSTS` de Django
- Si l'origine est inconnue ou absente : ferme la connexion avec un code HTTP 403 avant même l'upgrade WebSocket

**Importance :** Sans cette validation, n'importe quel site tiers pourrait ouvrir une connexion WebSocket vers l'API en utilisant les cookies de session de l'utilisateur (attaque CSRF sur WebSocket).

---

### JwtWebSocketMiddleware

Middleware personnalisé dans `apps/authentication/jwt_ws_middleware.py`.

**Problème résolu :** Le protocole WebSocket ne peut pas transmettre de headers HTTP arbitraires lors de la connexion depuis un navigateur. Il est donc impossible d'envoyer un header `Authorization: Bearer <token>`. La solution standard est de passer le token en **query parameter** lors de l'URL d'upgrade.

**Flux de validation :**

```
ws://host/ws/game/XXXX/?token=eyJhbGc...
                              │
                              ▼
           ┌──────────────────────────────┐
           │  Extraire token depuis        │
           │  scope["query_string"]        │
           └──────────────────────────────┘
                              │
                              ▼
           ┌──────────────────────────────┐
           │  AccessToken(token)           │
           │  (simplejwt)                  │
           └──────────────────────────────┘
                    │               │
              ✓ Valide          ✗ Invalide / expiré
                    │               │
                    ▼               ▼
           scope["user"]    Ferme connexion
           = User.objects   code WebSocket
           .get(user_id)    4003
                    │
                    ▼
           Passe au middleware
              suivant
```

**Code de fermeture 4003 :** Les codes WebSocket `4000-4999` sont réservés aux applications. `4003` signifie ici "non autorisé" (équivalent HTTP 403).

**Sécurité du token en query param :** Le token JWT apparaît dans les logs du serveur. En production, la connexion se faisant via TLS (wss://), le token est chiffré en transit mais peut apparaître dans les logs Nginx. Pour mitiger ce risque, les tokens utilisés pour les WebSocket doivent avoir une durée de vie courte.

---

## Pourquoi l'ordre est critique

Certains middlewares dépendent explicitement du travail effectué par des middlewares antérieurs :

| Middleware                        | Dépend de                                                                        |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `AuthenticationMiddleware` (8)    | `SessionMiddleware` (5) — nécessite la session pour identifier l'utilisateur     |
| `MessageMiddleware` (9)           | `SessionMiddleware` (5) — stocke les messages en session                         |
| `MaintenanceMiddleware` (11)      | `AuthenticationMiddleware` (8) — vérifie si l'utilisateur accède à `/admin/`     |
| `AuditlogMiddleware` (12)         | `AuthenticationMiddleware` (8) — nécessite `request.user` peuplé                 |
| `CorsMiddleware` (2)              | Doit précéder `SessionMiddleware` — doit traiter les OPTIONS avant toute session |
| `PrometheusMetricsMiddleware` (3) | Doit précéder la logique métier — pour mesurer la latence totale                 |

**Exemple de dysfonctionnement si l'ordre est inversé :**
- Mettre `AuditlogMiddleware` avant `AuthenticationMiddleware` : l'auteur des modifications ne serait jamais enregistré (toujours `AnonymousUser`)
- Mettre `CorsMiddleware` après `SessionMiddleware` : les requêtes preflight OPTIONS échoueraient car `SessionMiddleware` essaierait de créer une session pour des requêtes sans corps

---

## Middlewares personnalisés

### Structure d'un middleware Django

```python
class MonMiddleware:
    def __init__(self, get_response):
        # Appelé une seule fois au démarrage du serveur
        self.get_response = get_response

    def __call__(self, request):
        # Code exécuté AVANT la vue (requête descendante)
        # ...

        response = self.get_response(request)  # Appel à la vue (ou middleware suivant)

        # Code exécuté APRÈS la vue (réponse montante)
        # ...

        return response
```

### Court-circuit (ex. MaintenanceMiddleware)

```python
class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        config = SiteConfiguration.get_solo()
        if config.maintenance_mode and not request.path.startswith("/admin/"):
            return HttpResponse(
                config.maintenance_message,
                status=503,
                content_type="text/plain",
            )
        # get_response N'EST PAS appelé → court-circuit
        return self.get_response(request)
```

Quand `get_response` n'est pas appelé, les middlewares plus profonds et la vue ne sont jamais exécutés. La réponse remonte directement en sens inverse à travers les middlewares déjà traversés (1 à 10).
