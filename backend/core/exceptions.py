"""Core exception classes for the document ingestion and parsing pipeline."""

from typing import Optional
from backend.models.enums import ExtractionStatus


class DocumentParsingError(Exception):
    """Raised when a document cannot be parsed due to extraction failures or severe corruption."""

    def __init__(
        self,
        source_file: str,
        extraction_status: ExtractionStatus,
        reason: Optional[str] = None,
    ):
        self.source_file = source_file
        self.extraction_status = extraction_status
        self.reason = reason or "Document extraction status is FAILED"
        super().__init__(
            f"Parsing rejected for '{source_file}' with status '{extraction_status}': {self.reason}"
        )
