# Marker OCR API

API REST pour la conversion de PDFs en Markdown utilisant Marker.

## 🚀 Démarrage Rapide

```bash
# Démarrer l'environnement de développement
make dev

# L'application est disponible à:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🧪 Tests

**TOUS les tests sont centralisés dans `tests/`**

```bash
# Exécuter tous les tests
make test

# Tests rapides (< 6s)
make test-quick

# Tests par type
make test-backend-modelFree    # Tests unitaires (< 1s)
make test-backend-FullStack    # Tests d'intégration ML
make test-frontend             # Tests React

# Vérifier la centralisation
make verify-tests
```

### Structure des Tests

```
tests/
├── pytest.ini           # Configuration pytest (centralisé ici ✅)
├── backend/
│   ├── modelFree/      # Tests unitaires sans ML (28 tests, < 1s)
│   └── FullStack/      # Tests d'intégration avec ML (6 tests)
└── frontend/           # Tests React (Jest)
```

Voir `CENTRALIZED_TESTS.md` pour les détails.

## 📚 Documentation

- **tests/TESTING.md** - Guide complet et centralisé des tests
- **MARKER_LLM_USAGE.md** - Utilisation de Marker avec LLM
- **tests/README.md** - Vue d'ensemble de la structure des tests

## 🏗️ Architecture

- **Backend**: FastAPI avec Marker pour l'OCR
- **Frontend**: React avec Vite
- **Tests**: 100% conteneurisés (Docker + Make)
- **ML**: Modèles Marker pour traitement PDF

## 🐳 Docker

```bash
# Développement (hot reload)
make dev

# Tests
make test

# Construction des images
make build-test
```

## 📋 Commandes Principales

```bash
make dev              # Démarrer développement
make test             # Tous les tests
make verify-tests     # Vérifier centralisation
make test-marks       # Voir marks pytest disponibles
make help             # Afficher toutes les commandes
```

## 🔧 Configuration

- Environnement: `.env` (voir `.env.example`)
- Tests: `tests/pytest.ini`
- Frontend: `frontend/jest.config.js`

## 📝 Conventions

- **Tests**: TOUT dans `tests/` (règle absolue)
- **Code**: Anglais (commentaires, variables)
- **Docs**: Français pour les guides utilisateur
- **Commits**: Messages en français

## 🤝 Contribution

1. Créer les tests dans `tests/`
2. Exécuter `make verify-tests`
3. S'assurer que `make test` passe
4. Commiter

## 📖 Plus d'Informations

Documentation:
- **Tests**: `tests/TESTING.md` (documentation complète centralisée)
- **Règles**: `.cursorrules` et `.cursorrules-tests`
- **API Usage**: `MARKER_LLM_USAGE.md`
