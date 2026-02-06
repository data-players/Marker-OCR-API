---
name: he-test
description: Phases de test - scénarios TDD, tests de développement, tests browser, tests automatisés
arguments:
  - name: action
    description: Type de test à exécuter
    required: true
    enum: [scenarios, dev, browser, auto]
---

Exécution d'une phase de test du workflow Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-test/SKILL.md`

## Actions disponibles

| Action | Phase | Description |
|--------|-------|-------------|
| `scenarios` | TEST-SPEC (Phase 2) | Écrire les scénarios de test (TDD, AVANT le code) |
| `dev` | DEV-TEST (Phase 4) | Tests de développement (unitaires + intégration) |
| `browser` | TEST-BROWSER (Phase 6) | Tests interactifs sur navigateur (E2E) |
| `auto` | TEST-AUTO (Phase 7) | Exécuter tous les tests automatisés (CI) |

---

{{#if (eq action "scenarios")}}
## Phase TEST-SPEC: Écriture des scénarios

**Objectif**: Écrire les tests AVANT l'implémentation (TDD/BDD)

**Prérequis**:
- `spec_complete: true`
- `specification.md` existe
- **PAS de code implémenté**

**Processus**:

1. Lire `specification.md`:
   - Extraire User Stories et critères d'acceptation
   - Identifier parcours principal et alternatifs
   - Lister les cas d'erreur

2. Créer les scénarios E2E (Playwright):
   ```
   {test_e2e}/{feature_id}.spec.ts
   ```

3. Créer les squelettes de tests unitaires:
   ```
   {test_unit}/{feature}.test.ts
   ```

4. Créer les squelettes de tests d'intégration:
   ```
   {test_integration}/{feature}.test.ts
   ```

**Transition**: `test_scenarios_written: true` → Phase DEV
{{/if}}

{{#if (eq action "dev")}}
## Phase DEV-TEST: Tests de développement

**Objectif**: Valider le code avec tests unitaires et d'intégration

**Prérequis**:
- `implementation_complete: true`
- Build et lint passent
- Squelettes de tests existent (de TEST-SPEC)

**Processus**:

1. Compléter les tests unitaires (transformer `it.todo()` en vrais tests)

2. Compléter les tests d'intégration

3. Exécuter les tests:
   ```bash
   npm run test:unit
   npm run test:integration
   ```

4. Vérifier la couverture (minimum 80%)

**Transition**: 
- ✅ Succès → `dev_tests_passed: true` → Phase REVIEW-CODE
- ❌ Échec → Retour Phase DEV pour corrections
{{/if}}

{{#if (eq action "browser")}}
## Phase TEST-BROWSER: Tests interactifs

**Objectif**: Tester l'application sur un navigateur réel

**Prérequis**:
- `code_review_passed: true`
- Application démarrable

**Processus**:

1. Démarrer l'application:
   ```bash
   npm run dev &
   npx wait-on http://localhost:3000
   ```

2. Tests interactifs avec les outils browser MCP:
   - `browser_navigate` → Aller sur les pages
   - `browser_snapshot` → Capturer l'état
   - `browser_click/type` → Interagir
   - `browser_take_screenshot` → Capturer si problème

3. Exécuter les tests E2E:
   ```bash
   npx playwright test --headed --project=chromium
   ```

4. Documenter les résultats

**Transition**: 
- ✅ Succès → `browser_tests_passed: true` → Phase TEST-AUTO
- ❌ Échec → Retour Phase DEV pour corrections
{{/if}}

{{#if (eq action "auto")}}
## Phase TEST-AUTO: Tests automatisés complets

**Objectif**: Exécuter tous les tests automatisés (CI)

**Prérequis**:
- `browser_tests_passed: true`
- Tous les tests écrits

**Processus**:

1. Exécuter tous les tests:
   ```bash
   npm run test:unit
   npm run test:integration
   npm run test:e2e
   ```

2. Vérifier la couverture globale (minimum 80%)

3. Analyser les résultats:
   - Identifier les échecs
   - Catégoriser les problèmes

**Transition**:
- ✅ Tous passent → `auto_tests_passed: true` → Phase REVIEW-FINAL
- ❌ Échecs → Retour Phase TEST-SPEC pour revoir les scénarios
{{/if}}
