---
name: he-init
description: Initialise un projet vierge pour Heracles - crée structure, constitution et architecture
arguments:
  - name: project_type
    description: Type de projet (optionnel, sera demandé si non fourni)
    required: false
    enum: [webapp, api, cli, library, mobile]
---

Initialisation d'un nouveau projet vierge avec Heracles.

## Instructions pour l'agent

Lire et suivre les instructions de: `.heracles/agents/skills/he-init/SKILL.md`

## Objectif

Créer la structure de base d'un projet vierge :
- Constitution du projet
- Spécifications (PRD, architecture)
- Structure de répertoires adaptée au stack

## Prérequis

- Projet **vierge** (pas de code existant)
- Si projet existant détecté → utiliser `/he-analyzer`

## Processus

1. **Vérifier** que le projet est vierge

2. **Dialoguer** avec l'utilisateur :
   - Type de projet (webapp, API, CLI, lib...)
   - Stack technique (langages, frameworks)
   - Architecture (monolithe, microservices...)
   - Contraintes (performance, sécurité...)
   - Plateforme Git

3. **Rechercher** les best practices du stack choisi

4. **Créer les fichiers** :
   - `constitution.md` (règles non négociables)
   - `spec/PRD.md` (spécifications produit)
   - `spec/architecture.md` (architecture technique)

5. **Créer la structure** selon le stack :
   ```
   src/           # Code source
   test/          # Tests (unit, integration, e2e)
   doc/           # Documentation
   spec/          # Spécifications
   ```

6. **Enrichir AGENTS.md** avec les références

## Résultat

Projet **PRÊT** pour les workflows feature.

Prochaine étape : `/he-workflow start "description"`

{{#if project_type}}
## Configuration suggérée

Type de projet sélectionné: **{{project_type}}**

L'agent va proposer une configuration adaptée à ce type de projet.
{{/if}}
