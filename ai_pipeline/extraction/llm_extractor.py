"""
LLM-based entity and relationship extractor using instructor.
"""

import os
import hashlib
import logging
from typing import Literal

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

from ai_pipeline.extraction.base_extractor import (
    BaseExtractor,
    ExtractionResult,
    ExtractedEntity,
    ExtractedRelationship,
)

logger = logging.getLogger(__name__)

# Define schemas for the LLM to output
class LLMEntity(BaseModel):
    name: str = Field(..., description="The exact name of the entity.")
    type: str = Field(..., description="Entity type, e.g., PERSON, ORGANIZATION, LOCATION, CONCEPT.")
    description: str | None = Field(None, description="Brief description of this entity.")

class LLMRelationship(BaseModel):
    source_entity_name: str = Field(..., description="Name of the source entity.")
    target_entity_name: str = Field(..., description="Name of the target entity.")
    relationship_type: str = Field(..., description="Type of relationship, e.g., WORKS_FOR, LOCATED_IN, RELATES_TO.")
    description: str | None = Field(None, description="Description of the relationship.")

class LLMExtraction(BaseModel):
    entities: list[LLMEntity]
    relationships: list[LLMRelationship]


class LlmExtractor(BaseExtractor):
    """Extractor that uses an OpenAI-compatible LLM via Instructor for structured output."""

    def __init__(self):
        # Allow override for local LLMs (e.g., Ollama or vLLM)
        api_key = os.getenv("OPENAI_API_KEY", "dummy")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        self.model_name = os.getenv("EXTRACTION_MODEL", "gpt-4o-mini")
        
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            self._client = instructor.from_openai(client)
        except Exception as e:
            logger.error("Failed to initialize LlmExtractor client: %s", e)
            raise

    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """Generate a deterministic ID for an entity."""
        normalized_name = name.strip().lower()
        normalized_type = entity_type.strip().upper()
        unique_string = f"{normalized_name}:{normalized_type}"
        return hashlib.md5(unique_string.encode("utf-8")).hexdigest()

    def extract(self, text: str) -> ExtractionResult:
        if not text or not text.strip():
            return ExtractionResult(entities=[], relationships=[])

        prompt = (
            "Analyze the following text and extract all important entities and the relationships between them. "
            "Ensure that relationship source and target names exactly match the extracted entity names.\n\n"
            f"Text:\n{text}"
        )

        try:
            response: LLMExtraction = self._client.chat.completions.create(
                model=self.model_name,
                response_model=LLMExtraction,
                messages=[
                    {"role": "system", "content": "You are a precise knowledge graph extraction system."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
        except Exception as e:
            logger.error("LLM Extraction failed: %s", e)
            # Return empty result on failure to prevent pipeline crash, or raise?
            # For graph building, we can log and return empty.
            return ExtractionResult(entities=[], relationships=[])

        # Post-process to deterministically ID entities and link relationships
        entity_map = {}
        extracted_entities = []
        
        for llm_ent in response.entities:
            ent_id = self._generate_entity_id(llm_ent.name, llm_ent.type)
            if ent_id not in entity_map:
                ent = ExtractedEntity(
                    id=ent_id,
                    name=llm_ent.name,
                    type=llm_ent.type,
                    description=llm_ent.description
                )
                entity_map[llm_ent.name.strip().lower()] = ent
                extracted_entities.append(ent)

        extracted_relationships = []
        for llm_rel in response.relationships:
            source_key = llm_rel.source_entity_name.strip().lower()
            target_key = llm_rel.target_entity_name.strip().lower()
            
            source_ent = entity_map.get(source_key)
            target_ent = entity_map.get(target_key)
            
            if source_ent and target_ent:
                rel = ExtractedRelationship(
                    source_id=source_ent.id,
                    target_id=target_ent.id,
                    type=llm_rel.relationship_type.upper(),
                    description=llm_rel.description
                )
                extracted_relationships.append(rel)

        return ExtractionResult(entities=extracted_entities, relationships=extracted_relationships)
