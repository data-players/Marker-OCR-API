---
name: he-workflow
description: Gère l'état du workflow, les transitions entre phases et les actions système (start, init, finalize)
triggers:
  keywords: [workflow, start, resume, status, sessions, init, finalize]
  phases: [init, finalize]
  commands: ["/workflow start", "/workflow resume", "/workflow status", "/workflow sessions"]
capabilities:
  - read_files
  - write_files
  - execute_commands
  - manage_sessions
constraints:
  - Ne jamais faire le travail des autres skills
  - Toujours mettre à jour WORKFLOW_STATE.md après chaque action
  - Respecter les conditions de sortie avant transition
---

# Skill: Orchestrator

> Gère l'état du workflow, les transitions et les actions système

## Description

Ce skill est le **cerveau du workflow**. Il gère :
- Création et gestion des sessions dans `.heracles/sessions/`
- Création/lecture/mise à jour de l'état de session
- Transitions entre phases
- Actions de finalisation (commit, PR)
- Gestion des conditions de sortie

## ⚠️ Fichiers Protégés

**NE JAMAIS modifier** les fichiers dans `.heracles/agents/` - ce sont les fichiers du framework.

**Fichiers MODIFIABLES** :
- `AGENTS.md` - Point d'entrée du projet (peut être enrichi)
- `constitution.md`, `spec/*` - Configuration du projet
- `src/*`, `test/*`, `doc/*` - Code du projet
- `.heracles/sessions/*` - États des workflows

## Templates Disponibles

Les templates sont dans `.heracles/agents/templates/` :
- `WORKFLOW_STATE.template.md` - État de session
- `constitution.template.md` - Constitution du projet
- `PRD.template.md` - Spécifications fonctionnelles
- `architecture.template.md` - Architecture et normes
- `AGENTS.template.md` - Point d'entrée enrichi

## Triggers

Ce skill est appelé quand :
- `/workflow start` - Vérifier projet + créer session + démarrer
- `/workflow resume` - Reprendre session active
- `/workflow status` - Afficher l'état
- `/workflow sessions` - Lister les sessions
- `/workflow switch <id>` - Changer de session
- `/workflow goto <phase>` - Aller à une phase
- `/workflow init` - Forcer initialisation projet vierge
- `/workflow analyze` - Forcer analyse projet existant
- `action=init` - Initialisation du projet (Setup)
- `action=finalize` - Finalisation (Phase finale workflow)

---

## Actions

### ACTION: start

**Objectif**: Vérifier l'état du projet, puis créer une session et démarrer le workflow

**⚠️ IMPORTANT**: Avant de créer une session, vérifier que le projet est PRÊT.

**Étapes**:

1. **Vérifier si le projet est prêt**
   ```bash
   # Le projet est prêt si ces fichiers existent
   PROJECT_READY="false"
   
   if [ -f "constitution.md" ]; then
     if [ -f "spec/architecture.md" ] || grep -q "architecture" AGENTS.md 2>/dev/null; then
       PROJECT_READY="true"
     fi
   fi
   
   echo "Projet prêt: ${PROJECT_READY}"
   ```
   
   **Si projet NON prêt** :
   - Détecter si projet vierge ou existant
   - Appeler `@he-init` (vierge) ou `@he-analyze` (existant)
   - Puis revenir à `ACTION: start`

2. **Vérifier sessions existantes**
   ```bash
   # Lister les sessions existantes
   bash .heracles/agents/scripts/workflow-helper.sh sessions
   ```

3. **Créer la session** (uniquement si projet PRÊT)
   ```bash
   # Utiliser le helper script
   bash .heracles/agents/scripts/workflow-helper.sh start "${FEATURE_DESCRIPTION}"
   
   # Ou manuellement:
   SESSION_ID="$(date +%Y%m%d-%H%M%S)-${FEATURE_SLUG}"
   mkdir -p ".heracles/sessions/${SESSION_ID}/specs"
   mkdir -p ".heracles/sessions/${SESSION_ID}/review-reports"
   mkdir -p ".heracles/sessions/${SESSION_ID}/logs"
   
   # Copier le template
   cp .heracles/agents/templates/WORKFLOW_STATE.template.md \
      ".heracles/sessions/${SESSION_ID}/WORKFLOW_STATE.md"
   ```

4. **Remplir l'état initial**
   - `session_id: {SESSION_ID}`
   - `feature_id: {auto-increment}`
   - `feature_description: {description}`
   - `current_phase: spec` ← Toujours SPEC (le projet est déjà prêt)
   - `started_at: {timestamp}`

5. **Créer issue Git** (si configuré)
   ```bash
   bash .heracles/agents/scripts/create-issue.sh "Feature: ${FEATURE_DESCRIPTION}"
   ```

6. **Créer branche Git**
   ```bash
   FEATURE_NUM=$(read_state_value 'feature_id')
   git checkout -b "feature/${FEATURE_NUM}-${FEATURE_SLUG}"
   ```

7. **Confirmer le démarrage**
   ```
   ✅ Projet configuré.
   
   📂 Session créée: {SESSION_ID}
   🎯 Feature: {description}
   
   → Démarrage Phase SPEC
   ```

---

### ACTION: finalize

**Objectif**: Finalisation du workflow (Phase 5)

**Prérequis**: 
- `tests_passed: true`
- `review_passed: true`

**Étapes**:

1. **Vérifier prérequis**
   ```bash
   # Lire WORKFLOW_STATE.md et vérifier conditions
   if ! grep -q "tests_passed: true" WORKFLOW_STATE.md; then
     echo "ERROR: Tests not passed"
     exit 1
   fi
   if ! grep -q "review_passed: true" WORKFLOW_STATE.md; then
     echo "ERROR: Review not passed"
     exit 1
   fi
   ```

2. **Git Add**
   ```bash
   git add .
   ```

3. **Git Commit**
   ```bash
   FEATURE_ID=$(grep "feature_id:" WORKFLOW_STATE.md | cut -d':' -f2 | tr -d ' ')
   FEATURE_DESC=$(grep "feature_description:" WORKFLOW_STATE.md | cut -d':' -f2-)
   
   git commit -m "feat(${FEATURE_ID}): ${FEATURE_DESC}
   
   - Implemented according to specification
   - All tests passing
   - Code review passed
   
   Closes #${ISSUE_NUM}"
   ```

4. **Git Push**
   ```bash
   BRANCH=$(git branch --show-current)
   git push origin ${BRANCH}
   ```

5. **Créer PR/MR**
   ```bash
   bash scripts/create-pr.sh
   ```

6. **Marquer le workflow comme terminé**
   ```markdown
   conditions_met:
     workflow_complete: true
   current_phase: complete
   completed_at: [timestamp]
   ```

7. **Archiver la session**
   ```bash
   SESSION_ID=$(cat .heracles/current_session)
   
   # Déplacer vers archives
   mkdir -p .heracles/sessions/archived
   mv ".heracles/sessions/${SESSION_ID}" ".heracles/sessions/archived/${SESSION_ID}"
   
   # Supprimer le lien de session active
   rm -f .heracles/current_session
   ```

8. **Nettoyer les fichiers temporaires** (dans la session archivée)
   ```bash
   ARCHIVE_DIR=".heracles/sessions/archived/${SESSION_ID}"
   
   # Supprimer logs temporaires si trop volumineux
   find "${ARCHIVE_DIR}/logs" -name "*.tmp" -delete 2>/dev/null || true
   
   # Garder seulement les fichiers importants:
   # - WORKFLOW_STATE.md (état final)
   # - specs/ (spécifications)
   # - review-reports/ (rapports de review)
   ```

---

### ACTION: status

**Objectif**: Afficher l'état actuel du workflow

**Output**:
```markdown
## 📊 Workflow Status

**Session**: {session_id}
**Feature**: {feature_id} - {feature_description}
**Phase actuelle**: {current_phase}
**Étape**: {current_step}

### ✅ Conditions validées
- [x] init_complete
- [x] spec_complete
- [ ] implementation_complete
- [ ] tests_passed
- [ ] review_passed

### 📁 Fichiers créés
- constitution.md
- specs/001-feature/specification.md
- specs/001-feature/plan.md

### 🕐 Timeline
- Started: {started_at}
- Last update: {updated_at}
```

---

### ACTION: goto

**Objectif**: Forcer le passage à une phase spécifique

**Usage**: `/workflow goto <phase>`

**Phases valides**: `init`, `spec`, `dev`, `test`, `review`, `finalize`

**Comportement**:
1. Vérifier que la phase est valide
2. Avertir si des conditions ne sont pas remplies
3. Demander confirmation
4. Mettre à jour `current_phase` dans l'état

---

## Template: WORKFLOW_STATE.md

Quand tu crées `WORKFLOW_STATE.md`, utilise ce format exact :

```markdown
# Workflow State

> ⚠️ Ce fichier est géré automatiquement par les skills du workflow.
> Ne pas modifier manuellement.

## Session Info
- **session_id**: {uuid}
- **started_at**: {ISO timestamp}
- **updated_at**: {ISO timestamp}

## Feature Info
- **feature_id**: {XXX}
- **feature_description**: {description}
- **feature_slug**: {kebab-case}
- **issue_number**: {num or null}
- **branch_name**: {branch}

## Workflow Progress
- **current_phase**: {phase}
- **current_step**: {step}
- **loop_count**: {num}

## Conditions Met
```yaml
init_complete: false
spec_complete: false
implementation_complete: false
tests_passed: false
review_passed: false
workflow_complete: false
```

## Context Data
```yaml
# Données passées entre skills
architecture_type: null
tech_stack: []
git_platform: null
```

## History
| Timestamp | Phase | Action | Result |
|-----------|-------|--------|--------|
| {ts} | init | started | success |

## Notes
<!-- Notes de l'agent pour le contexte -->
```

---

## Mise à jour de l'État

Quand tu mets à jour `WORKFLOW_STATE.md`, tu DOIS :

1. **Lire le fichier complet** d'abord
2. **Modifier UNIQUEMENT** les champs pertinents
3. **Mettre à jour** `updated_at`
4. **Ajouter** une entrée dans History
5. **Conserver** tout le reste intact

Exemple de mise à jour :
```markdown
## Workflow Progress
- **current_phase**: dev  <!-- Changé de 'spec' -->
- **current_step**: implement
- **loop_count**: 0

## Conditions Met
```yaml
init_complete: true
spec_complete: true  <!-- Changé de false -->
implementation_complete: false
```

## History
| Timestamp | Phase | Action | Result |
|-----------|-------|--------|--------|
| 2026-01-23T10:00:00Z | init | started | success |
| 2026-01-23T10:15:00Z | init | completed | success |
| 2026-01-23T10:16:00Z | spec | started | success |
| 2026-01-23T11:00:00Z | spec | completed | success |  <!-- Ajouté -->
```

---

## Logique de Transition

```python
def determine_next_phase(current_state):
    phase = current_state.current_phase
    conditions = current_state.conditions_met
    feedback = current_state.context.get('dev_feedback', {})
    
    if phase == "init":
        if conditions.init_complete:
            return "spec"
        return "init"  # Continue init
    
    if phase == "spec":
        if conditions.spec_complete:
            return "test-spec"  # Écrire scénarios AVANT dev
        return "spec"  # Continue spec
    
    if phase == "test-spec":
        if conditions.test_scenarios_written:
            return "dev"
        return "test-spec"  # Continue writing scenarios
    
    if phase == "dev":
        if conditions.implementation_complete:
            return "review-code"  # Review intermédiaire
        return "dev"  # Continue dev
    
    if phase == "review-code":
        if conditions.code_review_passed:
            return "test-browser"
        return "dev"  # Loop back to fix code
    
    if phase == "test-browser":
        if conditions.browser_tests_passed:
            return "test-auto"
        # Check if scenarios need fixing
        if feedback.get('source') == 'browser_test' and feedback.get('fix_scenarios'):
            return "test-spec"  # Fix scenarios
        return "dev"  # Fix implementation
    
    if phase == "test-auto":
        if conditions.auto_tests_passed:
            return "review-final"
        # Check if it's a test code issue vs implementation issue
        if feedback.get('source') == 'test' and feedback.get('fix_tests'):
            return "test-auto"  # Fix test code
        return "dev"  # Fix implementation
    
    if phase == "review-final":
        if conditions.final_review_passed:
            return "finalize"
        # Determine where to loop back
        if feedback.get('fix_tests'):
            return "test-auto"
        return "dev"  # Fix implementation
    
    if phase == "finalize":
        if conditions.workflow_complete:
            return "complete"
        return "finalize"
    
    return "error"
```

---

## Fichiers de Sortie

Ce skill crée/modifie :

| Fichier | Action | Quand |
|---------|--------|-------|
| `.heracles/sessions/{id}/WORKFLOW_STATE.md` | Create/Update | start, toutes actions |
| `AGENTS.md` | Update | init (enrichir avec références) |
| `constitution.md` | Create | init (depuis template) |
| `spec/PRD.md` | Create | init (depuis template) |
| `spec/architecture.md` | Create | init (depuis template, contient la structure) |
| `src/`, `test/`, `doc/`, `spec/` | Create dirs | init |


