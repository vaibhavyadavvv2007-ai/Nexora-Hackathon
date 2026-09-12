from enum import Enum


class RequirementType(str, Enum):
    """Categorization of JD requirements."""
    REQUIRED = "required"
    PREFERRED = "preferred"
    RESPONSIBILITY = "responsibility"


class MatchType(str, Enum):
    """Origin and methodology of matched skill or semantic evidence."""
    EXACT = "exact"
    ALIAS = "alias"
    PHRASE = "phrase"
    FUZZY = "fuzzy"
    SEMANTIC_EXACT = "semantic_exact"
    SEMANTIC_RELATED = "semantic_related"
    SEMANTIC_INFERRED = "semantic_inferred"
    LEXICAL = "lexical"
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN = "unknown"


class SectionType(str, Enum):
    """Recognized resume and document sections."""
    EXPERIENCE = "experience"
    SKILLS = "skills"
    PROJECTS = "projects"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    SUMMARY = "summary"
    HEADER = "header"
    OTHER = "other"


class DocumentType(str, Enum):
    """Target category for parsed PDF documents."""
    JOB_DESCRIPTION = "job_description"
    RESUME = "resume"
    UNKNOWN = "unknown"


class ExtractionStatus(str, Enum):
    """Macro status of the PDF extraction."""
    SUCCESS = "SUCCESS"
    LOW_QUALITY = "LOW_QUALITY"
    FAILED = "FAILED"


class ExtractionQuality(str, Enum):
    """Detailed quality assessment of extracted text content."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEEDS_OCR = "NEEDS_OCR"
    EMPTY = "EMPTY"
    CORRUPTED = "CORRUPTED"

