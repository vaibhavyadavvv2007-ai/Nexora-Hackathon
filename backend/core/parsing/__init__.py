from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Union

from backend.core.normalization.skill_normalizer import SkillNormalizer
def inspect_document(*args, **kwargs):
    from backend.core.parsing.inspector import inspect_document as _inspect
    return _inspect(*args, **kwargs)


def inspect_job_description(*args, **kwargs):
    from backend.core.parsing.inspector import inspect_job_description as _inspect
    return _inspect(*args, **kwargs)


def inspect_resume(*args, **kwargs):
    from backend.core.parsing.inspector import inspect_resume as _inspect
    return _inspect(*args, **kwargs)
from backend.core.exceptions import DocumentParsingError
from backend.core.parsing.jd_parser import JobDescriptionParser
from backend.core.parsing.pdf_extractor import PDFExtractor
from backend.core.parsing.resume_parser import ResumeParser
from backend.core.parsing.section_classifier import SectionClassifier
from backend.models.document import JobDescription, Resume
from backend.models.enums import DocumentType


class BaseDocumentParser(ABC):
    """Abstract interface for extracting text and structure from documents."""

    @abstractmethod
    def extract_text_from_pdf(self, source: Union[str, Path, BinaryIO]) -> str:
        """Extract raw text and page layout from a PDF document."""
        raise NotImplementedError

    @abstractmethod
    def parse_job_description(self, source: Union[str, Path, BinaryIO], doc_id: str = "jd_001") -> JobDescription:
        """Parse a Job Description PDF into structured domain models."""
        raise NotImplementedError

    @abstractmethod
    def parse_resume(
        self,
        source: Union[str, Path, BinaryIO],
        candidate_id: str = "cand_001",
        candidate_name: Optional[str] = None,
    ) -> Resume:
        """Parse a candidate resume PDF into structured domain models."""
        raise NotImplementedError


class DocumentParser(BaseDocumentParser):
    """Unified document parser connecting PDFExtractor, JobDescriptionParser, and ResumeParser."""

    def __init__(self, skill_normalizer: Optional[SkillNormalizer] = None):
        self.normalizer = skill_normalizer or SkillNormalizer()
        self.extractor = PDFExtractor()
        self.jd_parser = JobDescriptionParser(skill_normalizer=self.normalizer)
        self.resume_parser = ResumeParser(skill_normalizer=self.normalizer)

    def extract_text_from_pdf(self, source: Union[str, Path, BinaryIO]) -> str:
        result = self.extractor.extract(source, document_type=DocumentType.RESUME)
        return result.text

    def parse_job_description(self, source: Union[str, Path, BinaryIO], doc_id: str = "jd_001") -> JobDescription:
        extraction = self.extractor.extract(source, document_type=DocumentType.JOB_DESCRIPTION)
        return self.jd_parser.parse(extraction, jd_id=doc_id)

    def parse_resume(
        self,
        source: Union[str, Path, BinaryIO],
        candidate_id: str = "cand_001",
        candidate_name: Optional[str] = None,
    ) -> Resume:
        extraction = self.extractor.extract(source, document_type=DocumentType.RESUME)
        resume = self.resume_parser.parse(extraction, candidate_id=candidate_id)
        if candidate_name:
            resume.name = candidate_name
        return resume


__all__ = [
    "BaseDocumentParser",
    "DocumentParser",
    "DocumentParsingError",
    "JobDescriptionParser",
    "PDFExtractor",
    "ResumeParser",
    "SectionClassifier",
    "SkillNormalizer",
    "inspect_document",
    "inspect_job_description",
    "inspect_resume",
]
