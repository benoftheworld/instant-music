# Linters & Qualité du code

## Vue d'ensemble des outils

| Outil       | Langage / Cible | Rôle                                        | Config                              |
|-------------|-----------------|---------------------------------------------|-------------------------------------|
| **ruff**    | Python          | Lint + formatage (remplace black, flake8, isort) | `pyproject.toml` (racine)      |
| **bandit**  | Python          | Scan de sécurité (OWASP)                    | `pyproject.toml` + `_devops/linter/.bandit.yml` |
| **mypy**    | Python          | Vérification statique des types             | `backend/pyproject.toml`            |
| **hadolint**| Dockerfile      | Bonnes pratiques Docker                     | `_devops/linter/.hadolint.yaml`     |
| **shellcheck** | Bash         | Lint shell scripts                          | (inline CI)                         |
| **yamllint**| YAML            | Validation et style des fichiers YAML       | `_devops/linter/.yamllint.yml`      |
| **eslint**  | TypeScript      | Lint React/TypeScript                       | `frontend/.eslintrc.json`           |
| **prettier**| TS/CSS/JSON     | Formatage frontend                          | `frontend/.prettierrc`              |

---

## Lancer les linters

### Tout vérifier en une commande

```bash
make lint
```

### Par outil

```bash
# Ruff — lint Python
ruff check backend/

# Ruff — vérifier le formatage (sans modifier)
ruff format --check backend/

# Ruff — formater automatiquement
ruff format backend/

# Bandit — scan de sécurité
bandit -r backend/ -c pyproject.toml -ll -q

# Mypy — vérification des types
mypy backend/ --config-file backend/pyproject.toml

# Yamllint — YAML
yamllint -c _devops/linter/.yamllint.yml .

# Hadolint — Dockerfiles
hadolint backend/Dockerfile
hadolint backend/Dockerfile.prod

# ShellCheck — scripts bash
shellcheck _devops/script/deploy.sh _devops/script/backup.sh

# ESLint — frontend
cd frontend && npx eslint src/

# Prettier — frontend (vérification)
cd frontend && npx prettier --check src/

# Prettier — frontend (formatage)
cd frontend && npx prettier --write src/
```

---

## Configuration ruff (racine `pyproject.toml`)

Ruff remplace **black** (formatage), **isort** (tri des imports) et **flake8** (analyse statique).

**Règles activées :**

| Code  | Ensemble       | Description                   |
|-------|---------------|-------------------------------|
| `E`   | pycodestyle   | Erreurs de style PEP 8        |
| `W`   | pycodestyle   | Avertissements PEP 8          |
| `F`   | pyflakes      | Erreurs de logique Python     |
| `I`   | isort         | Ordre des imports             |
| `B`   | flake8-bugbear| Bugs potentiels et mauvaises pratiques |
| `UP`  | pyupgrade     | Syntaxe Python moderne        |
| `C90` | mccabe        | Complexité cyclomatique       |
| `N`   | pep8-naming   | Conventions de nommage        |
| `SIM` | flake8-simplify | Simplification du code      |

**Règles ignorées :**

- `E501` — longueur de ligne (gérée par le formatter)
- `B008` — appels de fonctions dans les arguments par défaut (courant en Django)
- `N806` — variable en majuscule dans une fonction (conventions QuerySet Django)

---

## Pre-commit

Les hooks s'exécutent automatiquement au `git commit`.

### Installation

```bash
make pre-commit-install
# ou
pre-commit install
```

### Hooks configurés

| Hook                | Outil          | Action                              |
|--------------------|----------------|-------------------------------------|
| `trailing-whitespace` | pre-commit  | Supprime les espaces en fin de ligne |
| `end-of-file-fixer` | pre-commit   | Ajoute un saut de ligne final        |
| `check-yaml`       | pre-commit     | Valide la syntaxe YAML               |
| `check-merge-conflict` | pre-commit | Détecte les marqueurs de conflits   |
| `check-toml`       | pre-commit     | Valide la syntaxe TOML               |
| `debug-statements` | pre-commit     | Détecte les `print()` / `breakpoint()` oubliés |
| `ruff`             | ruff-pre-commit | Lint Python + auto-fix             |
| `ruff-format`      | ruff-pre-commit | Formatage Python                   |
| `bandit`           | bandit         | Scan de sécurité Python              |
| `prettier`         | prettier       | Formatage TypeScript/CSS/JSON        |

### Lancer sur tous les fichiers (sans commit)

```bash
make pre-commit-run
# ou
pre-commit run --all-files
```

---

## CI/CD GitHub Actions

Le pipeline CI (`.github/workflows/ci.yml`) tourne les mêmes vérifications à chaque
push sur `main` ou `develop` :

```
lint-python   → ruff check + ruff format --check + bandit
lint-docker   → hadolint (tous les Dockerfiles)
lint-shell    → shellcheck (tous les .sh)
lint-yaml     → yamllint
trivy-scan    → scan CVE CRITICAL/HIGH sur les images Docker
sbom          → génération SBOM (SPDX JSON)
backend-tests → pytest
frontend-tests → vitest
```

---

## Conventions de style Python

- **Longueur de ligne** : 88 caractères (ruff default / PEP 8)
- **Guillemets** : doubles (`"string"`)
- **Imports** : ordre isort (stdlib → third-party → local), géré par ruff rule `I`
- **Typage** : progressif — `disallow_untyped_defs = true` activé sur les modules critiques de `games/` et `playlists/`
- **Migrations** : exclues du lint (auto-générées)
