from typing import Optional
from pydantic import BaseModel, Field
from backend.models.enums import MatchType, SectionType
from backend.models.requirement import Requirement


class EvidenceChunk(BaseModel):
    """Granular evidence unit (sentence or bullet) extracted from a document."""
    id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="Text body of the evidence chunk")
    section: SectionType = Field(default=SectionType.OTHER, description="Document section where evidence was found")
    page: int = Field(default=1, ge=1, description="1-indexed PDF page number")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction or OCR confidence score [0, 1]")
    source_file: str = Field(..., description="Origin PDF filename or relative path")


class MatchEvidence(BaseModel):
    """Associates a specific requirement with candidate evidence and match metrics."""
    requirement: Requirement = Field(..., description="Target JD requirement")
    evidence: EvidenceChunk = Field(..., description="Candidate evidence chunk matching the requirement")
    match_type: MatchType = Field(..., description="Matching engine category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall matching confidence bounded to [0, 1]")
    similarity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score for semantic matches [0, 1]"
    )
