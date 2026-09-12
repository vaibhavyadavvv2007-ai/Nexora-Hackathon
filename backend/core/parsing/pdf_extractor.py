import io
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union
import fitz  # PyMuPDF

from backend.config.settings import Settings, get_settings
from backend.models.enums import DocumentType, ExtractionQuality, ExtractionStatus
from backend.models.pdf_extraction import (
    BatchExtractionResult,
    BatchExtractionSummary,
    PageExtraction,
    PDFExtractionResult,
    TextBlock,
)


class PDFExtractor:
    """Robust PDF text and block extraction engine powered by PyMuPDF."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def extract(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        document_type: DocumentType = DocumentType.UNKNOWN,
        source_name: Optional[str] = None
    ) -> PDFExtractionResult:
        """Extract text, blocks, and quality assessment from a PDF.

        Args:
            source: File path, raw bytes, or file-like binary stream.
            document_type: Category of document (JD, Resume, etc.).
            source_name: Optional explicit name/identifier for the source file.

        Returns:
            Structured PDFExtractionResult with per-page details, blocks, and quality status.
        """
        resolved_name = self._resolve_source_name(source, source_name)

        # Pre-validation: check file path existence and extension if path-like
        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if not path_obj.exists():
                return self._create_error_result(
                    source_name=resolved_name,
                    document_type=document_type,
                    quality=ExtractionQuality.CORRUPTED,
                    warning=f"Source file not found: {path_obj}"
                )
            if path_obj.suffix.lower() not in self.settings.SUPPORTED_FILE_TYPES:
                return self._create_error_result(
                    source_name=resolved_name,
                    document_type=document_type,
                    quality=ExtractionQuality.CORRUPTED,
                    warning=f"Unsupported file format '{path_obj.suffix}'. Allowed: {self.settings.SUPPORTED_FILE_TYPES}"
                )

        # Open document with PyMuPDF
        doc = None
        try:
            doc = self._open_fitz_document(source)
        except Exception as exc:
            return self._create_error_result(
                source_name=resolved_name,
                document_type=document_type,
                quality=ExtractionQuality.CORRUPTED,
                warning=f"Failed to read or parse PDF: {exc}"
            )

        try:
            # Check for encryption
            if doc.is_encrypted and doc.needs_pass:
                return self._create_error_result(
                    source_name=resolved_name,
                    document_type=document_type,
                    quality=ExtractionQuality.CORRUPTED,
                    warning="PDF document is password-protected or encrypted"
                )

            # Check for 0-page documents
            if doc.page_count == 0:
                return self._create_error_result(
                    source_name=resolved_name,
                    document_type=document_type,
                    quality=ExtractionQuality.EMPTY,
                    warning="PDF document contains 0 pages"
                )

            # Extract page by page
            pages: List[PageExtraction] = []
            all_blocks: List[TextBlock] = []

            for page_idx in range(len(doc)):
                page_num = page_idx + 1  # 1-indexed
                page = doc[page_idx]

                # Check for images on page
                images = page.get_images()
                has_images = len(images) > 0

                # Extract text
                page_raw_text = page.get_text("text") or ""

                # Extract text blocks: tuple (x0, y0, x1, y1, text, block_no, block_type)
                raw_blocks = page.get_text("blocks") or []
                page_blocks: List[TextBlock] = []

                for block in raw_blocks:
                    if len(block) >= 7:
                        x0, y0, x1, y1, b_text, b_no, b_type = block[:7]
                        # block_type 0 = text, block_type 1 = image
                        if b_type == 1:
                            has_images = True
                            continue
                        if b_type == 0 and b_text.strip():
                            tb = TextBlock(
                                text=b_text.strip(),
                                page_number=page_num,
                                block_number=int(b_no),
                                bbox=(float(x0), float(y0), float(x1), float(y1))
                            )
                            page_blocks.append(tb)

                # FIX 1: Preserve visual reading order by sorting blocks (y0 ascending, then x0 ascending)
                page_blocks.sort(
                    key=lambda b: (
                        b.bbox[1] if b.bbox else 0.0,
                        b.bbox[0] if b.bbox else 0.0
                    )
                )
                all_blocks.extend(page_blocks)

                page_extraction = PageExtraction(
                    page_number=page_num,
                    text=page_raw_text,
                    character_count=len(page_raw_text),
                    text_blocks=page_blocks,
                    has_images=has_images
                )
                pages.append(page_extraction)

            # Assemble full document text
            full_text = "\n\n".join(p.text for p in pages).strip()
            total_chars = len(full_text)

            # Quality Assessment
            status, quality, warnings = self._assess_quality(
                doc_pages=pages,
                total_chars=total_chars,
                full_text=full_text
            )

            return PDFExtractionResult(
                source_file=resolved_name,
                document_type=document_type,
                page_count=len(pages),
                pages=pages,
                text=full_text,
                text_blocks=all_blocks,
                character_count=total_chars,
                extraction_status=status,
                extraction_method="pymupdf_text",
                extraction_quality=quality,
                warnings=warnings
            )

        finally:
            if doc is not None:
                doc.close()

    def extract_batch(
        self,
        sources: List[Union[str, Path, bytes, BinaryIO]],
        document_type: DocumentType = DocumentType.RESUME,
        source_names: Optional[List[str]] = None
    ) -> BatchExtractionResult:
        """Extract a batch of PDF documents with fault isolation.

        One failed or corrupt PDF will NOT halt execution of the remaining files.
        Enforces MAX_RESUME_COUNT constraint from settings.

        Args:
            sources: List of files, paths, or byte streams.
            document_type: DocumentType category.
            source_names: Optional list of corresponding filenames.

        Returns:
            BatchExtractionResult with individual documents and aggregate summary metrics.

        Raises:
            ValueError: If the number of sources exceeds MAX_RESUME_COUNT.
        """
        # Enforce MAX_RESUME_COUNT
        if len(sources) > self.settings.MAX_RESUME_COUNT:
            raise ValueError(
                f"Batch size ({len(sources)}) exceeds maximum allowed resume count ({self.settings.MAX_RESUME_COUNT})."
            )

        results: List[PDFExtractionResult] = []

        for idx, src in enumerate(sources):
            # Unnamed byte/stream sources receive unique names (e.g. document_001.pdf, document_002.pdf)
            if source_names and idx < len(source_names):
                name = source_names[idx]
            elif isinstance(src, (str, Path)):
                name = Path(src).name
            else:
                name = f"document_{idx + 1:03d}.pdf"

            try:
                res = self.extract(source=src, document_type=document_type, source_name=name)
                results.append(res)
            except Exception as unhandled_exc:
                results.append(
                    self._create_error_result(
                        source_name=name,
                        document_type=document_type,
                        quality=ExtractionQuality.CORRUPTED,
                        warning=f"Unexpected extraction error: {unhandled_exc}"
                    )
                )

        summary = BatchExtractionSummary(
            processed=len(results),
            successful=sum(1 for r in results if r.extraction_status == ExtractionStatus.SUCCESS),
            low_quality=sum(1 for r in results if r.extraction_status == ExtractionStatus.LOW_QUALITY),
            failed=sum(1 for r in results if r.extraction_status == ExtractionStatus.FAILED),
        )

        return BatchExtractionResult(summary=summary, documents=results)

    def _assess_quality(
        self,
        doc_pages: List[PageExtraction],
        total_chars: int,
        full_text: str
    ) -> Tuple[ExtractionStatus, ExtractionQuality, List[str]]:
        """Assess the readability, completeness, and cleanliness of extracted text."""
        warnings: List[str] = []
        any_images = any(p.has_images for p in doc_pages)

        # 1. Zero extractable text across entire document
        if total_chars == 0:
            if any_images:
                warnings.append("Document appears to be scanned or image-only; no extractable text found (OCR required).")
                return ExtractionStatus.LOW_QUALITY, ExtractionQuality.NEEDS_OCR, warnings
            else:
                warnings.append("Document contains no extractable text content.")
                return ExtractionStatus.FAILED, ExtractionQuality.EMPTY, warnings

        status = ExtractionStatus.SUCCESS
        quality = ExtractionQuality.HIGH

        # 2. FIX 2: Per-page scan-quality escalation (detect mixed scanned/text documents)
        suspicious_pages = [
            p.page_number for p in doc_pages
            if p.has_images and p.character_count < self.settings.EMPTY_PAGE_CHAR_THRESHOLD
        ]
        if suspicious_pages:
            pages_str = ", ".join(str(pn) for pn in suspicious_pages)
            warnings.append(
                f"Pages [{pages_str}] appear to be scanned or image-only with insufficient extractable text (OCR required)."
            )
            # If all or majority (>= 50%) of pages are suspicious, classify as NEEDS_OCR / LOW_QUALITY
            if len(suspicious_pages) >= len(doc_pages) / 2:
                status = ExtractionStatus.LOW_QUALITY
                quality = ExtractionQuality.NEEDS_OCR
            else:
                # Document has suspicious pages; quality cannot remain HIGH
                quality = ExtractionQuality.MEDIUM

        # 3. Very low character count (below threshold)
        if total_chars < self.settings.MIN_EXTRACTION_CHAR_COUNT:
            if any_images:
                status = ExtractionStatus.LOW_QUALITY
                quality = ExtractionQuality.NEEDS_OCR
                warnings.append(
                    f"Extracted character count ({total_chars}) is below minimum threshold ({self.settings.MIN_EXTRACTION_CHAR_COUNT}) "
                    f"and embedded images were detected; OCR may be required."
                )
            else:
                status = ExtractionStatus.LOW_QUALITY
                quality = ExtractionQuality.LOW
                warnings.append(
                    f"Insufficient text content: extracted {total_chars} characters "
                    f"(minimum required is {self.settings.MIN_EXTRACTION_CHAR_COUNT})."
                )

        # 4. Non-alphabetic ratio check (symbol corruption, binary artifacts, font encoding issues)
        alpha_count = sum(c.isalpha() for c in full_text)
        alpha_ratio = alpha_count / total_chars if total_chars > 0 else 0.0

        if alpha_ratio < self.settings.MIN_ALPHA_RATIO:
            status = ExtractionStatus.LOW_QUALITY
            quality = ExtractionQuality.LOW
            warnings.append(
                f"Low alphabetic character ratio ({alpha_ratio:.1%}, minimum expected {self.settings.MIN_ALPHA_RATIO:.1%}); "
                f"excessive non-alphabetic symbols or potential encoding corruption detected."
            )

        # 5. Suspiciously empty pages in multi-page document (pages without images but empty text)
        if len(doc_pages) > 1:
            empty_text_only_pages = [
                p.page_number for p in doc_pages
                if not p.has_images and p.character_count < self.settings.EMPTY_PAGE_CHAR_THRESHOLD
            ]
            if empty_text_only_pages:
                pages_str = ", ".join(str(pn) for pn in empty_text_only_pages)
                warnings.append(
                    f"Pages [{pages_str}] contain suspiciously low or empty text without images."
                )
                if status == ExtractionStatus.SUCCESS and quality == ExtractionQuality.HIGH:
                    quality = ExtractionQuality.MEDIUM

        return status, quality, warnings

    def _open_fitz_document(self, source: Union[str, Path, bytes, BinaryIO]) -> fitz.Document:
        """Internal helper to load a PyMuPDF Document instance from various sources."""
        if isinstance(source, (str, Path)):
            return fitz.open(str(source))
        elif isinstance(source, bytes):
            return fitz.open(stream=source, filetype="pdf")
        elif hasattr(source, "read"):
            data = source.read()
            return fitz.open(stream=data, filetype="pdf")
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    def _resolve_source_name(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        explicit_name: Optional[str],
        default_fallback: str = "document_001.pdf"
    ) -> str:
        """Derive a readable filename from input source."""
        if explicit_name:
            return explicit_name
        if isinstance(source, (str, Path)):
            return Path(source).name
        return default_fallback

    def _create_error_result(
        self,
        source_name: str,
        document_type: DocumentType,
        quality: ExtractionQuality,
        warning: str
    ) -> PDFExtractionResult:
        """Factory for failed or corrupted document extraction results."""
        return PDFExtractionResult(
            source_file=source_name,
            document_type=document_type,
            page_count=0,
            pages=[],
            text="",
            text_blocks=[],
            character_count=0,
            extraction_status=ExtractionStatus.FAILED,
            extraction_method="pymupdf_text",
            extraction_quality=quality,
            warnings=[warning]
        )
