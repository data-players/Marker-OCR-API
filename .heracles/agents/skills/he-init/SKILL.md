---
name: he-init
description: Initialise un projet vierge pour Heracles - crée la structure, constitution et architecture
triggers:
  keywords: [init, initialize, initialiser, setup, nouveau projet, new project]
  commands: ["/workflow init", "/he-init"]
  automatic: true  # Appelé automatiquement si projet vierge détecté
capabilities:
  - read_files
  - write_files
  - create_directories
  - execute_commands
  - web_search
constraints:
  - Ne JAMAIS modifier un projet existant (utiliser @he-analyze à la place)
  - Dialoguer avec l'utilisateur pour les choix d'architecture
  - Utiliser les templates fournis
  - Créer une structure cohérente avec le stack choisi
output_format: |
  ## ✅ Projet initialisé
  **Type**: {project_type}
  **Stack**: {tech_stack}
  **Structure**: Créée selon spec/architecture.md
  **Projet maintenant PRÊT pour workflows feature**
---

# Skill: Project Initializer

> Initialisation structurelle des projets vierges (Phase SETUP)

## Description

Ce skill initialise un **projet vierge** pour Heracles en :
- Dialoguant avec l'utilisateur sur l'architecture et le stack
- Créant la constitution du projet
- Créant les spécifications projet (PRD, architecture)
- Créant la structure de répertoires

**Note** : Ce skill ne gère PAS les projets existants. Pour ceux-ci, utiliser `@he-analyze`.

**Note** : Cette action n'a PAS de session. Elle modifie le projet globalement.

## Triggers

Ce skill est appelé quand :
- `/workflow init` - Commande explicite
- `/he-init` - Commande directe
- `/workflow start` quand projet NON PRÊT et projet VIERGE

## Détection de Projet Vierge

Un projet est considéré comme **vierge** si AUCUNE de ces conditions n'est vraie :
- Présence de fichier de dépendances (`package.json`, `requirements.txt`, `go.mod`, etc.)
- Présence de répertoire source (`src/`, `lib/`, `app/`)
- Présence de code significatif

```bash
# Indicateurs d'un projet existant
PROJECT_TYPE="new"
[ -f "package.json" ] || [ -f "requirements.txt" ] || [ -f "go.mod" ] || \
[ -f "Cargo.toml" ] || [ -f "pom.xml" ] || [ -f "composer.json" ] && PROJECT_TYPE="existing"
[ -d "src" ] || [ -d "lib" ] || [ -d "app" ] && PROJECT_TYPE="existing"
```

**Si `PROJECT_TYPE="existing"`** → Redirection vers `@he-analyze`

---

## Processus d'Initialisation

### Étape 1: Dialogue Architecture (Interactif)

**Questions à poser** :

```
🏗️ Configuration du nouveau projet

1. **Type de projet** :
   - [ ] Application Web (frontend + backend)
   - [ ] API / Backend seul
   - [ ] CLI / Outil en ligne de commande
   - [ ] Librairie / Package
   - [ ] Mobile App
   - [ ] Autre: ___

2. **Stack technique** :
   - Langage principal: ___
   - Framework(s): ___
   - Base de données: ___
   - Autres outils: ___

3. **Architecture** :
   - [ ] Monolithe
   - [ ] Microservices
   - [ ] Serverless
   - [ ] Hybride

4. **Contraintes** :
   - Performance: ___
   - Sécurité: ___
   - Compliance: ___

5. **Plateforme Git** :
   - [ ] GitLab
   - [ ] GitHub
   - [ ] Gitea
   - [ ] Aucune
```

**Attendre les réponses** avant de continuer.

### Étape 2: Recherche Best Practices (Web Search)

Utiliser la recherche web pour documenter :

```
Rechercher: "{stack} best practices 2026"
Rechercher: "{framework} project structure recommended"
Rechercher: "{stack} testing strategy"
Rechercher: "{stack} security guidelines"
```

Documenter les résultats pour enrichir l'architecture.

### Étape 3: Créer les Spécifications Projet

Utiliser les templates fournis :

```bash
mkdir -p spec
cp .heracles/agents/templates/PRD.template.md spec/PRD.md
cp .heracles/agents/templates/architecture.template.md spec/architecture.md
```

**Remplir `spec/PRD.md`** avec :
- Vision du projet
- Personas cibles
- Cas d'usage principaux
- Contraintes et exigences

**Remplir `spec/architecture.md`** avec :
- Stack technique détaillé
- Structure des répertoires sources
- Conventions de nommage
- Patterns architecturaux
- Stratégie de test

### Étape 4: Créer Constitution

```bash
cp .heracles/agents/templates/constitution.template.md constitution.md
```

Remplir avec les **règles non négociables** du projet :
- Standards de code
- Règles de sécurité
- Conventions obligatoires
- Garde-fous

### Étape 5: Enrichir AGENTS.md

Mettre à jour le fichier `AGENTS.md` à la racine :

```markdown
## Configuration du Projet

| Document | Emplacement | Description |
|----------|-------------|-------------|
| Architecture | spec/architecture.md | Structure et stack technique |
| Spécifications | spec/PRD.md | Vision et exigences |
| Constitution | constitution.md | Règles non négociables |

## Stack Technique

- **Langage**: {langage}
- **Framework**: {framework}
- **Tests**: {test_framework}
```

### Étape 6: Créer Structure Projet

La structure est définie dans `spec/architecture.md`.
Créer les répertoires selon le stack choisi :

```bash
# Structure de base commune
mkdir -p src test/{unit,integration,e2e} doc spec

# Exemples selon le stack:

# TypeScript/Node.js
mkdir -p src/{components,services,utils,types}

# Python
mkdir -p src/{models,services,utils,api}

# Go
mkdir -p cmd pkg internal
```

### Étape 7: Initialiser Fichiers de Base

Selon le stack, créer les fichiers de configuration :

**TypeScript/Node.js** :
```bash
# package.json, tsconfig.json, etc.
npm init -y
```

**Python** :
```bash
# requirements.txt, pyproject.toml, etc.
touch requirements.txt
```

### Étape 8: Mettre à jour État

```yaml
conditions_met:
  init_complete: true

detected_structure:
  source_dir: "src"
  test_dir: "test"
  test_unit: "test/unit"
  test_integration: "test/integration"
  test_e2e: "test/e2e"
  doc_dir: "doc"
  spec_dir: "spec"
```

---

## Fichiers Créés

| Fichier | Source | Description |
|---------|--------|-------------|
| `AGENTS.md` | Enrichi | Références vers config |
| `constitution.md` | Template | Règles non négociables |
| `spec/PRD.md` | Template | Spécifications produit |
| `spec/architecture.md` | Template | Architecture technique |
| `src/` | Créé | Répertoire sources |
| `test/` | Créé | Répertoires de test |
| `doc/` | Créé | Documentation |

---

## Sortie Succès

```
---
## ✅ Projet initialisé avec succès

**Configuration**:
- Type: {project_type}
- Stack: {tech_stack}
- Architecture: {architecture_type}
- Git Platform: {git_platform}

**Fichiers créés**:
- `constitution.md` ✓
- `spec/PRD.md` ✓
- `spec/architecture.md` ✓
- Structure répertoires ✓

**Prochaine étape**:
Le projet est maintenant **PRÊT** pour les workflows feature.

Démarrer avec: `/workflow start "description de la feature"`
---
```

---

## Sortie si Projet Existant Détecté

```
---
## ⚠️ Projet existant détecté

Ce skill est réservé aux **projets vierges**.

**Détecté**:
- {fichiers_existants}

**Action recommandée**:
Utiliser `@he-analyze` pour analyser et s'adapter au projet existant.

→ Redirection vers `@he-analyze`
---
```

---

## Règles Absolues

### TU DOIS TOUJOURS :
1. Vérifier que le projet est vierge AVANT toute action
2. Dialoguer avec l'utilisateur pour les choix d'architecture
3. Utiliser les templates fournis
4. Créer une structure cohérente avec le stack choisi
5. Documenter les choix dans `spec/architecture.md`
6. Enrichir `AGENTS.md` avec les références

### TU NE DOIS JAMAIS :
1. Initialiser un projet existant (utiliser `@he-analyze`)
2. Créer des fichiers sans dialogue préalable
3. Imposer un stack sans validation utilisateur
4. Modifier des fichiers existants du projet
5. Créer une structure incohérente avec l'architecture choisie
