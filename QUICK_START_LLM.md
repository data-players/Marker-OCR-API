# 🚀 Quick Start - LLM Analysis

## Démarrage en 3 minutes

### 1. Configuration (30 secondes)

Ajouter vos identifiants Infomaniak dans `.env` :

```bash
# Créer ou éditer .env
nano .env

# Ajouter ces lignes (obtenues depuis https://manager.infomaniak.com/v3/ai)
LLM_PRODUCT_ID="105448"  # Votre product ID
LLM_API_TOKEN="Bearer votre_token_ici"  # Votre Bearer token
```

**Vos identifiants** :
- Product ID: `105448`
- Token déjà configuré dans votre `.env`

### 2. Redémarrer les services (30 secondes)

```bash
make dev-down
make dev
```

### 3. Tester la fonctionnalité (2 minutes)

#### Option A : Interface Web (Recommandé)

1. Ouvrir http://localhost:3000
2. Uploader un PDF
3. Configurer et lancer l'OCR
4. Une fois l'OCR terminé, cliquer sur **"Start Analysis"**
5. Remplir :
   - **Introduction** : "Extraire les informations clés de ce document"
   - **Ajouter des champs** avec le bouton "Add Field"
   - Exemple de champ :
     - Nom : `document_type`
     - Type : `string`
     - Description : "Type de document"
6. Cliquer sur **"Start LLM Analysis"**
7. Attendre les résultats (2-10 secondes)

#### Option B : Script de Test

```bash
cd /home/simon/GIT/IA/agent-tools/Marker-OCR-API
./tests/local/quick_llm_test.sh
```

---

## 📖 Exemples Rapides

### Facture

**Introduction** :
```
Extraire les informations de facturation : vendeur, montant, date
```

**Champs** :
- `vendor_name` (string) : "Nom du vendeur"
- `invoice_number` (string) : "Numéro de facture"
- `total_amount` (number) : "Montant total"
- `invoice_date` (string) : "Date de la facture"

### CV/Resume

**Introduction** :
```
Extraire les informations du candidat : nom, email, compétences
```

**Champs** :
- `full_name` (string) : "Nom complet"
- `email` (string) : "Adresse email"
- `skills` (array) : "Liste des compétences techniques"
- `years_experience` (integer) : "Années d'expérience"

### Contrat

**Introduction** :
```
Extraire les informations contractuelles clés
```

**Champs** :
- `parties` (array) : "Parties au contrat"
- `effective_date` (string) : "Date d'effet"
- `termination_date` (string) : "Date de fin"
- `payment_terms` (string) : "Conditions de paiement"

---

## 🔧 Dépannage Rapide

### "LLM API not configured"

```bash
# Vérifier que les identifiants sont dans .env
grep LLM_PRODUCT_ID .env
grep LLM_API_TOKEN .env

# Si vides, ajouter les identifiants
echo 'LLM_PRODUCT_ID="105448"' >> .env
echo 'LLM_API_TOKEN="Bearer votre_token"' >> .env

# Redémarrer
make dev-down && make dev
```

### "Analysis failed"

1. Vérifier les logs backend :
   ```bash
   make dev-logs
   ```

2. Tester avec le service mock :
   ```bash
   cd backend
   python ../tests/local/test_llm_analysis_example.py
   ```

### "Connection timeout"

Augmenter le timeout dans `.env` :
```bash
LLM_TIMEOUT=120  # 2 minutes au lieu de 60s
```

---

## 📚 Documentation Complète

- **Guide Détaillé** : [LLM_ANALYSIS_GUIDE.md](LLM_ANALYSIS_GUIDE.md)
- **Changelog** : [CHANGELOG_LLM_FEATURE.md](CHANGELOG_LLM_FEATURE.md)
- **Résumé Implémentation** : [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🎯 Types de Champs Disponibles

| Type | Usage | Exemple |
|------|-------|---------|
| `string` | Texte | Nom, adresse, description |
| `number` | Nombre décimal | Prix, pourcentage |
| `integer` | Nombre entier | Âge, quantité |
| `boolean` | Vrai/Faux | Actif, validé |
| `array` | Liste | Compétences, items |
| `object` | Objet imbriqué | Adresse complète |

---

## ✨ Astuces

### Descriptions Claires

✅ **Bon** :
```
"Date de la facture au format ISO (YYYY-MM-DD) si possible"
```

❌ **Mauvais** :
```
"date"
```

### Champs Requis

Marquer comme "required" uniquement les champs **absolument nécessaires**.

### Modèle LLM

- **GPT-3.5-turbo** : Rapide et économique
- **GPT-4** : Plus précis mais plus lent/coûteux

Changer dans `.env` :
```bash
LLM_MODEL="gpt-4"
```

---

## 🚀 Prêt à Utiliser !

La fonctionnalité est maintenant active et prête à l'emploi.

**Prochaines étapes** :
1. Tester avec vos propres documents
2. Créer des schémas personnalisés
3. Ajuster les descriptions pour meilleure précision
4. Consulter les guides pour fonctionnalités avancées

---

**Besoin d'aide ?** Consultez [LLM_ANALYSIS_GUIDE.md](LLM_ANALYSIS_GUIDE.md)

