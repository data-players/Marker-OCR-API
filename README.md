# Marker OCR API

Une API moderne de traitement OCR pour documents PDF utilisant la technologie Marker, construite avec FastAPI et React.

**🔥 Développement local avec hot reloading complet !**

---

## ⚠️ Important : Structure Production/Développement

Ce repository contient **uniquement le code source et configurations de développement/tests**.

**Pour la PRODUCTION :** Voir le repo séparé `../Marker-OCR-API-prod/`

| Aspect | Ce Repo | Repo Production |
|--------|---------|-----------------|
| **Docker Compose** | Dev & Test seulement | Production avec Traefik |
| **Reverse Proxy** | ❌ Aucun | ✅ Traefik |
| **SSL/TLS** | ❌ HTTP local | ✅ Let's Encrypt auto |
| **Domaine** | localhost | ocr.data-players.com |
| **Accès** | 127.0.0.1 local | HTTPS public |
| **Hot Reload** | ✅ Activé | ❌ Désactivé |

---

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
| **Dev** 🔥 | Développement local | `make dev` | Hot reloading, volumes montés, debug |
| **Test** ⚡ | Tests automatisés | `make test` | Images légères, mocks, < 2s |

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

# Maintenance
make down                   # Arrêter tous les services
make clean                  # Nettoyer les containers
```

**📚 Pour toutes les commandes** → Voir **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)**

**⚠️ Pour la Production** → Voir `../Marker-OCR-API-prod/` (Traefik, Reverse Proxy, SSL/TLS automatique)

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
├── backend/                     # API FastAPI (port 8000)
│   ├── app/                    # Code source (hot reload)
│   ├── Dockerfile.dev          # Image développement
│   ├── Dockerfile.test         # Image test légère
│   └── Dockerfile              # Image production
├── frontend/                   # Interface React (port 3000)
│   ├── src/                    # Code source (hot reload)
│   ├── Dockerfile.dev          # Image développement
│   └── Dockerfile              # Image production
├── docker-compose.dev.yml      # Dev local (hot reloading)
├── docker-compose.test.yml     # Tests automatisés
├── Makefile                    # Commandes simplifiées
├── DOCKER_COMPOSE_GUIDE.md     # Guide des environnements
└── MAKEFILE_GUIDE.md           # Documentation complète

../Marker-OCR-API-prod/         ← PRODUCTION avec Traefik
├── docker-compose.yml          # Production avec reverse proxy
├── traefik/                    # Configuration Traefik
├── .env.example                # Variables d'environnement
└── QUICK_START.md              # Démarrage production
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

⚠️ **Les docker-compose de ce repo (dev/test) ne sont PAS pour la production !**

**Pour déployer en production :** Voir `../Marker-OCR-API-prod/`

```bash
cd ../Marker-OCR-API-prod

# Configuration
cp .env.example .env
nano .env  # Mettre à jour les passwords

# Déploiement
bash init-traefik.sh
make build
make up
```

**URLs Production :**
- Frontend : `https://ocr.data-players.com`
- Backend API : `https://api.ocr.data-players.com`
- API Docs : `https://api.ocr.data-players.com/docs`
- Traefik Dashboard : `https://traefik.ocr.data-players.com`

Voir `../Marker-OCR-API-prod/QUICK_START.md` pour démarrage 5 minutes

## 📚 Documentation

**Ce Repo (Développement & Tests) :**
- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Référence complète des commandes
- **[DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)** - Guide des environnements (dev/test)
- **[API Documentation](http://localhost:8000/docs)** - Swagger/OpenAPI automatique
- **Architecture détaillée** - Voir `.cursorrules`

**Production (Repo Séparé) :**
- **[../Marker-OCR-API-prod/QUICK_START.md](../Marker-OCR-API-prod/QUICK_START.md)** - Démarrage 5 minutes
- **[../Marker-OCR-API-prod/README.md](../Marker-OCR-API-prod/README.md)** - Documentation complète
- **[../Marker-OCR-API-prod/MIGRATION_GUIDE.md](../Marker-OCR-API-prod/MIGRATION_GUIDE.md)** - Guide migration Nginx → Traefik

## 🤝 Contribution

1. Fork le projet
2. Développer avec `make dev` (hot reloading)
3. Tester avec `make test` (< 2 secondes)
4. Pull Request

## 📜 Licence

[MIT License](LICENSE)