# Knowledge Graph Architecture

> **Document:** 06_KNOWLEDGE_GRAPH.md
> **Version:** 1.0.0
> **Status:** Active — Phase 7 Completed
> **Last Updated:** 2026-07-27
> **Author:** Architecture Team

---

## 1. Purpose

This document defines the Knowledge Graph architecture for the Hybrid GraphRAG system, detailing how document chunks are processed into entities and relationships and stored in Neo4j for graph-based retrieval.

---

## 2. Graph Schema Design

The graph database utilizes a flexible, generic schema to accommodate diverse document domains without requiring upfront ontology modeling.

### Nodes

| Node Label | Properties | Description |
|---|---|---|
| `Document` | `id` (UUID), `filename`, `file_type` | Represents a source document ingested into the system. |
| `Chunk` | `id` (UUID), `chunk_index`, `page_number` | Represents a semantic chunk derived from a `Document`. |
| `Entity` | `id` (Hash), `name`, `type` | Represents a real-world object, concept, or person. |

### Relationships

| Relationship Type | Source | Target | Properties | Description |
|---|---|---|---|---|
| `HAS_CHUNK` | `Document` | `Chunk` | - | Links a document to its parsed chunks. |
| `MENTIONS` | `Chunk` | `Entity` | - | Links a chunk to the entities it contains. |
| `RELATES_TO` | `Entity` | `Entity` | `type`, `description` | Semantic relationship between two entities. |

### Constraints and Deduplication

1. **Uniqueness:** Uniqueness constraints are enforced on the `id` property for `Document`, `Chunk`, and `Entity` nodes.
2. **Entity Deduplication:** Entity IDs are generated deterministically using an MD5 hash of `normalized_name + ":" + type`. This ensures that identical entities across different chunks and documents resolve to the exact same node in the graph via Cypher's `MERGE` operation.

---

## 3. Extraction Pipeline

The extraction pipeline leverages Large Language Models (LLMs) to dynamically extract entities and relationships from chunk text.

### Workflow
1. **Trigger:** `GraphExtractionService` fetches chunks with `PENDING` graph extraction status.
2. **LLM Extraction:** `LlmExtractor` sends the chunk text to the LLM (e.g., via Groq API) along with a structured prompt.
3. **Structured Parsing:** The `instructor` library enforces the output schema (`LLMEntity` and `LLMRelationship` Pydantic models).
4. **Graph Sync:** The extracted models are passed to `Neo4jService` and upserted into the database atomically per-chunk.

### Status Tracking
The PostgreSQL `document_chunks` table acts as the state machine for the graph pipeline:
- `entity_extraction_status`: Tracks LLM extraction (`PENDING`, `EXTRACTING`, `COMPLETED`, `FAILED`).
- `graph_sync_status`: Tracks Neo4j ingestion (`PENDING`, `SYNCING`, `COMPLETED`, `FAILED`).

---

## 4. Production Considerations

- **Asynchronous Processing:** Graph extraction runs as an `asyncio` background task to prevent blocking the main API response.
- **Transactions:** Cypher `MERGE` operations are grouped into a single write transaction per chunk.
- **Idempotency:** Re-running the sync process for the same chunk is safe due to `MERGE` constraints.
