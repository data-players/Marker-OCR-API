# Architecture et Normes de Développement

> Ce document définit l'architecture technique, les normes de développement et les bonnes pratiques du projet.
> Il est créé lors de la phase INIT et sert de référence tout au long du développement.
>
> **✅ Ce fichier peut être modifié** - Il est spécifique à ce projet.

---

## 📁 Configuration des Chemins du Projet

> **IMPORTANT**: Cette section définit la structure des fichiers utilisée par Heracles.
> Les skills du workflow utilisent ces chemins pour savoir où créer/lire les fichiers.

### Chemins Principaux

```yaml
# Configuration Heracles - Chemins du projet
paths:
  source_dir: "src"              # Répertoire du code source
  test_dir: "test"               # Répertoire des tests
  doc_dir: "doc"                 # Répertoire de documentation
  spec_dir: "spec"               # Répertoire des spécifications projet
  
  # Sous-répertoires de tests
  test_unit: "test/unit"         # Tests unitaires
  test_integration: "test/integration"  # Tests d'intégration
  test_e2e: "test/e2e"           # Tests End-to-End
```

### Arborescence Complète

```
project/
├── AGENTS.md               # Point d'entrée Heracles (modifiable)
├── constitution.md         # Principes du projet
│
├── src/                    # Code source
│   └── {voir section 3.1}
│
├── test/                   # Tests
│   ├── unit/               # Tests unitaires
│   ├── integration/        # Tests d'intégration
│   └── e2e/                # Tests End-to-End
│
├── doc/                    # Documentation
│   └── api/                # Documentation API
│
├── spec/                   # Spécifications projet
│   ├── PRD.md              # Product Requirements Document
│   └── architecture.md     # Ce fichier
│
└── .heracles/              # Framework (LECTURE SEULE)
    ├── sessions/           # Sessions de workflow (modifiable)
    └── agents/             # Framework Heracles (NE PAS MODIFIER)
```

---

## 1. Vue d'Ensemble de l'Architecture

### 1.1 Type d'Architecture
[ex: Monolithique, Microservices, Serverless, Jamstack]

### 1.2 Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        [CLIENT]                              │
│                   (Browser / Mobile)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      [FRONTEND]                              │
│                   (React / Vue / etc.)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST / GraphQL
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       [BACKEND]                              │
│                   (Node.js / Python / etc.)                  │
├─────────────────────────┼───────────────────────────────────┤
│   [Service A]           │           [Service B]              │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      [DATABASE]                              │
│                  (PostgreSQL / MongoDB)                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Décisions Architecturales (ADR)

| # | Décision | Raison | Alternatives Rejetées |
|---|----------|--------|----------------------|
| ADR-001 | [Décision] | [Pourquoi] | [Alternatives] |
| ADR-002 | [Décision] | [Pourquoi] | [Alternatives] |

---

## 2. Stack Technique

### 2.1 Frontend

| Catégorie | Technologie | Version | Usage |
|-----------|-------------|---------|-------|
| Framework | [React/Vue/Svelte] | [x.x] | UI principale |
| Langage | [TypeScript/JavaScript] | [x.x] | Code source |
| Style | [Tailwind/CSS Modules] | [x.x] | Styling |
| État | [Redux/Zustand/Pinia] | [x.x] | State management |
| Routing | [React Router/Vue Router] | [x.x] | Navigation |

### 2.2 Backend

| Catégorie | Technologie | Version | Usage |
|-----------|-------------|---------|-------|
| Runtime | [Node.js/Python/Go] | [x.x] | Exécution |
| Framework | [Express/FastAPI/Gin] | [x.x] | API |
| ORM | [Prisma/SQLAlchemy/GORM] | [x.x] | Base de données |
| Validation | [Zod/Pydantic] | [x.x] | Input validation |

### 2.3 Infrastructure

| Catégorie | Technologie | Usage |
|-----------|-------------|-------|
| Base de données | [PostgreSQL/MongoDB] | Données principales |
| Cache | [Redis] | Cache & sessions |
| File Storage | [S3/MinIO] | Fichiers uploadés |
| Hosting | [Vercel/AWS/Docker] | Déploiement |

### 2.4 Outils de Développement

| Catégorie | Outil | Configuration |
|-----------|-------|---------------|
| Lint | [ESLint/Ruff] | [lien vers config] |
| Format | [Prettier/Black] | [lien vers config] |
| Test | [Vitest/Pytest/Playwright] | [lien vers config] |
| Build | [Vite/Webpack] | [lien vers config] |

---

## 3. Structure des Sources

### 3.1 Structure par Stack Technologique

Choisir la structure adaptée au stack du projet :

#### TypeScript/JavaScript (React/Vue/Next.js)
```
src/
├── components/         # Composants UI réutilisables
├── pages/              # Pages/routes
├── services/           # Logique métier
├── api/                # Endpoints API / clients API
├── hooks/              # Custom hooks (React)
├── utils/              # Fonctions utilitaires
├── types/              # Types TypeScript
└── config/             # Configuration
```

#### Python (Django/FastAPI/Flask)
```
src/
├── api/                # Routes API
├── models/             # Modèles de données
├── services/           # Services métier
├── schemas/            # Schémas Pydantic
├── core/               # Configuration et utilitaires
└── utils/              # Utilitaires
```

#### Go
```
cmd/                    # Points d'entrée
├── server/
│   └── main.go
internal/               # Code privé
├── api/
├── models/
└── services/
pkg/                    # Code partageable
└── utils/
```

#### Rust
```
src/
├── main.rs             # Point d'entrée
├── lib.rs              # Exports
├── api/                # Routes API
├── models/             # Structures de données
├── services/           # Logique métier
└── utils/              # Utilitaires
```

### 3.2 Organisation du Code

#### Par Type (recommandé pour petits projets)
```
src/
├── components/
├── services/
├── utils/
```

#### Par Feature (recommandé pour grands projets)
```
src/
├── features/
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── dashboard/
│   └── settings/
```

#### Par Domaine (Domain-Driven Design)
```
src/
├── domain/
│   ├── user/
│   │   ├── entities/
│   │   ├── repositories/
│   │   └── use-cases/
│   └── order/
├── infrastructure/
└── presentation/
```

---

## 4. Normes de Code

### 4.1 Conventions de Nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| Fichiers composants | PascalCase | `UserProfile.tsx` |
| Fichiers utilitaires | kebab-case | `date-utils.ts` |
| Variables | camelCase | `userName` |
| Constantes | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Types/Interfaces | PascalCase | `UserProfile` |
| Fonctions | camelCase | `getUserById()` |
| Classes | PascalCase | `UserService` |
| Hooks | camelCase avec use | `useAuth()` |

### 4.2 Structure des Fichiers

```typescript
// 1. Imports externes
import React from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Imports internes (ordre: types, utils, components, hooks)
import type { User } from '@/types';
import { formatDate } from '@/utils/date';
import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';

// 3. Types locaux
interface Props {
  userId: string;
}

// 4. Constantes
const DEFAULT_AVATAR = '/images/default-avatar.png';

// 5. Composant/Fonction principale
export function UserProfile({ userId }: Props) {
  // ...
}

// 6. Sous-composants (si nécessaire)
function UserAvatar() {
  // ...
}

// 7. Export par défaut (optionnel)
export default UserProfile;
```

### 4.3 Règles TypeScript

```typescript
// ✅ BON: Types explicites pour les paramètres de fonction
function getUser(id: string): Promise<User> { ... }

// ❌ MAUVAIS: any
function getUser(id: any): any { ... }

// ✅ BON: Interface pour les objets
interface CreateUserInput {
  name: string;
  email: string;
}

// ✅ BON: Type pour les unions/alias
type Status = 'pending' | 'active' | 'inactive';

// ✅ BON: Utiliser unknown au lieu de any pour les données externes
function parseJSON(data: string): unknown { ... }
```

### 4.4 Règles de Formatage

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

## 5. Patterns et Bonnes Pratiques

### 5.1 Gestion des Erreurs

```typescript
// ✅ BON: Erreurs typées et descriptives
class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code: string
  ) {
    super(message);
  }
}

// ✅ BON: Try-catch avec logging
try {
  await createUser(data);
} catch (error) {
  logger.error('Failed to create user', { error, data });
  throw new ApiError('User creation failed', 500, 'USER_CREATE_FAILED');
}
```

### 5.2 Validation des Données

```typescript
// ✅ BON: Validation avec Zod
const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
});

// Valider côté serveur TOUJOURS
const validatedData = createUserSchema.parse(requestBody);
```

### 5.3 Gestion de l'État (Frontend)

```typescript
// ✅ BON: État local pour UI simple
const [isOpen, setIsOpen] = useState(false);

// ✅ BON: État global pour données partagées
const { user } = useUserStore();

// ✅ BON: React Query pour données serveur
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
});
```

### 5.4 Tests

```typescript
// ✅ BON: Test descriptif avec AAA pattern
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a user with valid data', async () => {
      // Arrange
      const input = { name: 'John', email: 'john@example.com' };
      
      // Act
      const user = await userService.createUser(input);
      
      // Assert
      expect(user.id).toBeDefined();
      expect(user.name).toBe('John');
    });
  });
});
```

---

## 6. Sécurité

### 6.1 Règles Non-Négociables

- [ ] **Jamais** de secrets dans le code source
- [ ] **Toujours** valider les inputs côté serveur
- [ ] **Toujours** utiliser des requêtes paramétrées (SQL)
- [ ] **Toujours** échapper les outputs (XSS)
- [ ] **Toujours** vérifier les autorisations

### 6.2 Authentification

```typescript
// ✅ BON: Middleware d'authentification
async function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  try {
    const payload = await verifyToken(token);
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid token' });
  }
}
```

### 6.3 Variables d'Environnement

```bash
# .env.example (à versionner)
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET=your-secret-here
API_KEY=your-api-key

# NE JAMAIS versionner .env
```

---

## 7. Performance

### 7.1 Cibles

| Métrique | Cible | Critique |
|----------|-------|----------|
| Time to First Byte (TTFB) | < 200ms | < 500ms |
| First Contentful Paint (FCP) | < 1.8s | < 3s |
| Largest Contentful Paint (LCP) | < 2.5s | < 4s |
| API Response Time (p95) | < 500ms | < 1s |

### 7.2 Optimisations

```typescript
// ✅ BON: Lazy loading des composants
const Dashboard = lazy(() => import('@/pages/Dashboard'));

// ✅ BON: Memoization
const MemoizedComponent = memo(ExpensiveComponent);

// ✅ BON: Pagination
const users = await db.user.findMany({
  take: 20,
  skip: (page - 1) * 20,
});
```

---

## 8. Git Workflow

### 8.1 Branches

| Branch | Usage | Protection |
|--------|-------|------------|
| `main` | Production stable | Protégée, PR required |
| `develop` | Intégration (optionnel) | Protégée |
| `feature/XXX-desc` | Nouvelles features | - |
| `fix/XXX-desc` | Corrections | - |
| `hotfix/XXX-desc` | Urgences production | - |

### 8.2 Commits

Format: `type(scope): description`

```bash
# Types
feat:     Nouvelle fonctionnalité
fix:      Correction de bug
docs:     Documentation
style:    Formatage (pas de changement de code)
refactor: Refactoring
test:     Ajout/modification de tests
chore:    Maintenance (dépendances, scripts)

# Exemples
feat(auth): add password reset functionality
fix(api): handle null response from external service
docs(readme): update installation instructions
```

### 8.3 Pull Requests

Checklist avant merge :
- [ ] Code review approuvée
- [ ] Tous les tests passent
- [ ] Pas de conflits
- [ ] Documentation mise à jour

---

## 9. Commandes Utiles

```bash
# Développement
npm run dev          # Démarrer serveur dev
npm run build        # Build production
npm run lint         # Vérifier linting
npm run format       # Formater le code

# Tests
npm run test         # Tous les tests
npm run test:unit    # Tests unitaires
npm run test:e2e     # Tests E2E
npm run test:cov     # Couverture

# Base de données
npm run db:migrate   # Appliquer migrations
npm run db:seed      # Seed données
npm run db:studio    # Interface DB
```

---

## 10. Références

- [Documentation du framework]
- [Guide de style interne]
- [Documentation API]

---

> **Dernière mise à jour**: [Date]
> **Version**: 1.0.0
