# Contribuer à InstantMusic

Merci de votre intérêt pour le projet ! Ce guide explique comment contribuer.

---

## Configuration de l'environnement de développement

### 1. Prérequis

- Docker 24+ avec Docker Compose v2
- Git
- Python 3.11+ (pour les hooks pre-commit locaux)
- Node.js 20+ (pour les hooks pre-commit front)

### 2. Fork et clone

```bash
git clone https://github.com/<votre-fork>/instant-music.git
cd instant-music
```

### 3. Variables d'environnement

```bash
cp backend/.env.example backend/.env
# Les valeurs par défaut fonctionnent pour le développement local
```

### 4. Lancement

```bash
make deploy-dev
```

### 5. Installer les hooks pre-commit

```bash
pip install pre-commit
make pre-commit-install
```

---

## Workflow de contribution

### Branches

| Type          | Convention              | Exemple                       |
|---------------|-------------------------|-------------------------------|
| Fonctionnalité | `feature/<description>` | `feature/add-friend-invite`   |
| Correctif     | `fix/<description>`     | `fix/websocket-disconnect`    |
| Hotfix prod   | `hotfix/<description>`  | `hotfix/score-calculation`    |
| Documentation | `docs/<description>`    | `docs/update-architecture`    |

### Étapes

1. Créer une branche depuis `develop` (ou `main` si besoin)
2. Faire les modifications
3. S'assurer que les linters et tests passent (`make lint && make test`)
4. Committer (les hooks pre-commit s'exécutent automatiquement)
5. Ouvrir une Pull Request vers `develop`

---

## Conventions de commit

```
type(scope): description courte

Corps optionnel (pourquoi, pas quoi)

Refs #<issue>
```

**Types :**
- `feat` — nouvelle fonctionnalité
- `fix` — correction de bug
- `docs` — documentation uniquement
- `style` — formatage, pas de changement de logique
- `refactor` — refactorisation sans fix ni feature
- `test` — ajout ou modification de tests
- `chore` — maintenance (deps, config, CI)

**Exemples :**
```
feat(games): add spectator mode to game rooms
fix(auth): handle expired Google OAuth token correctly
docs(readme): update local setup instructions
```

---

## Tests

Chaque modification doit être couverte par des tests :

```bash
# Backend — pytest
make test-backend

# Frontend — vitest
make test-frontend

# Couverture de code
make test-coverage
```

### Écrire des tests backend

Les tests se trouvent dans `backend/apps/<app>/tests.py` ou `backend/apps/<app>/tests/`.

```python
# Exemple de test d'API
from rest_framework.test import APITestCase

class GameAPITests(APITestCase):
    def test_create_room(self):
        response = self.client.post("/api/games/rooms/", {...})
        self.assertEqual(response.status_code, 201)
```

**Important :** les tests CI s'exécutent sans Docker (pas de vraie DB).
Utilisez `pytest-django` avec `@pytest.mark.django_db` et des fixtures.

### Écrire des tests frontend

Les tests se trouvent dans `frontend/src/**/__tests__/` ou `.test.tsx` à côté des composants.

```tsx
// Exemple avec vitest + testing-library
import { render, screen } from "@testing-library/react";
import { QuizQuestion } from "./QuizQuestion";

test("affiche le titre de la question", () => {
  render(<QuizQuestion title="Quel est cet artiste ?" />);
  expect(screen.getByText("Quel est cet artiste ?")).toBeInTheDocument();
});
```

---

## Structure du code backend

### Ajouter une nouvelle app Django

```bash
# Dans le container
make dev-shell
python manage.py startapp <app_name>
mv <app_name> apps/
```

Puis ajouter l'app dans `backend/config/settings/base.py` → `INSTALLED_APPS`.

### Créer des migrations

```bash
make dev-makemigrations
```

Les migrations sont **versionnées** dans Git. Ne pas modifier les migrations existantes
une fois mergées sur `main`.

---

## Style de code

Voir [docs/LINTERS.md](LINTERS.md) pour la configuration complète.

**Résumé :**
- Python : ruff format (88 chars, double quotes)
- TypeScript : prettier (100 chars, single quotes, trailing commas ES5)
- YAML : yamllint (120 chars max)
- Dockerfiles : hadolint

---

## Pull Request checklist

Avant de soumettre une PR :

- [ ] Les tests passent (`make test`)
- [ ] Les linters passent (`make lint`)
- [ ] Les migrations sont incluses si le modèle change
- [ ] La documentation est mise à jour si nécessaire
- [ ] Les variables d'environnement nouvelles sont documentées dans `.env.example`
