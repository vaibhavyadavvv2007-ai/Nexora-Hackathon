from typing import Optional
from pydantic import BaseModel, Field
from backend.models.enums import MatchType, SectionType


class Skill(BaseModel):
    """Normalized candidate skill identified in document."""
    canonical_name: str = Field(..., description="Standardized canonical skill identifier (e.g. 'kubernetes')")
    surface_form: str = Field(..., description="Actual token or text matched in the resume (e.g. 'K8s')")
    match_type: MatchType = Field(default=MatchType.EXACT, description="Type of match: exact, alias, fuzzy, etc.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score bounded to [0, 1]")
    section: SectionType = Field(default=SectionType.SKILLS, description="Document section where skill was found")
    source_page: int = Field(default=1, ge=1, description="1-indexed source PDF page number")

    @property
    def name(self) -> str:
        """Alias for surface_form or canonical_name for frontend compatibility."""
        return self.surface_form or self.canonical_name

    @property
    def canonical(self) -> str:
        """Alias for canonical_name for frontend compatibility."""
        return self.canonical_name
