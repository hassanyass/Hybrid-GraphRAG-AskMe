# Hybrid GraphRAG Enterprise Knowledge Assistant

> An AI-powered enterprise document assistant combining Retrieval Augmented Generation (RAG), Knowledge Graphs, Vector Search, and Large Language Model integration for intelligent, explainable document understanding.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB.svg)](https://reactjs.org/)

---

## 1. Overview

**Hybrid GraphRAG Enterprise Knowledge Assistant** is a production-grade AI system designed to transform how organizations interact with their document repositories. The system employs a hybrid retrieval architecture that combines:

- **Retrieval Augmented Generation (RAG)** — Grounds LLM responses in verified organizational knowledge, reducing hallucinations and ensuring factual accuracy.
- **Knowledge Graph** — Captures and traverses entity relationships across documents, enabling multi-hop reasoning and contextual understanding.
- **Vector Search** — Provides semantic similarity matching for natural language queries against document embeddings.
- **Large Language Model Integration** — Generates human-readable, contextually rich responses synthesized from retrieved knowledge.

By fusing vector-based semantic retrieval with graph-based relational retrieval, the system delivers answers that are both semantically relevant and structurally grounded in the relationships between concepts.

---

## 2. System Objectives

| Objective | Description |
|---|---|
| **Intelligent Document Understanding** | Automatically parse, chunk, and extract structured knowledge from uploaded documents across multiple formats (PDF, DOCX, TXT, Markdown). |
| **Semantic Search** | Enable natural language queries that retrieve contextually relevant passages using dense vector embeddings. |
| **Knowledge Relationship Extraction** | Identify and store entities, relationships, and hierarchies from documents in a knowledge graph for structured traversal. |
| **Explainable AI Responses** | Provide transparent, source-attributed answers with traceability back to original documents and reasoning paths. |

---

## 3. Planned Technology Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18+ | Component-based UI framework |
| TypeScript | Type-safe frontend development |
| Tailwind CSS | Utility-first styling framework |

### Backend
| Technology | Purpose |
|---|---|
| Python 3.11+ | Core backend language |
| FastAPI | High-performance async API framework |

### AI & Processing
| Technology | Purpose |
|---|---|
| LangChain | LLM orchestration and chain management |
| BGE-M3 | Multilingual dense embeddings |
| GPT-OSS-120B via Groq | High-speed LLM inference |

### Storage & Databases
| Technology | Purpose |
|---|---|
| PostgreSQL | Relational data and metadata storage |
| Qdrant | Vector database for semantic search |
| Neo4j | Graph database for knowledge relationships |
| MinIO | S3-compatible object storage for documents |

---

## 4. Project Structure

```
HybridGraphRAG/
├── backend/            # FastAPI backend application
│   ├── api/            # API route controllers
│   ├── core/           # Application configuration and startup
│   ├── models/         # SQLAlchemy / Pydantic models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic layer
│   ├── repositories/   # Data access layer
│   └── utils/          # Shared utility functions
├── frontend/           # React + TypeScript frontend application
│   ├── src/            # Application source code
│   └── public/         # Static assets
├── ai_pipeline/        # AI processing pipeline
│   ├── embeddings/     # Embedding generation modules
│   ├── extraction/     # Entity and relationship extraction
│   ├── chunking/       # Document chunking strategies
│   └── llm/            # LLM integration and prompt management
├── infrastructure/     # Infrastructure-as-code and deployment configs
│   ├── docker/         # Dockerfiles for each service
│   ├── k8s/            # Kubernetes manifests (future)
│   └── nginx/          # Reverse proxy configuration
├── docs/               # Project documentation
├── tests/              # Test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
├── scripts/            # Development and deployment scripts
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
├── docker-compose.yml  # Docker Compose orchestration
├── README.md           # This file
└── LICENSE             # Project license
```

---

## 5. Development Status

- [x] **Phase 0** — Foundation (Project structure, documentation, configuration)
- [x] **Phase 1** — Backend Foundation (FastAPI setup, project config, health checks)
- [x] **Phase 2** — Database Layer (PostgreSQL schemas, migrations, repositories)
- [x] **Phase 3** — Authentication (JWT auth, RBAC, session management)
- [x] **Phase 4** — Document Management (Upload, parsing, storage pipeline)
- [ ] **Phase 5** — AI Pipeline (Embedding generation, chunking, extraction)
- [ ] **Phase 6** — Knowledge Storage (Qdrant indexing, Neo4j graph construction)
- [ ] **Phase 7** — RAG Engine (Hybrid retrieval, reranking, context assembly)
- [ ] **Phase 8** — LLM Integration (Groq inference, prompt engineering, response generation)
- [ ] **Phase 9** — Frontend (React UI, search interface, document viewer)
- [ ] **Phase 10** — Deployment (Docker, CI/CD, monitoring, production hardening)

---

## 6. Getting Started

> **Note:** The project is actively in development. The backend is currently capable of handling document uploads and managing user identities.

### Implemented Features

- **Authentication**: Stateless JWT-based authentication using Supabase.
- **Database Layer**: Async PostgreSQL integration via SQLAlchemy and Alembic.
- **Document Upload**: Secured FastAPI endpoint for multipart file uploads with size and MIME validation.
- **Object Storage**: MinIO integration for decoupling binary files from relational data.

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd HybridGraphRAG

# Copy environment template
cp .env.example .env
# Edit .env with your configuration values

# Start infrastructure services
docker-compose up -d
```

Further setup instructions will be added as AI and Frontend phases are finalized.

---

## 7. Documentation

Comprehensive documentation is maintained in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| [Architecture](docs/01_ARCHITECTURE.md) | System architecture and design principles |
| [System Design](docs/02_SYSTEM_DESIGN.md) | Detailed system design and component interactions |
| [Database Design](docs/03_DATABASE_DESIGN.md) | Database schemas and data modeling |
| [API Design](docs/04_API_DESIGN.md) | REST API specifications and contracts |
| [AI Pipeline](docs/05_AI_PIPELINE.md) | AI processing pipeline design |
| [RAG Design](docs/06_RAG_DESIGN.md) | Retrieval Augmented Generation architecture |
| [Security Design](docs/07_SECURITY_DESIGN.md) | Security architecture and policies |
| [Deployment Guide](docs/08_DEPLOYMENT_GUIDE.md) | Deployment procedures and infrastructure |
| [Development Guidelines](docs/09_DEVELOPMENT_GUIDELINES.md) | Coding standards and conventions |
| [Decision Log](docs/10_DECISION_LOG.md) | Architectural decision records |

---

## 8. License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 9. Contributing

Contribution guidelines will be established in a future phase. All contributions must adhere to the [Development Guidelines](docs/09_DEVELOPMENT_GUIDELINES.md).

---

*Last updated: 2026-07-27 — Phase 4: Document Management System*
