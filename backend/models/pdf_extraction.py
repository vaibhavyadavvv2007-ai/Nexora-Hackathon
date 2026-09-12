from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.models.enums import DocumentType, ExtractionQuality, ExtractionStatus


class TextBlock(BaseModel):
    """Granular text block with bounding box and page source information."""
    text: str = Field(..., description="Extracted text within block")
    page_number: int = Field(..., ge=1, description="1-indexed source page number")
    block_number: Optional[int] = Field(default=None, description="Block sequence index on the page")
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        default=None,
        description="Bounding box coordinates (x0, y0, x1, y1)"
    )


class PageExtraction(BaseModel):
    """Structured extraction per individual document page."""
    page_number: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(default="", description="Concatenated raw text for the page")
    character_count: int = Field(default=0, ge=0, description="Number of characters on this page")
    text_blocks: List[TextBlock] = Field(default_factory=list, description="Ordered text blocks on page")
    has_images: bool = Field(default=False, description="Whether any raster images exist on this page")


class PDFExtractionResult(BaseModel):
    """Comprehensive structured result of PDF ingestion and text extraction."""
    source_file: str = Field(..., description="Filename or path of the ingested document")
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN, description="Classified document type")
    page_count: int = Field(default=0, ge=0, description="Total pages in the PDF document")
    pages: List[PageExtraction] = Field(default_factory=list, description="Extracted per-page details")
    text: str = Field(default="", description="Full aggregated document text")
    text_blocks: List[TextBlock] = Field(default_factory=list, description="All aggregated text blocks across pages")
    character_count: int = Field(default=0, ge=0, description="Total characters extracted")
    extraction_status: ExtractionStatus = Field(..., description="Macro status: SUCCESS, LOW_QUALITY, or FAILED")
    extraction_method: str = Field(default="pymupdf_text", description="Tool or algorithm used for extraction")
    extraction_quality: ExtractionQuality = Field(..., description="Detailed quality tier or failure reason")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or quality alerts")


class BatchExtractionSummary(BaseModel):
    """Aggregated outcome metrics for a batch extraction run."""
    processed: int = Field(default=0, ge=0, description="Total documents submitted")
    successful: int = Field(default=0, ge=0, description="Documents extracted with SUCCESS status")
    low_quality: int = Field(default=0, ge=0, description="Documents extracted with LOW_QUALITY status")
    failed: int = Field(default=0, ge=0, description="Documents that failed extraction")


class BatchExtractionResult(BaseModel):
    """Collection of extracted documents accompanied by summary statistics."""
    summary: BatchExtractionSummary = Field(..., description="Aggregate execution counts")
    documents: List[PDFExtractionResult] = Field(default_factory=list, description="Individual extraction records")
