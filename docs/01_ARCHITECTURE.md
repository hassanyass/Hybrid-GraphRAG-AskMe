# Hybrid GraphRAG Enterprise Knowledge Assistant — Architecture

> **Document:** 01_ARCHITECTURE.md
> **Version:** 0.1.0
> **Status:** Initial Draft — Phase 0 Foundation
> **Last Updated:** 2026-07-27
> **Author:** Architecture Team

---

## 1. Purpose

This document defines the overall system architecture for the Hybrid GraphRAG Enterprise Knowledge Assistant. It serves as the authoritative reference for all architectural decisions, layer boundaries, component responsibilities, and integration patterns.

This document will be continuously updated as the system evolves through each development phase.

---

## 2. Introduction

The Hybrid GraphRAG Enterprise Knowledge Assistant is an AI-powered system that enables intelligent document understanding through a combination of semantic vector retrieval and knowledge graph traversal. The architecture is designed to be modular, scalable, and maintainable, following clean architecture principles with clear separation of concerns.

---

## 3. Architecture Goals

| Goal | Description |
|---|---|
| **Modularity** | Each subsystem is independently deployable and replaceable without affecting others. |
| **Scalability** | The system supports horizontal scaling of compute-intensive components (embedding, LLM inference). |
| **Maintainability** | Clean layer separation ensures that changes in one layer do not cascade to others. |
| **Extensibility** | New document types, retrieval strategies, and LLM providers can be added without modifying core logic. |
| **Security** | All data access is authenticated and authorized. Secrets are never stored in source code. |
| **Observability** | Structured logging, health checks, and metrics are built into every component. |

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│              React + TypeScript Frontend                        │
├─────────────────────────────────────────────────────────────────┤
│                     API Gateway / Reverse Proxy                 │
│                          (Nginx)                                │
├─────────────────────────────────────────────────────────────────┤
│                     Application Layer                           │
│              FastAPI Backend (Controllers + Services)           │
├─────────────────────────────────────────────────────────────────┤
│                     AI Processing Layer                         │
│        Embeddings │ Chunking │ Extraction │ LLM Integration     │
├──────────────────┬──────────────────┬───────────────────────────┤
│  Knowledge       │   Data Storage   │   Object Storage          │
│  Storage Layer   │   Layer          │   Layer                   │
│  (Qdrant + Neo4j)│   (PostgreSQL)   │   (MinIO)                 │
└──────────────────┴──────────────────┴───────────────────────────┘
```

---

## 5. Main Layers

### 5.1 Presentation Layer

- **Technology:** React 18+, TypeScript, Tailwind CSS
- **Responsibility:** User interface for document upload, search, query interaction, and result visualization.
- **Communication:** Communicates exclusively with the Application Layer via REST API calls.
- **Phase:** 9

### 5.2 Application Layer

- **Technology:** Python 3.11+, FastAPI
- **Responsibility:** API controllers, business logic services, authentication, authorization, and request validation.
- **Pattern:** Controller → Service → Repository (Clean Architecture)
- **Phase:** 1, 3

### 5.3 AI Processing Layer

- **Technology:** LangChain, BGE-M3, Groq
- **Responsibility:** Document chunking, embedding generation, entity/relationship extraction, LLM prompt management, and response generation.
- **Sub-components:**
  - `embeddings/` — Dense vector generation using BGE-M3
  - `chunking/` — Document segmentation strategies
  - `extraction/` — Named entity and relationship extraction
  - `llm/` — LLM integration, prompt templates, and chain orchestration
- **Phase:** 5, 8

### 5.4 Knowledge Storage Layer

- **Technology:** Qdrant (vectors), Neo4j (graph)
- **Responsibility:** Persists and indexes the two retrieval modalities — semantic embeddings and knowledge graph triples.
- **Phase:** 6

### 5.5 Data Storage Layer

- **Technology:** PostgreSQL (relational), MinIO (objects)
- **Responsibility:** Stores structured application data (users, documents, metadata, audit logs) and raw document files.
- **Phase:** 2, 4

---

## 6. Cross-Cutting Concerns

### 6.1 Configuration Management
- All configuration via environment variables.
- No hard-coded values in source code.
- Template provided in `.env.example`.

### 6.2 Error Handling
- Centralized exception handling middleware.
- Structured error responses with error codes.
- Detailed internal logging; safe external messages.

### 6.3 Logging & Observability
- Structured JSON logging.
- Request tracing with correlation IDs.
- Health check endpoints for all services.

### 6.4 Security
- JWT-based authentication.
- Role-based access control (RBAC).
- Input validation at API boundary.
- See [07_SECURITY_DESIGN.md](07_SECURITY_DESIGN.md) for details.

---

## 7. Current Architecture Status

| Phase | Status |
|---|---|
| Phase 0 — Foundation | ✅ Completed |
| Phase 1 — Backend Foundation | ⬜ Not Started |
| Phase 2 — Database Layer | ⬜ Not Started |
| Phase 3 — Authentication | ⬜ Not Started |
| Phase 4 — Document Management | ⬜ Not Started |
| Phase 5 — AI Pipeline | ⬜ Not Started |
| Phase 6 — Knowledge Storage | ⬜ Not Started |
| Phase 7 — RAG Engine | ⬜ Not Started |
| Phase 8 — LLM Integration | ⬜ Not Started |
| Phase 9 — Frontend | ⬜ Not Started |
| Phase 10 — Deployment | ⬜ Not Started |

---

## 8. Change History

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-07-27 | 0.1.0 | Initial architecture document created during Phase 0 Foundation. | Architecture Team |
