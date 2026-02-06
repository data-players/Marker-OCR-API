---
name: he-analyze
description: Analyse un projet existant pour adapter Heracles à sa structure
---

Analyse du projet pour adapter Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-analyze/SKILL.md`

## Objectif

Analyser un projet existant pour:
- Détecter sa structure (répertoires sources, tests, docs, specs)
- Identifier le stack technologique
- Comprendre les conventions en place
- Générer une configuration d'adaptation

**Principe**: Heracles s'adapte au projet, **pas l'inverse**.

## Processus

### 1. Scanner la Structure

Chercher les répertoires existants:

| Type | Patterns à chercher |
|------|---------------------|
| Sources | `src/`, `lib/`, `app/`, `packages/`, `cmd/` |
| Tests | `test/`, `tests/`, `__tests__/`, `spec/`, `e2e/` |
| Documentation | `doc/`, `docs/`, `documentation/` |
| Spécifications | `spec/`, `specs/`, `design/`, `rfc/` |

### 2. Détecter le Stack

Analyser les fichiers de configuration:

| Fichier | Stack |
|---------|-------|
| `package.json` | Node.js / JS / TS |
| `tsconfig.json` | TypeScript |
| `requirements.txt` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

### 3. Analyser les Conventions

Détecter:
- **Nommage**: kebab-case, camelCase, PascalCase, snake_case
- **Organisation**: par type, par feature, par domaine
- **Tests**: co-localisés, séparés, miroir

### 4. Générer la Configuration

Créer `.heracles/sessions/{session_id}/PROJECT_ANALYSIS.md` avec:
- Structure détectée
- Stack identifié
- Conventions en place
- Chemins adaptés pour Heracles

### 5. Mettre à jour le Contexte

Dans `WORKFLOW_STATE.md`, ajouter:

```yaml
detected_structure:
  source_dir: "{detected}"
  test_dir: "{detected}"
  doc_dir: "{detected}"
  spec_dir: "{detected}"
stack:
  language: "{detected}"
  framework: "{detected}"
conventions:
  file_naming: "{detected}"
```

## Règles absolues

✅ **TOUJOURS**:
- Scanner TOUS les répertoires avant de conclure
- Respecter la structure existante
- Documenter les conventions détectées

❌ **JAMAIS**:
- Modifier des fichiers existants
- Renommer des répertoires
- Réorganiser le code existant
- Forcer la structure standard

## Sortie

```
✅ Analyse du projet terminée

Type de projet: Existant ({stack})
Structure détectée:
- Sources: {path}
- Tests: {path}
- Documentation: {path}

Conventions identifiées:
- Nommage: {convention}
- Organisation: {pattern}

Configuration générée: PROJECT_ANALYSIS.md

Heracles est maintenant adapté à ce projet.
```
