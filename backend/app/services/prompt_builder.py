"""
Prompt Builder Service.

Constructs the final prompt combining context, graph facts, user questions,
and strict instructional constraints.
"""

from backend.app.models.retrieval import GraphSearchResult


class PromptBuilder:
    """Service for building LLM prompts from context and graph facts."""

    def build_prompt(
        self, 
        question: str, 
        document_context: str, 
        graph_result: GraphSearchResult
    ) -> str:
        """
        Assemble the final prompt block for the LLM.
        """
        # Format Graph Facts
        graph_facts = self._format_graph_facts(graph_result)

        # Assemble Prompt
        prompt = f"""You are a helpful Enterprise Knowledge Assistant.

Your task is to answer the user's question based strictly on the provided Context and Knowledge Graph Facts below.

================================================================================
KNOWLEDGE GRAPH FACTS
================================================================================
{graph_facts if graph_facts.strip() else "No relevant graph facts found."}

================================================================================
RETRIEVED CONTEXT
================================================================================
{document_context}

================================================================================
INSTRUCTIONS
================================================================================
1. ONLY answer using the provided Retrieved Context and Knowledge Graph Facts.
2. NEVER hallucinate or invent information outside of what is provided.
3. If the provided information does not contain the answer, explicitly state: "The provided documents do not contain the answer."
4. CITE your sources for every factual claim. Use the format [Filename, Page X] or [Filename, Section Y] based on the headers provided in the context.
5. Answer in exactly the same language used by the user's question.

================================================================================
USER QUESTION
================================================================================
{question}
"""
        return prompt

    def _format_graph_facts(self, graph_result: GraphSearchResult) -> str:
        """Format entities and relationships into a readable facts string."""
        if not graph_result or (not graph_result.entities and not graph_result.relationships):
            return ""

        facts = []
        
        # Add Entities
        if graph_result.entities:
            facts.append("Key Entities Mentioned:")
            for entity in graph_result.entities:
                facts.append(f"- {entity.name} (Type: {entity.type})")
        
        # Add Relationships
        if graph_result.relationships:
            facts.append("\nKey Relationships:")
            # We need to map IDs to names for readable relationships
            entity_map = {e.id: e.name for e in graph_result.entities}
            
            for rel in graph_result.relationships:
                src_name = entity_map.get(rel.source_id, "Unknown Entity")
                tgt_name = entity_map.get(rel.target_id, "Unknown Entity")
                desc_str = f" ({rel.description})" if rel.description else ""
                facts.append(f"- {src_name} --[{rel.type}]--> {tgt_name}{desc_str}")
                
        return "\n".join(facts)
