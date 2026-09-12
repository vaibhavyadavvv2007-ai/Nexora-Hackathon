from pathlib import Path
from typing import List
import fitz
import pytest

from backend.config.settings import Settings
from backend.core.parsing.pdf_extractor import PDFExtractor
from backend.models.enums import DocumentType, ExtractionQuality, ExtractionStatus


# ---------------------------------------------------------------------------
# Synthetic PDF Generation Helpers
# ---------------------------------------------------------------------------

def create_synthetic_pdf(pages_text: List[str]) -> bytes:
    """Generate in-memory PDF bytes with the specified text for each page."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        if text.strip():
            page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_synthetic_image_only_pdf() -> bytes:
    """Generate in-memory PDF with an embedded image and zero extractable text."""
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 60), 1)
    pix.clear_with(200)
    page.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=pix)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def extractor() -> PDFExtractor:
    """PDFExtractor fixture with standard test settings."""
    settings = Settings(
        MIN_EXTRACTION_CHAR_COUNT=100,
        MIN_ALPHA_RATIO=0.40,
        EMPTY_PAGE_CHAR_THRESHOLD=10
    )
    return PDFExtractor(settings=settings)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_normal_single_page_pdf(extractor: PDFExtractor):
    """1. Normal single-page PDF with adequate text produces SUCCESS and HIGH quality."""
    text_content = (
        "Summary: Senior Software Engineer with deep expertise in Python, FastAPI, and Distributed Systems. "
        "Experienced in architecting scalable machine learning pipelines, building asynchronous APIs, and "
        "collaborating in agile product teams to deliver high-impact production software."
    )
    pdf_bytes = create_synthetic_pdf([text_content])

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="candidate_single_page.pdf"
    )

    assert result.source_file == "candidate_single_page.pdf"
    assert result.document_type == DocumentType.RESUME
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.character_count > 100
    assert result.extraction_status == ExtractionStatus.SUCCESS
    assert result.extraction_quality == ExtractionQuality.HIGH
    assert len(result.warnings) == 0

    # Verify blocks and page number
    assert len(result.text_blocks) > 0
    assert result.text_blocks[0].page_number == 1
    assert result.text_blocks[0].bbox is not None


def test_multi_page_pdf_page_numbers_preserved(extractor: PDFExtractor):
    """2. Multi-page PDF correctly preserves 1-indexed page numbers across pages and blocks."""
    page_1 = (
        "Page One Content: Professional Overview. Software Engineering experience spanning "
        "multiple technical domains including cloud infrastructure and backend API microservices."
    )
    page_2 = (
        "Page Two Content: Technical Projects and Architecture. Built full-stack applications "
        "using modern frontend frameworks, containerization tools, and automated CI/CD workflows."
    )
    page_3 = (
        "Page Three Content: Education and Certifications. Bachelor of Science in Computer Science. "
        "Certified in Cloud Architecture and Advanced Machine Learning Engineering."
    )
    pdf_bytes = create_synthetic_pdf([page_1, page_2, page_3])

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="candidate_three_pages.pdf"
    )

    assert result.page_count == 3
    assert len(result.pages) == 3
    assert [p.page_number for p in result.pages] == [1, 2, 3]

    # Verify each block corresponds to its source page
    p1_blocks = [b for b in result.text_blocks if b.page_number == 1]
    p2_blocks = [b for b in result.text_blocks if b.page_number == 2]
    p3_blocks = [b for b in result.text_blocks if b.page_number == 3]

    assert len(p1_blocks) > 0
    assert len(p2_blocks) > 0
    assert len(p3_blocks) > 0
    assert result.extraction_status == ExtractionStatus.SUCCESS


def test_empty_document(extractor: PDFExtractor):
    """3. Empty document with no text content generates FAILED status and EMPTY quality."""
    pdf_bytes = create_synthetic_pdf([""])  # 1 blank page

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="blank_resume.pdf"
    )

    assert result.character_count == 0
    assert result.extraction_status == ExtractionStatus.FAILED
    assert result.extraction_quality == ExtractionQuality.EMPTY
    assert any("no extractable text" in w.lower() for w in result.warnings)


def test_very_low_text_document(extractor: PDFExtractor):
    """4. Very low text document (below minimum character count) is marked LOW_QUALITY."""
    low_text = "Hello world."  # 12 characters, well below MIN_EXTRACTION_CHAR_COUNT (100)
    pdf_bytes = create_synthetic_pdf([low_text])

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="sparse_resume.pdf"
    )

    assert result.character_count < 100
    assert result.extraction_status == ExtractionStatus.LOW_QUALITY
    assert result.extraction_quality == ExtractionQuality.LOW
    assert any("below minimum" in w.lower() or "insufficient" in w.lower() for w in result.warnings)


def test_scanned_image_only_pdf_detection(extractor: PDFExtractor):
    """5. Scanned/image-only PDF is detected without crashing and marked NEEDS_OCR / LOW_QUALITY."""
    pdf_bytes = create_synthetic_image_only_pdf()

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="scanned_resume.pdf"
    )

    assert result.extraction_status == ExtractionStatus.LOW_QUALITY
    assert result.extraction_quality == ExtractionQuality.NEEDS_OCR
    assert any("ocr required" in w.lower() or "scanned" in w.lower() for w in result.warnings)


def test_excessive_non_alphabetic_content(extractor: PDFExtractor):
    """6. Document with excessive symbol/corrupted glyph content is flagged as LOW_QUALITY."""
    garbled_symbols = "###$$$%%%^^^&&&***((()))___+++=~`{}|:<>?[];',./1234567890" * 3  # > 100 chars, ~0% alpha
    pdf_bytes = create_synthetic_pdf([garbled_symbols])

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="corrupted_symbols.pdf"
    )

    assert result.extraction_status == ExtractionStatus.LOW_QUALITY
    assert any("low alphabetic character ratio" in w.lower() for w in result.warnings)


def test_invalid_pdf(extractor: PDFExtractor):
    """7. Invalid or malformed PDF bytes do not crash and return FAILED with CORRUPTED quality."""
    invalid_bytes = b"This is plainly not a valid PDF file stream at all."

    result = extractor.extract(
        source=invalid_bytes,
        document_type=DocumentType.RESUME,
        source_name="malformed.pdf"
    )

    assert result.extraction_status == ExtractionStatus.FAILED
    assert result.extraction_quality == ExtractionQuality.CORRUPTED
    assert result.character_count == 0
    assert any("failed to read" in w.lower() or "parse" in w.lower() for w in result.warnings)


def test_missing_file(extractor: PDFExtractor):
    """8. Missing file path returns FAILED status gracefully."""
    missing_path = Path("c:/non_existent_folder_xyz/missing_file.pdf")

    result = extractor.extract(
        source=missing_path,
        document_type=DocumentType.JOB_DESCRIPTION
    )

    assert result.extraction_status == ExtractionStatus.FAILED
    assert result.extraction_quality == ExtractionQuality.CORRUPTED
    assert any("not found" in w.lower() for w in result.warnings)


def test_batch_extraction_multiple_pdfs(extractor: PDFExtractor):
    """9. Batch extraction processes multiple resumes and aggregates summary metrics."""
    valid_text_1 = "Valid Resume One text with rich qualifications in backend Python engineering and cloud systems." * 2
    valid_text_2 = "Valid Resume Two text detailing extensive work in distributed databases and container pipelines." * 2
    valid_text_3 = "Valid Resume Three text showing expertise in API design, automated testing, and software reliability." * 2

    sources = [
        create_synthetic_pdf([valid_text_1]),
        create_synthetic_pdf([valid_text_2]),
        create_synthetic_pdf([valid_text_3]),
    ]
    names = ["resume_1.pdf", "resume_2.pdf", "resume_3.pdf"]

    batch_result = extractor.extract_batch(sources=sources, source_names=names)

    assert batch_result.summary.processed == 3
    assert batch_result.summary.successful == 3
    assert batch_result.summary.low_quality == 0
    assert batch_result.summary.failed == 0
    assert len(batch_result.documents) == 3


def test_one_failed_file_inside_valid_batch(extractor: PDFExtractor):
    """10. One corrupted file in a batch does not stop remaining valid resumes from being extracted."""
    valid_text = "Good Resume with sufficient text and solid technical credentials for software development." * 2
    low_text = "Too short."
    corrupt_bytes = b"Not a real PDF stream."

    sources = [
        create_synthetic_pdf([valid_text]),
        corrupt_bytes,
        create_synthetic_pdf([low_text])
    ]
    names = ["valid.pdf", "corrupt.pdf", "low_quality.pdf"]

    batch_result = extractor.extract_batch(sources=sources, source_names=names)

    assert batch_result.summary.processed == 3
    assert batch_result.summary.successful == 1
    assert batch_result.summary.failed == 1
    assert batch_result.summary.low_quality == 1

    # Check individual records
    assert batch_result.documents[0].extraction_status == ExtractionStatus.SUCCESS
    assert batch_result.documents[1].extraction_status == ExtractionStatus.FAILED
    assert batch_result.documents[2].extraction_status == ExtractionStatus.LOW_QUALITY


# ---------------------------------------------------------------------------
# Regression Tests for Phase 2 Review Fixes
# ---------------------------------------------------------------------------

def test_two_column_reading_order(extractor: PDFExtractor):
    """FIX 1: Two-column PDF blocks are sorted in visual reading order (y0 ascending, then x0 ascending)."""
    doc = fitz.open()
    page = doc.new_page()

    # Insert text blocks in deliberately scrambled order
    # Block 1: Right Lower
    page.insert_textbox(fitz.Rect(320, 300, 520, 400), "Right Lower: Projects and Achievements")
    # Block 2: Left Top
    page.insert_textbox(fitz.Rect(50, 80, 250, 180), "Left Top: Candidate Summary")
    # Block 3: Left Lower
    page.insert_textbox(fitz.Rect(50, 300, 250, 400), "Left Lower: Work Experience")
    # Block 4: Right Top
    page.insert_textbox(fitz.Rect(320, 80, 520, 180), "Right Top: Core Competencies")

    pdf_bytes = doc.tobytes()
    doc.close()

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="two_column_resume.pdf"
    )

    assert len(result.text_blocks) == 4

    # Verify blocks are sorted by y0 then x0:
    # 1. Left Top (y0=80, x0=50)
    # 2. Right Top (y0=80, x0=320)
    # 3. Left Lower (y0=300, x0=50)
    # 4. Right Lower (y0=300, x0=320)
    assert result.text_blocks[0].text.startswith("Left Top")
    assert result.text_blocks[1].text.startswith("Right Top")
    assert result.text_blocks[2].text.startswith("Left Lower")
    assert result.text_blocks[3].text.startswith("Right Lower")

    # Spatial check: y0 must be non-decreasing, and if y0 is equal, x0 must be increasing
    for i in range(len(result.text_blocks) - 1):
        curr_bbox = result.text_blocks[i].bbox
        next_bbox = result.text_blocks[i + 1].bbox
        assert curr_bbox is not None and next_bbox is not None
        # Either next block is lower on page, or at same vertical level but further right
        assert (next_bbox[1] > curr_bbox[1]) or (
            abs(next_bbox[1] - curr_bbox[1]) < 1.0 and next_bbox[0] >= curr_bbox[0]
        )


def test_mixed_scanned_text_document(extractor: PDFExtractor):
    """FIX 2: Partially scanned document (Page 1 text, Pages 2 & 3 image-only) escalates quality and identifies pages."""
    doc = fitz.open()

    # Page 1: Normal clean text with ample characters
    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "Candidate Summary: Senior Software Engineer with substantial experience in backend systems. "
        "Proficient in Python, API design, database modeling, and automated cloud deployments."
    )

    # Page 2: Image-only (zero extractable text)
    p2 = doc.new_page()
    pix2 = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 1)
    pix2.clear_with(220)
    p2.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=pix2)

    # Page 3: Image-only (zero extractable text)
    p3 = doc.new_page()
    pix3 = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 1)
    pix3.clear_with(220)
    p3.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=pix3)

    pdf_bytes = doc.tobytes()
    doc.close()

    result = extractor.extract(
        source=pdf_bytes,
        document_type=DocumentType.RESUME,
        source_name="mixed_scanned_resume.pdf"
    )

    # Quality must NOT remain HIGH
    assert result.extraction_quality != ExtractionQuality.HIGH
    assert result.extraction_quality == ExtractionQuality.NEEDS_OCR
    assert result.extraction_status == ExtractionStatus.LOW_QUALITY

    # Explicit warning must identify affected page numbers (2 and 3)
    assert any("2" in w and "3" in w for w in result.warnings)
    assert any("ocr required" in w.lower() for w in result.warnings)


def test_unnamed_byte_sources_unique_names_in_batch(extractor: PDFExtractor):
    """Small Fix 1: Unnamed byte/stream sources receive unique names: document_001.pdf, document_002.pdf."""
    text_1 = "Valid document one with sufficient content for testing." * 3
    text_2 = "Valid document two with sufficient content for testing." * 3

    sources = [
        create_synthetic_pdf([text_1]),
        create_synthetic_pdf([text_2])
    ]

    batch_result = extractor.extract_batch(sources=sources)

    assert len(batch_result.documents) == 2
    assert batch_result.documents[0].source_file == "document_001.pdf"
    assert batch_result.documents[1].source_file == "document_002.pdf"


def test_batch_enforces_max_resume_count():
    """Small Fix 2: Batch extraction raises ValueError when source count exceeds MAX_RESUME_COUNT."""
    custom_settings = Settings(
        MAX_RESUME_COUNT=2,
        MIN_EXTRACTION_CHAR_COUNT=50
    )
    strict_extractor = PDFExtractor(settings=custom_settings)

    sources = [
        create_synthetic_pdf(["Sample resume text 1 " * 5]),
        create_synthetic_pdf(["Sample resume text 2 " * 5]),
        create_synthetic_pdf(["Sample resume text 3 " * 5])
    ]

    with pytest.raises(ValueError) as exc_info:
        strict_extractor.extract_batch(sources=sources)

    assert "exceeds maximum allowed resume count (2)" in str(exc_info.value)


def test_encrypted_pdf_handling(extractor: PDFExtractor):
    """Small Fix 3: Encrypted/password-protected PDF is caught and returned as FAILED / CORRUPTED."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Confidential applicant dossier content.")
    encrypted_bytes = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secure_password_123",
        owner_pw="admin_owner_pwd"
    )
    doc.close()

    result = extractor.extract(
        source=encrypted_bytes,
        document_type=DocumentType.RESUME,
        source_name="password_protected.pdf"
    )

    assert result.extraction_status == ExtractionStatus.FAILED
    assert result.extraction_quality == ExtractionQuality.CORRUPTED
    assert any("password" in w.lower() or "encrypted" in w.lower() for w in result.warnings)

