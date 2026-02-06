# ARBITRAGE.md - Règles d'Utilisation de Heracles

> **Compatibilité**: Claude Code | Cursor | Windsurf | VS Code | OpenCode
> **Workflows disponibles**: Heracles

---

## Rôle

Ce fichier détermine si le workflow Heracles doit être utilisé et vérifie l'état d'initialisation du projet.

---

## ⚠️ FICHIER PROTÉGÉ

Ce fichier fait partie du framework Heracles et ne doit **JAMAIS être modifié** par l'agent.
Pour les configurations spécifiques au projet, utiliser le fichier `AGENTS.md` à la racine du projet.

---

## 🔄 Flux de Décision Heracles

```
┌─────────────────────────────────────────────────────────────┐
│                    MESSAGE UTILISATEUR                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 1: VÉRIFIER SESSION ACTIVE                           │
│  Chercher "Heracles Session ID" dans la mémoire             │
│  Si trouvé → Reprendre workflow (sauf demande hors-workflow)│
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 2: ARBITRAGE - HERACLES NÉCESSAIRE ?                 │
│  Analyser l'intention de l'utilisateur                      │
│  Si NON → Répondre directement, FIN                         │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 3: VÉRIFIER ÉTAT DU PROJET                           │
│  Le projet est-il initialisé/analysé ?                      │
│  → Vérifier existence de constitution.md                    │
│  → Vérifier référence architecture dans AGENTS.md           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
        ┌──────────────────┴──────────────────┐
        ▼                                      ▼
┌───────────────────┐                ┌───────────────────┐
│ PROJET NON PRÊT   │                │ PROJET PRÊT       │
│                   │                │                   │
│ → Phase SETUP     │                │ → Workflow FEATURE│
│   (init ou        │                │   (SPEC → DEV →   │
│    analyze)       │                │    TEST → ...)    │
└───────────────────┘                └───────────────────┘
```

---

## 🧠 Gestion de Session par Mémoire de Conversation

### Principe Fondamental

La persistance de l'ID de session repose sur la **mémoire de conversation de l'agent**, pas sur l'environnement système.

### À CHAQUE DÉBUT DE MESSAGE

L'agent DOIT :
1. **Chercher dans sa mémoire** de conversation un "Heracles Session ID"
2. **Si trouvé** → C'est la session active, la reprendre
3. **Si non trouvé** → Pas de session active pour cette conversation

### À CHAQUE FIN DE MESSAGE (si session active)

L'agent DOIT terminer son message par :
```
---
📌 **Information de session persistante (ne pas effacer):**
**Heracles Session ID: {session_id}**
```

---

## Étape 1 : Vérifier Session Active

**Faire confiance UNIQUEMENT à la mémoire de conversation.**

Chercher le pattern : `Heracles Session ID: ...`

**Si session trouvée dans la mémoire :**
- Par défaut → Charger `.heracles/agents/HERACLES.md` et reprendre le workflow
- SAUF si l'utilisateur indique explicitement vouloir faire autre chose

**Si pas de session dans la mémoire :**
- Passer à l'étape 2

---

## Étape 2 : Arbitrage - Heracles Nécessaire ?

### ✅ UTILISER Heracles si :

| Critère | Exemples |
|---------|----------|
| **Nouvelle fonctionnalité** | "ajoute une feature de...", "implémente le système de..." |
| **Issue/ticket important** | "réalise l'issue #42", "travaille sur le ticket..." |
| **Refactoring majeur** | "refactorise le système de...", "migre vers..." |
| **Nouvelle page/composant** | "crée une page de...", "ajoute un nouveau composant..." |
| **Intégration externe** | "intègre l'API de...", "connecte avec..." |
| **Demande explicite** | "/heracles", "/workflow start" |

### ❌ NE PAS utiliser Heracles si :

| Critère | Exemples |
|---------|----------|
| **Question simple** | "comment fonctionne X ?", "explique-moi..." |
| **Correction mineure** | "corrige ce typo", "renomme cette variable" |
| **Debug rapide** | "pourquoi cette erreur ?" |
| **Configuration simple** | "change le port", "modifie cette constante" |
| **Refus explicite** | "sans workflow", "directement", "juste..." |

---

## Étape 3 : Vérifier État du Projet

**AVANT de démarrer un workflow feature**, vérifier si le projet est prêt.

### Comment Détecter si le Projet est Initialisé/Analysé

Un projet est considéré comme **PRÊT** si :

```
constitution.md existe
ET
(
  spec/architecture.md existe
  OU
  AGENTS.md contient une référence vers un fichier d'architecture
)
```

### Commandes de Vérification

```bash
# Vérifier si constitution existe
[ -f "constitution.md" ] && echo "constitution: OK"

# Vérifier si architecture existe (standard ou référencée)
[ -f "spec/architecture.md" ] && echo "architecture: OK"

# Ou vérifier dans AGENTS.md si une référence existe
grep -q "architecture" AGENTS.md && echo "architecture reference: OK"
```

### Comportement selon l'État du Projet

#### CAS A : Projet NON PRÊT (pas initialisé/analysé)

```
🔧 Le projet n'a pas encore été configuré pour Heracles.

Je détecte que c'est [un projet vierge / un projet existant].

Avant de démarrer le workflow, je dois :
- [Projet vierge] → Initialiser le projet (créer constitution, architecture, structure)
- [Projet existant] → Analyser le projet (détecter structure, conventions, stack)

Voulez-vous procéder à [l'initialisation / l'analyse] du projet ?
```

**Attendre confirmation**, puis :
- Projet vierge → Appeler `@he-init`
- Projet existant → Appeler `@he-analyze`

#### CAS B : Projet PRÊT (déjà initialisé/analysé)

```
✅ Projet configuré.

🚀 Démarrage du workflow pour : "{description}"
→ /workflow start "{description}"
```

Passer directement au workflow feature (Phase SPEC).

---

## Étape 4 : Comportement Final

### Session active + demande liée
```
📂 Session Heracles active: {session_id}
→ Reprise du workflow en cours
```

### Session active + demande hors workflow
```
💡 Session Heracles en cours, mais je traite cette demande séparément.
   (Tapez /workflow resume pour reprendre)
```

### Pas de session + Heracles nécessaire + Projet PRÊT
```
🚀 Démarrage du workflow Heracles pour : "{description}"
→ Création de session et démarrage phase SPEC
```

### Pas de session + Heracles nécessaire + Projet NON PRÊT
```
🔧 Configuration du projet requise avant de démarrer.
→ [Initialisation / Analyse] du projet
```

### Pas de session + demande simple
L'agent répond directement sans mentionner Heracles.

---

## Commandes Explicites

| Commande | Action |
|----------|--------|
| `/workflow start "..."` | Démarrer workflow (vérifie projet d'abord) |
| `/workflow resume` | Reprendre workflow actif |
| `/workflow status` | Afficher état actuel |
| `/workflow sessions` | Lister toutes les sessions |
| `/workflow init` | Forcer initialisation projet |
| `/workflow analyze` | Forcer analyse projet existant |
| `/heracles` | Alias intelligent |

---

## Chargement de Heracles

Quand Heracles doit être activé :

```
📂 Chargement du workflow Heracles...
→ Lecture de .heracles/agents/HERACLES.md
```

**IMPORTANT**: Une fois Heracles chargé, l'agent suit **exclusivement** les instructions de `.heracles/agents/HERACLES.md`.

---

## Règles Absolues

1. **Ne JAMAIS lancer un workflow feature** si le projet n'est pas initialisé/analysé
2. **Toujours vérifier l'état du projet** avant de créer une nouvelle session
3. **Ne JAMAIS lancer Heracles sans confirmation** pour une nouvelle session
4. **Toujours reprendre automatiquement** une session active (sauf refus explicite)
5. **Analyser l'intention** avant de proposer Heracles
6. **Respecter le choix** de l'utilisateur
7. **TOUJOURS mentionner l'ID de session** à la fin si session active
8. **Ne JAMAIS modifier ce fichier** ni aucun fichier dans `.heracles/agents/`
