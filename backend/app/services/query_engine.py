"""
Query Engine Service.

Orchestrates the entire hybrid retrieval pipeline from user query
to final formatted LLM response.
"""

from typing import Any

from backend.app.services.query_service import QueryService
from backend.app.services.hybrid_retriever import HybridRetriever
from backend.app.services.reranker_service import RerankerService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.prompt_builder import PromptBuilder
from backend.app.services.llm_service import LLMService
from backend.app.services.response_service import ResponseFormatter, QueryResponse


class QueryEngine:
    """The central orchestrator for answering user questions."""

    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        reranker: RerankerService,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm_service: LLMService,
        response_formatter: ResponseFormatter
    ):
        self._retriever = hybrid_retriever
        self._reranker = reranker
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._llm = llm_service
        self._formatter = response_formatter

    async def query(self, question: str) -> QueryResponse:
        """
        Execute the full hybrid retrieval and generation pipeline.
        """
        # 1. Retrieve raw results from Qdrant and Neo4j
        raw_results = await self._retriever.retrieve(question)
        
        # 2. Merge, deduplicate, and rerank
        ranked_chunks = await self._reranker.rerank(
            raw_results.vector_results, 
            raw_results.graph_result
        )
        
        # 3. Build string context
        context = self._context_builder.build_context(ranked_chunks)
        
        # 4. Build prompt
        prompt = self._prompt_builder.build_prompt(
            question=question,
            document_context=context,
            graph_result=raw_results.graph_result
        )
        
        # 5. Generate Answer via LLM
        answer = await self._llm.answer(prompt)
        
        # 6. Format Final Response
        return self._formatter.format_response(
            answer=answer,
            retrieved_chunks=ranked_chunks,
            graph_entities=raw_results.graph_result.entities
        )
