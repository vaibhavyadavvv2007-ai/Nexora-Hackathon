from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.models.enums import SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class JobDescription(BaseModel):
    """Structured representation of a Job Description document."""
    id: str = Field(..., description="Unique JD identifier")
    title: str = Field(..., description="Job title")
    source_file: str = Field(..., description="Path or filename of the source PDF")
    raw_text: str = Field(..., description="Full extracted raw text")
    requirements: List[Requirement] = Field(default_factory=list, description="All parsed structured requirements")
    required_skills: List[str] = Field(default_factory=list, description="Explicit canonical required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Explicit canonical preferred skills")
    responsibilities: List[str] = Field(default_factory=list, description="List of key duties and responsibilities")
    requirement_chunks: List[EvidenceChunk] = Field(
        default_factory=list,
        description="Chunked requirements for granular semantic comparison"
    )


class Resume(BaseModel):
    """Structured representation of an applicant resume document."""
    candidate_id: str = Field(..., description="Unique applicant/resume ID")
    name: str = Field(..., description="Candidate display name")
    source_file: str = Field(..., description="Source resume PDF filename")
    raw_text: str = Field(..., description="Full extracted raw text")
    sections: Dict[SectionType, str] = Field(
        default_factory=dict,
        description="Text content segmented by document section"
    )
    skills: List[Skill] = Field(default_factory=list, description="Normalized skills extracted from resume")
    evidence_chunks: List[EvidenceChunk] = Field(
        default_factory=list,
        description="Chunked candidate text with section attribution"
    )
