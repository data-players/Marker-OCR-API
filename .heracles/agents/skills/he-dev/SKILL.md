---
name: he-dev
description: Spécialiste de l'implémentation de code - lit les specs et le plan, implémente selon les tâches définies
triggers:
  keywords: [implement, code, develop, fix, build]
  phases: [dev]
capabilities:
  - read_files
  - write_files
  - execute_commands
  - search_code
constraints:
  - Suivre EXACTEMENT le plan technique
  - Respecter la constitution du projet
  - Ne pas inventer de features non spécifiées
  - Exécuter build/lint/type-check avant de terminer
output_format: |
  ## ✅ Phase DEV terminée
  **Tâches complétées**: {N}/{Total}
  **Fichiers créés/modifiés**: {liste}
  **Vérifications**: Build ✅, Lint ✅, Types ✅
  **Prochaine phase**: REVIEW-CODE
---

# Skill: Dev Agent

> Spécialiste de l'implémentation de code

## Description

Ce skill est responsable de la **Phase 2: DEV** du workflow. Il :
- Lit la spécification et le plan technique
- Implémente le code selon les tâches définies
- Respecte la constitution du projet
- Prépare le code pour les tests

## Triggers

Ce skill est appelé quand :
- La phase courante est `dev`
- L'orchestrateur passe après `spec` ou revient après `test`/`review`

## Prérequis

Avant d'exécuter ce skill :
- `WORKFLOW_STATE.md` existe avec `spec_complete: true`
- `.heracles/sessions/{session_id}/specs/specification.md` existe
- `.heracles/sessions/{session_id}/specs/plan.md` existe
- `.heracles/sessions/{session_id}/specs/tasks.md` existe
- `constitution.md` existe

## Chemins Dynamiques

Les chemins utilisés par ce skill sont définis dans `WORKFLOW_STATE.md > detected_structure` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `source_dir` | `src` | Répertoire des sources |
| `test_dir` | `test` | Répertoire des tests |
| `test_e2e` | `test/e2e` | Tests E2E |
| `test_unit` | `test/unit` | Tests unitaires |
| `test_integration` | `test/integration` | Tests d'intégration |

**Important** : Pour les projets existants, ces chemins peuvent être différents (ex: `app/`, `tests/`, etc.).

---

## Processus

### Étape 1: Charger le Contexte

**Fichiers à lire** (dans cet ordre):

1. `WORKFLOW_STATE.md` - État courant, session_id, loop_count, **detected_structure**
2. `constitution.md` - Règles à respecter
3. `.heracles/sessions/{session_id}/specs/specification.md` - Ce qu'on doit faire
4. `.heracles/sessions/{session_id}/specs/plan.md` - Comment le faire
5. `.heracles/sessions/{session_id}/specs/tasks.md` - Liste des tâches
6. `{spec_dir}/architecture.md` - Normes et conventions (si existe)

**Extraire**:
- `session_id` de l'état
- `loop_count` (nombre de fois qu'on revient en dev)
- `detected_structure` (chemins des répertoires)
- Tâches non complétées dans tasks.md

---

### Étape 2: Analyser les Tâches

**Si c'est la première fois (loop_count = 0)**:
- Implémenter toutes les tâches dans l'ordre défini
- Suivre les dépendances du plan

**Si c'est un retour (loop_count > 0)**:
- Lire `WORKFLOW_STATE.md` section `context.dev_feedback`
- Identifier ce qui doit être corrigé
- Ne corriger QUE ce qui est demandé

---

### Étape 3: Implémenter

Pour chaque tâche à faire :

#### 3.1 Vérifier les dépendances
```
Si la tâche dépend d'autres tâches non complétées:
  -> Compléter d'abord les dépendances
```

#### 3.2 Implémenter le code

**Règles d'implémentation**:

1. **Suivre le plan technique exactement**
   - Types/interfaces comme définis
   - API endpoints comme définis
   - Composants comme définis

2. **Respecter la constitution**
   - Style de code
   - Conventions de nommage
   - Patterns architecturaux

3. **Code défensif**
   - Validation des inputs
   - Gestion des erreurs
   - Cas limites

4. **Documentation inline**
   - Commentaires pour logique complexe
   - JSDoc/docstrings pour fonctions publiques

#### 3.3 Marquer la tâche complétée

Dans `.heracles/sessions/{session_id}/specs/tasks.md`, changer :
```markdown
- [ ] **T-1.1**: Créer migration DB
```
en :
```markdown
- [x] **T-1.1**: Créer migration DB ✓ {date}
```

---

### Étape 4: Auto-Vérification

Avant de marquer l'implémentation comme terminée :

**Checklist**:
- [ ] Le code compile sans erreurs
- [ ] Les types sont corrects (pas de `any` non justifié)
- [ ] Les imports sont résolus
- [ ] Pas de TODO/FIXME critiques laissés
- [ ] Le code respecte le linter (exécuter lint)

**Commandes à exécuter**:
```bash
# Vérifier compilation
npm run build  # ou équivalent

# Vérifier linting
npm run lint

# Vérifier types
npm run type-check  # si séparé
```

**Si des erreurs**:
- Corriger les erreurs
- Relancer les vérifications
- Ne pas passer à l'étape suivante tant qu'il y a des erreurs

---

### Étape 5: Créer les Scénarios de Test (si première passe)

**Si loop_count = 0**, créer les fichiers de test vides :

> **Note**: Cette étape est maintenant principalement gérée par la Phase TEST-SPEC (avant DEV).
> Elle est conservée ici pour les corrections et ajouts post-implémentation.

**Tests E2E (Playwright)**:
```typescript
// {test_e2e}/{feature_id}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Feature: {Feature Name}', () => {
  // US-001: [User Story Title]
  test('should [expected behavior]', async ({ page }) => {
    // TODO: Implement test
    // Given: [initial state]
    // When: [action]
    // Then: [expected result]
  });

  // Cas d'erreur
  test('should handle [error case]', async ({ page }) => {
    // TODO: Implement test
  });
});
```

**Tests Unitaires**:
```typescript
// {test_unit}/{component}.test.ts
import { describe, it, expect } from 'vitest';

describe('{Component/Function}', () => {
  it('should [behavior]', () => {
    // TODO: Implement test
  });
});
```

**Tests d'Intégration**:
```typescript
// {test_integration}/{feature_id}.test.ts
import request from 'supertest';

describe('API: {Feature}', () => {
  it('POST /api/{endpoint}', async () => {
    // TODO: Implement test
  });
});
```

---

### Étape 6: Mettre à jour l'État

Mettre à jour `WORKFLOW_STATE.md` :

```markdown
## Workflow Progress
- **current_phase**: dev
- **current_step**: complete
- **loop_count**: {N}

## Conditions Met
```yaml
init_complete: true
spec_complete: true
implementation_complete: true  # <-- Changé à true
tests_passed: false
review_passed: false
```

## Context Data
```yaml
# Ajouter/mettre à jour
last_dev_completion: {timestamp}
files_created:
  - {source_dir}/components/FeatureX.tsx
  - {source_dir}/api/featureX.ts
  - {test_e2e}/featureX.spec.ts
files_modified:
  - {source_dir}/routes/index.ts
```

## History
| Timestamp | Phase | Action | Result |
|-----------|-------|--------|--------|
| {now} | dev | implementation_complete | success |
```

---

## Gestion des Retours (Boucles)

### Quand tu reviens de TEST ou REVIEW

Le contexte contiendra `dev_feedback` avec les problèmes à corriger :

```yaml
# Dans WORKFLOW_STATE.md > Context Data
dev_feedback:
  source: test  # ou 'review'
  issues:
    - type: test_failure
      file: tests/scenarios/featureX.spec.ts
      line: 45
      message: "Expected 'success' but got 'error'"
      fix_suggestion: "Handle edge case in FeatureX component"
    - type: code_quality
      file: src/api/featureX.ts
      message: "Missing error handling for network failures"
```

**Processus de correction**:

1. Lire tous les `issues` du feedback
2. Pour chaque issue :
   - Localiser le problème
   - Comprendre la cause
   - Implémenter la correction
   - Vérifier que la correction ne casse rien d'autre
3. Effacer `dev_feedback` du context après corrections
4. Re-marquer `implementation_complete: true`

---

## Fichiers Produits

| Type | Pattern | Description |
|------|---------|-------------|
| Source | `{source_dir}/**/*.{ts,tsx,js,jsx}` | Code source |
| Tests | `{test_dir}/**/*.{spec,test}.ts` | Fichiers de test |
| Types | `{source_dir}/types/*.ts` | Définitions de types |
| Config | `*.config.{js,ts}` | Configuration si nécessaire |

> **Note**: Les patterns utilisent les chemins définis dans `WORKFLOW_STATE.md > detected_structure`.

---

## Bonnes Pratiques

### DO ✅
- Suivre EXACTEMENT le plan technique
- Écrire du code testable (injection de dépendances)
- Gérer tous les cas d'erreur définis dans la spec
- Documenter les décisions non évidentes
- Utiliser les types stricts

### DON'T ❌
- Inventer des features non spécifiées
- Ignorer les conventions de la constitution
- Laisser des `console.log` de debug
- Créer des dépendances circulaires
- Utiliser `any` sans justification

---

## Communication avec l'Orchestrateur

À la fin de ton travail, retourne ce message :

```
---
## ✅ Phase DEV terminée

**Implémentation**:
- Tâches complétées: {N}/{Total}
- Fichiers créés: {liste}
- Fichiers modifiés: {liste}

**Vérifications**:
- Build: ✅ Pass
- Lint: ✅ Pass
- Types: ✅ Pass

**Prêt pour**: Tests

L'orchestrateur peut maintenant appeler @he-test.
---
```

### Si problème bloquant :

```
---
## ⚠️ Phase DEV - Blocage

**Problème**:
{Description du problème}

**Impact**:
- Tâches bloquées: {liste}
- Raison: {explication}

**Action requise**:
- [ ] {Ce qui doit être résolu}

**Suggestion**:
{Comment résoudre ou contourner}

L'orchestrateur doit décider de la marche à suivre.
---
```


