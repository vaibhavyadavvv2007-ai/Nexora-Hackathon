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
