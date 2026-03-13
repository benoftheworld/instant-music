# Normes de développement — InstantMusic

## Vue d'ensemble

Ce document définit les conventions et standards à respecter pour contribuer au projet InstantMusic. Ces règles garantissent la cohérence, la lisibilité et la maintenabilité du code sur le long terme.

> **Règle d'or** : Le code est lu beaucoup plus souvent qu'il n'est écrit. Privilégiez toujours la lisibilité à la concision.

---

## 1. Conventions Git

### Format des commits

InstantMusic utilise la convention **Conventional Commits** :

```
<type>(<scope>): <description courte en français>

[corps optionnel]

[footer optionnel]
```

#### Types de commits

| Type       | Usage                                    | Exemple                                             |
| ---------- | ---------------------------------------- | --------------------------------------------------- |
| `feat`     | Nouvelle fonctionnalité                  | `feat(games): ajouter le mode karaoké`              |
| `fix`      | Correction de bug                        | `fix(auth): corriger le refresh du token JWT`       |
| `docs`     | Documentation uniquement                 | `docs(api): documenter les endpoints WebSocket`     |
| `style`    | Formatage, pas de changement logique     | `style(frontend): reformater les composants game`   |
| `refactor` | Refactoring sans nouvelle fonctionnalité | `refactor(games): extraire la logique de scoring`   |
| `test`     | Ajout ou modification de tests           | `test(games): ajouter tests pour calculate_score`   |
| `chore`    | Maintenance, dépendances                 | `chore(deps): mettre à jour Django à 5.1.1`         |
| `perf`     | Amélioration de performance              | `perf(games): optimiser la requête des classements` |
| `ci`       | Modifications CI/CD                      | `ci: ajouter le job de typecheck mypy`              |

#### Exemples de bons commits

```
feat(bonus): implémenter le système de vol de points

Le bonus `steal` prend 10% des points du joueur en tête.
Si ce joueur a un bouclier actif, le vol est bloqué.

- Nouveau modèle GameBonus
- BonusService.apply_steal_bonus()
- Message WebSocket bonus_blocked

Refs: #142
```

```
fix(websocket): corriger la reconnexion après timeout

Le hook useWebSocket ne relançait pas la connexion si
le timeout était dû à une inactivité serveur (code 1001).

Ajout du code 1001 dans la liste des codes déclenchant
la reconnexion automatique.

Fixes: #157
```

#### Ce qu'il faut éviter

```bash
# Mauvais (trop vague)
git commit -m "fix bug"
git commit -m "wip"
git commit -m "update"

# Mauvais (trop long pour le titre)
git commit -m "feat: ajouter la fonctionnalité de quiz musical avec support WebSocket et calcul de scores et système de bonus et achievements"

# Bon
git commit -m "feat(games): implémenter la boucle complète d'un round"
```

### Gestion des branches

#### Nomenclature

```
feature/<description-courte>   ← Nouvelle fonctionnalité
fix/<description-courte>       ← Correction de bug
hotfix/<description-courte>    ← Correction urgente en production
docs/<description-courte>      ← Documentation
refactor/<description-courte>  ← Refactoring
test/<description-courte>      ← Ajout de tests
```

#### Exemples

```bash
git checkout -b feature/mode-karaoke
git checkout -b fix/reconnexion-websocket
git checkout -b hotfix/score-calcul-incorrect
git checkout -b docs/api-websocket
```

#### Workflow Git (Gitflow simplifié)

```
main
  │  ← Production stable, tags de version
  │
  ├── develop
  │     │  ← Intégration continue, base de travail
  │     │
  │     ├── feature/mode-karaoke    ← merge → develop → PR → merge
  │     ├── fix/auth-token          ← merge → develop → PR → merge
  │     └── feature/achievements   ← merge → develop → PR → merge
  │
  └── hotfix/scoring-bug            ← merge → main + develop (urgence)
```

```
Workflow standard :
1. Créer une branche depuis develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/nouvelle-fonctionnalite

2. Développer + commiter régulièrement
   git add backend/apps/games/services.py
   git commit -m "feat(games): ajouter calcul bonus streak"

3. Pousser et créer une PR vers develop
   git push -u origin feature/nouvelle-fonctionnalite
   gh pr create --base develop

4. CI passe + review → merge squash vers develop

5. develop → main via PR pour les releases
```

---

## 2. Python / Django

### Formatage avec Ruff

Ruff est l'outil de formatage et linting Python. Il est configuré dans `pyproject.toml` à la racine.

```toml
# pyproject.toml (section ruff)
[tool.ruff]
line-length = 88          # Longueur de ligne maximale (black standard)
target-version = "py311"  # Python 3.11 minimum

[tool.ruff.format]
quote-style = "double"    # Guillemets doubles obligatoires
indent-style = "space"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "ANN"]
# E/W: pycodestyle, F: pyflakes, I: isort, B: bugbear...
```

```bash
# Vérifier le code
make lint

# Formater automatiquement
make format

# Ou directement
ruff format backend/
ruff check --fix backend/
```

### Règles Python importantes

```python
# ✓ Guillemets doubles
message = "Bonjour"

# ✗ Guillemets simples
message = 'Bonjour'

# ✓ Type hints obligatoires pour les fonctions publiques
def calculate_score(response_time: float, is_correct: bool) -> int:
    ...

# ✗ Pas de type hints
def calculate_score(response_time, is_correct):
    ...

# ✓ Docstrings en français pour les méthodes non triviales
def apply_bonus_effects(player: GamePlayer, bonus_type: str) -> dict:
    """
    Applique les effets immédiats d'un bonus activé.

    Args:
        player: Le joueur qui active le bonus
        bonus_type: Le type de bonus (double_points, shield, etc.)

    Returns:
        dict contenant les effets à broadcaster via WebSocket
    """
    ...

# ✓ Constantes en MAJUSCULES
BASE_POINTS = 1000
TIME_PENALTY = 20

# ✓ Utiliser les f-strings (pas .format() ni %)
message = f"Game {game.room_code} started by {user.username}"
```

### Sécurité avec Bandit

Bandit analyse le code Python pour détecter les vulnérabilités de sécurité.

```bash
# Lancer bandit
cd backend && bandit -r apps/ -c pyproject.toml

# Ou via make
make lint  # inclut bandit
```

Règles bandit importantes :

```python
# ✗ Ne JAMAIS faire (bandit B105/B106)
password = "hardcoded_password"
SECRET_KEY = "my-secret-key"

# ✓ Utiliser les variables d'environnement
import os
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# ✗ Ne pas utiliser random pour la sécurité (bandit B311)
import random
token = random.randint(100000, 999999)

# ✓ Utiliser secrets pour les valeurs cryptographiques
import secrets
token = secrets.token_hex(32)

# ✗ Requêtes SQL brutes (bandit B608)
cursor.execute(f"SELECT * FROM users WHERE id={user_id}")

# ✓ Toujours utiliser le paramétrage
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
# Ou mieux : utiliser l'ORM Django
User.objects.filter(id=user_id)
```

### Vérification des types avec MyPy

```bash
make typecheck
# ou
cd backend && mypy apps/
```

Configuration dans `pyproject.toml` :

```toml
[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
```

---

## 3. Tests Python (pytest)

### Structure des tests

```
backend/apps/<app>/
├── tests.py          ← Fichier simple (< 100 lignes de tests)
└── tests/            ← Ou répertoire pour les grandes apps
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_views.py
    └── test_consumers.py
```

### Conventions pytest

```python
# ✓ Marquer les tests nécessitant la DB
@pytest.mark.django_db
def test_game_creation():
    game = GameFactory.create()
    assert game.room_code is not None
    assert len(game.room_code) == 6

# ✓ Utiliser des factories (pas de fixtures manuelles)
# Utiliser factory_boy
class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game
    room_code = factory.Sequence(lambda n: f"GAME{n:02d}")
    status = 'waiting'
    game_mode = 'classique'

# ✓ Nommer clairement les tests
def test_calculate_score_returns_max_when_answered_immediately():
    score = calculate_score(response_time=0.1, is_correct=True)
    assert score == BASE_POINTS

def test_calculate_score_returns_zero_for_wrong_answer():
    score = calculate_score(response_time=5.0, is_correct=False)
    assert score == 0

# ✓ Tests WebSocket avec pytest-asyncio
@pytest.mark.asyncio
async def test_game_consumer_start_game():
    communicator = WebsocketCommunicator(application, "/ws/game/TEST01/")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.send_json_to({"type": "start_game"})
    response = await communicator.receive_json_from()
    assert response["type"] == "game_started"
    await communicator.disconnect()
```

### Lancer les tests

```bash
# Tous les tests backend
make test-backend
# équivalent à: cd backend && pytest -q

# Tests d'une app spécifique
cd backend && pytest apps/games/ -v

# Un test spécifique
cd backend && pytest apps/games/tests/test_services.py::test_calculate_score -v

# Avec couverture
make test-coverage
# Rapport HTML dans backend/htmlcov/index.html
```

---

## 4. TypeScript / React

### Formatage avec Prettier

```json
// frontend/.prettierrc
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

```bash
# Vérifier le formatage
cd frontend && npm run lint

# Formater automatiquement
cd frontend && npx prettier --write src/
```

### Conventions TypeScript

```typescript
// ✓ Types explicites pour les props de composants
interface QuizQuestionProps {
  question: Question
  onAnswer: (answer: string) => void
  hasAnswered: boolean
  timeLeft: number
}

// ✗ any est interdit (sauf cas très exceptionnels)
const processData = (data: any) => { ... }

// ✓ Utiliser des types précis
const processData = (data: GameWebSocketMessage) => { ... }

// ✓ Guillemets simples pour les strings TypeScript
const apiUrl = 'http://localhost:8000'

// ✓ Noms de composants en PascalCase
export default function QuizQuestion({ question, onAnswer }: QuizQuestionProps) { ... }

// ✓ Noms de hooks en camelCase commençant par use
export const useGameTimer = (duration: number) => { ... }

// ✓ Noms de services en camelCase
export const gameService = { ... }

// ✓ Types/interfaces en PascalCase
interface GamePlayer { ... }
type GameMode = 'classique' | 'rapide' | ...

// ✓ Constantes en SCREAMING_SNAKE_CASE ou camelCase
const BASE_POINTS = 1000
const defaultOptions = { retries: 3 }
```

### Règles React

```typescript
// ✓ Composants fonctionnels uniquement (pas de classes)
function MyComponent() { ... }

// ✓ Hooks dans le bon ordre (pas dans des conditions)
function MyComponent() {
  const [count, setCount] = useState(0)  // 1er
  const { data } = useQuery(...)          // 2ème
  const user = useAuthStore(...)          // 3ème
  // ✗ Jamais de hook dans un if/loop/etc.
}

// ✓ useCallback pour les handlers passés en props
const handleAnswer = useCallback((answer: string) => {
  sendAnswer(answer)
}, [sendAnswer])

// ✓ useMemo pour les calculs coûteux
const sortedPlayers = useMemo(
  () => [...players].sort((a, b) => b.score - a.score),
  [players]
)

// ✓ Décomposer les grandes fonctions JSX
function GamePlayPage() {
  if (phase === 'playing') return <PlayingView />
  if (phase === 'showing_results') return <ResultsView />
  return <WaitingView />
}
```

### Tests Frontend (Vitest + Testing Library)

```typescript
// frontend/src/components/game/__tests__/QuizQuestion.test.tsx

import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import QuizQuestion from '../QuizQuestion'

describe('QuizQuestion', () => {
  const mockQuestion = {
    audio_url: 'https://example.com/audio.mp3',
    choices: ['Shape of You', 'Blinding Lights', 'Bad Guy', 'Levitating'],
    question_text: 'Quel est le titre ?'
  }

  it('affiche les 4 choix de réponse', () => {
    render(
      <QuizQuestion
        question={mockQuestion}
        onAnswer={vi.fn()}
        hasAnswered={false}
        timeLeft={30}
      />
    )

    expect(screen.getByText('Shape of You')).toBeInTheDocument()
    expect(screen.getByText('Blinding Lights')).toBeInTheDocument()
  })

  it('appelle onAnswer avec la bonne réponse au clic', () => {
    const onAnswer = vi.fn()
    render(
      <QuizQuestion
        question={mockQuestion}
        onAnswer={onAnswer}
        hasAnswered={false}
        timeLeft={30}
      />
    )

    fireEvent.click(screen.getByText('Shape of You'))
    expect(onAnswer).toHaveBeenCalledWith('Shape of You')
  })

  it('désactive les boutons si déjà répondu', () => {
    render(
      <QuizQuestion
        question={mockQuestion}
        onAnswer={vi.fn()}
        hasAnswered={true}  // Déjà répondu
        timeLeft={30}
      />
    )

    const buttons = screen.getAllByRole('button')
    buttons.forEach(btn => expect(btn).toBeDisabled())
  })
})
```

---

## 5. Migrations Django

### Règles absolues

```bash
# ✓ Créer les migrations avec la commande
make dev-makemigrations
# ou
python manage.py makemigrations

# ✓ Toujours commiter les migrations avec le code qui les génère
git add backend/apps/games/migrations/0005_add_bonus_type.py
git add backend/apps/games/models.py
git commit -m "feat(games): ajouter le champ bonus_type au GameAnswer"

# ✗ Ne JAMAIS modifier une migration déjà mergée sur main
# Créez plutôt une nouvelle migration "corrective"
```

### Bonnes pratiques

```python
# ✓ Migrations atomiques (une modification = une migration)
# 0005_add_bonus_type.py : seulement ajouter bonus_type

# ✗ Ne pas mélanger des modifications sans rapport
# 0005_multiple_changes.py : ajouter bonus_type + modifier score + renommer champ

# ✓ Vérifier les migrations avant de commiter
python manage.py migrate --check
python manage.py showmigrations

# ✓ Data migrations pour les transformations de données
# Utiliser RunPython pour les migrations complexes
class Migration(migrations.Migration):
    def forwards_func(apps, schema_editor):
        Game = apps.get_model("games", "Game")
        for game in Game.objects.filter(status='in_progress'):
            game.status = 'cancelled'
            game.save()

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
```

---

## 6. Variables d'environnement

### Règle principale

**Toute nouvelle variable d'environnement doit être documentée dans `.env.example`.**

```bash
# .env.example (toujours à jour avec les commentaires)

# Django
DJANGO_SECRET_KEY=your-secret-key-here    # Générer: python -c "import secrets; print(secrets.token_hex(50))"
DJANGO_DEBUG=True                          # False en production

# Nouvelle variable ajoutée : documenter ici !
MY_NEW_SERVICE_API_KEY=                   # Clé API pour le service X. Obtenir sur https://...
```

### Ce qu'il ne faut jamais faire

```bash
# ✗ Valeurs sensibles dans le code
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"  # bandit B105

# ✗ Valeurs dans les fichiers de config Django
DATABASES = {
    'default': {
        'PASSWORD': 'my-real-password',  # ✗
    }
}

# ✓ Toujours depuis os.environ
import os
DATABASES = {
    'default': {
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),  # ✓
    }
}
```

---

## 7. Sécurité

### Checklist développeur

```
Avant chaque PR :

[ ] Aucun secret hardcodé (passer bandit)
[ ] Toutes les entrées utilisateur sont validées (DRF serializers)
[ ] Les endpoints privés nécessitent authentification (IsAuthenticated)
[ ] Pas de requêtes SQL brutes non paramétrées
[ ] Pas de eval() ou exec() sur des données utilisateur
[ ] Les téléchargements de fichiers sont validés (type, taille)
[ ] Les nouvelles variables .env sont dans .env.example
```

### Validation des entrées Django

```python
# ✓ Toujours valider avec des serializers DRF
class CreateGameSerializer(serializers.ModelSerializer):
    total_rounds = serializers.IntegerField(min_value=5, max_value=50)
    round_duration = serializers.IntegerField(min_value=10, max_value=120)
    game_mode = serializers.ChoiceField(choices=GAME_MODE_CHOICES)

    class Meta:
        model = Game
        fields = ['total_rounds', 'round_duration', 'game_mode', 'playlist']

# ✓ Permissions DRF explicites
class GameViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]  # Jamais AllowAny pour les endpoints privés
```

---

## 8. Pre-commit hooks

Les pre-commit hooks s'exécutent automatiquement avant chaque `git commit` pour empêcher de commiter du code qui ne respecte pas les conventions.

### Installation

```bash
make pre-commit-install
# ou
pip install pre-commit
pre-commit install
```

### Hooks configurés

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff              # Linting Python
      - id: ruff-format       # Formatage Python

  - repo: https://github.com/PyCQA/bandit
    hooks:
      - id: bandit            # Sécurité Python
        args: ["-c", "pyproject.toml"]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: detect-private-key  # Empêche de commiter des clés privées !
```

---

## 9. Documentation

### Quand mettre à jour la documentation

```
Changement de code                    → Action documentation
───────────────────                    ────────────────────
Nouveau endpoint API               →  Mettre à jour Swagger (docstring + serializer)
Nouveau mode de jeu                →  docs/game/02-modes-de-jeu.md
Nouveau type de bonus              →  docs/game/03-systeme-bonus.md
Nouveau achievement                →  docs/game/04-systeme-achievements.md
Nouvelle variable d'environnement  →  .env.example + docs/deployment/01-local.md
Changement d'architecture          →  docs/architecture/
```

### Documentation API avec DRF Spectacular

Les endpoints API sont auto-documentés via les docstrings Django :

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class GameViewSet(ModelViewSet):

    @extend_schema(
        summary="Créer une nouvelle partie",
        description="Crée une nouvelle partie avec les paramètres donnés. L'utilisateur devient automatiquement l'hôte.",
        request=CreateGameSerializer,
        responses={201: GameSerializer, 400: ErrorSerializer},
    )
    def create(self, request):
        ...
```

### README et changelogs

Chaque merge vers `main` (release) devrait inclure une mise à jour du `CHANGELOG.md` décrivant les changements utilisateur.

---

## 10. Résumé — Commandes essentielles

```bash
# Avant de coder
git pull origin develop
make deploy-dev
make dev-migrate

# Pendant le développement
make logs-dev          # Voir les logs
make dev-shell         # Shell Django

# Avant de commiter
make test              # Tests
make lint              # Linting
make typecheck         # Types Python
cd frontend && npm run lint  # Linting frontend

# Commiter
git add <fichiers-spécifiques>   # Jamais git add -A
git commit -m "type(scope): description"

# Créer une PR
git push -u origin feature/ma-feature
gh pr create --base develop
```
