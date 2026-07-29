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

    async def query(self, question: str, workspace_id: str | None = None) -> QueryResponse:
        """
        Execute the full hybrid retrieval and generation pipeline.
        """
        import logging
        logger = logging.getLogger(__name__)

        # 1. Retrieve raw results from Qdrant and Neo4j
        raw_results = await self._retriever.retrieve(question, workspace_id=workspace_id)
        
        # 2. Merge, deduplicate, and rerank
        ranked_chunks = await self._reranker.rerank(
            raw_results.vector_results, 
            raw_results.graph_result
        )
        
        # 3. Build string context
        context = self._context_builder.build_context(ranked_chunks)
        graph_facts = self._prompt_builder._format_graph_facts(raw_results.graph_result)
        
        # Determine if we should call LLM
        num_chunks = len(ranked_chunks)
        has_graph = bool(graph_facts.strip())
        context_len = len(context)
        llm_called = num_chunks > 0 or has_graph
        reason = "Context found" if llm_called else "No context retrieved (early exit)"

        logger.info(
            "\nQUERY: %s\n"
            "Retrieved vector chunks: %d\n"
            "Retrieved graph facts: %s\n"
            "Context length: %d\n"
            "LLM called: %s\n"
            "Reason: %s",
            question,
            num_chunks,
            "Yes" if has_graph else "No",
            context_len,
            llm_called,
            reason
        )

        if not llm_called:
            return self._formatter.format_response(
                answer="The provided documents do not contain enough information to answer this question.",
                retrieved_chunks=[],
                graph_entities=[]
            )

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
