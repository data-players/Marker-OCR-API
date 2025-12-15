# Tests réels avec Marker et fichiers PDF

Ce guide explique comment tester Marker avec de vrais fichiers PDF pour observer les logs et les sous-étapes détaillées.

## 🎯 Objectif

Tester Marker avec des fichiers PDF réels pour :
- Observer les logs générés par Marker pendant le traitement
- Vérifier que les sous-étapes détaillées sont capturées
- Déboguer le système de suivi de progression

## 📋 Prérequis

- Docker et Docker Compose installés
- Fichiers PDF de test dans `test/file-to-parse/`

## 🚀 Utilisation rapide

### Méthode 1 : Script automatique (recommandé)

```bash
# Construire, démarrer et exécuter le test
./test-real-pdf.sh test

# Ou avec make
make test-real-pdf
```

### Méthode 2 : Commandes individuelles

```bash
# 1. Construire l'image de test (première fois uniquement)
./test-real-pdf.sh build
# ou
make test-real-pdf-build

# 2. Démarrer les services
./test-real-pdf.sh start

# 3. Exécuter le test
./test-real-pdf.sh test

# 4. Ouvrir un shell interactif pour explorer
./test-real-pdf.sh shell
# ou
make test-real-pdf-shell

# 5. Voir les logs en temps réel
./test-real-pdf.sh logs
# ou
make test-real-pdf-logs

# 6. Arrêter les services
./test-real-pdf.sh stop
# ou
make test-real-pdf-stop
```

## 🔍 Commandes disponibles

| Commande | Description |
|----------|-------------|
| `./test-real-pdf.sh build` | Construire l'image Docker avec Marker |
| `./test-real-pdf.sh start` | Démarrer les services |
| `./test-real-pdf.sh test` | Exécuter le test complet (build + start + test) |
| `./test-real-pdf.sh shell` | Ouvrir un shell interactif dans le conteneur |
| `./test-real-pdf.sh logs` | Voir les logs en temps réel |
| `./test-real-pdf.sh stop` | Arrêter les services |

## 📁 Structure des fichiers

```
Marker-OCR-API/
├── docker-compose.test-real.yml    # Configuration Docker Compose pour tests réels
├── backend/
│   ├── Dockerfile.test-real        # Dockerfile avec dépendances Marker complètes
│   └── test_marker_logs.py         # Script de test Python
├── test/
│   └── file-to-parse/
│       └── exemple_facture.pdf    # Fichier PDF de test
└── test-real-pdf.sh                # Script principal de test
```

## 🧪 Exécution manuelle dans le conteneur

Si vous préférez exécuter les commandes manuellement :

```bash
# Démarrer le conteneur
docker-compose -f docker-compose.test-real.yml up -d

# Exécuter le script de test
docker-compose -f docker-compose.test-real.yml exec backend-test-real \
  bash -c "export MARKER_DEBUG_LOGS=1 && python3 /app/test_marker_logs.py"

# Ou ouvrir un shell interactif
docker-compose -f docker-compose.test-real.yml exec backend-test-real bash

# Dans le shell, vous pouvez :
python3 /app/test_marker_logs.py
pytest tests/ -v
python3 -c "from app.services.document_parser import DocumentParserService; print('OK')"
```

## 📊 Ce qui est testé

Le script de test vérifie :

1. **Détection des sous-étapes** : Vérifie que les sous-étapes sont capturées pendant le traitement
2. **Logs Marker** : Affiche tous les logs générés par Marker (si `MARKER_DEBUG_LOGS=1`)
3. **Génération Markdown** : Vérifie que le Markdown est généré correctement
4. **Callbacks de progression** : Teste le système de callbacks pour le suivi en temps réel

## 🔧 Configuration

### Variables d'environnement

Le conteneur de test utilise ces variables :

- `MARKER_DEBUG_LOGS=1` : Active l'affichage de tous les logs Marker
- `LOG_LEVEL=DEBUG` : Active les logs de debug
- `PYTHONPATH=/app` : Configure le chemin Python

### Volumes montés

- `./backend:/app:ro` : Code de l'application (lecture seule)
- `./shared/uploads:/app/uploads` : Répertoire d'upload
- `./shared/outputs:/app/outputs` : Répertoire de sortie
- `./test:/app/../test:ro` : Répertoire de test avec PDFs

## 🐛 Débogage

### Voir tous les logs Marker

Les logs Marker sont affichés automatiquement si `MARKER_DEBUG_LOGS=1` est défini.

### Tester avec un autre fichier PDF

1. Placez votre PDF dans `test/file-to-parse/`
2. Modifiez `backend/test_marker_logs.py` pour pointer vers votre fichier
3. Exécutez `./test-real-pdf.sh test`

### Vérifier que Marker est installé

```bash
docker-compose -f docker-compose.test-real.yml exec backend-test-real \
  python3 -c "import marker; print('Marker version:', marker.__version__)"
```

## ⚠️ Notes importantes

1. **Première construction** : La première construction de l'image peut prendre 5-10 minutes car elle télécharge les modèles ML de Marker.

2. **Espace disque** : Les modèles Marker nécessitent plusieurs Go d'espace disque.

3. **Mémoire** : Le traitement de PDF nécessite au moins 4 Go de RAM.

4. **Différence avec Dockerfile.test** :
   - `Dockerfile.test` : Léger, sans Marker (pour tests unitaires rapides)
   - `Dockerfile.test-real` : Complet, avec Marker (pour tests réels sur PDF)

## 📝 Exemple de sortie

```
========================================
Testing Marker log capture with real PDF
========================================
📄 Processing: /app/../test/file-to-parse/exemple_facture.pdf
--------------------------------------------------------------------------------
📊 Step: Model Initialization -> in_progress
[MARKER LOG] INFO: marker.converters.pdf: Loading PDF...
[MARKER LOG] INFO: marker.renderers.markdown: Rendering page 1...
✅ Sub-step detected: 📄 Loading PDF pages
✅ Sub-step detected: 🔍 Analyzing document layout
✅ Sub-step detected: 🎨 Rendering Markdown output
--------------------------------------------------------------------------------
✅ Processing completed!
📝 Sub-steps captured: 8
  1. 📄 Loading PDF pages
  2. 🔍 Analyzing document layout
  3. 🤖 Initializing AI models for text detection
  4. 📝 Extracting text for Markdown
  5. 📊 Processing tables and formatting
  6. 🎨 Rendering Markdown output
  7. ✅ Markdown conversion completed
  8. 📊 Finalizing table structures
📄 Markdown length: 1234 characters
```

## 🔗 Voir aussi

- [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) - Guide complet du Makefile
- [TEST_MARKER_LOGS.md](TEST_MARKER_LOGS.md) - Guide pour tester les logs Marker
- [README.md](README.md) - Documentation principale





