---
name: he-workflow
description: Heracles workflow management - start, resume, status, or manage sessions
arguments:
  - name: action
    description: Action to perform
    required: true
    enum: [start, resume, status, sessions, switch, goto, stop, init, analyze, finalize]
  - name: param
    description: Parameter for the action (feature description for start, session_id for switch, phase for goto)
    required: false
---

Execute Heracles workflow command.

## Actions disponibles

| Action | Description | Paramètre |
|--------|-------------|-----------|
| `start` | Démarrer un nouveau workflow | Description de la feature |
| `resume` | Reprendre le workflow actif | - |
| `status` | Afficher l'état actuel | - |
| `sessions` | Lister toutes les sessions | - |
| `switch` | Changer de session | session_id |
| `goto` | Aller à une phase | phase (init, spec, dev, test, review, finalize) |
| `stop` | Suspendre le workflow | - |
| `init` | Initialiser le projet (structure, constitution) | - |
| `analyze` | Analyser un projet existant | - |
| `finalize` | Finaliser le workflow (commit, PR) | - |

## Exécution

{{#if (eq action "start")}}
Démarrage d'un nouveau workflow Heracles pour: "{{param}}"

1. Lire `.heracles/agents/ARBITRAGE.md` pour les règles d'arbitrage
2. Si approprié, charger `.heracles/agents/HERACLES.md`
3. Créer une nouvelle session et démarrer le workflow
{{/if}}

{{#if (eq action "resume")}}
Reprise du workflow Heracles actif.

1. Chercher l'ID de session dans la mémoire de conversation
2. Lire `.heracles/agents/HERACLES.md`
3. Reprendre là où on s'était arrêté
{{/if}}

{{#if (eq action "status")}}
Afficher l'état du workflow Heracles actuel.

1. Chercher la session active
2. Lire `WORKFLOW_STATE.md`
3. Afficher le résumé
{{/if}}

{{#if (eq action "sessions")}}
Lister toutes les sessions Heracles.

```bash
ls -la .heracles/sessions/
```
{{/if}}

{{#if (eq action "switch")}}
Changer vers la session: {{param}}

1. Vérifier que la session existe
2. Charger son état
3. Reprendre le workflow
{{/if}}

{{#if (eq action "goto")}}
Aller à la phase: {{param}}

⚠️ Cette action peut sauter des étapes. Utilisez avec précaution.
{{/if}}

{{#if (eq action "stop")}}
Suspendre le workflow actuel.

La session reste intacte et peut être reprise avec `/workflow resume`.
{{/if}}

{{#if (eq action "init")}}
Initialisation du projet Heracles.

1. Lire `.heracles/agents/HERACLES.md`
2. Détecter si le projet est vierge ou existant
3. Si vierge: créer structure standard (constitution, specs, répertoires)
4. Si existant: appeler l'analyse du projet
5. Créer les fichiers de configuration Heracles
{{/if}}

{{#if (eq action "analyze")}}
Analyse d'un projet existant.

1. Lire `.heracles/agents/skills/project-analyzer/SKILL.md`
2. Scanner la structure du projet
3. Détecter le stack technologique
4. Identifier les conventions en place
5. Générer `PROJECT_ANALYSIS.md` avec la configuration adaptée
{{/if}}

{{#if (eq action "finalize")}}
Finalisation du workflow Heracles.

⚠️ Prérequis: tests et review doivent être passés.

1. Vérifier les conditions de sortie (tests_passed, review_passed)
2. Git add + commit avec message structuré
3. Git push sur la branche feature
4. Créer la Pull Request / Merge Request
5. Archiver la session
{{/if}}
