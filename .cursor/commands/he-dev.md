---
name: he-dev
description: Phase DEV - Implémentation du code selon les spécifications
arguments:
  - name: task
    description: ID de tâche spécifique à implémenter (optionnel, sinon toutes)
    required: false
---

Démarrage de la phase DEV du workflow Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-dev/SKILL.md`

## Prérequis

Vérifier avant de commencer:
- `WORKFLOW_STATE.md` avec `spec_complete: true`
- `.heracles/sessions/{session_id}/specs/specification.md` existe
- `.heracles/sessions/{session_id}/specs/plan.md` existe
- `.heracles/sessions/{session_id}/specs/tasks.md` existe
- `constitution.md` existe

## Comportement

{{#if task}}
**Implémentation de la tâche {{task}}**

1. Lire la tâche spécifique dans `tasks.md`
2. Vérifier ses dépendances
3. Implémenter uniquement cette tâche
4. Marquer comme complétée
{{else}}
**Implémentation complète**

1. Charger le contexte:
   - `WORKFLOW_STATE.md` → session_id, loop_count, detected_structure
   - `constitution.md` → règles à respecter
   - `specification.md` → ce qu'on doit faire
   - `plan.md` → comment le faire
   - `tasks.md` → liste des tâches

2. Analyser les tâches:
   - Si `loop_count = 0`: implémenter toutes les tâches
   - Si `loop_count > 0`: lire `dev_feedback` et corriger

3. Pour chaque tâche:
   - Vérifier les dépendances
   - Implémenter selon le plan technique
   - Respecter la constitution
   - Marquer comme complétée
{{/if}}

## Règles d'implémentation

✅ **DO**:
- Suivre EXACTEMENT le plan technique
- Respecter les conventions de `constitution.md`
- Écrire du code testable
- Gérer tous les cas d'erreur de la spec
- Documenter les décisions non évidentes

❌ **DON'T**:
- Inventer des features non spécifiées
- Ignorer les conventions
- Laisser des `console.log` de debug
- Utiliser `any` sans justification

## Auto-vérification

Avant de terminer, exécuter:
```bash
npm run build
npm run lint
npm run type-check
```

## Transition

Une fois terminé:
- Mettre à jour `WORKFLOW_STATE.md` avec `implementation_complete: true`
- Annoncer: "Phase DEV terminée → Prochaine phase: REVIEW-CODE"
