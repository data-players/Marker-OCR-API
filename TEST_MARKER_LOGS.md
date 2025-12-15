# Test des logs Marker

Ce guide explique comment tester la capture des logs Marker pour voir les sous-étapes détaillées pendant le rendu Markdown.

## Méthode 1 : Via l'API (recommandé)

1. **Démarrer les services Docker** :
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. **Activer le mode debug** (dans le conteneur backend) :
```bash
docker-compose -f docker-compose.dev.yml exec backend-dev bash -c "export MARKER_DEBUG_LOGS=1"
```

3. **Télécharger et traiter le PDF via l'API** :
```bash
curl -X POST "http://localhost:8000/api/documents/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test/file-to-parse/exemple_facture.pdf" \
  -F "output_format=markdown" \
  -F "extract_images=false"
```

4. **Observer les logs** :
```bash
docker-compose -f docker-compose.dev.yml logs -f backend-dev | grep "MARKER LOG"
```

## Méthode 2 : Script de test direct

1. **Exécuter le script de test dans le conteneur** :
```bash
docker-compose -f docker-compose.dev.yml exec backend-dev bash -c "export MARKER_DEBUG_LOGS=1 && python3 /app/test_marker_logs.py"
```

## Ce qu'il faut observer

- Les logs Marker apparaissent avec le préfixe `[MARKER LOG]`
- Les sous-étapes détectées apparaissent avec `✅ Sub-step detected:`
- Si aucun log Marker n'apparaît, cela signifie que Marker ne génère pas de logs détaillés pendant le rendu

## Résolution du problème

Si Marker ne génère pas de logs détaillés, il faudra :
1. Instrumenter manuellement le processus de rendu
2. Diviser l'appel `markdown_converter(file_path)` en plusieurs étapes mesurables
3. Utiliser des hooks/intercepteurs si disponibles dans Marker



