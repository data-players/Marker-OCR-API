# Guide Complet des Tests - Marker OCR API

> **Documentation complète et centralisée des tests**
> Tout ce qui concerne les tests est ici, dans `tests/`

## Table des Matières

1. [Règle Absolue de Centralisation](#règle-absolue-de-centralisation)
2. [Architecture des Tests](#architecture-des-tests)
3. [Organisation avec Pytest Marks](#organisation-avec-pytest-marks)
4. [Structure des Répertoires](#structure-des-répertoires)
5. [Exécution des Tests](#exécution-des-tests)
6. [Commandes Make](#commandes-make)
7. [Configuration Docker](#configuration-docker)
8. [Écrire de Nouveaux Tests](#écrire-de-nouveaux-tests)
9. [CI/CD et Vérification](#cicd-et-vérification)
10. [Référence Complète](#référence-complète)

---

## Règle Absolue de Centralisation

### 🚨 RÈGLE CRITIQUE

**TOUS les fichiers liés aux tests DOIVENT être dans `tests/`**

```
✅ AUTORISÉ
tests/
├── TESTING.md          # Ce fichier - documentation complète
├── pytest.ini          # Configuration pytest
├── .gitignore          # Artifacts de test
├── backend/            # Tests backend
│   ├── conftest.py
│   ├── modelFree/      # Tests unitaires
│   └── FullStack/      # Tests d'intégration
└── frontend/           # Tests frontend

❌ INTERDIT
pytest.ini              # Racine - INTERDIT
backend/test_*.py       # Backend - INTERDIT
frontend/src/*.test.jsx # Frontend - INTERDIT
tests/local/            # Tests manuels - INTERDIT (supprimé)
```

### Vérification

```bash
# Vérifier qu'aucun test n'existe hors de tests/
find . -name "test_*.py" -o -name "*.test.jsx" | grep -v "tests/" || echo "✓ All tests centralized"
```

---

## Architecture des Tests

### Philosophie

**Principe fondamental**: Tests 100% conteneurisés avec Docker + Make + Pytest

- ✅ **Conteneurisé** - Aucune dépendance locale
- ✅ **Reproductible** - Identique partout (local, CI/CD)
- ✅ **Organisé** - Pytest marks pour flexibilité
- ✅ **Rapide** - Tests unitaires < 1s
- ✅ **Complet** - Tests d'intégration avec ML

### Deux Niveaux de Tests

#### 1. Tests modelFree (Rapides)

**Conteneur**: `backend-test-modelfree`

```yaml
Objectif: Tests unitaires sans ML
Build: ~30 secondes
Exécution: < 1 seconde
Dependencies: requirements-minimal.txt
Cas d'usage: TDD, développement rapide
```

**Caractéristiques**:
- Services mockés
- Pas de modèles ML
- Tests unitaires purs
- Feedback instantané

**Exécution**:
```bash
make test-backend-modelFree
make test-by-mark MARK=unit
```

#### 2. Tests FullStack (Intégration)

**Conteneur**: `backend-test-fullstack`

```yaml
Objectif: Tests d'intégration avec ML
Build: ~7 minutes
Exécution: ~1 seconde par test
Dependencies: minimal + base + models
Cas d'usage: Validation complète, CI/CD
```

**Caractéristiques**:
- Services réels
- Modèles ML Marker complets
- Traitement réel de PDFs
- Tests end-to-end

**Exécution**:
```bash
make test-backend-FullStack
make test-by-mark MARK=integration
make test-by-mark MARK=ml
```

---

## Organisation avec Pytest Marks

### Marks Disponibles

| Mark | Description | Conteneur | Temps Typique |
|------|-------------|-----------|---------------|
| `unit` | Tests unitaires isolés | modelFree | < 100ms |
| `integration` | Tests d'intégration | FullStack | ~1s |
| `api` | Tests d'endpoints API | FullStack | Variable |
| `ml` | Tests nécessitant ML | FullStack | > 1s |
| `slow` | Tests lents | FullStack | > 5s |
| `modelfree` | Sans ML | modelFree | < 1s |
| `fullstack` | Avec ML complet | FullStack | Variable |

### Application des Marks

**Au niveau du module** (recommandé):

```python
"""Test file description."""
import pytest

# Marks au niveau du module
pytestmark = [pytest.mark.unit, pytest.mark.modelfree]

class TestMyFeature:
    def test_something(self):
        assert True
```

**Au niveau de la classe**:

```python
@pytest.mark.integration
@pytest.mark.ml
class TestIntegration:
    def test_with_marker(self):
        pass
```

### Exécution par Marks

```bash
# Afficher les marks
make test-marks

# Exécuter par mark
make test-by-mark MARK=unit
make test-by-mark MARK=integration
make test-by-mark MARK=ml

# Expressions complexes
make test-by-mark MARK="integration and ml"
make test-by-mark MARK="not slow"
make test-by-mark MARK="unit or integration"
```

---

## Structure des Répertoires

### Arborescence Complète

```
tests/
├── TESTING.md                     # ← Ce fichier (documentation complète)
├── pytest.ini                     # Configuration pytest
├── .gitignore                     # Artifacts ignorés
│
├── backend/
│   ├── conftest.py               # Fixtures partagées backend
│   │
│   ├── modelFree/                # Tests unitaires (28 tests, < 1s)
│   │   ├── conftest.py           # Fixtures avec mocks
│   │   └── test_services/
│   │       ├── test_file_handler.py      # @unit @modelfree
│   │       └── test_serialization.py     # @unit @modelfree
│   │
│   └── FullStack/                # Tests d'intégration (6 tests)
│       ├── conftest.py           # Fixtures avec services réels
│       ├── file-to-parse/        # PDFs de test
│       │   ├── exemple_facture.pdf
│       │   └── LECLERC.pdf
│       ├── test_api_url_upload_integration.py  # @integration @ml @api
│       └── test_marker_output.py               # @integration @ml
│
└── frontend/                      # Tests frontend (1 test)
    └── src/
        └── App.test.jsx
```

### Organisation des Tests Backend

#### `backend/modelFree/` - Tests Sans ML

**Objectif**: Tests unitaires rapides sans dépendances ML

| Aspect | Détail |
|--------|--------|
| **Exécution** | < 1s (startup) |
| **Dépendances** | Mock services, pas de modèles ML |
| **Container** | `backend-test-modelfree` |
| **Dockerfile** | `backend/Dockerfile.test-modelFree` |
| **Build Time** | ~30 secondes |

**Tests Disponibles**:
- `test_services/test_file_handler.py` - Tests du gestionnaire de fichiers (mocks)
- `test_services/test_serialization.py` - Tests de sérialisation (mocks)

**Usage**:
```bash
# Tous les tests modelFree
make test-backend-modelFree

# Docker direct
docker compose -f docker-compose.test-modelFree.yml run --rm \
  backend-test-modelfree pytest /tests/backend/modelFree/ -v
```

#### `backend/FullStack/` - Tests Avec ML

**Objectif**: Tests d'intégration end-to-end avec traitement Marker réel

| Aspect | Détail |
|--------|--------|
| **Exécution** | ~1s par test (ML loading) |
| **Dépendances** | Marker complet avec modèles ML |
| **Container** | `backend-test-fullstack` |
| **Dockerfile** | `backend/Dockerfile.test-FullStack` |
| **Build Time** | ~7 minutes |

**Tests Disponibles**:
- `test_api_url_upload_integration.py` - Tests d'intégration API avec traitement réel
- `test_marker_output.py` - Tests de sortie Marker
- `file-to-parse/` - PDFs de test pour traitement réel:
  - `exemple_facture.pdf` - Facture exemple
  - `LECLERC.pdf` - Document LECLERC

**Usage**:
```bash
# Tous les tests FullStack
make test-backend-FullStack

# Docker direct
docker compose -f docker-compose.test-FullStack.yml run --rm \
  backend-test-fullstack pytest /tests/backend/FullStack/ -v
```

### Organisation des Tests Frontend

#### `frontend/src/` - Tests React/Jest

**Objectif**: Tests de composants React

| Aspect | Détail |
|--------|--------|
| **Exécution** | ~5s |
| **Framework** | Jest + React Testing Library |
| **Container** | `frontend-test` |
| **Config** | `frontend/jest.config.js` |

**Tests Disponibles**:
- `App.test.jsx` - Tests du composant App principal

**Usage**:
```bash
# Tests frontend
make test-frontend

# Docker direct
docker compose -f docker-compose.test-modelFree.yml run --rm frontend-test
```

### Fichiers de Configuration

- **`tests/pytest.ini`**: Configuration pytest complète (marks, logging, etc.)
- **`tests/.gitignore`**: Artifacts de test ignorés
- **`tests/backend/conftest.py`**: Fixtures partagées backend
- **`frontend/jest.config.js`**: Config Jest pointant vers `tests/frontend/`

---

## Exécution des Tests

### Tests Complets

```bash
# Suite complète (~30s)
make test

# Détail de l'exécution:
# 1. Build des images Docker (si nécessaire)
# 2. Tests modelFree (28 tests, < 1s)
# 3. Tests FullStack (6 tests, ~1s)
# 4. Tests frontend (1 test, ~5s)
# 5. Résumé et statut
```

### Tests Rapides

```bash
# Tests rapides uniquement (~6s)
make test-quick

# Inclut:
# - Tests modelFree (backend)
# - Tests frontend
# (Exclut: Tests FullStack ML)
```

### Tests par Conteneur

```bash
# Tests unitaires (modelFree)
make test-backend-modelFree        # < 1s

# Tests intégration (FullStack)
make test-backend-FullStack        # ~1s

# Tests frontend
make test-frontend                 # ~5s
```

### Tests par Mark

```bash
# Tests unitaires uniquement
make test-by-mark MARK=unit

# Tests d'intégration
make test-by-mark MARK=integration

# Tests ML
make test-by-mark MARK=ml

# Tests API
make test-by-mark MARK=api

# Combinaisons
make test-by-mark MARK="integration and ml"
make test-by-mark MARK="not slow"
```

### Tests avec Coverage

```bash
# Coverage backend
make test-backend-modelFree-report

# Rapport généré dans:
# test-results/backend-coverage/index.html
```

### Tests en Mode Watch

```bash
# Backend (re-exécute sur changement)
make test-watch-backend

# Frontend (re-exécute sur changement)
make test-watch-frontend
```

---

## Commandes Make

### Commandes Principales

```bash
# Tests
make test                          # Tous les tests (~30s)
make test-quick                    # Tests rapides (~6s)
make test-backend-modelFree        # Unit tests (< 1s)
make test-backend-FullStack        # Integration tests (~1s)
make test-frontend                 # Frontend tests (~5s)

# Organisation
make test-marks                    # Afficher marks disponibles
make test-by-mark MARK=unit        # Tests par mark

# Vérification
# Tous les tests sont centralisés dans tests/

# Build
make build-test                    # Build toutes images test
make build-test-modelFree          # Build image modelFree
make build-test-FullStack          # Build image FullStack

# Debugging
make test-FullStack-shell          # Shell interactif FullStack
make test-FullStack-logs           # Logs FullStack
make test-FullStack-stop           # Arrêter services
```

### Commandes Docker Directes

```bash
# Tests modelFree
docker compose -f docker-compose.test-modelFree.yml run --rm \
  backend-test-modelfree pytest /tests/backend/modelFree/ -v

# Tests FullStack
docker compose -f docker-compose.test-FullStack.yml run --rm \
  backend-test-fullstack pytest /tests/backend/FullStack/ -v

# Tests avec mark
docker compose -f docker-compose.test-modelFree.yml run --rm \
  backend-test-modelfree pytest -m unit -v

# Shell interactif
docker compose -f docker-compose.test-FullStack.yml run --rm \
  backend-test-fullstack bash
```

---

## Configuration Docker

### Fichiers Docker Compose

#### docker-compose.test-modelFree.yml

```yaml
Services:
- backend-test-modelfree  # Tests unitaires Python
- frontend-test           # Tests React

Volumes:
- ./backend:/app:ro       # Code backend (lecture seule)
- ./tests:/tests:ro       # Tests (lecture seule)
- ./shared/uploads        # Uploads (écriture)

Working Directory: /tests
```

#### docker-compose.test-FullStack.yml

```yaml
Services:
- backend-test-fullstack  # Tests intégration Python + ML
- redis-test              # Redis pour tests

Volumes:
- ./backend:/app:ro       # Code backend (lecture seule)
- ./tests:/tests:ro       # Tests (lecture seule)
- ./shared/uploads        # Uploads (écriture)

Working Directory: /tests
```

### Dockerfiles

#### Dockerfile.test-modelFree

```dockerfile
FROM python:3.11-slim
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt
COPY . .
WORKDIR /app
ENV PYTHONPATH=/app
ENV ENVIRONMENT=test
```

**Build**: ~30s  
**Size**: ~500MB  
**Usage**: Tests unitaires rapides

#### Dockerfile.test-FullStack

```dockerfile
FROM python:3.11-slim
# ML dependencies (tesseract, poppler, etc.)
COPY requirements-models.txt requirements-minimal.txt requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-models.txt
RUN pip install --no-cache-dir -r requirements-minimal.txt
RUN pip install --no-cache-dir -r requirements-base.txt
COPY . .
WORKDIR /app
ENV PYTHONPATH=/app
ENV ENVIRONMENT=test
```

**Build**: ~7min  
**Size**: ~5GB  
**Usage**: Tests d'intégration avec ML

---

## Écrire de Nouveaux Tests

### Test Unitaire (modelFree)

**1. Créer le fichier**

```bash
# Emplacement
tests/backend/modelFree/test_services/test_my_service.py
```

**2. Écrire le test**

```python
"""
Unit tests for MyService.
Fast tests without external dependencies.
"""
import pytest

# Marks au niveau du module
pytestmark = [pytest.mark.unit, pytest.mark.modelfree]


class TestMyService:
    """Test cases for MyService."""

    def test_my_function(self, file_handler_service):
        """Test my function with mocked dependencies."""
        result = file_handler_service.my_method()
        assert result is not None
        assert result.status == "success"
```

**3. Exécuter**

```bash
make test-by-mark MARK=unit
# ou
make test-backend-modelFree
```

### Test d'Intégration (FullStack)

**1. Créer le fichier**

```bash
# Emplacement
tests/backend/FullStack/test_my_integration.py
```

**2. Écrire le test**

```python
"""
Integration tests for MyFeature with real Marker processing.
"""
import pytest

# Marks au niveau du module
pytestmark = [pytest.mark.integration, pytest.mark.fullstack, pytest.mark.ml]


class TestMyIntegration:
    """Integration tests with real services."""

    @pytest.mark.asyncio
    async def test_real_processing(self, document_parser_service):
        """Test real PDF processing with Marker models."""
        pdf_path = "/tests/backend/FullStack/file-to-parse/exemple_facture.pdf"
        
        result = await document_parser_service.parse_document(
            file_path=pdf_path,
            output_format="markdown"
        )
        
        assert result is not None
        assert "markdown" in result
        assert len(result["markdown"]) > 0
```

**3. Exécuter**

```bash
make test-by-mark MARK=integration
# ou
make test-backend-FullStack
```

### Test Frontend

**1. Créer le fichier**

```bash
# Emplacement
tests/frontend/src/MyComponent.test.jsx
```

**2. Écrire le test**

```javascript
import { render, screen } from '@testing-library/react'
import MyComponent from 'MyComponent'  // Via modulePaths

test('renders my component', () => {
  render(<MyComponent />)
  const element = screen.getByTestId('my-component')
  expect(element).toBeInTheDocument()
})
```

**3. Exécuter**

```bash
make test-frontend
```

### Bonnes Pratiques

#### ✅ À FAIRE

- Créer tests dans `tests/backend/` ou `tests/frontend/`
- Ajouter marks appropriés (`@pytest.mark.unit`, etc.)
- Utiliser mocks pour tests unitaires
- Utiliser services réels pour tests d'intégration
- Documenter le test avec docstrings
- Garder tests < 100ms pour unit tests
- Un test = une fonctionnalité

#### ❌ À ÉVITER

- Tests hors de `tests/`
- Tests sans marks
- Tests unitaires lents (> 100ms)
- Tests d'intégration sans mark `integration`
- Tests qui dépendent d'autres tests
- Tests avec side effects non nettoyés
- Hardcoding de chemins

---

## CI/CD et Vérification

### Vérification de la Centralisation

Tous les tests sont maintenant centralisés dans `tests/`. Les règles dans `.cursorrules` et cette documentation assurent que cette structure est maintenue.

### Intégration CI/CD

#### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run all tests
        run: make test
```

#### GitLab CI

```yaml
test:
  stage: test
  script:
    - make test
  artifacts:
    reports:
      junit: test-results/*.xml
```

### Métriques de Performance

| Catégorie | Nombre | Temps | Status |
|-----------|--------|-------|--------|
| Backend modelFree | 28 tests | 0.32s | ✅ |
| Backend FullStack | 6 tests | 0.97s | ✅ |
| Frontend | 1 test | 5.9s | ✅ |
| **Total** | **35 tests** | **~7s** | **✅** |

---

## Référence Complète

### Configuration pytest.ini

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = /tests

# Markers
markers =
    unit: Fast unit tests (< 100ms)
    integration: Integration tests
    api: API endpoint tests
    ml: Tests requiring ML models
    slow: Slow tests (> 5s)
    modelfree: Without ML dependencies
    fullstack: With full ML stack

# Options
addopts = -v --strict-markers --tb=short --color=yes
asyncio_mode = auto

# Logging (disabled for read-only volumes)
log_cli = false
log_cli_level = INFO
```

### Structure Complète

```
Marker-OCR-API/
├── tests/                              ← TOUT est ici
│   ├── TESTING.md                      ← Cette documentation
│   ├── pytest.ini                      ← Config pytest
│   ├── .gitignore                      ← Artifacts
│   │
│   ├── backend/
│   │   ├── conftest.py                 ← Fixtures backend
│   │   ├── modelFree/                  ← 28 tests unitaires
│   │   │   ├── conftest.py
│   │   │   └── test_services/
│   │   │       ├── test_file_handler.py
│   │   │       └── test_serialization.py
│   │   └── FullStack/                  ← 6 tests intégration
│   │       ├── conftest.py
│   │       ├── file-to-parse/
│   │       │   ├── exemple_facture.pdf
│   │       │   └── LECLERC.pdf
│   │       ├── test_api_url_upload_integration.py
│   │       └── test_marker_output.py
│   │
│   └── frontend/                       ← 1 test React
│       └── src/
│           └── App.test.jsx
│
├── backend/                            ← Code backend
│   ├── app/
│   ├── Dockerfile
│   ├── Dockerfile.test-modelFree       ← Image test légère
│   └── Dockerfile.test-FullStack       ← Image test complète
│
├── frontend/                           ← Code frontend
│   ├── src/
│   └── jest.config.js                  ← Pointe vers tests/frontend/
│
├── docker-compose.test-modelFree.yml   ← Config test modelFree
├── docker-compose.test-FullStack.yml   ← Config test FullStack
├── Makefile                            ← Commandes principales
├── .cursorrules                        ← Règles projet
└── README.md                           ← Documentation projet
```

### Commandes Complètes

```bash
# Tests
make test                              # Tous (~30s)
make test-quick                        # Rapides (~6s)
make test-unit                         # Unit (< 1s)
make test-integration                  # Integration (~1s)
make test-frontend                     # Frontend (~5s)
make test-mark MARK=unit               # Par mark
make test-marks                        # Liste marks

# Build
make build-test                        # Toutes images
make build-test-modelFree              # Image modelFree
make build-test-FullStack              # Image FullStack

# Debug
make test-FullStack-shell              # Shell interactif
make test-FullStack-logs               # Logs
make test-watch-backend                # Watch mode

# Coverage
make test-backend-modelFree-report     # Avec coverage

# Développement
make dev                               # Start dev environment
make dev-backend                       # Backend only
make dev-frontend                      # Frontend only
```

### Résolution de Problèmes

#### Tests non trouvés

```bash
# Vérifier working directory
docker compose -f docker-compose.test-modelFree.yml run --rm \
  backend-test-modelfree pwd
# Doit afficher: /tests

# Vérifier pytest.ini
docker compose -f docker-compose.test-modelFree.yml run --rm \
  backend-test-modelfree cat /tests/pytest.ini
```

#### Erreurs de chemin

```bash
# Chemins corrects dans conteneur:
# - Code backend: /app
# - Tests: /tests
# - pytest.ini: /tests/pytest.ini
# - Working dir: /tests
```

#### Permissions

```bash
# Les volumes sont montés en lecture seule sauf:
# - /app/uploads (écriture)
# - /app/outputs (écriture)
```

---

## Résumé

### Points Clés

✅ **Centralisation Absolue** - TOUT dans `tests/`  
✅ **100% Docker** - Aucune dépendance locale  
✅ **Pytest Marks** - Organisation flexible  
✅ **Deux Niveaux** - modelFree (rapide) + FullStack (ML)  
✅ **Make Commands** - Interface simple et cohérente  
✅ **Règles Strictes** - Voir `.cursorrules`  
✅ **Documentation Unique** - Ce fichier contient TOUT  
✅ **CI/CD Ready** - Configuration pour pipelines  

### Commandes Essentielles

```bash
make test              # Tous les tests
make test-quick        # Tests rapides
make test-marks        # Voir marks disponibles
make help              # Toutes les commandes
```

### Contact et Support

Pour toute question sur les tests:
1. Lire ce document (`tests/TESTING.md`)
2. Consulter `.cursorrules` (section Test Organization)
3. Consulter `README.md` à la racine

---

**Dernière mise à jour**: Décembre 2024  
**Version**: 2.0  
**Status**: ✅ Tests 100% centralisés et documentés

