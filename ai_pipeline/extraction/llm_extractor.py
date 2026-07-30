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

# Removed API key rotation utilities

logger = logging.getLogger(__name__)

# Define schemas for the LLM to output
class LLMEntity(BaseModel):
    name: str = Field(..., description="The exact name of the entity.")
    type: str = Field(..., description="Entity type, e.g., PERSON, ORGANIZATION, LOCATION, CONCEPT.")
    description: str | None = Field(None, description="Brief description of this entity.")

class LLMRelationship(BaseModel):
    source_entity_name: str = Field(
        ...,
        alias="source",
        description="Name of the source entity.",
    )
    target_entity_name: str = Field(
        ...,
        alias="target",
        description="Name of the target entity.",
    )
    relationship_type: str = Field(
        ...,
        alias="type",
        description="Type of relationship, e.g., WORKS_FOR, LOCATED_IN, RELATES_TO.",
    )
    description: str | None = Field(None, description="Description of the relationship.")

    model_config = {"populate_by_name": True}

class LLMExtraction(BaseModel):
    entities: list[LLMEntity]
    relationships: list[LLMRelationship]


class LlmExtractor(BaseExtractor):
    """Extractor that uses an OpenAI-compatible LLM via Instructor for structured output."""

    def __init__(self):
        from backend.app.services.llm_service import (
            LLM_PROVIDER,
            LLM_MODEL,
            resolve_openai_compatible_config,
        )

        self.model_name = os.getenv("EXTRACTION_MODEL") or LLM_MODEL
        self.provider = LLM_PROVIDER

        try:
            api_key, base_url = resolve_openai_compatible_config(LLM_PROVIDER)
            self.base_url = base_url
            self._api_key = api_key
            self._base_url = base_url
            
            self._initialize_client()
            
            logger.info(
                "Initialized LlmExtractor (provider=%s, model=%s, base_url=%s, mode=JSON)",
                LLM_PROVIDER,
                self.model_name,
                base_url or "https://api.openai.com/v1",
            )
        except Exception as e:
            logger.error("Failed to initialize LlmExtractor client: %s", e)
            raise

    def _initialize_client(self):
        """Initialize or reinitialize the OpenAI client with current credentials."""
        # Create OpenAI client with max_retries=4 to handle basic rate limits automatically
        self.client = OpenAI(
            api_key=self._api_key, 
            base_url=self._base_url,
            max_retries=4
        )
        # Use JSON mode instead of TOOLS mode for broader provider compatibility.
        # TOOLS mode relies on function-calling which Groq validates strictly and
        # rejects when the model outputs field names that differ from the schema.
        self._client = instructor.from_openai(
            self.client, 
            mode=instructor.Mode.JSON
        )

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

        logger.info("Starting extraction")

        import time
        max_attempts = 4
        for attempt in range(max_attempts):
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
                
                logger.info("Extraction successful on attempt %d", attempt + 1)
                return self._process_extraction_response(response)
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 5
                        logger.warning("Rate limit hit during extraction (attempt %d). Waiting %d seconds...", attempt + 1, wait_time)
                        time.sleep(wait_time)
                        continue
                logger.error("Extraction failed with error: %s", e)
                return ExtractionResult(entities=[], relationships=[])
                
        return ExtractionResult(entities=[], relationships=[])

    def _process_extraction_response(self, response: LLMExtraction) -> ExtractionResult:
        """Process the LLM extraction response into the standard format."""
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
