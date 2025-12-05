# Guide Makefile - Marker OCR API

**📚 Référence technique complète de toutes les commandes disponibles**

Ce guide documente tous les targets Makefile disponibles avec leurs options et cas d'usage. Pour une introduction rapide, voir le [README.md](README.md).

## 🏗️ Architecture des Commandes

Les commandes sont organisées par **profils Docker** :

- **`dev`** → Développement avec hot reloading
- **`test`** → Tests rapides avec images légères  
- **`production`** → Déploiement optimisé

## 📋 Référence Complète

### Commandes d'Aide

```bash
make help                   # Affiche toutes les commandes disponibles avec descriptions
```

### Setup Initial

```bash
make setup                  # Setup complet : crée directories + build images dev/test
make setup-docker           # Alias pour setup
```

## 🔥 Environnement de Développement

### Démarrage/Arrêt

```bash
make dev                    # Démarrer environnement complet (backend + frontend + redis)
make dev-build              # Build + démarrer environnement de développement
make dev-down               # Arrêter environnement de développement
make dev-restart            # Arrêter puis redémarrer (dev-down + dev)
```

### Services Individuels

```bash
make dev-backend            # Backend + Redis seulement (port 8000)
make dev-frontend           # Frontend seulement (port 3000)
```

### Monitoring Développement

```bash
make dev-logs               # Logs temps réel de tous les services dev
make dev-logs-backend       # Logs backend développement seulement
make dev-logs-frontend      # Logs frontend développement seulement
```

### Accès aux Containers

```bash
make shell-backend-dev      # Bash interactif dans container backend-dev
make shell-frontend-dev     # Shell interactif dans container frontend-dev
make shell-redis            # Redis CLI
```

## 🚀 Environnement de Production

### Démarrage/Arrêt

```bash
make prod                   # Démarrer environnement production (port 80 + 8000)
make prod-build             # Build + démarrer production
make prod-down              # Arrêter environnement production
```

### Monitoring Production

```bash
make prod-logs              # Logs temps réel des services production
```

## 🧪 Tests

### Tests Rapides (Recommandés)

```bash
make test                   # Tous les tests (backend + frontend) < 2s
make test-backend           # Tests backend avec image légère < 1s
make test-frontend          # Tests frontend ~3s
```

### Tests Avancés

```bash
make test-backend-fast-report  # Tests backend + rapport HTML de couverture
make test-watch-backend     # Tests backend en mode watch (développement)
make test-watch-frontend    # Tests frontend en mode watch (développement)
```

## 🛠️ Build d'Images

### Build Global

```bash
make build                  # Build TOUTES les images (dev, test, production)
make build-dev              # Build images développement seulement
make build-test             # Build images test seulement  
make build-prod             # Build images production seulement
```

### Build par Service

```bash
make build-backend-dev      # Image backend développement
make build-frontend-dev     # Image frontend développement
make build-backend-test     # Image backend test légère
```

## 📊 Monitoring et Diagnostic

### État des Services

```bash
make status                 # État de tous les containers (ps détaillé)
make health                 # Health check basique
make logs                   # Logs de tous les services actifs
```

## 🧹 Nettoyage et Maintenance

### Nettoyage Standard

```bash
make down                   # Arrêter TOUS les services (tous profils)
make clean                  # Supprimer containers arrêtés + images non utilisées
make clean-test             # Supprimer uniquement les résultats de test
```

### Nettoyage Complet ⚠️

```bash
make clean-all              # ATTENTION: Supprime tout (containers, images, volumes)
                           # Demande confirmation utilisateur
```

## 🔧 Commandes Techniques Avancées

### Architecture des Requirements

Le projet utilise **deux fichiers de dépendances** pour optimiser les builds :

```bash
# Backend production/développement (complet)
backend/requirements.txt        # Toutes les dépendances incluant Marker/PyTorch
                               # Build time: ~7 minutes
                               # Usage: Dockerfile, Dockerfile.dev

# Backend tests (minimal)  
backend/requirements-minimal.txt # Dépendances essentielles seulement
                               # Build time: ~30 secondes
                               # Usage: Dockerfile.test (utilisé directement)
```

**Différences clés :**
- `requirements.txt` → Inclut Marker, PyTorch, dépendances ML lourdes
- `requirements-minimal.txt` → Exclut les dépendances ML, services mockés

**Architecture Dockerfile :**
```dockerfile
# Production/Développement
COPY requirements.txt .
RUN pip install -r requirements.txt

# Tests (optimisé)  
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt  # Directement !
```

### Variables d'Environnement Utilisées

```bash
COMPOSE_FILE=docker-compose.yml    # Fichier Docker Compose principal
BACKEND_DIR=backend               # Répertoire source backend
FRONTEND_DIR=frontend             # Répertoire source frontend  
TEST_RESULTS_DIR=test-results     # Répertoire de sortie des tests
```

### Profils Docker Compose

Les commandes utilisent ces profils :

```bash
# Aucun profil (services communs)
redis                       # Toujours disponible

# Profil "dev"  
backend-dev                 # Backend avec hot reloading
frontend-dev                # Frontend avec hot reloading

# Profil "test"
backend-test                # Backend avec image légère
frontend-test               # Frontend pour tests

# Profil "production" (Deprecated - use Marker-OCR-API-prod)
backend                     # Backend optimisé
frontend                    # Frontend avec serveur HTTP simple
```

## 📈 Métriques de Performance

### Temps de Build Moyens

| Target | Première fois | Rebuild | Avec cache |
|--------|---------------|---------|------------|
| `make build-dev` | ~2 min | ~30s | ~10s |
| `make build-test` | ~1 min | ~15s | ~5s |
| `make build-prod` | ~10 min | ~3 min | ~1 min |

### Temps d'Exécution

| Commande | Durée | Notes |
|----------|-------|-------|
| `make dev` | ~10s | Startup complet |
| `make test` | < 2s | Tests complets |
| `make test-backend` | < 1s | Tests backend seuls |
| `make prod` | ~15s | Startup production |

## 🔄 Workflows d'Usage

### Développement Quotidien

```bash
make dev                    # 1. Démarrer environnement
# ... développer avec hot reloading ...
make test                   # 2. Valider avant commit
make dev-down               # 3. Arrêter proprement
```

### Debug d'un Problème

```bash
make status                 # 1. Vérifier état des services
make dev-logs               # 2. Voir logs en temps réel
make shell-backend-dev      # 3. Accès shell si besoin
make dev-restart            # 4. Redémarrer si nécessaire
```

### Tests en Développement

```bash
make test-watch-backend     # Terminal 1: Tests backend continus
make test-watch-frontend    # Terminal 2: Tests frontend continus
make dev-logs               # Terminal 3: Logs développement
```

### Validation Pré-Production

```bash
make test                   # 1. Tests rapides complets
make build-prod             # 2. Build images production
make prod                   # 3. Test environnement production
make health                 # 4. Vérifier santé services
make prod-down              # 5. Arrêter après validation
```

## 🆘 Résolution de Problèmes

### Problèmes de Ports

```bash
# Erreur "port already in use"
make down                   # Arrêter tous les services
netstat -tulpn | grep :3000 # Vérifier ports occupés
make dev                    # Redémarrer
```

### Problèmes de Hot Reloading

```bash
# Hot reloading ne fonctionne pas
make dev-logs               # Vérifier erreurs
docker-compose --profile dev ps -v  # Vérifier volumes montés
make dev-restart            # Redémarrer environnement
```

### Problèmes de Cache Docker

```bash
# Cache problématique
make build-dev --no-cache   # Rebuild sans cache
make clean                  # Nettoyer images
make setup                  # Rebuild complet
```

### Problèmes de Permissions (Linux)

```bash
# Permissions sur fichiers
sudo chown -R $USER:$USER ./backend ./frontend ./shared
make dev-restart
```

### Tests Lents ou Défaillants

```bash
# Utiliser l'image légère
make test-backend           # Au lieu de tests complets

# Rebuild images de test
make build-test
make test

# Tests individuels pour debug
docker-compose --profile test run --rm backend-test pytest tests/test_services/ -v
```

## 🔍 Commandes de Diagnostic

### Informations Détaillées

```bash
# Voir configuration Docker Compose
docker-compose --profile dev config

# Inspecter une image
docker inspect marker-ocr-api-backend-dev

# Statistiques resources
docker stats

# Espace disque Docker
docker system df
```

### Logs Avancés

```bash
# Logs avec timestamps
make dev-logs --timestamps

# Logs spécifiques avec filtre
docker-compose --profile dev logs backend-dev --tail=50

# Suivre logs d'un service spécifique
docker-compose --profile dev logs -f frontend-dev
```

## 📝 Commandes Dépréciées

Ces commandes existent pour compatibilité mais sont dépréciées :

```bash
make dev-local              # DÉPRÉCIÉ: Utiliser 'make dev' 
make setup-local            # DÉPRÉCIÉ: Utiliser 'make setup'
```

---

**💡 Conseils d'utilisation :**

- **Développement** : `make dev` + `make dev-logs` (2 terminaux)
- **Tests rapides** : `make test` (< 2 secondes)
- **Validation** : `make test` + `make prod` + `make health`
- **Debug** : `make dev-logs` + `make shell-backend-dev`

**🚨 Attention :**

- `make clean-all` supprime **tout** (confirmation requise)
- Les profils Docker ne peuvent pas être mélangés
- Le hot reloading nécessite des volumes correctement montés 