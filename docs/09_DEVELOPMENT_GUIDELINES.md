# Development Guidelines

> **Document:** 09_DEVELOPMENT_GUIDELINES.md
> **Version:** 0.1.0
> **Status:** Active — Enforced from Phase 0
> **Last Updated:** 2026-07-27
> **Author:** Architecture Team

---

## 1. Purpose

This document establishes the engineering standards, coding conventions, and development practices for the Hybrid GraphRAG Enterprise Knowledge Assistant. All contributors must adhere to these guidelines to ensure consistency, maintainability, and production readiness.

---

## 2. General Rules

| Rule | Description |
|---|---|
| **No hard-coded values** | All configurable values must be loaded from environment variables or configuration files. |
| **No API keys in source code** | Secrets must never appear in source files, commits, or logs. Use `.env` files locally and secret managers in production. |
| **Environment-based configuration** | All configuration is driven by environment variables. See `.env.example` for the complete template. |
| **Clean architecture** | Follow separation of concerns with clearly defined layers. No business logic in controllers; no database access in services. |
| **Reusable components** | Extract common patterns into shared utilities. Avoid code duplication across modules. |
| **Business logic isolation** | Business logic resides exclusively in the service layer, never in API controllers or repository methods. |

---

## 3. Backend Rules (Python / FastAPI)

### 3.1 Language & Typing

- Use **Python 3.11+** for all backend code.
- Use **type hints** on all function signatures (parameters and return types).
- Use **Pydantic** models for all request/response validation.

### 3.2 Architecture Pattern

Follow the **Controller → Service → Repository** pattern:

```
┌──────────────────┐
│  API Controller   │  ← Receives HTTP requests, validates input, returns responses
│  (api/)           │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Service Layer    │  ← Contains all business logic, orchestrates operations
│  (services/)      │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Repository Layer │  ← Data access only — CRUD operations, queries
│  (repositories/)  │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Database         │  ← PostgreSQL, Qdrant, Neo4j, MinIO
└──────────────────┘
```

### 3.3 Core Practices

- **Dependency Injection** — Use FastAPI's `Depends()` for injecting services and repositories.
- **Pydantic Schemas** — Separate schemas for request input, response output, and database models.
- **Exception Handling** — Use custom exception classes. Never expose raw stack traces to API consumers.
- **Async by default** — Use `async def` for all I/O-bound operations.
- **Repository Pattern** — All database access goes through repository classes. Services never call the database directly.

### 3.4 File Organization

```
backend/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── documents.py
│   │   │   ├── search.py
│   │   │   └── auth.py
│   │   └── router.py
│   └── dependencies.py
├── core/
│   ├── config.py          # Settings from environment variables
│   ├── security.py        # JWT, hashing utilities
│   └── exceptions.py      # Custom exception classes
├── models/
│   ├── document.py        # SQLAlchemy models
│   └── user.py
├── schemas/
│   ├── document.py        # Pydantic schemas
│   └── user.py
├── services/
│   ├── document_service.py
│   └── search_service.py
├── repositories/
│   ├── document_repository.py
│   └── user_repository.py
└── utils/
    ├── logger.py
    └── helpers.py
```

---

## 4. Frontend Rules (React / TypeScript)

### 4.1 Language & Configuration

- Use **TypeScript** in **strict mode** (`"strict": true` in `tsconfig.json`).
- No `any` types unless explicitly justified and documented.

### 4.2 Component Design

- **Reusable components** — Build small, composable components in a shared `components/` directory.
- **Feature-based organization** — Group related components, hooks, and utilities by feature.
- **Centralized API services** — All HTTP calls go through a centralized API client layer.

### 4.3 File Organization

```
frontend/src/
├── components/           # Shared, reusable UI components
│   ├── Button/
│   ├── Modal/
│   └── Layout/
├── features/             # Feature-specific modules
│   ├── documents/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api.ts
│   └── search/
├── services/             # Centralized API client
│   └── apiClient.ts
├── hooks/                # Shared custom hooks
├── types/                # Global TypeScript type definitions
├── utils/                # Shared utilities
└── App.tsx
```

---

## 5. Naming Conventions

### 5.1 Python

| Element | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `document_service.py` |
| Classes | `PascalCase` | `DocumentService` |
| Functions | `snake_case` | `get_document_by_id()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE` |
| Private methods | `_leading_underscore` | `_validate_input()` |
| Type variables | `PascalCase` | `DocumentType` |

### 5.2 React / TypeScript

| Element | Convention | Example |
|---|---|---|
| Components | `PascalCase.tsx` | `DocumentViewer.tsx` |
| Hooks | `useSomething.ts` | `useDocuments.ts` |
| Utilities | `camelCase.ts` | `formatDate.ts` |
| Types/Interfaces | `PascalCase` | `DocumentResponse` |
| Constants | `UPPER_SNAKE_CASE` | `API_BASE_URL` |
| CSS Modules | `PascalCase.module.css` | `DocumentViewer.module.css` |

### 5.3 Database

| Element | Convention | Example |
|---|---|---|
| Tables | `snake_case` (plural) | `documents` |
| Columns | `snake_case` | `created_at` |
| Indexes | `ix_{table}_{column}` | `ix_documents_user_id` |
| Foreign keys | `fk_{table}_{ref_table}` | `fk_documents_users` |

---

## 6. Git Conventions

### 6.1 Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `refactor` — Code restructuring without behavior change
- `test` — Adding or updating tests
- `chore` — Build, CI, or tooling changes

**Examples:**
```
feat(backend): add document upload endpoint
fix(ai-pipeline): handle empty document chunks
docs(architecture): update system layer diagram
```

### 6.2 Branch Naming

```
<type>/<short-description>
```

**Examples:**
```
feature/document-upload
bugfix/embedding-null-check
docs/api-specification
```

---

## 7. Documentation Rules

Every new major component must trigger updates to:

| Document | When to Update |
|---|---|
| [01_ARCHITECTURE.md](01_ARCHITECTURE.md) | New layers, services, or major component additions |
| [04_API_DESIGN.md](04_API_DESIGN.md) | New or modified API endpoints |
| [10_DECISION_LOG.md](10_DECISION_LOG.md) | Any significant technical decision |

### 7.1 Code Documentation

- **All public functions** must have docstrings explaining purpose, parameters, and return values.
- **Complex algorithms** must include inline comments explaining the "why," not the "what."
- **Configuration values** must be documented in `.env.example` with clear descriptions.

---

## 8. Testing Standards

| Test Type | Directory | Responsibility |
|---|---|---|
| Unit tests | `tests/unit/` | Test individual functions and methods in isolation |
| Integration tests | `tests/integration/` | Test component interactions with real dependencies |
| End-to-end tests | `tests/e2e/` | Test complete user flows through the full system |

### 8.1 Requirements

- Minimum **80% code coverage** for backend services.
- All API endpoints must have integration tests.
- Tests must be deterministic — no flaky tests allowed.
- Use fixtures and factories for test data, never production data.

---

## 9. Change History

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-27 | 0.1.0 | Initial development guidelines created during Phase 0 Foundation. | Architecture Team |
