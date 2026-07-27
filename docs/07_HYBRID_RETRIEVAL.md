# Hybrid Retrieval Engine Architecture (Phase 8)

This document describes the complete retrieval flow that powers the HybridGraphRAG AI assistant. It orchestrates vector similarity search (Qdrant) with knowledge graph traversals (Neo4j) to ground the final LLM response in factual, structured, and semantic context.

## 1. High-Level Architecture

The Retrieval Engine combines deep semantic search (via dense embeddings) with structural relationship search (via Knowledge Graph).

```mermaid
graph TD
    A[User Question] --> B[Query Service]
    B --> C{Parallel Execution}
    C -->|Vector Search| D[(Qdrant Vector DB)]
    C -->|Graph Search| E[(Neo4j Graph DB)]
    D --> F[Hybrid Retriever]
    E --> F
    F --> G[Reranker Service]
    G --> H[Context Builder]
    H --> I[Prompt Builder]
    I --> J[LLM Service]
    J --> K[Response Formatter]
    K --> L[API Response]
```

## 2. Request Flow & Service Responsibilities

### 1. `QueryService`
Normalizes the incoming user query, validates it, and generates a dense vector embedding using `EmbeddingService`. 
- **Output**: `QueryEmbeddingResult`

### 2. `HybridRetriever`
Orchestrates parallel calls to Qdrant and Neo4j using `asyncio.gather`.
- **Vector Flow (`QdrantService.search`)**: Finds semantically similar text chunks using Cosine Distance. Returns matching payload IDs.
- **Graph Flow (`Neo4jService.search_graph`)**: Performs keyword-based node matching and traverses 1-hop relationships. Returns connected document chunks.
- **Enrichment**: Fetches actual chunk contents for Qdrant hits from PostgreSQL.

### 3. `RerankerService`
Merges chunks retrieved from both paths, deduplicating via `chunk_id`.
Calculates a final weighted score based on environment configuration:
```text
FinalScore = (VectorScore * VECTOR_WEIGHT) + (GraphConfidence * GRAPH_WEIGHT)
```
- Defaults: `VECTOR_WEIGHT = 0.7`, `GRAPH_WEIGHT = 0.3`

### 4. `ContextBuilder`
Takes the sorted `HybridSearchResult` objects and builds the textual context block for the LLM. 
- Groups chunks by source `document_id`.
- Sorts chunks internally by `chunk_index` to maintain reading flow.
- Truncates context aggressively if it approaches `MAX_CONTEXT_TOKENS` limits.

### 5. `PromptBuilder`
Combines the User Question, Context String, and Graph Facts (Relationships & Entities) into a structured system prompt.
Enforces strict anti-hallucination instructions.

### 6. `LLMService`
A provider-agnostic interface that dispatches the prompt to OpenAI, Gemini, Ollama, or Azure based on the `LLM_PROVIDER` environment variable.

### 7. `ResponseFormatter`
Assembles the LLM output text alongside structured metadata (extracted citations, retrieved raw chunks, matching graph entities, and overall confidence score) into a unified `QueryResponse` JSON object.

## 3. Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant API as ChatRouter
    participant Engine as QueryEngine
    participant QuerySvc as QueryService
    participant Retriever as HybridRetriever
    participant Reranker as RerankerService
    participant LLM as LLMService

    User->>API: POST /api/v1/chat/query
    API->>Engine: query(question)
    
    Engine->>QuerySvc: process_query(question)
    QuerySvc-->>Engine: QueryEmbeddingResult
    
    Engine->>Retriever: retrieve()
    par Vector Search
        Retriever->>Qdrant: search()
    and Graph Search
        Retriever->>Neo4j: search_graph()
    end
    Retriever-->>Engine: HybridRetrievalOutput
    
    Engine->>Reranker: rerank(vector_results, graph_results)
    Reranker-->>Engine: List[HybridSearchResult]
    
    Engine->>Engine: build_context() & build_prompt()
    
    Engine->>LLM: answer(prompt)
    LLM-->>Engine: String Answer
    
    Engine->>API: format_response()
    API-->>User: JSON QueryResponse
```
