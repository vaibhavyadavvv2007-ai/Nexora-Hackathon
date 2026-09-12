from pydantic import BaseModel, Field
from backend.models.enums import RequirementType


class Requirement(BaseModel):
    """Structured requirement extracted from Job Description."""
    id: str = Field(..., description="Unique identifier for the requirement (e.g. req_01)")
    name: str = Field(..., description="Human-readable requirement label or technology name")
    type: RequirementType = Field(..., description="Requirement tier: required, preferred, or responsibility")
    canonical_name: str = Field(..., description="Normalized canonical skill/domain key")
    weight: float = Field(default=1.0, ge=0.0, description="Relative importance weight")
    critical: bool = Field(default=False, description="Whether this is a non-negotiable hard requirement")
    source_text: str = Field(..., description="Original verbatim sentence or bullet from the JD")
