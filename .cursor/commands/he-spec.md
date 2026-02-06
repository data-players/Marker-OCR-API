---
name: he-spec
description: Phase SPEC - Spécification fonctionnelle et technique de la feature
arguments:
  - name: mode
    description: Mode d'exécution
    required: false
    enum: [start, continue]
    default: "start"
---

Démarrage de la phase SPEC du workflow Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-spec/SKILL.md`

## Comportement

{{#if (eq mode "start")}}
**Démarrage de la spécification**

1. Vérifier les prérequis:
   - `WORKFLOW_STATE.md` existe
   - `constitution.md` existe
   - `feature_description` est définie

2. Lancer le **dialogue fonctionnel** avec l'utilisateur:
   - Questions sur le contexte utilisateur
   - Questions sur le comportement attendu
   - Questions sur les critères d'acceptation
   - Questions sur les contraintes
   - Questions sur les priorités (MVP)

3. **Ne pas commencer la rédaction** avant d'avoir toutes les réponses !
{{else}}
**Reprise de la spécification**

1. Relire le contexte existant dans `WORKFLOW_STATE.md`
2. Reprendre là où le dialogue s'était arrêté
3. Compléter les fichiers de spec si nécessaire
{{/if}}

## Livrables attendus

À la fin de cette phase, créer:

1. `.heracles/sessions/{session_id}/specs/specification.md`
   - User Stories avec critères d'acceptation
   - Parcours utilisateur (happy path + alternatifs)
   - Cas d'erreur
   - Interfaces UI

2. `.heracles/sessions/{session_id}/specs/plan.md`
   - Architecture technique
   - Modèles de données
   - API design
   - Stratégie de test

3. `.heracles/sessions/{session_id}/specs/tasks.md`
   - Macro-tâches et micro-tâches
   - Dépendances entre tâches
   - Ordre d'exécution

## Transition

Une fois terminé:
- Mettre à jour `WORKFLOW_STATE.md` avec `spec_complete: true`
- Annoncer: "Phase SPEC terminée → Prochaine phase: TEST-SPEC"
