"""Developer inspection utility for structured document parsing output.

Provides programmatic and CLI inspection of parsed Job Descriptions and Resumes as readable JSON.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, BinaryIO, Dict, Union

from backend.core.normalization.skill_normalizer import SkillNormalizer
from backend.core.parsing.jd_parser import JobDescriptionParser
from backend.core.parsing.pdf_extractor import PDFExtractor
from backend.core.parsing.resume_parser import ResumeParser
from backend.models.document import JobDescription, Resume
from backend.models.enums import DocumentType
from backend.models.pdf_extraction import PDFExtractionResult


def inspect_job_description(
    source: Union[str, Path, BinaryIO, PDFExtractionResult],
    jd_id: str = "jd_inspect",
) -> str:
    """Process a JD PDF or extraction result and return structured parser output as formatted JSON.

    Args:
        source: File path, stream, or existing PDFExtractionResult.
        jd_id: Identifier for the job description.

    Returns:
        Indented JSON string containing extracted requirements, responsibilities, chunks, pages, and confidence.
    """
    if isinstance(source, PDFExtractionResult):
        extraction = source
    else:
        extractor = PDFExtractor()
        extraction = extractor.extract(source, document_type=DocumentType.JOB_DESCRIPTION)

    parser = JobDescriptionParser()
    jd: JobDescription = parser.parse(extraction, jd_id=jd_id)
    return jd.model_dump_json(indent=2)


def inspect_resume(
    source: Union[str, Path, BinaryIO, PDFExtractionResult],
    candidate_id: str = "cand_inspect",
) -> str:
    """Process a Resume PDF or extraction result and return structured parser output as formatted JSON.

    Args:
        source: File path, stream, or existing PDFExtractionResult.
        candidate_id: Identifier for the candidate.

    Returns:
        Indented JSON string containing candidate name, sections, skills, chunks, pages, and confidence.
    """
    if isinstance(source, PDFExtractionResult):
        extraction = source
    else:
        extractor = PDFExtractor()
        extraction = extractor.extract(source, document_type=DocumentType.RESUME)

    parser = ResumeParser()
    resume: Resume = parser.parse(extraction, candidate_id=candidate_id)
    return resume.model_dump_json(indent=2)


def inspect_document(
    source: Union[str, Path, BinaryIO, PDFExtractionResult],
    doc_type: Union[DocumentType, str] = DocumentType.RESUME,
    doc_id: str = "inspect_001",
) -> str:
    """Process any document (JD or Resume) and return structured parser output as formatted JSON."""
    type_val = doc_type.value if isinstance(doc_type, DocumentType) else str(doc_type).lower()
    if type_val in ("job_description", "jd"):
        return inspect_job_description(source, jd_id=doc_id)
    elif type_val in ("resume", "cv"):
        return inspect_resume(source, candidate_id=doc_id)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}. Must be 'job_description' or 'resume'.")


def main() -> None:
    """CLI entrypoint for inspecting PDF parsing results."""
    parser = argparse.ArgumentParser(
        description="Inspect structured parser output (requirements, skills, sections, chunks, pages) as JSON."
    )
    parser.add_argument("pdf_path", type=str, help="Path to PDF file to inspect.")
    parser.add_argument(
        "--type",
        "-t",
        dest="doc_type",
        choices=["jd", "job_description", "resume", "cv"],
        default="resume",
        help="Type of document (default: resume)",
    )
    parser.add_argument("--id", dest="doc_id", default="inspect_doc", help="Identifier for the document model.")
    parser.add_argument("--output", "-o", dest="output_file", type=str, default=None, help="Optional output JSON file path.")

    args = parser.parse_args()

    try:
        json_output = inspect_document(args.pdf_path, doc_type=args.doc_type, doc_id=args.doc_id)
        if args.output_file:
            Path(args.output_file).write_text(json_output, encoding="utf-8")
            print(f"Structured inspection result written to {args.output_file}")
        else:
            print(json_output)
    except Exception as exc:
        print(f"Error inspecting document: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
