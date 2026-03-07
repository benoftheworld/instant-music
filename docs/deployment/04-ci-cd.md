# CI/CD — Intégration et déploiement continus

## Vue d'ensemble

InstantMusic utilise **GitHub Actions** pour automatiser les tests, le linting et les vérifications de qualité à chaque commit et Pull Request. Ce système garantit que le code qui rejoint la branche principale respecte les standards du projet.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE CI/CD                                    │
│                                                                          │
│   Développeur                                                            │
│        │ git push feature/xxx                                            │
│        ▼                                                                 │
│   GitHub                                                                 │
│        │ Déclenche GitHub Actions                                        │
│        ▼                                                                 │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────────┐ │
│   │  Job: lint │  │ Job: test  │  │ Job: type  │  │ Job: docker-lint  │ │
│   │  ruff      │  │  pytest    │  │  mypy      │  │  hadolint         │ │
│   │  bandit    │  │  vitest    │  │            │  │  yamllint         │ │
│   │  eslint    │  │            │  │            │  │                   │ │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────────┬─────────┘ │
│         │               │               │                   │           │
│         └───────────────┴───────────────┴───────────────────┘           │
│                                     │                                   │
│                             Tous ✓ (ou ✗) ?                             │
│                                     │                                   │
│                    ✓ → PR mergeable │ ✗ → PR bloquée                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Fichier de workflow principal

### `.github/workflows/ci.yml`

```yaml
# .github/workflows/ci.yml

name: CI

# ─── Déclenchement ────────────────────────────────────────────────────────────
on:
  push:
    branches:
      - develop       # Push direct sur develop
      - main          # Push direct sur main
  pull_request:
    branches:
      - develop       # PR vers develop
      - main          # PR vers main

# ─── Variables d'environnement globales ───────────────────────────────────────
env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

# ─── Jobs ─────────────────────────────────────────────────────────────────────
jobs:

  # ─────────────────────────────────────────────────────────────────────────────
  # JOB 1 : Lint Python + Docker + YAML
  # ─────────────────────────────────────────────────────────────────────────────
  lint:
    name: "Lint"
    runs-on: ubuntu-latest

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configurer Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Installer les dépendances de lint
        run: |
          pip install ruff bandit

      - name: Ruff — Vérification du style Python
        run: |
          ruff check backend/
          ruff format --check backend/

      - name: Bandit — Analyse de sécurité
        run: |
          bandit -r backend/apps/ -c pyproject.toml --exit-zero

      - name: Hadolint — Lint des Dockerfiles
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: frontend/Dockerfile
          config: _devops/linter/.hadolint.yaml

      - name: Hadolint — Dockerfile backend
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: backend/Dockerfile
          config: _devops/linter/.hadolint.yaml

      - name: YAMLlint — Lint des fichiers YAML
        run: |
          pip install yamllint
          yamllint -c _devops/linter/.yamllint.yml .

  # ─────────────────────────────────────────────────────────────────────────────
  # JOB 2 : Tests backend (pytest)
  # ─────────────────────────────────────────────────────────────────────────────
  test-backend:
    name: "Tests Backend"
    runs-on: ubuntu-latest

    # Services Docker nécessaires aux tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_instantmusic
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurer Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Installer les dépendances Python
        run: |
          cd backend
          pip install -r requirements/test.txt

      - name: Lancer les tests pytest
        env:
          DJANGO_SETTINGS_MODULE: config.settings.test
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5432
          POSTGRES_DB: test_instantmusic
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SECRET_KEY: test-secret-key-not-for-production
        run: |
          cd backend
          pytest -q --tb=short --cov=apps --cov-report=xml

      - name: Uploader le rapport de couverture
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: backend

  # ─────────────────────────────────────────────────────────────────────────────
  # JOB 3 : Tests frontend (vitest)
  # ─────────────────────────────────────────────────────────────────────────────
  test-frontend:
    name: "Tests Frontend"
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurer Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Installer les dépendances npm
        run: |
          cd frontend
          npm ci  # Installation exacte depuis package-lock.json

      - name: ESLint — Lint TypeScript/React
        run: |
          cd frontend
          npm run lint

      - name: Vitest — Lancer les tests
        run: |
          cd frontend
          npm test -- --run --reporter=verbose --coverage

      - name: Uploader la couverture frontend
        uses: codecov/codecov-action@v4
        with:
          file: frontend/coverage/coverage-final.json
          flags: frontend

  # ─────────────────────────────────────────────────────────────────────────────
  # JOB 4 : Vérification des types Python (mypy)
  # ─────────────────────────────────────────────────────────────────────────────
  typecheck:
    name: "Type Check"
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurer Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Installer les dépendances
        run: |
          cd backend
          pip install -r requirements/base.txt
          pip install mypy django-stubs djangorestframework-stubs

      - name: Mypy — Vérification des types
        run: |
          cd backend
          mypy apps/ --ignore-missing-imports
```

---

## Déclenchement des workflows

### Règles de déclenchement

```
Événement                          Jobs déclenchés
──────────────────────────────     ───────────────────────────
push sur develop                → lint + test-backend + test-frontend + typecheck
push sur main                   → lint + test-backend + test-frontend + typecheck
PR vers develop                 → lint + test-backend + test-frontend + typecheck
PR vers main                    → lint + test-backend + test-frontend + typecheck
```

### Protection des branches

Pour configurer la protection de branche dans GitHub :
```
Paramètres du repo → Branches → Add rule
  Branch name pattern: main
  ✓ Require status checks to pass before merging
    Status checks requis: lint, test-backend, test-frontend, typecheck
  ✓ Require branches to be up to date before merging
  ✓ Require pull request reviews before merging (1 reviewer minimum)
```

---

## Dependabot — Mises à jour automatiques

Dependabot surveille les dépendances et propose automatiquement des PRs de mise à jour.

```yaml
# .github/dependabot.yml

version: 2

updates:
  # Dépendances Python (pip)
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"     # Chaque semaine
      day: "monday"
      time: "09:00"
      timezone: "Europe/Paris"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "votre-equipe"
    # Grouper les mises à jour mineures ensemble
    groups:
      django-and-drf:
        patterns:
          - "django*"
          - "djangorestframework*"
          - "channels*"
      testing:
        patterns:
          - "pytest*"
          - "factory-boy"

  # Dépendances JavaScript (npm)
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Paris"
    labels:
      - "dependencies"
      - "javascript"
    groups:
      react-ecosystem:
        patterns:
          - "react"
          - "react-dom"
          - "react-router*"
      tanstack:
        patterns:
          - "@tanstack/*"

  # Images Docker
  - package-ecosystem: "docker"
    directory: "/backend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"

  - package-ecosystem: "docker"
    directory: "/frontend"
    schedule:
      interval: "weekly"

  # GitHub Actions elles-mêmes
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
    labels:
      - "dependencies"
      - "github-actions"
```

### Workflow avec les PRs Dependabot

```
Dependabot ouvre une PR :
  "chore(deps): bump django from 5.1.0 to 5.1.1"

├── CI s'exécute automatiquement
│
├── Si CI ✓ et mise à jour mineure/patch :
│   → Peut être auto-merged (si configuré)
│
└── Si CI ✓ et mise à jour majeure :
    → Review humaine obligatoire
    → Lire le CHANGELOG de la dépendance
    → Vérifier les breaking changes
```

---

## Couverture de tests

### Objectifs de couverture

| Composant           | Couverture minimale | Cible |
| ------------------- | ------------------- | ----- |
| Backend services    | 80%                 | 90%   |
| Backend views/API   | 70%                 | 85%   |
| Backend models      | 60%                 | 80%   |
| Frontend composants | 60%                 | 80%   |
| Frontend stores     | 80%                 | 90%   |
| Frontend services   | 70%                 | 85%   |

### Voir la couverture localement

```bash
# Backend
make test-coverage
# → Ouvrir backend/htmlcov/index.html dans le navigateur

# Frontend
cd frontend && npm run test:coverage
# → Ouvrir frontend/coverage/index.html dans le navigateur
```

---

## Workflow recommandé — Du développement à la production

### Workflow complet

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DU CODE À LA PRODUCTION                              │
└─────────────────────────────────────────────────────────────────────────┘

1. CRÉER UNE BRANCHE
   ─────────────────
   git checkout develop
   git pull origin develop
   git checkout -b feature/mon-ajout


2. DÉVELOPPER
   ──────────
   # Coder + tester en local
   make test
   make lint
   make typecheck


3. OUVRIR UNE PR VERS DEVELOP
   ────────────────────────────
   git add <fichiers>
   git commit -m "feat(scope): description"
   git push -u origin feature/mon-ajout
   gh pr create --base develop --title "feat: ..." --body "..."

   → CI s'exécute automatiquement (lint + tests + typecheck)
   → Review de code par un collègue
   → Si tout ✓ → Merge squash dans develop


4. INTÉGRATION DANS DEVELOP
   ─────────────────────────
   → develop est déployé sur l'environnement de staging (si configuré)
   → Tests manuels/QA
   → Régression vérifiée


5. RELEASE VERS MAIN
   ───────────────────
   # PR de develop vers main
   gh pr create --base main --head develop \
     --title "release: v1.2.0" \
     --body "Résumé des changements..."

   → CI s'exécute sur la PR
   → Review obligatoire
   → Merge → Tag de version
   git tag v1.2.0
   git push origin v1.2.0


6. DÉPLOIEMENT PRODUCTION
   ────────────────────────
   # Sur le serveur de production
   git pull origin main
   docker compose -f _devops/docker/docker-compose.prod.yml up -d --build
   docker compose exec backend python manage.py migrate
```

### Hotfix en urgence

Pour les bugs critiques en production :

```bash
# 1. Créer la branche depuis main (pas develop)
git checkout main
git pull origin main
git checkout -b hotfix/fix-scoring-bug

# 2. Corriger le bug, tester
make test

# 3. PR vers MAIN et DEVELOP simultanément
gh pr create --base main
gh pr create --base develop

# 4. Après merge et déploiement, créer un tag
git tag v1.1.1
git push origin v1.1.1
```

---

## Analyse du temps d'exécution CI

Temps typiques des jobs :

| Job                   | Durée typique | Peut être optimisé       |
| --------------------- | ------------- | ------------------------ |
| lint                  | 1-2 min       | Cache pip                |
| test-backend          | 3-5 min       | Cache pip, DB en service |
| test-frontend         | 2-4 min       | Cache npm                |
| typecheck             | 1-2 min       | Cache pip                |
| **Total (parallèle)** | **~5-6 min**  |                          |

### Optimisations en place

1. **Cache pip/npm** : Les dépendances sont mises en cache entre les runs
2. **Jobs parallèles** : `lint`, `test-backend`, `test-frontend`, `typecheck` tournent en parallèle
3. **Services Docker** : PostgreSQL et Redis sont des services natifs GitHub Actions (pas de docker-compose)

---

## Déboguer une CI qui échoue

```bash
# 1. Lire l'output du job qui a échoué dans l'interface GitHub
# Actions → dernier run → job concerné → étape en échec

# 2. Reproduire localement
make lint           # Si le job lint a échoué
make test-backend   # Si les tests backend ont échoué
make test-frontend  # Si les tests frontend ont échoué
make typecheck      # Si mypy a échoué

# 3. Exemples d'erreurs courantes

# Ruff : ligne trop longue
# E501 Line too long (92 > 88 characters)
# → Raccourcir la ligne ou utiliser # noqa: E501 (exceptionnel)

# Pytest : fixture manquante
# fixture 'db' not found
# → Ajouter @pytest.mark.django_db au test

# Mypy : type inconnu
# error: Cannot find implementation or library stub for module named "channels"
# → Ajouter dans mypy.ini : ignore_missing_imports = true

# ESLint : hook dans une condition
# React Hook "useState" cannot be called inside a callback
# → Déplacer le hook au niveau du composant
```
