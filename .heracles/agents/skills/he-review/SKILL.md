---
name: he-review
description: Spécialiste de l'audit qualité - review code (intermédiaire) et review final (sécurité, performance, documentation)
triggers:
  keywords: [review, audit, quality, security, performance]
  phases: [review-code, review-final]
  actions: [code_review, final_review]
capabilities:
  - read_files
  - execute_commands
  - search_code
constraints:
  - Vérifier la conformité à la constitution
  - Vérifier la conformité à la specification
  - Score minimum 80% pour passer
  - Documenter tous les issues avec severity et fix suggestion
output_format: |
  ## ✅ Phase REVIEW terminée
  **Score global**: {X}%
  **Constitution**: {X}%, Specification: {X}%, Security: {X}%, Performance: {X}%
  **Issues critiques**: {N}
  **Prochaine phase**: FINALIZE (ou DEV/TEST si échec)
---

# Skill: Review Agent

> Spécialiste de l'audit qualité et de la revue de code

## Description

Ce skill gère **2 phases distinctes** du workflow :
- **Phase 4 (REVIEW-CODE)**: Audit intermédiaire du code AVANT les tests
- **Phase 7 (REVIEW-FINAL)**: Audit final complet avant merge

## Triggers et Actions

Ce skill est appelé avec une action spécifique :

| Action | Phase | Quand |
|--------|-------|-------|
| `code_review` | REVIEW-CODE | Après DEV, avant TEST-BROWSER |
| `final_review` | REVIEW-FINAL | Après TEST-AUTO, avant FINALIZE |

---

# ACTION: code_review (Phase 4 - REVIEW-CODE)

## Objectif
Audit qualité du code **AVANT** les tests fonctionnels.
Focus sur : structure, patterns, constitution compliance.

## Prérequis
- `WORKFLOW_STATE.md` avec `implementation_complete: true`
- Code implémenté dans `{source_dir}/` (défini dans `detected_structure`)
- `constitution.md` disponible
- `.heracles/sessions/{session_id}/specs/specification.md` disponible

## Chemins Dynamiques

Les chemins utilisés par ce skill sont définis dans `WORKFLOW_STATE.md > detected_structure` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `source_dir` | `src` | Répertoire des sources |
| `test_dir` | `test` | Répertoire des tests |
| `spec_dir` | `spec` | Répertoire des specs projet |

## Processus

### Étape 1: Charger le Contexte

**Fichiers à lire**:
1. `WORKFLOW_STATE.md` - Session ID, fichiers créés/modifiés, **detected_structure**
2. `constitution.md` - Standards à vérifier
3. `.heracles/sessions/{session_id}/specs/specification.md` - Ce qui devait être implémenté
4. `.heracles/sessions/{session_id}/specs/plan.md` - Architecture prévue
5. `{spec_dir}/architecture.md` - Normes et conventions (si existe)

### Étape 2: Review Constitution Compliance

Vérifier UNIQUEMENT :
- [ ] Conventions de nommage
- [ ] Formatage (Prettier/ESLint)
- [ ] Structure de fichiers
- [ ] Patterns architecturaux
- [ ] Types TypeScript (pas de `any`)
- [ ] Gestion d'erreurs basique

**Commandes**:
```bash
npm run lint
npm run type-check
```

### Étape 3: Review Specification Compliance

Pour chaque User Story, vérifier :
- [ ] Fonctionnalité implémentée
- [ ] Critères d'acceptation couverts (code présent)
- [ ] Pas de fonctionnalité hors spec

### Étape 4: Score et Décision

**Calcul score (simplifié)**:
```
Constitution: 50%
Specification: 50%
---
TOTAL >= 80% = PASS
```

**Si PASS**:
```yaml
conditions_met:
  code_review_passed: true
```

**Si FAIL**:
```yaml
current_phase: dev
conditions_met:
  implementation_complete: false
  code_review_passed: false

context:
  dev_feedback:
    source: code_review
    score: 65
    issues:
      - type: constitution_violation
        rule: "Naming convention"
        file: src/components/myComponent.tsx
        message: "Should be PascalCase: MyComponent.tsx"
        severity: medium
```

### Sortie

```
---
## ✅ Phase REVIEW-CODE terminée

**Score**: 85%
- Constitution: 90%
- Specification: 80%

**Issues mineures** (non bloquantes):
- [Liste si applicable]

**Prochaine phase**: TEST-BROWSER
---
```

---

# ACTION: final_review (Phase 7 - REVIEW-FINAL)

## Objectif
Audit qualité **COMPLET** avant merge.
Focus sur : sécurité, performance, documentation, qualité globale.

## Prérequis
- `WORKFLOW_STATE.md` avec `auto_tests_passed: true`
- Tous les tests passés
- `constitution.md` disponible
- `specs/{feature_id}/specification.md` disponible

## Processus (Final Review)

### Étape 1: Charger le Contexte

**Fichiers à lire**:

1. `WORKFLOW_STATE.md` - Session ID, fichiers modifiés, résultats tests, **detected_structure**
2. `constitution.md` - Standards à vérifier
3. `.heracles/sessions/{session_id}/specs/specification.md` - Critères d'acceptation
4. `.heracles/sessions/{session_id}/specs/plan.md` - Architecture prévue
5. `{spec_dir}/architecture.md` - Normes et conventions (si existe)
6. Tous les fichiers source créés/modifiés dans `{source_dir}/`
7. Rapports de tests (coverage, résultats)

---

### Étape 2: Review Constitution Compliance (Complète)

**Vérifier chaque règle de la constitution**:

#### 2.1 Style de Code

- [ ] Conventions de nommage respectées
- [ ] Formatage consistant (Prettier/ESLint)
- [ ] Imports organisés
- [ ] Pas de code mort
- [ ] Commentaires appropriés

**Commandes**:
```bash
npm run lint
npm run format:check
```

#### 2.2 Architecture

- [ ] Structure de fichiers conforme
- [ ] Patterns architecturaux respectés
- [ ] Séparation des responsabilités
- [ ] Pas de dépendances circulaires

#### 2.3 Qualité

- [ ] Pas de `any` non justifié (TypeScript)
- [ ] Gestion d'erreurs complète
- [ ] Pas de magic numbers
- [ ] DRY (pas de duplication)
- [ ] SOLID principles suivis

**Format de rapport**:

```markdown
### Constitution Compliance

| Règle | Status | Détails |
|-------|--------|---------|
| Nommage | ✅ Pass | Conventions respectées |
| Formatage | ✅ Pass | ESLint clean |
| Architecture | ⚠️ Warning | Un composant trop gros |
| Types | ✅ Pass | Pas de `any` |
| Erreurs | ❌ Fail | Catch vide ligne 45 |

**Score**: 4/5 (80%)
```

---

### Étape 3: Review Specification Compliance

**Vérifier chaque critère d'acceptation**:

Pour chaque User Story dans la spec :

1. Lire les critères d'acceptation
2. Vérifier dans le code que chaque critère est implémenté
3. Tracer le lien code ↔ critère

**Format de rapport**:

```markdown
### Specification Compliance

#### US-001: [User Story Title]
| Critère | Implémenté | Fichier | Ligne |
|---------|------------|---------|-------|
| Critère 1 | ✅ | src/feature.ts | 23-45 |
| Critère 2 | ✅ | src/feature.ts | 67-89 |
| Critère 3 | ❌ | - | Non trouvé |

#### US-002: [User Story Title]
...

**Score**: 8/9 critères (89%)
```

---

### Étape 4: Security Audit

**Checklist de sécurité**:

#### 4.1 Input Validation
- [ ] Tous les inputs utilisateur validés
- [ ] Sanitization des strings
- [ ] Validation côté serveur (pas que client)

#### 4.2 Authentication/Authorization
- [ ] Routes protégées identifiées
- [ ] Vérification des permissions
- [ ] Tokens validés correctement

#### 4.3 Data Protection
- [ ] Pas de secrets dans le code
- [ ] Données sensibles non loggées
- [ ] HTTPS utilisé

#### 4.4 Common Vulnerabilities
- [ ] SQL Injection protégé (queries paramétrées)
- [ ] XSS protégé (échappement output)
- [ ] CSRF protégé (tokens)
- [ ] Path traversal protégé

**Commandes**:
```bash
# Scan de dépendances
npm audit

# Scan de secrets (si outil installé)
gitleaks detect --source .
```

**Format de rapport**:

```markdown
### Security Audit

| Catégorie | Status | Détails |
|-----------|--------|---------|
| Input Validation | ✅ Pass | Zod schemas utilisés |
| Auth/Authz | ✅ Pass | Middleware JWT en place |
| Data Protection | ⚠️ Warning | Email loggé (à vérifier) |
| SQL Injection | ✅ Pass | Prisma/ORM utilisé |
| XSS | ✅ Pass | React escape par défaut |
| npm audit | ✅ Pass | 0 vulnérabilités |

**Score**: 5/6 (83%)
**Vulnérabilités critiques**: 0
```

---

### Étape 5: Performance Review

**Vérifications**:

#### 5.1 Database
- [ ] Queries optimisées (pas de N+1)
- [ ] Index appropriés
- [ ] Pas de requêtes dans les boucles

#### 5.2 Frontend
- [ ] Composants memoizés si nécessaire
- [ ] Lazy loading utilisé
- [ ] Bundle size raisonnable

#### 5.3 API
- [ ] Pagination implémentée
- [ ] Caching si approprié
- [ ] Response time acceptable

**Format de rapport**:

```markdown
### Performance Review

| Aspect | Status | Détails |
|--------|--------|---------|
| DB Queries | ✅ Pass | Includes utilisés, pas de N+1 |
| Indexation | ⚠️ Warning | Index manquant sur field_x |
| Bundle Size | ✅ Pass | +12KB (acceptable) |
| Memoization | ✅ Pass | React.memo utilisé |

**Recommandations**:
- Ajouter index sur `feature_x.field_x`
```

---

### Étape 6: Code Quality Score

**Calcul du score global**:

```
Constitution Compliance: 80% × 0.25 = 20%
Specification Compliance: 89% × 0.30 = 26.7%
Security: 83% × 0.30 = 24.9%
Performance: 75% × 0.15 = 11.25%
---
TOTAL: 82.85%
```

**Seuil de passage**: 80% (configurable dans constitution)

---

### Étape 7: Décision

```
SI score >= 80% ET pas de vulnérabilité critique :
  -> final_review_passed: true
  -> Continuer vers FINALIZE

SI score >= 80% MAIS warnings importants :
  -> Demander confirmation à l'utilisateur
  -> Si OK: final_review_passed: true
  -> Si refus: déterminer où retourner

SI score < 80% OU vulnérabilité critique :
  -> final_review_passed: false
  -> Analyser les issues:
     - Si problème de code: retour DEV
     - Si problème de tests: retour TEST-AUTO (fix_tests: true)
     - Si les deux: retour DEV
```

---

### Étape 8: Mettre à jour l'État

#### Si review passe :

```markdown
## Workflow Progress
- **current_phase**: review-final
- **current_step**: complete

## Conditions Met
```yaml
auto_tests_passed: true
final_review_passed: true  # <-- Changé à true
```

## Context Data
```yaml
review_results:
  constitution_score: 80
  spec_score: 89
  security_score: 83
  performance_score: 75
  total_score: 82.85
  critical_issues: 0
  warnings: 2
  approved_at: {timestamp}
```

## History
| {now} | review-final | approved | score: 82.85% |
```

#### Si review échoue (retour DEV) :

```markdown
## Workflow Progress
- **current_phase**: dev  # <-- Retour en dev
- **current_step**: fix_required
- **loop_count**: {N+1}

## Conditions Met
```yaml
implementation_complete: false  # <-- Reset
code_review_passed: false
browser_tests_passed: false
auto_tests_passed: false
final_review_passed: false
```

## Context Data
```yaml
dev_feedback:
  source: final_review
  fix_tests: false  # true si c'est un problème de tests
  score: 65
  issues:
    - type: constitution_violation
      rule: "Error handling"
      file: src/api/feature.ts
      line: 45
      message: "Empty catch block"
      severity: high
      fix: "Add proper error logging and handling"
    - type: security
      category: "Data Protection"
      file: src/utils/logger.ts
      message: "Email logged in plain text"
      severity: medium
      fix: "Mask email in logs"
```

## History
| {now} | review-final | rejected | score: 65%, issues: 2 |
```

#### Si review échoue (retour TEST-AUTO pour fix tests) :

```markdown
## Workflow Progress
- **current_phase**: test-auto  # <-- Retour aux tests
- **current_step**: fix_tests
- **loop_count**: {N+1}

## Conditions Met
```yaml
auto_tests_passed: false  # <-- Reset
final_review_passed: false
```

## Context Data
```yaml
dev_feedback:
  source: final_review
  fix_tests: true  # Indique que c'est un problème de tests
  issues:
    - type: test_coverage
      message: "Coverage insuffisant sur module X"
      fix: "Ajouter tests pour les cas limites"
    - type: test_quality
      file: tests/unit/feature.test.ts
      message: "Tests trop superficiels"
      fix: "Ajouter assertions plus précises"
```

## History
| {now} | review-final | rejected | fix_tests required |
```

---

## Rapport de Review Complet

Générer un rapport markdown complet :

```markdown
# Code Review Report

> Feature: {feature_id} - {feature_description}
> Date: {timestamp}
> Reviewer: AI Review Agent

## Summary

| Metric | Score | Status |
|--------|-------|--------|
| Constitution | 80% | ✅ Pass |
| Specification | 89% | ✅ Pass |
| Security | 83% | ✅ Pass |
| Performance | 75% | ⚠️ Acceptable |
| **TOTAL** | **82.85%** | **✅ APPROVED** |

## Critical Issues
None

## Warnings
1. Index manquant sur `feature_x.field_x`
2. Email visible dans logs (non critique)

## Detailed Reports

### Constitution Compliance
[Détails...]

### Specification Compliance
[Détails...]

### Security Audit
[Détails...]

### Performance Review
[Détails...]

## Recommendations
1. Ajouter index DB avant mise en production
2. Masquer emails dans logs (prochaine itération)

## Conclusion
✅ Code approuvé pour merge avec les warnings notés.
```

Sauvegarder dans : `.heracles/sessions/{session_id}/review-reports/final-review.md`

---

## Communication avec l'Orchestrateur

### Si review-final passe :

```
---
## ✅ Phase REVIEW-FINAL terminée

**Score global**: 82.85%

**Résumé**:
| Catégorie | Score |
|-----------|-------|
| Constitution | 80% |
| Specification | 89% |
| Security | 83% |
| Performance | 75% |

**Issues critiques**: 0
**Warnings**: 2 (documentés)

**Rapport complet**: `.heracles/sessions/{session_id}/review-reports/final-review.md`

**Prochaine phase**: FINALIZE

L'orchestrateur peut maintenant appeler @he-workflow action=finalize.
---
```

### Si review-final échoue (retour DEV) :

```
---
## ❌ Phase REVIEW-FINAL - Retour en DEV requis

**Score global**: 65% (minimum: 80%)

**Issues à corriger**:
| Sévérité | Catégorie | Problème |
|----------|-----------|----------|
| HIGH | Constitution | Empty catch block |
| MEDIUM | Security | Email en clair dans logs |

**Détails envoyés** à `WORKFLOW_STATE.md > context.dev_feedback`

**Retour à**: Phase DEV (loop_count: {N+1})

L'orchestrateur doit appeler @he-dev pour corrections.
---
```

### Si review-final échoue (retour TEST-AUTO) :

```
---
## ❌ Phase REVIEW-FINAL - Amélioration des tests requise

**Score global**: 78% (minimum: 80%)

**Problème principal**: Couverture de tests insuffisante

**Issues à corriger**:
| Type | Détail |
|------|--------|
| Coverage | Module X non couvert (45%) |
| Quality | Tests trop superficiels sur Y |

**Détails envoyés** à `WORKFLOW_STATE.md > context.dev_feedback`

**Retour à**: Phase TEST-AUTO (pour améliorer les tests)

L'orchestrateur doit appeler @he-test action=run_tests.
---
```


