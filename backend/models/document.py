from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from backend.models.enums import RequirementType, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class JobDescription(BaseModel):
    """Structured representation of a Job Description document.
    
    The canonical source of truth for all requirements is `requirements[]`.
    `required_skills` and `preferred_skills` are synchronized from `requirements`.
    """
    id: str = Field(..., description="Unique JD identifier")
    role_title: str = Field(default="", description="Canonical job/role title")
    title: Optional[str] = Field(
        default=None,
        description="[DEPRECATED: Use `role_title` as canonical] Alias for role_title for backward compatibility"
    )
    source_file: str = Field(..., description="Path or filename of the source PDF")
    raw_text: str = Field(..., description="Full extracted raw text")
    requirements: List[Requirement] = Field(
        default_factory=list,
        description="Canonical source of truth for all parsed structured requirements"
    )
    responsibilities: List[str] = Field(
        default_factory=list,
        description="List of key duties and responsibilities"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Explicit canonical required skills synchronized strictly from skill-matchable requirements"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Explicit canonical preferred skills synchronized strictly from skill-matchable requirements"
    )
    requirement_chunks: List[EvidenceChunk] = Field(
        default_factory=list,
        description="Chunked requirements for granular semantic comparison"
    )

    @model_validator(mode="after")
    def sync_canonical_skills_and_title(self) -> "JobDescription":
        # Synchronize title and role_title (role_title is canonical)
        if not self.role_title and self.title:
            self.role_title = self.title
        elif not self.title and self.role_title:
            self.title = self.role_title

        # Derive required_skills and preferred_skills ONLY from skill-matchable requirements
        if self.requirements:
            req_skills = [
                r.canonical_name for r in self.requirements
                if r.type == RequirementType.REQUIRED and r.is_skill_matchable
            ]
            pref_skills = [
                r.canonical_name for r in self.requirements
                if r.type == RequirementType.PREFERRED and r.is_skill_matchable
            ]
            # Deduplicate preserving order
            self.required_skills = list(dict.fromkeys(req_skills))
            self.preferred_skills = list(dict.fromkeys(pref_skills))

        return self


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
    experience: List[str] = Field(default_factory=list, description="Extracted work experience bullets/records")
    projects: List[str] = Field(default_factory=list, description="Extracted project bullets/records")
    education: List[str] = Field(default_factory=list, description="Extracted education bullets/records")
    summary: Optional[str] = Field(default=None, description="Candidate professional summary/objective")
    evidence_chunks: List[EvidenceChunk] = Field(
        default_factory=list,
        description="Chunked candidate text with section attribution and preserved page numbers"
    )

