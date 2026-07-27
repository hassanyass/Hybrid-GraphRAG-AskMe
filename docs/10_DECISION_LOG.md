# Architectural Decision Log

> **Document:** 10_DECISION_LOG.md
> **Version:** 0.1.0
> **Status:** Active — Updated continuously
> **Last Updated:** 2026-07-27
> **Author:** Architecture Team

---

## 1. Purpose

This document records all significant architectural and technical decisions made during the development of the Hybrid GraphRAG Enterprise Knowledge Assistant. Each decision is logged with its context, rationale, alternatives considered, and consequences.

This is a living document — every major decision must be recorded here before or during implementation.

---

## 2. Decision Format

Each decision follows this structure:

```
### ADR-XXX: [Title]
- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Deprecated | Superseded
- **Context:** Why was this decision needed?
- **Decision:** What was decided?
- **Alternatives Considered:** What other options were evaluated?
- **Consequences:** What are the implications of this decision?
```

---

## 3. Decision Records

---

### ADR-001: React + FastAPI Architecture

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  The system requires a frontend for user interaction and a backend for business logic, data processing, and AI orchestration. A technology stack was needed that supports rapid development, strong typing, and high-performance async operations.

- **Decision:**
  Selected **React** with **TypeScript** for the frontend and **FastAPI** (Python) for the backend, operating as a decoupled client-server architecture communicating via REST APIs.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | Next.js full-stack | Adds complexity; Python backend needed for AI/ML ecosystem. |
  | Django + templates | Server-rendered; less flexibility for rich interactive UIs. |
  | Flask | Lacks built-in async support and automatic OpenAPI generation. |

- **Consequences:**
  - Clear separation of frontend and backend enables independent deployment and scaling.
  - FastAPI's async support is critical for handling concurrent AI processing requests.
  - React's component model supports the complex, interactive UI requirements.
  - Two distinct tech stacks (Python + TypeScript) require broader team skill set.

---

### ADR-002: Hybrid GraphRAG Retrieval Approach

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  Standard RAG systems rely solely on vector similarity search, which excels at semantic matching but fails to capture structural relationships between entities. The system requires both semantic relevance and relationship-aware reasoning.

- **Decision:**
  Adopted a **Hybrid GraphRAG** approach that combines vector-based semantic retrieval (dense embeddings) with graph-based relational retrieval (knowledge graph traversal). Results from both modalities are fused and reranked before being passed to the LLM.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | Vector-only RAG | Misses entity relationships and multi-hop reasoning. |
  | Graph-only retrieval | Poor at semantic similarity matching for natural language queries. |
  | Keyword search (BM25) | Insufficient for semantic understanding of complex queries. |

- **Consequences:**
  - Improved answer accuracy through complementary retrieval modalities.
  - Enhanced explainability — graph paths provide transparent reasoning chains.
  - Increased system complexity with two retrieval subsystems to maintain.
  - Requires a fusion/reranking strategy to combine heterogeneous results.

---

### ADR-003: Qdrant + Neo4j for Knowledge Storage

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  The hybrid retrieval approach requires two specialized storage backends: one optimized for high-dimensional vector similarity search, and one optimized for graph traversal and relationship queries.

- **Decision:**
  Selected **Qdrant** as the vector database and **Neo4j** as the graph database.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | Pinecone (vectors) | Managed-only; less control over deployment and data residency. |
  | Weaviate (vectors) | Viable, but Qdrant offers a simpler API and better filtering capabilities. |
  | ArangoDB (graph) | Multi-model DB; Neo4j has a more mature graph query language (Cypher) and ecosystem. |
  | pgvector (vectors) | Suitable for small scale, but lacks advanced ANN indexing for production vector workloads. |

- **Consequences:**
  - Qdrant provides purpose-built vector indexing with filtering, payload storage, and high throughput.
  - Neo4j's Cypher query language simplifies complex graph traversal patterns.
  - Two additional infrastructure components to deploy and manage.
  - Both have active open-source communities and Docker support for development.

---

### ADR-004: Alembic for Database Schema Versioning

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  The system requires reproducible, controlled, and production-safe schema changes.

- **Decision:**
  Adopted **Alembic** for database schema version control alongside SQLAlchemy.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | Manual SQL scripts | Prone to human error, hard to version control and rollback. |
  | SQLAlchemy `create_all()` | Cannot manage updates to existing tables in production. |

- **Consequences:**
  - Ensures reproducible, controlled, and production-safe database changes.
  - Requires developers to generate and review migration scripts for any model change.

---

### ADR-005: Supabase Auth as Identity Provider

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  The application requires robust authentication, user management, and JWT token issuance without the operational overhead of building and securing custom password handling.

- **Decision:**
  Use **Supabase Auth** as the identity provider.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | Custom JWT / Password Hashing | High security risk; requires writing custom password reset, email verification, and OAuth flows. |
  | Auth0 | Excellent, but Supabase integrates natively with the PostgreSQL stack already chosen. |
  | Keycloak | Too heavy and complex for the current requirements. |

- **Consequences:**
  - Provides secure authentication, JWT management, and avoids implementing custom authentication logic.
  - The backend only needs to validate tokens and maintain a synchronized user profile table, eliminating password storage risks.

---

### ADR-006: MinIO for Document Object Storage

- **Date:** 2026-07-27
- **Status:** Accepted

- **Context:**
  The system needs a scalable, secure, and performant way to store raw uploaded documents before and during AI processing.

- **Decision:**
  Use **MinIO** as the S3-compatible object storage layer.

- **Alternatives Considered:**
  | Alternative | Reason for Rejection |
  |---|---|
  | PostgreSQL `BYTEA` | Bloats the relational database, heavily impacts backup/restore performance, and scales poorly for large binaries. |
  | Local Filesystem | Not scalable across multiple backend instances; creates stateful API nodes. |
  | AWS S3 | Vendor lock-in; requires external cloud connectivity for local development. |

- **Consequences:**
  - Separates large binary files from relational application data.
  - Ensures a stateless API layer that can scale horizontally.
  - Provides a standard S3-compatible API for future cloud migrations.

---

## 4. Pending Decisions

The following decisions are anticipated in upcoming phases:

| ID | Topic | Expected Phase |
|---|---|---|
| ADR-007 | Embedding model configuration | Phase 5 |
| ADR-008 | Graph schema design | Phase 6 |
| ADR-009 | Retrieval fusion algorithm | Phase 7 |
| ADR-010 | Prompt engineering framework | Phase 8 |
| ADR-011 | Deployment target (Docker Compose vs. Kubernetes) | Phase 10 |

---

## 5. Change History

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-27 | 0.1.0 | Initial decision log with ADR-001, ADR-002, and ADR-003. | Architecture Team |
| 2026-07-27 | 0.2.0 | Added ADR-004 for Alembic database migrations. | Architecture Team |
| 2026-07-27 | 0.3.0 | Added ADR-005 for Supabase Auth identity provider. | Architecture Team |
| 2026-07-27 | 0.4.0 | Added ADR-006 for MinIO object storage. | Architecture Team |
