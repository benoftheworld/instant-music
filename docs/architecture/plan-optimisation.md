# Plan d'optimisation d'architecture

Plan d'amélioration pour rendre InstantMusic professionnel, maintenable et évolutif.

---

## 1. Analyse de l'état actuel

### Points forts

- **Séparation claire** : Backend Django (REST + WS), Frontend React, Infrastructure Docker
- **Temps réel fonctionnel** : Django Channels + Redis channel layer opérationnel
- **CI/CD en place** : GitHub Actions avec linting, tests, sécurité (Trivy, Bandit)
- **Monitoring déployé** : Prometheus + Grafana + ELK stack
- **Code quality** : Pre-commit hooks, ruff, mypy, bandit

### Points à améliorer

| Domaine           | Constat                                          | Impact                          |
| ----------------- | ------------------------------------------------ | ------------------------------- |
| Tests             | Couverture de tests limitée                      | Régressions fréquentes          |
| Logging           | Pas de logging structuré (JSON)                  | Difficulté d'analyse des logs   |
| Error handling    | Gestion d'erreurs inconsistante côté WS          | UX dégradée en cas d'erreur     |
| Sécurité WS       | Pas de validation des permissions par message WS | Risque d'actions non autorisées |
| Performance       | Requêtes N+1 dans le consumer (`get_game_data`)  | Latence sous charge             |
| Configuration     | Secrets en fichier `.env` sans vault             | Risque de fuite                 |
| Documentation API | Swagger auto-généré mais non enrichi             | Intégration difficile           |

---

## 2. Architecture cible

### 2.1 — Backend : robustesse et maintenabilité

#### A. Logging structuré JSON

Remplacer le logging texte par du JSON structuré pour une exploitation optimale dans ELK.

**Fichiers concernés** : `backend/config/settings/base.py`, `backend/config/settings/production.py`

```python
LOGGING = {
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "logstash": {
            "class": "logging.handlers.SocketHandler",
            "host": "logstash",
            "port": 5000,
            "formatter": "json",
        },
    },
}
```

**Dépendance** : `python-json-logger`

#### B. Validation des permissions WebSocket

Actuellement, n'importe quel joueur connecté peut envoyer `start_game` ou `finish_game`. Il faut vérifier que seul l'hôte peut effectuer ces actions.

**Fichier** : `backend/apps/games/consumers.py`

```python
async def start_game(self, data):
    user = self.scope.get("user")
    is_host = await self._is_host(user)
    if not is_host:
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": "Seul l'hôte peut démarrer la partie"
        }))
        return
    # ... logique existante
```

Actions à protéger : `start_game`, `start_round`, `end_round`, `next_round`, `finish_game`.

#### C. Optimisation des requêtes N+1

Dans `GameConsumer.get_game_data()`, la boucle sur `game.players` génère des requêtes N+1.

**Correctif** : Utiliser `select_related` et `prefetch_related` de manière optimale, et sérialiser via DRF au lieu de construire le dict manuellement.

```python
game = Game.objects.select_related("host").prefetch_related(
    Prefetch("players", queryset=GamePlayer.objects.select_related("user"))
).get(room_code=self.room_code)
```

#### D. Circuit breaker pour APIs externes

Protéger les appels Deezer/YouTube/LRCLib avec un circuit breaker pour éviter les cascades de timeouts.

**Dépendance** : `pybreaker` ou implémentation simple

```python
import pybreaker

deezer_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="deezer_api"
)

@deezer_breaker
def get_playlist_tracks(self, playlist_id, limit=50):
    # ... appel API
```

#### E. Rate limiting sur les endpoints sensibles

Ajouter du throttling DRF sur les endpoints critiques.

**Fichier** : `backend/config/settings/base.py`

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "60/minute",
        "game_answer": "30/minute",
    },
}
```

---

### 2.2 — Frontend : qualité et UX

#### A. Gestion d'erreurs globale

Ajouter un `ErrorBoundary` React et un système de notifications toast.

**Composants à créer** :
- `components/ErrorBoundary.tsx` — Capture les erreurs React
- `components/ToastProvider.tsx` — Notifications utilisateur (react-hot-toast)

#### B. Types plus stricts pour les messages WebSocket

Remplacer le type générique `WebSocketMessage` par une union discriminée :

```typescript
type WSInbound =
  | { type: "player_join"; player: PlayerData }
  | { type: "player_answer"; answer: string; response_time: number }
  | { type: "start_game" }
  // ...

type WSOutbound =
  | { type: "player_joined"; player: PlayerData; game_data: GameData }
  | { type: "round_started"; round_data: RoundData }
  | { type: "round_ended"; results: RoundResults }
  // ...
```

#### C. Optimistic updates

Appliquer un feedback immédiat quand le joueur répond (avant confirmation serveur).

```typescript
const answerMutation = useMutation({
  mutationFn: submitAnswer,
  onMutate: (variables) => {
    // Feedback immédiat : bouton grisé, animation
    setAnswered(true);
  },
});
```

#### D. Service Worker pour le PWA

Ajouter un service worker via `vite-plugin-pwa` pour :
- Cache des assets statiques
- Mode hors-ligne (page d'attente)
- Notifications push (invitations de jeu)

---

### 2.3 — Tests : couverture et fiabilité

#### A. Tests unitaires backend

| Cible                                        | Fichier                            | Priorité |
| -------------------------------------------- | ---------------------------------- | -------- |
| Scoring (calculate_score, check_answer)      | `games/tests/test_scoring.py`      | Haute    |
| Fuzzy matching (normalize_text, fuzzy_match) | `games/tests/test_matching.py`     | Haute    |
| QuestionGeneratorService                     | `games/tests/test_questions.py`    | Moyenne  |
| GameService (start, submit, finish)          | `games/tests/test_game_service.py` | Haute    |
| Serializers                                  | `games/tests/test_serializers.py`  | Moyenne  |

#### B. Tests d'intégration WebSocket

```python
from channels.testing import WebsocketCommunicator

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_player_join_broadcast():
    communicator = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
    connected, _ = await communicator.connect()
    assert connected
    response = await communicator.receive_json_from()
    assert response["type"] == "connection_established"
```

#### C. Tests frontend

| Cible                                            | Priorité |
| ------------------------------------------------ | -------- |
| Composants de jeu (QuizQuestion, LyricsQuestion) | Haute    |
| Hooks (useWebSocket, useAuth)                    | Haute    |
| Pages (GamePlayPage, GameResultsPage)            | Moyenne  |
| Services (wsService reconnexion)                 | Haute    |

#### D. Objectif de couverture

| Domaine  | Actuel | Cible |
| -------- | ------ | ----- |
| Backend  | ~10%   | > 70% |
| Frontend | ~5%    | > 60% |

---

### 2.4 — Infrastructure : scalabilité et résilience

#### A. Health checks Docker améliorés

Ajouter des health checks à tous les services dans docker-compose :

```yaml
backend:
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000/api/alive/ || exit 1"]
    interval: 30s
    timeout: 5s
    retries: 3
    start_period: 30s

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3

celery:
  healthcheck:
    test: ["CMD-SHELL", "celery -A config inspect ping --timeout 5"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### B. Gestion des secrets

Migrer de `.env` vers Docker Secrets ou un vault :

| Approche                 | Complexité | Sécurité |
| ------------------------ | ---------- | -------- |
| Docker Secrets (compose) | Faible     | Moyenne  |
| HashiCorp Vault          | Élevée     | Haute    |
| AWS Secrets Manager      | Moyenne    | Haute    |

Recommandation : commencer par Docker Secrets, migrer vers Vault si nécessaire.

#### C. Backup automatisé

```yaml
# Tâche cron ou Celery Beat
backup-db:
  image: postgres:15-alpine
  command: >
    sh -c "pg_dump -h db -U $$POSTGRES_USER $$POSTGRES_DB | gzip > /backups/instant-music-$$(date +%Y%m%d_%H%M%S).sql.gz"
  volumes:
    - ./backups:/backups
```

Rétention : 7 jours en local, 30 jours en stockage distant (S3/MinIO).

#### D. Scaling horizontal

Pour gérer plus de joueurs simultanés :

```yaml
# docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: "1.0"
        memory: 512M
```

Le channel layer Redis permet déjà la communication entre workers. Nginx fait le load balancing en round-robin.

---

### 2.5 — Sécurité

#### A. Audit des dépendances

Automatiser la vérification des CVE :

```yaml
# .github/workflows/ci.yml (ajout)
- name: Python dependency audit
  run: pip-audit --strict

- name: NPM dependency audit
  run: npm audit --audit-level=high
  working-directory: frontend
```

#### B. Headers de sécurité

Vérifier / renforcer les headers Nginx :

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' https://*.dzcdn.net; connect-src 'self' wss:;" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

#### C. Validation des entrées WebSocket

Ajouter une validation stricte des payloads WS avec des schémas JSON :

```python
import jsonschema

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"const": "player_answer"},
        "answer": {"type": "string", "maxLength": 255},
        "response_time": {"type": "number", "minimum": 0, "maximum": 300},
    },
    "required": ["type", "answer", "response_time"],
}
```

---

### 2.6 — Qualité de code

#### A. Stratégie de branches Git

```
main (production)
  └── develop (intégration)
       ├── feature/xxx
       ├── fix/xxx
       └── hotfix/xxx (depuis main)
```

- Pull requests obligatoires vers `develop`
- Reviews requises (1 minimum)
- CI doit passer avant merge
- Merge `develop` → `main` pour les releases

#### B. Pre-commit hooks étendus

```yaml
# .pre-commit-config.yaml (ajouts)
- repo: https://github.com/pre-commit/mirrors-mypy
  hooks:
    - id: mypy
      additional_dependencies: [django-stubs, djangorestframework-stubs]

- repo: https://github.com/hadolint/hadolint
  hooks:
    - id: hadolint-docker
```

#### C. Convention de commits

Renforcer le format avec `commitlint` :

```
feat(games): ajout du mode blind test
fix(ws): correction de la reconnexion après timeout
docs(api): documentation des endpoints playlists
test(scoring): tests unitaires du calcul de score
refactor(services): extraction du service de scoring
```

---

## 3. Priorisation

### Phase 1 — Fondations (priorité haute)

| Action                           | Impact        | Effort |
| -------------------------------- | ------------- | ------ |
| Tests unitaires scoring/matching | Fiabilité     | Moyen  |
| Validation permissions WS (hôte) | Sécurité      | Faible |
| Optimisation requêtes N+1        | Performance   | Faible |
| Logging structuré JSON           | Observabilité | Faible |
| Health checks Docker             | Résilience    | Faible |

### Phase 2 — Qualité (priorité moyenne)

| Action                           | Impact         | Effort |
| -------------------------------- | -------------- | ------ |
| Tests d'intégration WS           | Fiabilité      | Moyen  |
| Types WS discriminés (frontend)  | Maintenabilité | Moyen  |
| Circuit breaker APIs externes    | Résilience     | Moyen  |
| Rate limiting DRF                | Sécurité       | Faible |
| ErrorBoundary + Toast (frontend) | UX             | Faible |

### Phase 3 — Scaling (priorité basse)

| Action                           | Impact           | Effort |
| -------------------------------- | ---------------- | ------ |
| Backup automatisé                | Sécurité données | Moyen  |
| Gestion secrets (Docker Secrets) | Sécurité         | Moyen  |
| PWA / Service Worker             | UX               | Élevé  |
| Scaling horizontal (replicas)    | Capacité         | Moyen  |
| CSP headers renforcés            | Sécurité         | Faible |

---

## 4. Récapitulatif des fichiers impactés

| Fichier                                     | Modifications                          |
| ------------------------------------------- | -------------------------------------- |
| `backend/config/settings/base.py`           | Logging JSON, throttling DRF           |
| `backend/apps/games/consumers.py`           | Permissions hôte, validation payload   |
| `backend/apps/games/services.py`            | Circuit breaker, optimisation requêtes |
| `frontend/src/types/index.ts`               | Union types WS discriminés             |
| `frontend/src/components/ErrorBoundary.tsx` | Nouveau composant                      |
| `_devops/docker/docker-compose.prod.yml`    | Health checks, replicas                |
| `_devops/nginx/nginx.conf`                  | Headers CSP, Permissions-Policy        |
| `.github/workflows/ci.yml`                  | Audit dépendances, couverture          |
| `backend/apps/games/tests/`                 | Nouveaux fichiers de tests             |
