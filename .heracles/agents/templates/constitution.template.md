# Constitution du Projet

> Ce document définit les principes fondamentaux et non-négociables du projet.
> Il est créé lors de la phase INIT et ne doit plus changer.
> 
> **Documents de référence** :
> - Spécifications fonctionnelles : `spec/PRD.md`
> - Architecture et normes : `spec/architecture.md`

## 1. Vision

### 1.1 Objectif du Projet
[Décrivez l'objectif principal du projet - détails dans spec/PRD.md]

### 1.2 Public Cible
[Qui sont les utilisateurs finaux ? - détails dans spec/PRD.md]

### 1.3 Valeur Apportée
[Quelle valeur le projet apporte-t-il ?]

---

## 2. Stack Technique

> Détails complets dans `spec/architecture.md`

### 2.1 Langages
- **Principal**: [ex: TypeScript]
- **Secondaires**: [ex: SQL, Bash]

### 2.2 Frameworks
- **Frontend**: [ex: React, Vue, Svelte]
- **Backend**: [ex: Node.js, Python, Go]
- **Base de données**: [ex: PostgreSQL, MongoDB]

### 2.3 Outils
- **Build**: [ex: Vite, Webpack]
- **Test**: [ex: Vitest, Playwright]
- **Lint**: [ex: ESLint, Prettier]

---

## 3. Structure du Projet

### 3.1 Répertoires Principaux

```
project/
├── src/           # Code source
├── test/          # Tests (unit/, integration/, e2e/)
├── doc/           # Documentation
└── spec/          # Spécifications
    ├── PRD.md           # Product Requirements Document
    └── architecture.md  # Architecture et normes
```

### 3.2 Structure des Sources
> Adaptée selon le stack - détails dans `spec/architecture.md`

```
src/
├── components/    # Composants UI réutilisables
├── pages/         # Pages/routes
├── services/      # Logique métier
├── api/           # Endpoints API
├── models/        # Modèles de données
├── utils/         # Utilitaires
└── types/         # Types TypeScript
```

### 3.3 Conventions de Nommage
- **Fichiers**: kebab-case pour fichiers, PascalCase pour composants
- **Variables**: camelCase
- **Constantes**: SCREAMING_SNAKE_CASE
- **Types/Interfaces**: PascalCase avec prefix I pour interfaces (optionnel)

---

## 4. Standards de Qualité

### 4.1 Code Style
- Formatage: [Prettier avec config standard]
- Linting: [ESLint avec règles strictes]
- Pas de `any` en TypeScript sauf justification documentée
- Pas de `console.log` en production

### 4.2 Tests

```
test/
├── unit/          # Tests unitaires
├── integration/   # Tests d'intégration
└── e2e/           # Tests End-to-End
```

- Couverture minimale: **80%** lignes
- Tests unitaires pour toute logique métier (`test/unit/`)
- Tests d'intégration pour tous les endpoints API (`test/integration/`)
- Tests E2E pour les parcours critiques (`test/e2e/`)

### 4.3 Documentation
- JSDoc/docstrings pour fonctions publiques
- README à jour
- Commentaires pour logique non évidente

---

## 5. Sécurité

### 5.1 Règles Non-Négociables
- [ ] Jamais de secrets dans le code
- [ ] Validation de tous les inputs côté serveur
- [ ] Authentification sur toutes les routes protégées
- [ ] Échappement de tous les outputs (XSS)
- [ ] Queries paramétrées (SQL injection)

### 5.2 Dépendances
- Audit régulier (`npm audit`)
- Pas de dépendances avec vulnérabilités critiques
- Mises à jour régulières

---

## 6. Performance

### 6.1 Cibles
- Time to First Byte: < 200ms
- Largest Contentful Paint: < 2.5s
- API Response Time: < 500ms (p95)

### 6.2 Pratiques
- Lazy loading pour les composants lourds
- Pagination pour les listes
- Caching approprié
- Pas de N+1 queries

---

## 7. Git Workflow

### 7.1 Branches
- `main`: Production stable
- `develop`: Intégration (optionnel)
- `feature/XXX-description`: Features
- `fix/XXX-description`: Corrections

### 7.2 Commits
Format: `type(scope): description`

Types:
- `feat`: Nouvelle feature
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Maintenance

### 7.3 Pull Requests
- Titre descriptif
- Description des changements
- Tests passants
- Review requise

---

## 8. Environnements

### 8.1 Development
- URL: `http://localhost:3000`
- Base de données locale

### 8.2 Staging
- URL: [À définir]
- Base de données de test

### 8.3 Production
- URL: [À définir]
- Base de données de production

---

## 9. Limites et Contraintes

### 9.1 Hors Scope
[Ce que le projet NE fait PAS]

### 9.2 Dépendances Externes
[Services ou APIs dont le projet dépend]

### 9.3 Contraintes Techniques
[Limitations connues]

---

## 10. Contacts et Ressources

### 10.1 Équipe
- **Lead**: [Nom]
- **Développeurs**: [Noms]

### 10.2 Documentation
- [Lien vers docs supplémentaires]
- [Lien vers maquettes]
- [Lien vers API docs]

---

> **Dernière mise à jour**: [Date]
> **Version**: 1.0.0


