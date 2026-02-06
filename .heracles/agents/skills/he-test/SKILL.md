---
name: he-test
description: Spécialiste des tests - écrit les scénarios (TDD), exécute les tests de développement, teste sur navigateur, lance les tests automatisés
triggers:
  keywords: [test, testing, scenario, e2e, unit, integration, browser]
  phases: [test-spec, dev-test, test-browser, test-auto]
  actions: [write_scenarios, dev_tests, browser_test, run_tests]
capabilities:
  - read_files
  - write_files
  - execute_commands
  - browser_navigation
  - take_screenshots
constraints:
  - Écrire les scénarios AVANT l'implémentation (TDD)
  - Utiliser Playwright pour tests E2E et browser
  - Couverture minimale 80%
  - Documenter tous les échecs avec fix_suggestion
output_format: |
  ## ✅ Phase TEST terminée
  **Résultats**: Unit {N}/{N} ✅, Integration {N}/{N} ✅, E2E {N}/{N} ✅
  **Couverture**: {X}%
  **Prochaine phase**: REVIEW (ou DEV si échec)
---

# Skill: Test Agent

> Spécialiste des tests automatisés et manuels

## Description

Ce skill gère **4 phases distinctes** du workflow :
- **Phase 2 (TEST-SPEC)**: Écriture des scénarios de test AVANT l'implémentation (TDD)
- **Phase 4 (DEV-TEST)**: Tests de développement (unitaires + intégration) après DEV
- **Phase 6 (TEST-BROWSER)**: Tests fonctionnels interactifs sur navigateur (E2E)
- **Phase 7 (TEST-AUTO)**: Exécution complète de tous les tests automatisés (CI)

## Triggers et Actions

Ce skill est appelé avec une action spécifique :

| Action | Phase | Quand |
|--------|-------|-------|
| `write_scenarios` | TEST-SPEC | Après SPEC, avant DEV |
| `dev_tests` | DEV-TEST | Après DEV, avant REVIEW-CODE |
| `browser_test` | TEST-BROWSER | Après REVIEW-CODE |
| `run_tests` | TEST-AUTO | Après TEST-BROWSER |

---

## Chemins Dynamiques

Les chemins utilisés par ce skill sont définis dans `WORKFLOW_STATE.md > detected_structure` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `test_dir` | `test` | Répertoire racine des tests |
| `test_unit` | `test/unit` | Tests unitaires |
| `test_integration` | `test/integration` | Tests d'intégration |
| `test_e2e` | `test/e2e` | Tests End-to-End |

**Important** : Toujours lire `WORKFLOW_STATE.md` pour obtenir les chemins réels du projet (peuvent être `tests/`, `__tests__/`, etc. pour des projets existants).

---

# ACTION: write_scenarios (Phase 2 - TEST-SPEC)

## Objectif
Écrire les scénarios de test fonctionnel **AVANT** l'implémentation.
C'est du TDD/BDD : les tests définissent le comportement attendu.

## Prérequis
- `WORKFLOW_STATE.md` existe avec `spec_complete: true`
- `specs/{feature_id}/specification.md` existe
- **PAS de code implémenté encore**

## Processus

### Étape 1: Lire la Spécification

Extraire de `specification.md` :
- User Stories et leurs critères d'acceptation
- Parcours utilisateur (happy path + alternatives)
- Cas d'erreur
- Interfaces utilisateur décrites

### Étape 2: Créer les Scénarios Playwright

> **Chemins dynamiques** : Lire `WORKFLOW_STATE.md > detected_structure` pour obtenir les répertoires.
> - `{test_dir}` = `detected_structure.test_dir` (défaut: `test`)
> - `{test_e2e}` = `detected_structure.test_e2e` (défaut: `test/e2e`)

**Fichier**: `{test_e2e}/{feature_id}.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature: {Feature Name}', () => {
  // Basé sur US-001
  test('US-001: should [expected behavior from spec]', async ({ page }) => {
    // Given: État initial (depuis spec section 3.1)
    await page.goto('/feature-page');
    
    // When: Actions utilisateur (depuis parcours principal)
    await page.fill('[data-testid="input-field"]', 'test value');
    await page.click('[data-testid="submit-button"]');
    
    // Then: Résultats attendus (depuis critères d'acceptation)
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  // Basé sur parcours alternatif Alt-A
  test('Alt-A: should handle [alternative case]', async ({ page }) => {
    // ...
  });

  // Basé sur cas d'erreur Err-A
  test('Err-A: should show error when [error condition]', async ({ page }) => {
    // ...
  });
});
```

### Étape 3: Créer les Squelettes de Tests Unitaires

**Fichier**: `{test_unit}/{feature}.test.ts` (où `{test_unit}` = `detected_structure.test_unit`, défaut: `test/unit`)

```typescript
import { describe, it, expect } from 'vitest';

describe('{Feature} - Unit Tests', () => {
  // Squelettes basés sur le plan technique
  describe('Validation', () => {
    it.todo('should validate required fields');
    it.todo('should reject invalid input');
  });

  describe('Business Logic', () => {
    it.todo('should process data correctly');
    it.todo('should handle edge cases');
  });
});
```

### Étape 4: Créer les Squelettes de Tests d'Intégration

**Fichier**: `{test_integration}/{feature}.test.ts` (où `{test_integration}` = `detected_structure.test_integration`, défaut: `test/integration`)

```typescript
import request from 'supertest';

describe('{Feature} API - Integration Tests', () => {
  // Basé sur les endpoints définis dans plan.md
  describe('POST /api/{endpoint}', () => {
    it.todo('should create resource with valid data');
    it.todo('should return 400 for invalid data');
    it.todo('should require authentication');
  });

  describe('GET /api/{endpoint}/:id', () => {
    it.todo('should return resource if exists');
    it.todo('should return 404 if not found');
  });
});
```

### Étape 5: Mettre à jour l'État

```yaml
conditions_met:
  test_scenarios_written: true

context:
  scenarios_created:
    - {test_e2e}/{feature_id}.spec.ts
    - {test_unit}/{feature}.test.ts
    - {test_integration}/{feature}.test.ts
```

### Sortie

```
---
## ✅ Phase TEST-SPEC terminée

**Scénarios créés** (chemins adaptés au projet):
- `{test_e2e}/{feature_id}.spec.ts` ({N} tests E2E)
- `{test_unit}/{feature}.test.ts` ({N} tests à implémenter)
- `{test_integration}/{feature}.test.ts` ({N} tests à implémenter)

**Couverture prévue**:
- User Stories: {N}/{N} couvertes
- Cas d'erreur: {N} testés
- Parcours alternatifs: {N} testés

**Prochaine phase**: DEV

L'implémentation peut commencer, les tests définissent le comportement attendu.
---
```

---

# ACTION: dev_tests (Phase 4 - DEV-TEST)

## Objectif
Exécuter et valider les tests de développement (unitaires + intégration) après la phase DEV.
Cette phase vérifie que le code implémenté fonctionne correctement avant la review.

## Prérequis
- `WORKFLOW_STATE.md` existe avec `implementation_complete: true`
- Le code est implémenté (phase DEV terminée)
- Build et lint passent
- Les squelettes de tests existent (créés en TEST-SPEC)

## Processus

### Étape 1: Lire l'État et les Chemins

1. **Lire `WORKFLOW_STATE.md`** pour :
   - `detected_structure.test_unit` (défaut: `test/unit`)
   - `detected_structure.test_integration` (défaut: `test/integration`)
   - `current_feature.files_modified` (fichiers implémentés)

2. **Vérifier les tests existants** :
   ```bash
   # Lister les fichiers de test
   find {test_unit} -name "*.test.ts" -o -name "*.spec.ts"
   find {test_integration} -name "*.test.ts" -o -name "*.spec.ts"
   ```

### Étape 2: Compléter les Tests Unitaires

Transformer les `it.todo()` créés en TEST-SPEC en vrais tests :

```typescript
// AVANT (squelette de TEST-SPEC)
it.todo('should validate required fields');

// APRÈS (test implémenté en DEV-TEST)
it('should validate required fields', () => {
  const result = validateInput({ name: '' });
  expect(result.valid).toBe(false);
  expect(result.errors).toContain('name is required');
});
```

**Règles** :
- Un test par comportement
- Nommer clairement : `should [action] when [condition]`
- Utiliser des données de test explicites
- Mocker les dépendances externes

### Étape 3: Compléter les Tests d'Intégration

Transformer les squelettes en vrais tests d'intégration :

```typescript
// AVANT (squelette)
it.todo('should create resource with valid data');

// APRÈS (test implémenté)
it('should create resource with valid data', async () => {
  const response = await request(app)
    .post('/api/users')
    .send({ name: 'John', email: 'john@test.com' });
  
  expect(response.status).toBe(201);
  expect(response.body).toHaveProperty('id');
});
```

**Règles** :
- Tester les endpoints réels
- Vérifier les codes de statut
- Valider la structure de la réponse
- Tester les cas d'erreur (400, 401, 404, etc.)

### Étape 4: Exécuter les Tests

```bash
# Tests unitaires
npm run test:unit
# ou
npx vitest run {test_unit}

# Tests d'intégration
npm run test:integration
# ou
npx vitest run {test_integration}
```

### Étape 5: Analyser les Résultats

**Si tous les tests passent** :
```yaml
conditions_met:
  dev_tests_passed: true

context:
  dev_tests:
    unit_tests: {passed}/{total}
    integration_tests: {passed}/{total}
    coverage: {X}%
```

**Si des tests échouent** :
```yaml
conditions_met:
  dev_tests_passed: false

context:
  dev_feedback:
    failed_tests:
      - name: "should validate required fields"
        file: "test/unit/validation.test.ts"
        error: "Expected false, received true"
        fix_suggestion: "Check validateInput() logic for empty name"
```

### Sortie Succès

```
---
## ✅ Phase DEV-TEST terminée

**Tests de développement**:
- Tests unitaires: {N}/{N} ✅
- Tests d'intégration: {N}/{N} ✅
- Couverture: {X}%

**Fichiers testés**:
- `{test_unit}/validation.test.ts`
- `{test_unit}/business-logic.test.ts`
- `{test_integration}/api.test.ts`

**Prochaine phase**: REVIEW-CODE

L'orchestrateur peut maintenant appeler @he-review action=code_review.
---
```

### Sortie Échec

```
---
## ❌ Phase DEV-TEST - Retour en DEV requis

**Échecs détectés**:
| Type | Test | Raison |
|------|------|--------|
| Unit | should validate required fields | Expected false, got true |
| Integration | POST /api/users | 500 Internal Server Error |

**Feedback envoyé** à `WORKFLOW_STATE.md > context.dev_feedback`

**Retour à**: Phase DEV (loop_count: {N+1})

L'orchestrateur doit appeler @he-dev pour corrections.
---
```

---

# ACTION: browser_test (Phase 6 - TEST-BROWSER)

## Objectif
Tester l'application de manière interactive sur un navigateur réel.
L'agent navigue, clique, et vérifie visuellement.

## Prérequis
- `WORKFLOW_STATE.md` avec `code_review_passed: true`
- Code implémenté et review passée
- Application démarrable (`npm run dev`)
- Scénarios écrits dans `tests/scenarios/`

## Processus

### Étape 1: Démarrer l'Application

```bash
# Démarrer le serveur de développement
npm run dev &

# Attendre que le serveur soit prêt
npx wait-on http://localhost:3000 --timeout 30000
```

### Étape 2: Tests Interactifs avec Browser MCP

**IMPORTANT**: Utiliser les outils browser MCP pour naviguer :

1. `mcp_cursor-ide-browser_browser_navigate` - Aller sur une page
2. `mcp_cursor-ide-browser_browser_snapshot` - Capturer l'état
3. `mcp_cursor-ide-browser_browser_click` - Cliquer sur un élément
4. `mcp_cursor-ide-browser_browser_type` - Saisir du texte
5. `mcp_cursor-ide-browser_browser_take_screenshot` - Screenshot si problème

**Parcours à tester**:

```
Pour chaque User Story dans specification.md:
  1. Naviguer vers la page concernée
  2. Effectuer les actions du parcours principal
  3. Vérifier les résultats attendus
  4. Tester les cas d'erreur
  5. Documenter les observations
```

### Étape 3: Exécuter les Scénarios E2E

```bash
# Exécuter les tests Playwright en mode headed (visible)
npx playwright test tests/scenarios/{feature_id}.spec.ts --headed --project=chromium
```

### Étape 4: Analyser et Documenter

Créer un rapport dans `.workflow/browser-test-results.md` :

```markdown
## Browser Test Results

### Tests Interactifs
- [x] Page charge correctement
- [x] Navigation fonctionne
- [x] Formulaire visible et accessible
- [ ] Animation de chargement (manquante)

### Tests E2E Playwright
- Passés: {N}
- Échoués: {M}

### Screenshots
- [Si échec, référencer les screenshots]

### Observations
- [Notes pour amélioration]
```

### Étape 5: Décision

```
SI tous les tests browser passent:
  -> browser_tests_passed: true
  -> Continuer vers TEST-AUTO

SI échecs dans les tests E2E:
  -> Analyser : bug code ou bug scénario ?
  -> Si bug code: retour DEV
  -> Si bug scénario: retour TEST-SPEC (fix_scenarios: true)

SI problèmes visuels non bloquants:
  -> Noter pour review finale
  -> Continuer
```

### Étape 6: Mettre à jour l'État

**Si succès**:
```yaml
conditions_met:
  browser_tests_passed: true

context:
  browser_test_results:
    interactive: passed
    e2e: passed
    observations: [...]
```

**Si échec (retour DEV)**:
```yaml
current_phase: dev
conditions_met:
  implementation_complete: false
  code_review_passed: false
  browser_tests_passed: false

context:
  dev_feedback:
    source: browser_test
    fix_scenarios: false  # ou true si c'est le scénario
    issues:
      - test: "US-001: should show success"
        message: "Timeout waiting for element"
        fix_suggestion: "Check data-testid attribute"
```

### Sortie

```
---
## ✅ Phase TEST-BROWSER terminée

**Résultats**:
- Tests interactifs: ✅
- Tests E2E Playwright: {N}/{N} ✅

**Observations**:
- [Liste des observations mineures]

**Prochaine phase**: TEST-AUTO
---
```

Ou si échec :

```
---
## ❌ Phase TEST-BROWSER - Retour requis

**Échecs**:
| Test | Problème | Action |
|------|----------|--------|
| US-001 | Element not found | Fix implementation |

**Retour à**: DEV (ou TEST-SPEC si scénarios incorrects)
---
```

---

# ACTION: run_tests (Phase 7 - TEST-AUTO)

## Objectif
Compléter et exécuter tous les tests automatisés.

## Prérequis
- `WORKFLOW_STATE.md` avec `browser_tests_passed: true`
- Squelettes de tests créés en phase TEST-SPEC
- Code implémenté

## Processus

### Étape 1: Compléter les Tests Unitaires

#### 2.1 Tests Unitaires

**Pour chaque fonction/composant clé**, écrire des tests :

```typescript
// tests/unit/{module}.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MyFunction } from '@/module';

describe('MyFunction', () => {
  // Setup
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Happy path
  it('should return expected result for valid input', () => {
    const result = MyFunction('valid input');
    expect(result).toBe('expected output');
  });

  // Edge cases
  it('should handle empty input', () => {
    expect(() => MyFunction('')).toThrow('Input required');
  });

  it('should handle null input', () => {
    expect(() => MyFunction(null)).toThrow('Input required');
  });

  // Error cases
  it('should throw on invalid input', () => {
    expect(() => MyFunction('invalid')).toThrow('Invalid input');
  });
});
```

**Couverture minimale** (depuis constitution ou défaut):
- Lignes: 80%
- Branches: 70%
- Fonctions: 80%

#### 2.2 Tests d'Intégration

**Pour chaque endpoint API**, écrire des tests :

```typescript
// tests/integration/{feature}.test.ts
import request from 'supertest';
import { app } from '@/app';
import { db } from '@/database';

describe('API: Feature X', () => {
  // Setup/Teardown
  beforeAll(async () => {
    await db.migrate();
  });

  afterAll(async () => {
    await db.close();
  });

  beforeEach(async () => {
    await db.truncate('feature_x');
  });

  // CRUD Operations
  describe('POST /api/feature-x', () => {
    it('should create resource with valid data', async () => {
      const response = await request(app)
        .post('/api/feature-x')
        .send({ field1: 'value', field2: 123 })
        .expect(201);

      expect(response.body).toMatchObject({
        id: expect.any(String),
        field1: 'value',
        field2: 123,
      });
    });

    it('should reject invalid data with 400', async () => {
      const response = await request(app)
        .post('/api/feature-x')
        .send({ field1: '' }) // Invalid: empty
        .expect(400);

      expect(response.body.error).toBe('validation_error');
    });

    it('should require authentication', async () => {
      await request(app)
        .post('/api/feature-x')
        .send({ field1: 'value' })
        // Sans token
        .expect(401);
    });
  });

  describe('GET /api/feature-x/:id', () => {
    it('should return resource if exists', async () => {
      // Setup: créer une ressource
      const created = await createTestResource();

      const response = await request(app)
        .get(`/api/feature-x/${created.id}`)
        .expect(200);

      expect(response.body.id).toBe(created.id);
    });

    it('should return 404 if not found', async () => {
      await request(app)
        .get('/api/feature-x/non-existent-id')
        .expect(404);
    });
  });
});
```

#### 2.3 Tests E2E (Playwright)

**Pour chaque User Story**, écrire des tests :

```typescript
// tests/scenarios/{feature}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Feature: {Feature Name}', () => {
  // Configuration
  test.beforeEach(async ({ page }) => {
    // Login si nécessaire
    await page.goto('http://localhost:3000');
  });

  // US-001: User Story Title
  test('US-001: should allow user to [action]', async ({ page }) => {
    // Given: État initial
    await page.goto('/feature-page');
    await expect(page.locator('h1')).toContainText('Feature Page');

    // When: Action utilisateur
    await page.fill('[data-testid="input-field"]', 'test value');
    await page.click('[data-testid="submit-button"]');

    // Then: Résultat attendu
    await expect(page.locator('[data-testid="success-message"]'))
      .toBeVisible();
    await expect(page.locator('[data-testid="result"]'))
      .toContainText('test value');
  });

  // Cas d'erreur
  test('should show error message on invalid input', async ({ page }) => {
    await page.goto('/feature-page');
    
    // Soumettre formulaire vide
    await page.click('[data-testid="submit-button"]');

    // Vérifier message d'erreur
    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText('Field is required');
  });

  // Cas limite
  test('should handle edge case: [description]', async ({ page }) => {
    // ...
  });
});
```

---

### Étape 3: Exécuter les Tests Automatisés

**Ordre d'exécution**:

```bash
# 1. Tests unitaires (rapides)
npm run test:unit
# Ou: npx vitest run

# 2. Tests d'intégration (moyens)
npm run test:integration
# Ou: npx vitest run tests/integration

# 3. Tests E2E (lents, nécessitent serveur)
npm run test:e2e
# Ou: npx playwright test
```

**Capturer les résultats**:

Pour chaque suite de tests, noter :
- Nombre de tests passés/échoués
- Détails des échecs
- Couverture (si disponible)

---

### Étape 4: Tests Browser Interactifs

**IMPORTANT**: Cette étape utilise Playwright pour tester visuellement l'application.

**Processus**:

1. **Démarrer l'application** (si pas déjà fait)
   ```bash
   npm run dev &
   # Attendre que le serveur soit prêt
   ```

2. **Naviguer et tester**
   
   Utiliser les outils browser MCP pour :
   - Naviguer vers chaque page de la feature
   - Effectuer les actions utilisateur
   - Vérifier les résultats visuellement
   - Prendre des screenshots si problèmes

3. **Scénarios à tester manuellement**:
   
   - [ ] Parcours principal (happy path)
   - [ ] Chaque cas d'erreur
   - [ ] Responsive (si applicable)
   - [ ] Accessibilité basique (focus, labels)

4. **Documenter les observations**:
   
   ```markdown
   ## Browser Test Results
   
   ### Parcours principal
   - [x] Page charge correctement
   - [x] Formulaire fonctionne
   - [x] Soumission réussie
   - [x] Message de succès affiché
   
   ### Cas d'erreur
   - [x] Validation affichée
   - [ ] Message d'erreur peu visible (minor)
   
   ### Observations
   - Animation de chargement manquante (suggestion)
   ```

---

### Étape 5: Analyser les Résultats

**Catégoriser les échecs**:

| Type | Sévérité | Action |
|------|----------|--------|
| Test unitaire échoue | High | Retour TEST-SPEC |
| Test intégration échoue | High | Retour TEST-SPEC |
| Test E2E échoue | High | Retour TEST-SPEC |
| Couverture insuffisante | Medium | Retour TEST-SPEC |
| Problème visuel mineur | Low | Note pour review |

**Décision**:

```
SI échecs (unit/integration/e2e/couverture) :
  -> Retour en TEST-SPEC pour revoir les scénarios
  -> tests_passed: false
  -> Feedback envoyé pour guider la révision

SI tous tests passent + couverture OK :
  -> tests_passed: true
  -> Continuer vers REVIEW-FINAL
```

---

### Étape 6: Mettre à jour l'État

#### Si tests passent :

```markdown
## Workflow Progress
- **current_phase**: test
- **current_step**: complete
- **loop_count**: {N}

## Conditions Met
```yaml
implementation_complete: true
tests_passed: true  # <-- Changé à true
review_passed: false
```

## Context Data
```yaml
test_results:
  unit:
    passed: 24
    failed: 0
    coverage: 85%
  integration:
    passed: 12
    failed: 0
  e2e:
    passed: 8
    failed: 0
  browser_manual:
    status: passed
    observations:
      - "Animation loading manquante (suggestion)"
```

## History
| {now} | test | all_tests_passed | success |
```

#### Si tests échouent :

```markdown
## Workflow Progress
- **current_phase**: dev  # <-- Retour en dev
- **current_step**: fix_required
- **loop_count**: {N+1}  # <-- Incrémenté

## Conditions Met
```yaml
implementation_complete: false  # <-- Reset
tests_passed: false
```

## Context Data
```yaml
dev_feedback:
  source: test
  issues:
    - type: test_failure
      suite: unit
      test: "MyFunction should handle empty input"
      file: tests/unit/myFunction.test.ts
      line: 23
      message: "Expected error to be thrown but function returned null"
      fix_suggestion: "Add null check in MyFunction before processing"
    - type: test_failure
      suite: e2e
      test: "should show success message"
      file: tests/scenarios/feature.spec.ts
      message: "Timeout waiting for success message"
      fix_suggestion: "Check if success message element has correct data-testid"
```

## History
| {now} | test | tests_failed | return_to_dev |
```

---

## Checklist de Sortie

Avant de rendre la main à l'orchestrateur :

- [ ] Tous les tests unitaires écrits pour le code critique
- [ ] Tests d'intégration pour tous les endpoints API
- [ ] Tests E2E pour les parcours utilisateur principaux
- [ ] Tous les tests exécutés
- [ ] Résultats documentés dans l'état
- [ ] Décision claire : pass ou return to dev

---

## Communication avec l'Orchestrateur

### Si tests passent :

```
---
## ✅ Phase TEST terminée

**Résultats**:
- Tests unitaires: {N}/{N} ✅
- Tests intégration: {N}/{N} ✅
- Tests E2E: {N}/{N} ✅
- Couverture: {X}%

**Tests browser**:
- Parcours principal: ✅
- Cas d'erreur: ✅
- Observations mineures: {liste si applicable}

**Prochaine phase**: REVIEW

L'orchestrateur peut maintenant appeler @he-review.
---
```

### Si tests échouent :

```
---
## ❌ Phase TEST-AUTO - Retour en TEST-SPEC requis

**Échecs détectés**:
| Suite | Test | Raison |
|-------|------|--------|
| unit | MyFunction empty input | Scénario non couvert |
| e2e | Success message | Timeout - élément non trouvé |

**Actions requises**:
1. Revoir les scénarios de test pour couvrir les cas manquants
2. Vérifier que les tests reflètent les spécifications
3. Adapter les scénarios si nécessaire

**Feedback envoyé** à `WORKFLOW_STATE.md > context.test_feedback`

**Retour à**: Phase TEST-SPEC (loop_count: {N+1})

L'orchestrateur doit appeler @he-test action=write_scenarios pour réviser les scénarios.
---
```


