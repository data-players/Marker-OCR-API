---
name: he-spec
description: Spécialiste de la spécification fonctionnelle et technique - dialogue, user stories, plan technique et découpage en tâches
triggers:
  keywords: [spec, specification, requirements, user story, plan, tasks]
  phases: [spec]
capabilities:
  - read_files
  - write_files
  - user_interaction
constraints:
  - Ne pas commencer la rédaction avant d'avoir toutes les réponses du dialogue
  - Toujours créer les 3 fichiers: specification.md, plan.md, tasks.md
  - Mettre à jour WORKFLOW_STATE.md avec spec_complete: true à la fin
output_format: |
  ## ✅ Phase SPEC terminée
  **Fichiers créés**: specification.md, plan.md, tasks.md
  **Résumé**: {N} user stories, {M} tâches, estimation {X}h
  **Prochaine phase**: TEST-SPEC
---

# Skill: Spec Agent

> Spécialiste de la spécification fonctionnelle et technique

## Description

Ce skill est responsable de la **Phase 1: SPEC** du workflow. Il :
- Dialogue avec l'utilisateur pour comprendre les besoins
- Crée une spécification fonctionnelle complète
- Crée un plan technique détaillé
- Découpe en tâches macros et micros

## Triggers

Ce skill est appelé quand :
- La phase courante est `spec`
- L'orchestrateur passe le relais après `init`

## Prérequis

Avant d'exécuter ce skill :
- `WORKFLOW_STATE.md` existe
- `constitution.md` existe (ou phase init complétée)
- `feature_description` est définie dans l'état

---

## Processus

### Étape 1: Dialogue Fonctionnel

**Objectif**: Comprendre précisément ce que l'utilisateur veut

**Questions à poser** (adapter selon contexte):

1. **Contexte utilisateur**
   - Qui sont les utilisateurs de cette feature ?
   - Dans quel contexte l'utiliseront-ils ?

2. **Comportement attendu**
   - Que doit faire exactement cette feature ?
   - Quel est le parcours utilisateur principal ?
   - Quels sont les parcours alternatifs ?

3. **Critères d'acceptation**
   - Comment saura-t-on que la feature fonctionne ?
   - Quels sont les cas limites à gérer ?
   - Quelles erreurs peuvent survenir ?

4. **Contraintes**
   - Y a-t-il des contraintes techniques ?
   - Des dépendances avec d'autres features ?
   - Des contraintes de performance ?

5. **Priorités**
   - Qu'est-ce qui est indispensable (MVP) ?
   - Qu'est-ce qui est souhaitable ?
   - Qu'est-ce qui peut attendre ?

**Ne pas commencer la rédaction avant d'avoir ces réponses !**

---

### Étape 2: Créer la Spécification

**Fichier**: `.heracles/sessions/{session_id}/specs/specification.md`

> **Note**: Les specs de feature sont stockées dans la session de workflow.
> Les specs projet globales (`PRD.md`, `architecture.md`) sont dans `{spec_dir}/` (défini dans `WORKFLOW_STATE.md > detected_structure.spec_dir`, par défaut `spec/`).

**Template**:

```markdown
# Spécification: {Feature Name}

> Feature ID: {feature_id}
> Créé: {date}
> Statut: Draft | Review | Approved

## 1. Vue d'ensemble

### 1.1 Contexte
[Pourquoi cette feature existe]

### 1.2 Objectifs
- Objectif 1
- Objectif 2

### 1.3 Non-objectifs (Out of scope)
- Ce qui n'est PAS inclus

## 2. User Stories

### US-001: [Titre]
**En tant que** [type d'utilisateur]
**Je veux** [action]
**Afin de** [bénéfice]

**Critères d'acceptation**:
- [ ] Critère 1
- [ ] Critère 2

**Notes**: [Détails supplémentaires]

### US-002: [Titre]
...

## 3. Parcours Utilisateur

### 3.1 Parcours Principal (Happy Path)
1. L'utilisateur [action 1]
2. Le système [réponse 1]
3. L'utilisateur [action 2]
4. Le système [réponse 2]
5. Résultat attendu: [état final]

### 3.2 Parcours Alternatifs
#### Alt-A: [Nom du cas]
- Condition: [quand ce cas se produit]
- Étapes: [liste des étapes]
- Résultat: [état final]

### 3.3 Cas d'Erreur
#### Err-A: [Nom de l'erreur]
- Condition: [quand cette erreur survient]
- Message: [message affiché]
- Action: [ce que l'utilisateur peut faire]

## 4. Interfaces Utilisateur

### 4.1 Écrans/Pages concernés
- Page A: [description]
- Page B: [description]

### 4.2 Composants UI
- Composant X: [description, comportement]
- Composant Y: [description, comportement]

### 4.3 Maquettes
[Références aux maquettes si disponibles, sinon description textuelle]

## 5. Données

### 5.1 Modèles de données
```
Entity: [Nom]
- field1: type (contraintes)
- field2: type (contraintes)
```

### 5.2 Règles de validation
- field1: [règles]
- field2: [règles]

### 5.3 États et transitions
```
[État A] --action--> [État B] --action--> [État C]
```

## 6. API (si applicable)

### 6.1 Endpoints
| Méthode | Path | Description |
|---------|------|-------------|
| POST | /api/x | Créer X |
| GET | /api/x/:id | Récupérer X |

### 6.2 Contrats API
```json
// POST /api/x
// Request
{
  "field1": "string",
  "field2": 123
}

// Response 200
{
  "id": "uuid",
  "field1": "string",
  "created_at": "ISO date"
}

// Response 400
{
  "error": "validation_error",
  "details": [...]
}
```

## 7. Critères d'Acceptation Globaux

- [ ] Toutes les user stories sont implémentées
- [ ] Tous les parcours sont testables
- [ ] Performance: [critères]
- [ ] Accessibilité: [critères]
- [ ] Sécurité: [critères]

## 8. Questions Ouvertes

- [ ] Question 1 (à clarifier avec [qui])
- [ ] Question 2

## 9. Références

- [Lien vers constitution.md](../constitution.md)
- [Lien vers documentation technique]
```

---

### Étape 3: Créer le Plan Technique

**Fichier**: `.heracles/sessions/{session_id}/specs/plan.md`

**Template**:

```markdown
# Plan Technique: {Feature Name}

> Feature ID: {feature_id}
> Basé sur: specification.md v{version}

## 1. Architecture

### 1.1 Composants impactés
- Frontend: [composants]
- Backend: [services/modules]
- Database: [tables/collections]

### 1.2 Diagramme d'architecture
```
[Client] --> [API Gateway] --> [Service A]
                          --> [Service B]
                               |
                               v
                           [Database]
```

### 1.3 Décisions architecturales
| Décision | Raison | Alternatives rejetées |
|----------|--------|----------------------|
| Utiliser X | Parce que Y | Z (car...) |

## 2. Modèles de Données

### 2.1 Schéma Database
```sql
CREATE TABLE feature_x (
  id UUID PRIMARY KEY,
  field1 VARCHAR(255) NOT NULL,
  field2 INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feature_x_field1 ON feature_x(field1);
```

### 2.2 Types TypeScript/Interfaces
```typescript
interface FeatureX {
  id: string;
  field1: string;
  field2?: number;
  createdAt: Date;
}

type CreateFeatureXInput = Omit<FeatureX, 'id' | 'createdAt'>;
```

## 3. API Design

### 3.1 Routes
```typescript
// routes/featureX.ts
router.post('/feature-x', validateInput, createFeatureX);
router.get('/feature-x/:id', getFeatureX);
router.put('/feature-x/:id', validateInput, updateFeatureX);
router.delete('/feature-x/:id', deleteFeatureX);
```

### 3.2 Validation
```typescript
const createSchema = z.object({
  field1: z.string().min(1).max(255),
  field2: z.number().optional(),
});
```

### 3.3 Gestion d'erreurs
- 400: Validation error
- 401: Non authentifié
- 403: Non autorisé
- 404: Ressource non trouvée
- 500: Erreur serveur

## 4. Frontend

### 4.1 Composants à créer
| Composant | Type | Props | État |
|-----------|------|-------|------|
| FeatureXForm | Form | onSubmit | formData |
| FeatureXList | Display | items | loading |

### 4.2 État global (si applicable)
```typescript
// store/featureX.ts
interface FeatureXState {
  items: FeatureX[];
  loading: boolean;
  error: string | null;
}
```

### 4.3 Hooks custom
```typescript
// hooks/useFeatureX.ts
function useFeatureX(id: string) {
  // ...
}
```

## 5. Sécurité

### 5.1 Authentication
- [ ] Endpoints protégés par auth
- [ ] Tokens validés

### 5.2 Authorization
- [ ] Vérification des permissions
- [ ] Row-level security si applicable

### 5.3 Validation Input
- [ ] Tous les inputs validés côté serveur
- [ ] Sanitization des strings
- [ ] Rate limiting

## 6. Performance

### 6.1 Optimisations prévues
- Indexation DB: [champs]
- Caching: [stratégie]
- Lazy loading: [où]

### 6.2 Métriques cibles
- Response time: < 200ms (p95)
- DB queries: < 5 par requête

## 7. Testing Strategy

### 7.1 Tests Unitaires
- Services: [liste]
- Composants: [liste]
- Utils: [liste]

### 7.2 Tests d'Intégration
- API endpoints: [liste]
- Database operations: [liste]

### 7.3 Tests E2E
- Parcours principal: [scénario]
- Cas d'erreur: [scénario]

### 7.4 Tests de Performance
- Load test: [scénario]
- Stress test: [scénario]

## 8. Dépendances

### 8.1 Packages à installer
```bash
npm install package-a package-b
npm install -D package-c
```

### 8.2 Services externes
- Service X: [usage, credentials needed]

## 9. Migration / Rollback

### 9.1 Plan de migration
1. Déployer migration DB
2. Déployer backend
3. Déployer frontend

### 9.2 Plan de rollback
1. Revert frontend
2. Revert backend
3. Revert migration (si possible)

## 10. Checklist pré-implémentation

- [ ] Spec approuvée
- [ ] Architecture validée
- [ ] Dépendances disponibles
- [ ] Environnement de test prêt
```

---

### Étape 4: Créer les Tasks

**Fichier**: `.heracles/sessions/{session_id}/specs/tasks.md`

**Template**:

```markdown
# Tasks: {Feature Name}

> Généré depuis: plan.md
> Estimation totale: {X} heures

## Macro-Tasks

### MT-1: Setup & Infrastructure
- [ ] **T-1.1**: Créer migration DB
- [ ] **T-1.2**: Créer modèles/types
- [ ] **T-1.3**: Setup routes API

### MT-2: Backend Implementation
- [ ] **T-2.1**: Implémenter endpoint CREATE
- [ ] **T-2.2**: Implémenter endpoint READ
- [ ] **T-2.3**: Implémenter endpoint UPDATE
- [ ] **T-2.4**: Implémenter endpoint DELETE
- [ ] **T-2.5**: Ajouter validation
- [ ] **T-2.6**: Ajouter gestion erreurs

### MT-3: Frontend Implementation
- [ ] **T-3.1**: Créer composant Form
- [ ] **T-3.2**: Créer composant List
- [ ] **T-3.3**: Créer hooks custom
- [ ] **T-3.4**: Intégrer dans pages

### MT-4: Testing
- [ ] **T-4.1**: Écrire tests unitaires backend
- [ ] **T-4.2**: Écrire tests unitaires frontend
- [ ] **T-4.3**: Écrire tests intégration API
- [ ] **T-4.4**: Écrire tests E2E

### MT-5: Polish
- [ ] **T-5.1**: Review sécurité
- [ ] **T-5.2**: Optimisation performance
- [ ] **T-5.3**: Documentation

## Ordre d'exécution

```
MT-1 (Setup)
    |
    v
MT-2 (Backend) --> MT-4.1, MT-4.3 (Tests Backend)
    |
    v
MT-3 (Frontend) --> MT-4.2, MT-4.4 (Tests Frontend)
    |
    v
MT-5 (Polish)
```

## Dépendances entre tasks

| Task | Dépend de |
|------|-----------|
| T-2.1 | T-1.1, T-1.2 |
| T-3.1 | T-2.1, T-2.2 |
| T-4.3 | T-2.* |
| T-4.4 | T-3.* |
```

---

### Étape 5: Mettre à jour l'État

Quand tu as terminé, mets à jour `WORKFLOW_STATE.md` :

```markdown
## Conditions Met
```yaml
init_complete: true
spec_complete: true  # <-- Changé à true
implementation_complete: false
tests_passed: false
review_passed: false
workflow_complete: false
```

## History
| Timestamp | Phase | Action | Result |
|-----------|-------|--------|--------|
| ... | ... | ... | ... |
| {now} | spec | completed | success |
```

---

## Chemins Dynamiques

Les chemins utilisés par ce skill sont définis dans `WORKFLOW_STATE.md > detected_structure` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `source_dir` | `src` | Répertoire des sources |
| `test_dir` | `test` | Répertoire des tests |
| `doc_dir` | `doc` | Répertoire de documentation |
| `spec_dir` | `spec` | Répertoire des specs projet |

Les specs de feature sont toujours dans `.heracles/sessions/{session_id}/specs/`.

---

## Checklist de Sortie

Avant de rendre la main à l'orchestrateur, vérifie :

- [ ] `.heracles/sessions/{session_id}/specs/specification.md` créé et complet
- [ ] `.heracles/sessions/{session_id}/specs/plan.md` créé et complet
- [ ] `.heracles/sessions/{session_id}/specs/tasks.md` créé avec toutes les tâches
- [ ] Toutes les questions ouvertes ont des réponses ou sont marquées
- [ ] `WORKFLOW_STATE.md` mis à jour avec `spec_complete: true`
- [ ] Entrée ajoutée dans History

---

## Communication avec l'Orchestrateur

À la fin de ton travail, retourne ce message :

```
---
## ✅ Phase SPEC terminée

**Fichiers créés**:
- `.heracles/sessions/{session_id}/specs/specification.md`
- `.heracles/sessions/{session_id}/specs/plan.md`
- `.heracles/sessions/{session_id}/specs/tasks.md`

**Résumé**:
- {N} user stories définies
- {M} tâches à implémenter
- Estimation: {X} heures

**Prochaine phase**: TEST-SPEC

L'orchestrateur peut maintenant appeler @he-test action=write_scenarios.
---
```


