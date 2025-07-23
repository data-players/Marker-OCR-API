# Marker OCR API

Une API moderne de traitement OCR pour documents PDF utilisant la technologie Marker, construite avec FastAPI et React.

**🔥 Tous les environnements utilisent Docker avec hot reloading complet !**

## 🚀 Démarrage Rapide (30 secondes)

```bash
# 1. Cloner le projet
git clone <repository-url> && cd Marker-OCR-API

# 2. Setup initial (construit toutes les images Docker)
make setup

# 3. Développement avec hot reloading
make dev
```

**Prêt !** ✨
- **Frontend** : http://localhost:3000 (hot reloading)
- **API Backend** : http://localhost:8000 (hot reloading) 
- **Documentation API** : http://localhost:8000/docs

## 🏗️ Architecture

### Environnements Docker

| Environnement | Usage | Commande | Caractéristiques |
|---------------|-------|----------|------------------|
| **Dev** 🔥 | Développement | `make dev` | Hot reloading, volumes montés, debug |
| **Test** ⚡ | Tests rapides | `make test` | Images légères, mocks, < 2s |
| **Prod** 🚀 | Production | `make prod` | Images optimisées, nginx, sécurisé |

### Stack Technologique

**Backend** (Python 3.11) : FastAPI + Uvicorn, Marker OCR, Redis, Pydantic, Pytest  
**Frontend** (Node.js 18) : React 18 + Vite, Tailwind CSS, Jest + Testing Library  
**Infrastructure** : Docker + Docker Compose, Hot reloading complet

## 🛠️ Commandes Essentielles

```bash
# Développement avec hot reloading
make dev                    # Backend + Frontend + Redis 
make dev-logs               # Logs en temps réel
make dev-down               # Arrêter

# Tests ultra-rapides (< 2 secondes)
make test                   # Tous les tests
make test-backend           # Backend seulement (< 1s)
make test-frontend          # Frontend seulement (~3s)

# Production
make prod                   # Environnement production
make prod-down              # Arrêter production

# Maintenance
make down                   # Arrêter tous les services
make clean                  # Nettoyer les containers
```

**📚 Pour toutes les commandes** → Voir **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)**

## 🔥 Hot Reloading

- **Backend** : Modifiez `backend/app/` → Reload automatique ~1-2s
- **Frontend** : Modifiez `frontend/src/` → Reload instantané ~100ms
- **Volumes montés** : Code source lié directement dans les containers

## 🧪 Tests Ultra-Rapides

- **Backend** : < 1 seconde (image légère sans ML, services mockés)
- **Frontend** : ~3 secondes (Jest + Babel + Testing Library)
- **Total** : < 2 secondes pour validation complète

## 📁 Structure du Projet

```
Marker-OCR-API/
├── backend/                 # API FastAPI (port 8000)
│   ├── app/                # Code source (hot reload)
│   ├── Dockerfile.dev      # Image développement
│   ├── Dockerfile.test     # Image test légère
│   └── Dockerfile          # Image production
├── frontend/               # Interface React (port 3000)
│   ├── src/                # Code source (hot reload)
│   ├── Dockerfile.dev      # Image développement
│   └── Dockerfile          # Image production
├── docker-compose.yml      # Orchestration multi-environnements
├── Makefile               # Commandes simplifiées
└── MAKEFILE_GUIDE.md      # Documentation complète
```

## 📋 Prérequis

**Minimum requis :**
- Docker & Docker Compose
- Make (généralement préinstallé)

**C'est tout !** Aucune installation Python, Node.js ou dépendances locales nécessaire.

## 🔧 Configuration

**Backend** : Variables dans `docker-compose.yml` ou `.env`  
**Frontend** : Configuration Vite dans `vite.config.js`  
**Docker** : Profils `dev`, `test`, `production` dans `docker-compose.yml`

## 📊 Performance

| Opération | Temps | Notes |
|-----------|-------|-------|
| **Setup initial** | ~2 min | Build toutes les images |
| **Tests complets** | < 2s | Images légères + mocks |
| **Hot reload backend** | ~1-2s | Uvicorn restart |
| **Hot reload frontend** | ~100ms | Vite HMR |
| **Startup dev** | ~10s | Tous les services |

## 🐛 Dépannage Rapide

```bash
# Port occupé → Redémarrer proprement
make down && make dev

# Hot reload ne marche pas → Redémarrer environnement  
make dev-restart

# Tests lents → Utiliser image légère
make test-backend

# Problème majeur → Reset complet
make clean && make setup && make dev
```

## 🚀 Déploiement Production

```bash
make prod-build             # Build + démarrer production
make health                 # Vérification santé
make prod-logs              # Monitoring
```

**URLs Production :** Frontend (port 80), Backend (port 8000), API Docs (/docs)

## 📚 Documentation

- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - **Référence complète des commandes**
- **[API Documentation](http://localhost:8000/docs)** - Swagger/OpenAPI automatique
- **Architecture détaillée** - Voir `.cursorrules`

## 🤝 Contribution

1. Fork le projet
2. Développer avec `make dev` (hot reloading)
3. Tester avec `make test` (< 2 secondes)
4. Pull Request

## 📜 Licence

[MIT License](LICENSE)