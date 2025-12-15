# Guide de Test - Système de Suivi des Étapes

## ✅ Modifications Appliquées

Tous les services ont été mis à jour et redémarrés :
- ✅ Backend redémarré avec les nouvelles modifications
- ✅ Frontend avec hot reload actif
- ✅ Redis nettoyé des anciens jobs

## 🧪 Comment Tester

### 1. Ouvrir l'Application

Ouvrez votre navigateur à l'adresse : **http://localhost:3000**

> **Important** : Si vous aviez déjà la page ouverte, faites un **rafraîchissement complet** :
> - Windows/Linux : `Ctrl + F5` ou `Ctrl + Shift + R`
> - Mac : `Cmd + Shift + R`

### 2. Télécharger un Nouveau Document

- Cliquez sur "Upload" ou glissez-déposez un fichier PDF
- Attendez que le téléchargement soit terminé

### 3. Configurer et Lancer le Traitement

- Choisissez vos options (format, qualité, etc.)
- Cliquez sur "Process Document"

### 4. Observer les Étapes en Temps Réel

Vous devriez maintenant voir :

```
Processing Steps
================

⭕ Model Initialization          [En attente]
   Loading AI models for document processing

⭕ File Validation               [En attente]
   Validating PDF file and checking accessibility

⭕ JSON Generation                [En attente]
   Generating structured JSON output

⭕ Markdown Generation            [En attente]
   Converting document to Markdown format

⭕ Metadata Extraction            [En attente]
   Extracting document metadata and images

⭕ Finalization                   [En attente]
   Finalizing results and cleanup
```

Puis, au fur et à mesure :

```
✅ Model Initialization          [2.45s]
   Loading AI models for document processing

🔄 File Validation               [En cours...]
   Validating PDF file and checking accessibility
```

Et enfin :

```
✅ Model Initialization          [2.45s]
✅ File Validation               [0.12s]
✅ JSON Generation               [3.87s]
✅ Markdown Generation           [2.34s]
✅ Metadata Extraction           [0.56s]
✅ Finalization                  [0.08s]

Summary: 6 completed | Total: 9.42s
```

## 🎨 Codes Couleur

- **Gris** (⭕) : Étape en attente
- **Bleu** (🔄) : Étape en cours (avec animation)
- **Vert** (✅) : Étape terminée (avec temps d'exécution)
- **Rouge** (❌) : Étape échouée

## 🔍 Vérifications

### Si vous voyez toujours l'ancienne barre de progression :

1. **Rafraîchissez complètement la page** (`Ctrl+F5`)
2. **Vérifiez que vous créez un NOUVEAU job** (pas un ancien)
3. **Vérifiez la console du navigateur** (F12) pour d'éventuelles erreurs

### Vérifier les logs en temps réel :

```bash
# Backend
docker compose -f docker-compose.dev.yml logs -f backend-dev

# Frontend  
docker compose -f docker-compose.dev.yml logs -f frontend-dev
```

### Vérifier qu'un nouveau job a bien le champ steps :

```bash
# Lister les jobs
docker exec marker-ocr-api-redis-1 redis-cli KEYS "job:*"

# Voir le contenu d'un job (remplacez JOB_ID)
docker exec marker-ocr-api-redis-1 redis-cli GET "job:JOB_ID" | python3 -m json.tool
```

Vous devriez voir un champ `"steps": [...]` dans la réponse.

## 📊 Différences Avant/Après

### Avant (Ancienne Version)
```
Processing Status
-----------------
Progress: 45%
[████████████░░░░░░░░░░░░░░]
```

### Après (Nouvelle Version)
```
Processing Steps
----------------
✅ Model Initialization          [2.45s]
✅ File Validation               [0.12s]
🔄 JSON Generation               [En cours...]
⭕ Markdown Generation           [En attente]
⭕ Metadata Extraction           [En attente]
⭕ Finalization                  [En attente]

Summary: 2 completed, 1 in progress
```

## 🐛 Dépannage

### Le frontend ne se met pas à jour
```bash
# Redémarrer le frontend
docker compose -f docker-compose.dev.yml restart frontend-dev

# Vider le cache du navigateur et recharger
```

### Le backend ne répond pas
```bash
# Vérifier les logs
docker compose -f docker-compose.dev.yml logs backend-dev --tail=50

# Redémarrer si nécessaire
docker compose -f docker-compose.dev.yml restart backend-dev
```

### Les étapes ne s'affichent pas
1. Vérifiez que Redis a été nettoyé
2. Créez un NOUVEAU job (pas un ancien)
3. Vérifiez la console du navigateur (F12)

## ✨ Fonctionnalités

- ✅ Suivi en temps réel de chaque étape
- ✅ Temps d'exécution précis pour chaque étape
- ✅ Temps total de traitement
- ✅ Indicateurs visuels clairs (couleurs, icônes)
- ✅ Compteurs de progression (X complétées, Y en cours)
- ✅ Rétrocompatibilité (barre de progression si pas de steps)





