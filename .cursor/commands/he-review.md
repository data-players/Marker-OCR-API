---
name: he-review
description: Phases de review - audit qualité du code et review finale
arguments:
  - name: action
    description: Type de review à exécuter
    required: true
    enum: [code, final]
---

Exécution d'une phase de review du workflow Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-review/SKILL.md`

## Actions disponibles

| Action | Phase | Description |
|--------|-------|-------------|
| `code` | REVIEW-CODE | Audit intermédiaire du code (avant tests browser) |
| `final` | REVIEW-FINAL | Audit final complet (avant merge) |

---

{{#if (eq action "code")}}
## Phase REVIEW-CODE: Audit intermédiaire

**Objectif**: Vérifier la qualité du code AVANT les tests fonctionnels

**Prérequis**:
- `implementation_complete: true`
- Code présent dans `{source_dir}/`
- `constitution.md` disponible

**Vérifications**:

1. **Constitution Compliance** (50% du score):
   - Conventions de nommage
   - Formatage (ESLint/Prettier)
   - Structure de fichiers
   - Patterns architecturaux
   - Types TypeScript (pas de `any`)
   - Gestion d'erreurs basique

2. **Specification Compliance** (50% du score):
   - Chaque User Story implémentée
   - Critères d'acceptation couverts
   - Pas de fonctionnalité hors spec

**Commandes**:
```bash
npm run lint
npm run type-check
```

**Seuil**: Score >= 80% pour passer

**Transition**:
- ✅ Succès → `code_review_passed: true` → Phase TEST-BROWSER
- ❌ Échec → Retour DEV avec `dev_feedback`
{{/if}}

{{#if (eq action "final")}}
## Phase REVIEW-FINAL: Audit complet

**Objectif**: Audit qualité COMPLET avant merge

**Prérequis**:
- `auto_tests_passed: true`
- Tous les tests passés

**Vérifications**:

1. **Constitution Compliance** (25%):
   - Style de code complet
   - Architecture respectée
   - Qualité du code

2. **Specification Compliance** (30%):
   - Tous critères d'acceptation validés
   - Traçabilité code ↔ spec

3. **Security Audit** (30%):
   - Input validation
   - Auth/Authz
   - Data protection
   - Vulnérabilités communes (SQLi, XSS, CSRF)
   ```bash
   npm audit
   ```

4. **Performance Review** (15%):
   - Queries DB optimisées
   - Bundle size
   - Memoization frontend

**Score global**: >= 80% + 0 vulnérabilité critique

**Rapport**: `.heracles/sessions/{session_id}/review-reports/final-review.md`

**Transition**:
- ✅ Succès → `final_review_passed: true` → Phase FINALIZE
- ❌ Échec code → Retour DEV
- ❌ Échec tests → Retour TEST-AUTO avec `fix_tests: true`
{{/if}}
