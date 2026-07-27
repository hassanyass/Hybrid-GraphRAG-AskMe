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
    participant Validation as Document Service (Validation)
    participant Storage as Storage Service
    participant MinIO as MinIO Bucket
    participant Repo as Document Repository
    participant DB as PostgreSQL (documents table)

    User->>API: POST /api/v1/documents/upload (Multipart File)
    API->>Validation: Verify size, format, empty state
    alt Validation Failed
        Validation-->>User: 400 Bad Request
    end
    Validation->>Storage: upload_file(user_id, file_stream, content_type)
    Storage->>MinIO: put_object(key={user_id}/{uuid}_{filename})
    MinIO-->>Storage: Success
    Storage-->>Validation: Return object_key
    Validation->>Repo: Create Document(object_key, UPLOADED)
    Repo->>DB: INSERT INTO documents
    DB-->>Repo: Returns Document Record
    Repo-->>Validation: Returns Document Entity
    Validation-->>API: Returns Document ID & Status
    API-->>User: 201 Created (Upload Response)
```

### Document Lifecycle States

Documents transition through the following states (`DocumentStatus` Enum):

1. **`UPLOADED`**: The document has been successfully verified, stored in MinIO, and a metadata record is created in PostgreSQL.
2. **`PROCESSING`**: The AI pipeline has picked up the document for chunking and embedding. *(Future Phase)*
3. **`COMPLETED`**: The AI pipeline successfully processed the document, inserting it into Qdrant and Neo4j. *(Future Phase)*
4. **`FAILED`**: An error occurred during AI pipeline processing. *(Future Phase)*

### Storage Strategy
- **MinIO**: Acts as the single source of truth for the raw binary files. Keys are prefixed with the `user_id` to enforce logical multi-tenancy at the storage level.
- **PostgreSQL**: Stores relational metadata (e.g., filename, size, MIME type) and the pointer (`storage_path`) to the MinIO object.
