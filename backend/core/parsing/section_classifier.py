import re
from typing import Optional, Tuple
from backend.models.enums import RequirementType, SectionType


class SectionClassifier:
    """Classifies text lines and headings into structured resume and JD sections."""

    RESUME_SECTION_PATTERNS = [
        (SectionType.SUMMARY, re.compile(r"^(professional\s+summary|summary|profile|about\s+me|objective|executive\s+summary)\b[:\s-]*$", re.IGNORECASE)),
        (SectionType.EXPERIENCE, re.compile(r"^(work\s+experience|professional\s+experience|employment\s+history|employment|internships|experience|work\s+history)\b[:\s-]*$", re.IGNORECASE)),
        (SectionType.PROJECTS, re.compile(r"^(projects|technical\s+projects|academic\s+projects|personal\s+projects|key\s+projects)\b[:\s-]*$", re.IGNORECASE)),
        (SectionType.SKILLS, re.compile(r"^(technical\s+skills|core\s+competencies|skills\s*(&|and)?\s*tools|technologies|skills|proficiencies|tools)\b[:\s-]*$", re.IGNORECASE)),
        (SectionType.EDUCATION, re.compile(r"^(education\s*(&|and)?\s*credentials|academic\s+background|education|qualifications|academic\s+history|degrees)\b[:\s-]*$", re.IGNORECASE)),
        (SectionType.CERTIFICATIONS, re.compile(r"^(certifications|licenses|credentials|certificates)\b[:\s-]*$", re.IGNORECASE)),
    ]

    JD_TIER_PATTERNS = [
        (RequirementType.REQUIRED, re.compile(r"^(minimum\s+qualifications|basic\s+qualifications|must\s+have|required\s+qualifications|qualifications|requirements|required)\b[:\s-]*$", re.IGNORECASE)),
        (RequirementType.PREFERRED, re.compile(r"^(preferred\s+qualifications|nice\s+to\s+have|preferred|bonus\s+points|bonus|desired\s+skills|good\s+to\s+have|pluses)\b[:\s-]*$", re.IGNORECASE)),
        (RequirementType.RESPONSIBILITY, re.compile(r"^(responsibilities|what\s+you\s+will\s+do|what\s+you'll\s+do|key\s+responsibilities|duties|role\s+overview)\b[:\s-]*$", re.IGNORECASE)),
    ]

    @classmethod
    def classify_resume_header(cls, text: str) -> Optional[SectionType]:
        """Check if a text line matches a known resume section header."""
        cleaned = re.sub(r"^[\s#*\->]+", "", text).strip()
        # Header candidate: short line or heading
        if len(cleaned) > 50:
            return None

        for section_type, pattern in cls.RESUME_SECTION_PATTERNS:
            if pattern.match(cleaned):
                return section_type
        return None

    @classmethod
    def classify_jd_header(cls, text: str) -> Optional[RequirementType]:
        """Check if a text line matches a known JD requirement tier header."""
        cleaned = re.sub(r"^[\s#*\->]+", "", text).strip()
        if len(cleaned) > 50:
            return None

        for req_type, pattern in cls.JD_TIER_PATTERNS:
            if pattern.match(cleaned):
                return req_type
        return None
