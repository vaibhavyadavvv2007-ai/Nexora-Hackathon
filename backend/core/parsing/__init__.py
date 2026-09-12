from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Union
from backend.models.document import JobDescription, Resume


class BaseDocumentParser(ABC):
    """Abstract interface for extracting text and structure from documents."""

    @abstractmethod
    def extract_text_from_pdf(self, source: Union[str, Path, BinaryIO]) -> str:
        """Extract raw text and page layout from a PDF document.

        Args:
            source: File path or file-like binary stream.

        Returns:
            Extracted raw text content.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_job_description(self, source: Union[str, Path, BinaryIO], doc_id: str) -> JobDescription:
        """Parse a Job Description PDF into structured domain models.

        Args:
            source: File path or file-like binary stream.
            doc_id: Unique identifier for the JD.

        Returns:
            Populated JobDescription instance.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_resume(self, source: Union[str, Path, BinaryIO], candidate_id: str, candidate_name: str) -> Resume:
        """Parse a candidate resume PDF into structured domain models.

        Args:
            source: File path or file-like binary stream.
            candidate_id: Unique applicant identifier.
            candidate_name: Candidate display name.

        Returns:
            Populated Resume instance.
        """
        raise NotImplementedError
