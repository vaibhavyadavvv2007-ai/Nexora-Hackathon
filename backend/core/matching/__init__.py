from abc import ABC, abstractmethod
from typing import List, Tuple
from backend.models.document import JobDescription, Resume
from backend.models.evidence import MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class BaseKeywordMatcher(ABC):
    """Abstract interface for deterministic lexical and keyword matching."""

    @abstractmethod
    def match_explicit_skills(
        self,
        resume_skills: List[Skill],
        jd_requirements: List[Requirement]
    ) -> Tuple[List[Skill], List[Requirement]]:
        """Identify matched vs missing requirements based strictly on explicit named skills.

        Note:
            Explicit named skill presence is authoritative. Semantic similarity
            must NOT automatically turn a missing technology into an explicitly matched one.

        Args:
            resume_skills: Extracted and normalized skills from candidate resume.
            jd_requirements: Required and preferred skills from the Job Description.

        Returns:
            Tuple of (matched_skills, missing_requirements).
        """
        raise NotImplementedError

    @abstractmethod
    def compute_lexical_evidence(
        self,
        resume: Resume,
        jd: JobDescription
    ) -> List[MatchEvidence]:
        """Compute keyword and BM25 lexical matches between resume evidence and JD requirements.

        Args:
            resume: Structured candidate resume.
            jd: Structured job description.

        Returns:
            List of MatchEvidence objects citing specific sections and confidence scores.
        """
        raise NotImplementedError


class BaseSemanticMatcher(ABC):
    """Abstract interface for local sentence-transformer semantic embedding and alignment."""

    @abstractmethod
    def compute_semantic_alignment(
        self,
        resume: Resume,
        jd: JobDescription
    ) -> List[MatchEvidence]:
        """Compute semantic cosine similarity between requirement chunks and candidate evidence chunks.

        Note:
            Retains top evidence per requirement above threshold. Distinguishes between
            SEMANTIC_EXACT, SEMANTIC_RELATED, and SEMANTIC_INFERRED.

        Args:
            resume: Structured candidate resume.
            jd: Structured job description.

        Returns:
            List of MatchEvidence objects containing cosine similarities and evidence references.
        """
        raise NotImplementedError


from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import SemanticMatcher

__all__ = [
    "BaseKeywordMatcher",
    "BaseSemanticMatcher",
    "KeywordMatcher",
    "SemanticMatcher",
]
