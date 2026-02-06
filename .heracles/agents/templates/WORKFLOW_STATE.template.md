# Workflow State

> ⚠️ Ce fichier est géré automatiquement par les skills du workflow.
> Ne pas modifier manuellement sauf en cas de debug.

## Session Info

- **session_id**: `{SESSION_ID}`
- **started_at**: `{STARTED_AT}`
- **updated_at**: `{UPDATED_AT}`

## Feature Info

- **feature_id**: `{FEATURE_ID}`
- **feature_description**: {FEATURE_DESCRIPTION}
- **feature_slug**: `{FEATURE_SLUG}`
- **issue_number**: `{ISSUE_NUMBER}`
- **branch_name**: `{BRANCH_NAME}`

## Workflow Progress

- **current_phase**: `{CURRENT_PHASE}`
- **current_step**: `{CURRENT_STEP}`
- **loop_count**: `{LOOP_COUNT}`

## Conditions Met

```yaml
init_complete: false
spec_complete: false
test_scenarios_written: false
implementation_complete: false
code_review_passed: false
browser_tests_passed: false
auto_tests_passed: false
final_review_passed: false
workflow_complete: false
```

## Context Data

```yaml
# Type de projet (détecté par project-analyzer ou défini en init)
project_type: null  # 'new' ou 'existing'

# Structure du projet (chemins adaptés)
detected_structure:
  source_dir: "src"           # Peut être "app", "lib", "packages", etc.
  test_dir: "test"            # Peut être "tests", "__tests__", "spec", etc.
  doc_dir: "doc"              # Peut être "docs", "documentation", etc.
  spec_dir: "spec"            # Peut être "specs", "design", "rfc", etc.
  
  # Sous-répertoires tests (adaptés au stack)
  test_unit: "test/unit"
  test_integration: "test/integration"
  test_e2e: "test/e2e"

# Configuration projet (défini en phase init)
architecture_type: null
tech_stack: []
git_platform: null  # gitlab, gitea, github, none
testing_framework: null

# Conventions détectées (pour projets existants)
conventions:
  file_naming: null           # kebab-case, camelCase, PascalCase, snake_case
  code_style: null            # prettier, standard, etc.
  test_pattern: null          # colocated, separated, mirrored

# Données de session (accumulées)
files_created: []
files_modified: []

# Feedback pour retours en boucle (rempli par test/review)
dev_feedback: null

# Résultats des phases
spec_summary: null
test_results: null
review_results: null
```

## History

| Timestamp | Phase | Action | Result |
|-----------|-------|--------|--------|
| {STARTED_AT} | workflow | created | initialized |

## Notes

<!-- 
Notes de l'agent pour conserver le contexte entre sessions.
Format libre.
-->


