"""
Base interfaces for entity and relationship extraction.
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field

class ExtractedEntity(BaseModel):
    id: str = Field(..., description="Deterministic ID (e.g. hash) of the entity.")
    name: str = Field(..., description="Normalized name of the entity.")
    type: str = Field(..., description="Type of the entity (e.g., PERSON, ORGANIZATION, CONCEPT).")
    description: str | None = Field(None, description="Optional brief description of the entity in this context.")

class ExtractedRelationship(BaseModel):
    source_id: str = Field(..., description="ID of the source entity.")
    target_id: str = Field(..., description="ID of the target entity.")
    type: str = Field(..., description="Type of relationship (e.g., MENTIONS, WORKS_FOR, RELATES_TO).")
    description: str | None = Field(None, description="Description of how they are related.")

class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]

class BaseExtractor(ABC):
    """Base class for knowledge graph extraction strategies."""
    
    @abstractmethod
    def extract(self, text: str) -> ExtractionResult:
        """
        Extract entities and relationships from text.
        
        Args:
            text: The text to extract from.
            
        Returns:
            An ExtractionResult containing entities and relationships.
        """
        pass
