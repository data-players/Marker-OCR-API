---
name: he-analyze
description: Analyse un projet existant pour détecter sa structure, ses conventions et s'y adapter sans le déformer
triggers:
  keywords: [analyze, analyse, detect, adapt, project-structure]
  commands: ["/workflow analyze"]
  automatic: true  # Appelé automatiquement si projet existant non analysé
capabilities:
  - read_files
  - list_directories
  - search_code
constraints:
  - Ne JAMAIS modifier la structure existante du projet
  - S'adapter aux conventions détectées, pas l'inverse
  - Créer les fichiers manquants (constitution, architecture) sans modifier l'existant
output_format: |
  ## ✅ Analyse du projet terminée
  **Type de projet**: {detected_type}
  **Stack**: {detected_stack}
  **Structure**: {structure_type}
  **Projet maintenant PRÊT pour workflows feature**
---

# Skill: Project Analyzer

> Analyse et adaptation aux projets existants (Phase SETUP)

## Description

Ce skill analyse un projet existant pour :
- Détecter sa structure actuelle (répertoires sources, tests, docs, specs)
- Identifier le stack technologique (langage, frameworks, outils)
- Comprendre les conventions en place (nommage, organisation)
- Créer `constitution.md` et `spec/architecture.md` adaptés au projet

**Principe fondamental** : Heracles s'adapte au projet, pas l'inverse.

**Note** : Ce skill fait partie de la phase SETUP (pas de session).

## Triggers

Ce skill est appelé quand :
- `/workflow analyze` - Commande explicite
- `/workflow start` quand projet NON PRÊT et projet EXISTANT
- Projet existant détecté et pas encore analysé

## Détection de Projet Non-Vierge

Un projet est considéré comme **non-vierge** si l'une de ces conditions est vraie :
- Présence d'un fichier de dépendances (`package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, etc.)
- Présence d'un répertoire source avec du code (`src/`, `lib/`, `app/`, etc.)
- Plus de 5 fichiers dans le répertoire racine (hors `.git`, `.heracles`)

---

## Processus d'Analyse

### Étape 1: Scanner la Structure

**Répertoires à chercher** (par ordre de priorité) :

#### Sources
| Pattern | Stack probable |
|---------|----------------|
| `src/` | Standard (JS/TS, Rust, Go, Java) |
| `lib/` | Ruby, Python, bibliothèques |
| `app/` | Rails, Laravel, Next.js |
| `packages/` | Monorepo |
| `cmd/`, `internal/`, `pkg/` | Go |
| `sources/` | Français/autre |

#### Tests
| Pattern | Framework probable |
|---------|-------------------|
| `test/` | Standard |
| `tests/` | Python, PHP |
| `spec/` | RSpec (Ruby) |
| `__tests__/` | Jest |
| `e2e/` | Tests E2E |
| `cypress/` | Cypress |
| `playwright/` | Playwright |

#### Documentation
| Pattern | Type |
|---------|------|
| `doc/` | Standard |
| `docs/` | GitHub Pages, standard |
| `documentation/` | Verbose |

#### Spécifications
| Pattern | Type |
|---------|------|
| `spec/` | Spécifications (si pas RSpec) |
| `specs/` | Spécifications |
| `design/` | Design docs |
| `rfc/` | RFC style |

**Script de détection** :

```bash
#!/bin/bash
# Détecter les répertoires existants

# Sources
for dir in src lib app packages cmd sources; do
  [ -d "$dir" ] && echo "SOURCE_DIR=$dir" && break
done

# Tests
for dir in test tests spec __tests__ e2e cypress playwright; do
  [ -d "$dir" ] && echo "TEST_DIR=$dir" && break
done

# Documentation
for dir in doc docs documentation; do
  [ -d "$dir" ] && echo "DOC_DIR=$dir" && break
done
```

---

### Étape 2: Détecter le Stack Technologique

#### Fichiers de Configuration

| Fichier | Stack |
|---------|-------|
| `package.json` | Node.js / JavaScript / TypeScript |
| `tsconfig.json` | TypeScript |
| `requirements.txt` / `pyproject.toml` / `setup.py` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` / `build.gradle` | Java |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `.csproj` / `*.sln` | C# / .NET |

#### Frameworks Frontend

| Indicateur | Framework |
|------------|-----------|
| `next.config.js` | Next.js |
| `nuxt.config.js` | Nuxt.js |
| `svelte.config.js` | SvelteKit |
| `angular.json` | Angular |
| `vite.config.ts` avec `@vitejs/plugin-react` | React + Vite |
| `vue.config.js` | Vue CLI |

#### Frameworks Backend

| Indicateur | Framework |
|------------|-----------|
| `nest-cli.json` | NestJS |
| `manage.py` | Django |
| `app.py` + `Flask` import | Flask |
| `main.go` + `gin` import | Gin (Go) |
| `Gemfile` + `rails` | Ruby on Rails |

---

### Étape 3: Analyser les Conventions

#### Nommage des Fichiers

Analyser un échantillon de fichiers pour détecter :
- `kebab-case` : `my-component.ts`
- `camelCase` : `myComponent.ts`
- `PascalCase` : `MyComponent.ts`
- `snake_case` : `my_component.py`

#### Structure de Composants

Détecter le pattern d'organisation :
- **Par type** : `components/`, `services/`, `utils/`
- **Par feature** : `features/auth/`, `features/dashboard/`
- **Par domaine** : `domain/user/`, `domain/order/`

#### Tests

Identifier la convention de tests :
- **Co-localisés** : `Component.tsx` + `Component.test.tsx`
- **Répertoire séparé** : `src/` + `test/`
- **Mirrored** : `src/services/auth.ts` → `test/services/auth.test.ts`

---

### Étape 4: Générer la Configuration

Créer `.heracles/sessions/{session_id}/PROJECT_ANALYSIS.md` :

```markdown
# Analyse du Projet

> Généré automatiquement par project-analyzer
> Date: {date}

## Structure Détectée

### Répertoires Principaux

| Type | Chemin | Détecté par |
|------|--------|-------------|
| Sources | `{path}` | {méthode} |
| Tests | `{path}` | {méthode} |
| Documentation | `{path}` | {méthode} |
| Spécifications | `{path}` | {méthode} |

### Répertoires Manquants

Les répertoires suivants n'existent pas et seront créés si nécessaire :
- [ ] `{path}` - {description}

## Stack Technologique

### Langages
- **Principal**: {langage}
- **Secondaires**: {liste}

### Frameworks
- **Frontend**: {framework} (v{version})
- **Backend**: {framework} (v{version})
- **Test**: {framework}

### Outils
- **Build**: {outil}
- **Lint**: {outil}
- **Format**: {outil}

## Conventions Détectées

### Nommage
- **Fichiers**: {convention}
- **Variables**: {convention}
- **Classes/Types**: {convention}

### Organisation
- **Pattern**: {pattern} (par type/feature/domaine)
- **Tests**: {pattern} (co-localisés/séparés/miroir)

### Exemples de Structure
```
{structure détectée}
```

## Configuration Heracles

### Chemins Adaptés

```yaml
# Configuration générée pour ce projet
paths:
  source: "{detected_source_dir}"
  test: "{detected_test_dir}"
  doc: "{detected_doc_dir}"
  spec: "{detected_spec_dir}"
  
  # Sous-répertoires tests (adaptés au stack)
  test_unit: "{detected_test_dir}/unit"
  test_integration: "{detected_test_dir}/integration"
  test_e2e: "{detected_test_dir}/e2e"
```

### Commandes Adaptées

```yaml
commands:
  build: "{detected_build_command}"
  test: "{detected_test_command}"
  lint: "{detected_lint_command}"
  format: "{detected_format_command}"
```

## Recommandations

### À Créer
- [ ] {fichier/répertoire à créer}

### À Conserver
- {ce qui doit rester intact}

### Attention
- {points de vigilance}
```

---

### Étape 5: Mettre à jour le Contexte

Ajouter au `WORKFLOW_STATE.md` :

```yaml
## Context Data

```yaml
# Configuration projet (détectée par project-analyzer)
project_type: existing  # ou 'new'
detected_structure:
  source_dir: "src"
  test_dir: "tests"
  doc_dir: "docs"
  spec_dir: "spec"
stack:
  language: "typescript"
  framework: "react"
  test_framework: "vitest"
conventions:
  file_naming: "kebab-case"
  code_style: "prettier"
```

---

## Cas Particuliers

### Monorepo

Si détecté (`packages/`, `apps/`, `workspace` dans package.json) :
1. Identifier les packages
2. Demander sur quel package travailler
3. Adapter les chemins au package sélectionné

### Projet Sans Structure Claire

Si aucune structure standard n'est détectée :
1. Lister les fichiers existants
2. Proposer une réorganisation (optionnelle)
3. S'adapter à la structure actuelle quoi qu'il en soit

### Projet Vierge

Si le projet est vierge, ne pas exécuter l'analyse et laisser l'orchestrateur créer la structure standard.

---

## Finalisation : Rendre le Projet PRÊT

Après l'analyse, ce skill doit créer les fichiers manquants pour que le projet soit **PRÊT**.

### Étape Finale : Créer les Fichiers Manquants

1. **Si `constitution.md` n'existe pas** :
   - Copier `.heracles/agents/templates/constitution.template.md` vers `constitution.md`
   - Remplir avec les informations détectées (stack, conventions)
   - Adapter les sections au projet existant

2. **Si `spec/architecture.md` n'existe pas** :
   - Créer `spec/` si le répertoire n'existe pas
   - Copier `.heracles/agents/templates/architecture.template.md` vers `spec/architecture.md`
   - Remplir avec la structure détectée et les conventions
   - **Documenter les chemins réels** utilisés par le projet

3. **Si `spec/PRD.md` n'existe pas** :
   - Copier `.heracles/agents/templates/PRD.template.md` vers `spec/PRD.md`
   - Laisser comme template à compléter

4. **Enrichir `AGENTS.md`** avec les références :
   ```markdown
   ## Configuration Projet
   
   - Constitution: [constitution.md](constitution.md)
   - Architecture: [spec/architecture.md](spec/architecture.md)
   - PRD: [spec/PRD.md](spec/PRD.md)
   
   ## Structure Détectée
   
   - Sources: `{source_dir}`
   - Tests: `{test_dir}`
   - Documentation: `{doc_dir}`
   ```

---

## Communication avec l'Orchestrateur

### Succès (Projet Existant Analysé)

```
---
## ✅ Analyse du projet terminée - Projet PRÊT

**Type de projet**: Existant ({stack détecté})

**Structure détectée**:
- Sources: `{path}`
- Tests: `{path}`
- Documentation: `{path}`
- Specs: `{path}`

**Conventions identifiées**:
- Nommage fichiers: {convention}
- Organisation: {pattern}

**Fichiers créés**:
- ✅ `constitution.md` (basé sur analyse)
- ✅ `spec/architecture.md` (structure documentée)
- ✅ `spec/PRD.md` (template)

**Le projet est maintenant PRÊT pour les workflows feature.**

→ L'orchestrateur peut démarrer `/workflow start "..."`
---
```

### Projet Vierge (Redirection)

```
---
## ℹ️ Projet vierge détecté

Aucune structure de projet existante trouvée.
Ce skill ne s'applique pas aux projets vierges.

→ Redirection vers `@he-init`
---
```

---

## Règles Absolues

### TU DOIS TOUJOURS :
1. Scanner TOUS les répertoires avant de conclure
2. Respecter la structure existante
3. Documenter les conventions détectées
4. Créer `constitution.md` et `spec/architecture.md` si absents
5. Enrichir `AGENTS.md` avec les références du projet

### TU NE DOIS JAMAIS :
1. Modifier des fichiers de CODE existants
2. Renommer des répertoires existants
3. Réorganiser le code existant
4. Ignorer les conventions en place
5. Forcer la structure standard sur un projet existant
