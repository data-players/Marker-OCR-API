# Configuration Infomaniak AI API

## 🔑 Vos Identifiants

Vous avez déjà configuré vos identifiants Infomaniak dans le fichier `.env` :

```bash
LLM_PRODUCT_ID="105448"
LLM_API_TOKEN="Bearer RKx_aA2LR7bP_8N2uZlaM1ynZ2ONgul_HmGQdJSrsupRRcJrWmNiLDSGbyI029MNhf9eUulW53Sonf7G"
LLM_MODEL="mistral3"
```

## 🌐 URL de l'API

L'URL est automatiquement construite par le backend :

```
https://api.infomaniak.com/1/ai/105448/openai/chat/completions
```

Format : `https://api.infomaniak.com/1/ai/{product_id}/openai/chat/completions`

## 📖 Documentation Officielle

Référence API Infomaniak :
https://developer.infomaniak.com/docs/api/post/1/ai/%7Bproduct_id%7D/openai/chat/completions

## ✅ Configuration Actuelle

Votre configuration est **déjà prête** dans le fichier `.env` créé.

### Vérification

Pour vérifier que tout est bien configuré :

```bash
# Vérifier les variables
grep LLM_ .env

# Devrait afficher :
# LLM_PRODUCT_ID="105448"
# LLM_API_TOKEN="Bearer RKx_aA2LR7bP_8N2uZlaM1ynZ2ONgul_HmGQdJSrsupRRcJrWmNiLDSGbyI029MNhf9eUulW53Sonf7G"
# LLM_MODEL="mistral3"
# LLM_TIMEOUT=60
```

## 🚀 Démarrage

Maintenant que la configuration est en place, vous pouvez démarrer :

```bash
# Démarrer les services
make dev

# Ou si déjà démarrés, redémarrer pour prendre en compte la config
make dev-down
make dev
```

## 🧪 Test de la Configuration

### Option 1 : Via l'Interface Web

1. Ouvrir http://localhost:3000
2. Uploader un PDF
3. Lancer l'OCR
4. Cliquer sur "Start Analysis" une fois l'OCR terminé
5. Définir un schéma simple et lancer

### Option 2 : Via le Script de Test

```bash
cd /home/simon/GIT/IA/agent-tools/Marker-OCR-API
./tests/local/quick_llm_test.sh
```

### Option 3 : Test Manuel avec curl

```bash
# 1. Upload un document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@tests/backend/FullStack/test_document.pdf"

# Récupérer le file_id de la réponse

# 2. Lancer l'OCR
curl -X POST http://localhost:8000/api/v1/documents/process \
  -F "file_id=VOTRE_FILE_ID" \
  -F "output_format=markdown"

# Récupérer le job_id et attendre la complétion

# 3. Lancer l'analyse LLM
curl -X POST http://localhost:8000/api/v1/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "VOTRE_JOB_ID",
    "introduction": "Extraire les informations clés",
    "schema": {
      "title": {
        "type": "string",
        "description": "Titre du document",
        "required": true
      }
    }
  }'
```

## 🔧 Modèles Disponibles

Selon la documentation Infomaniak, vous pouvez utiliser :

- `mistral3` (configuré) - Modèle Mistral AI
- `gpt-3.5-turbo` - OpenAI, rapide et économique
- `gpt-4` - OpenAI, plus précis
- `gpt-4-turbo` - OpenAI, équilibre vitesse/précision

**Actuellement configuré** : `mistral3`

Pour changer de modèle, modifiez dans `.env` :

```bash
LLM_MODEL="gpt-4"  # Ou autre modèle disponible
```

## 📊 Format de l'API

L'API Infomaniak est compatible avec le format OpenAI Chat Completions :

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "system",
      "content": "You are a data extraction assistant."
    },
    {
      "role": "user",
      "content": "Extract data from: ..."
    }
  ],
  "temperature": 0.1,
  "max_tokens": 4000
}
```

## 🔒 Sécurité

✅ **Token protégé** : Le token est stocké côté serveur uniquement  
✅ **Jamais exposé** : Le frontend ne voit jamais le token  
✅ **HTTPS** : En production, toutes les communications sont chiffrées  

## ⚠️ Important

**Ne jamais commiter le fichier `.env` avec vos vrais identifiants !**

Le fichier `.env` est déjà dans `.gitignore` pour éviter cela.

## 📞 Support

En cas de problème :

1. **Vérifier les logs** :
   ```bash
   make dev-logs
   ```

2. **Tester avec le mock** :
   ```bash
   cd backend
   python ../tests/local/test_llm_analysis_example.py
   ```

3. **Vérifier la configuration** :
   ```bash
   grep LLM_ .env
   ```

## ✅ Checklist

- [x] Product ID configuré (`105448`)
- [x] Bearer token configuré
- [x] Fichier `.env` créé
- [x] Variables d'environnement définies
- [ ] Services redémarrés (`make dev`)
- [ ] Test effectué

## 🎉 Prêt !

Votre configuration Infomaniak est complète et prête à l'emploi !

**Prochaine étape** : Redémarrer les services et tester la fonctionnalité.

```bash
make dev-down
make dev
```

Puis ouvrir http://localhost:3000 et tester avec un document !

