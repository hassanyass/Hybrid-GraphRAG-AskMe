# System Workflow

> **Document:** SYSTEM_WORKFLOW.md
> **Version:** 1.0.0
> **Status:** Active — Phase 4 Completed
> **Last Updated:** 2026-07-27
> **Author:** Architecture Team

---

## 1. Document Upload Workflow

This workflow describes the lifecycle of a document from the user's upload action through storage and metadata tracking.

```mermaid
sequenceDiagram
    participant User as Authenticated User
    participant API as Upload API
    participant Validation as Document Service
    participant Storage as Storage Service
    participant MinIO as MinIO Bucket
    participant Repo as Document Repository
    participant DB as PostgreSQL
    participant Pipeline as AI Pipeline Service
    participant Qdrant as Vector DB
    participant Neo4j as Graph DB

    User->>API: POST /api/v1/documents/upload
    API->>Validation: Verify size, format
    Validation->>Storage: upload_file()
    Storage->>MinIO: put_object()
    MinIO-->>Storage: Success
    Validation->>Repo: Create Document(UPLOADED)
    Repo->>DB: INSERT INTO documents
    Validation-->>API: Returns Document ID & Status
    API-->>User: 201 Created
    
    %% Background AI Pipeline
    API-)Pipeline: asyncio.create_task(process_document)
    Pipeline->>Repo: Update Document(PROCESSING)
    Pipeline->>Pipeline: Parse Document
    Pipeline->>Pipeline: Hybrid Chunking
    Pipeline->>DB: INSERT INTO document_chunks
    Pipeline->>Qdrant: Embed & Upsert Vectors
    Pipeline->>Repo: Update Document(COMPLETED)
    
    %% Background Graph Extraction
    Pipeline-)Neo4j: asyncio.create_task(process_chunks for Graph)
    Neo4j->>Neo4j: LLM Entity Extraction
    Neo4j->>Neo4j: Sync to Graph DB
    Neo4j->>DB: Update Chunk Statuses (SYNCED)
```

### Document Lifecycle States

Documents transition through the following states (`DocumentStatus` Enum):

1. **`UPLOADED`**: The document has been successfully verified, stored in MinIO, and a metadata record is created in PostgreSQL.
2. **`PROCESSING`**: The AI pipeline has picked up the document for parsing, chunking, and vector embedding.
3. **`COMPLETED`**: The AI pipeline successfully processed the document, inserting it into Qdrant. (Graph extraction continues asynchronously).
4. **`FAILED`**: An error occurred during AI pipeline processing.

### Storage Strategy
- **MinIO**: Acts as the single source of truth for the raw binary files. Keys are prefixed with the `user_id` to enforce logical multi-tenancy at the storage level.
- **PostgreSQL**: Stores relational metadata (e.g., filename, size, MIME type) and the pointer (`storage_path`) to the MinIO object. Contains the `document_chunks` table tracking Qdrant and Neo4j sync statuses.
