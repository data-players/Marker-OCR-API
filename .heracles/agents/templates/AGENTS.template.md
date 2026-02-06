# AGENTS.md - Point d'Entrée du Projet

> **✅ Ce fichier peut être modifié** - Il est spécifique à ce projet.
> L'agent peut ajouter des configurations et références propres au projet ici.

---

## Workflow Heracles

Pour les instructions du workflow, lire : `.heracles/agents/ARBITRAGE.md`

---

## Configuration du Projet

### Fichiers de Référence

| Document | Emplacement | Description |
|----------|-------------|-------------|
| **Architecture** | `spec/architecture.md` | Structure des fichiers, stack technique, normes |
| **Spécifications** | `spec/PRD.md` | Product Requirements Document |
| **Constitution** | `constitution.md` | Principes non-négociables du projet |

### Structure des Fichiers

La structure des fichiers de ce projet est définie dans : **`spec/architecture.md`**

> **Note pour l'agent** : Si le projet utilise une structure différente (projet existant),
> mettre à jour la référence ci-dessus et documenter les chemins dans le fichier approprié.

---

## Notes du Projet

<!-- 
L'agent peut ajouter des notes spécifiques au projet ci-dessous.
Par exemple : particularités, conventions locales, points d'attention, etc.
-->

---

## Fichiers Protégés

⚠️ **Ne JAMAIS modifier les fichiers dans `.heracles/agents/`** - Ce sont les fichiers du framework Heracles.

Les fichiers modifiables sont :
- Ce fichier (`AGENTS.md`)
- `constitution.md`
- `spec/*`
- `src/*`, `test/*`, `doc/*`
- `.heracles/sessions/*`
