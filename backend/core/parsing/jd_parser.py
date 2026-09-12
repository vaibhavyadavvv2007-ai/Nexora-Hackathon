import re
from typing import List, Optional
from backend.core.exceptions import DocumentParsingError
from backend.core.normalization.skill_normalizer import SkillNormalizer
from backend.core.parsing.section_classifier import SectionClassifier
from backend.models.document import JobDescription
from backend.models.enums import ExtractionStatus, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.pdf_extraction import PDFExtractionResult
from backend.models.requirement import Requirement


class JobDescriptionParser:
    """Parses a Job Description PDFExtractionResult into a structured JobDescription model."""

    def __init__(self, skill_normalizer: Optional[SkillNormalizer] = None):
        self.normalizer = skill_normalizer or SkillNormalizer()

    def parse(self, extraction: PDFExtractionResult, jd_id: str = "jd_001") -> JobDescription:
        """Parse structured JD requirements from a PDFExtractionResult.

        The canonical source of truth for all requirements is `JobDescription.requirements`.
        Rejects documents with extraction_status == FAILED.
        """
        # Critical Fix C1: Reject failed extractions
        if extraction.extraction_status == ExtractionStatus.FAILED:
            reason = (
                extraction.warnings[0]
                if extraction.warnings
                else f"Document extraction status is FAILED (quality: {extraction.extraction_quality})"
            )
            raise DocumentParsingError(
                source_file=extraction.source_file,
                extraction_status=extraction.extraction_status,
                reason=reason,
            )

        raw_text = extraction.text
        source_file = extraction.source_file

        role_title = self._extract_role_title(extraction)
        requirements: List[Requirement] = []
        responsibilities: List[str] = []
        requirement_chunks: List[EvidenceChunk] = []

        # Iterate through ordered text blocks from Phase 2
        current_tier: Optional[RequirementType] = None
        req_counter = 1
        chunk_counter = 1

        for block in extraction.text_blocks:
            lines = [ln.strip() for ln in block.text.split("\n") if ln.strip()]
            page_num = block.page_number

            for line in lines:
                # Check if line indicates non-requirement section (e.g. Soft Skills, About the Role)
                if SectionClassifier.is_non_requirement_jd_header(line):
                    current_tier = None
                    continue

                # Check if line is a tier header (e.g. "Requirements:", "Preferred Qualifications:")
                detected_tier = SectionClassifier.classify_jd_header(line)
                if detected_tier is not None:
                    current_tier = detected_tier
                    continue

                # Filter out pure headers/separators
                if len(line) < 3 or line.startswith("===") or line.startswith("---"):
                    continue

                # Skip header/introductory metadata lines before the first requirement tier or in non-requirement sections
                if current_tier is None:
                    continue

                # If we have a line of text, process it under current tier
                tier = current_tier
                confidence = 0.95

                # Look for skill mentions to establish canonical requirements
                skills_in_line = self.normalizer.extract_skills_from_text(
                    text=line,
                    section=SectionType.OTHER,
                    source_page=page_num,
                )
                # Deduplicate skills mentioned within the same line
                unique_skills = self.normalizer.deduplicate_skills(skills_in_line)

                if unique_skills:
                    # Named/normalizable technical skill requirement
                    for sk in unique_skills:
                        req_id = f"req_{req_counter:04d}"
                        req = Requirement(
                            id=req_id,
                            name=sk.canonical_name.title(),
                            type=tier,
                            canonical_name=sk.canonical_name,
                            weight=1.0,
                            critical=(tier == RequirementType.REQUIRED),
                            source_text=line,
                            source_page=page_num,
                            confidence=confidence,
                            is_skill_matchable=True,
                        )
                        requirements.append(req)
                        req_counter += 1
                else:
                    # Contextual, experience-related, or education requirement (NOT skill-matchable)
                    canonical_key = self._slugify(line[:40])
                    req_id = f"req_{req_counter:04d}"
                    req = Requirement(
                        id=req_id,
                        name=line[:50].strip(),
                        type=tier,
                        canonical_name=canonical_key,
                        weight=1.0,
                        critical=(tier == RequirementType.REQUIRED),
                        source_text=line,
                        source_page=page_num,
                        confidence=confidence * 0.8,
                        is_skill_matchable=False,
                    )
                    requirements.append(req)
                    req_counter += 1

                # If responsibility, add to responsibilities list
                if tier == RequirementType.RESPONSIBILITY:
                    responsibilities.append(line)

                # Create an evidence chunk preserving Phase 2 page number
                chunk = EvidenceChunk(
                    id=f"jd_chunk_{chunk_counter:04d}",
                    text=line,
                    section=SectionType.OTHER,
                    page=page_num,
                    confidence=confidence,
                    source_file=source_file,
                )
                requirement_chunks.append(chunk)
                chunk_counter += 1

        return JobDescription(
            id=jd_id,
            role_title=role_title,
            source_file=source_file,
            raw_text=raw_text,
            requirements=requirements,
            responsibilities=responsibilities,
            requirement_chunks=requirement_chunks,
        )

    def _extract_role_title(self, extraction: PDFExtractionResult) -> str:
        """Heuristically extract the role title from early blocks or text without fabricating defaults."""
        for block in extraction.text_blocks[:4]:
            text = block.text.strip()
            # Explicit label match (e.g. "Job Title: Backend Engineer")
            match = re.search(r"^(?:job\s+title|role|position)\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

            for raw_line in text.split("\n"):
                line = raw_line.strip()
                title_candidate = line.split("|")[0].strip()
                # Recognize concise role-like titles
                role_keywords = (
                    "engineer", "developer", "architect", "lead", "manager", "specialist",
                    "scientist", "intern", "analyst", "designer", "consultant", "administrator"
                )
                if 4 <= len(title_candidate) <= 60 and any(kw in title_candidate.lower() for kw in role_keywords):
                    if not title_candidate.lower().startswith(("summary", "about", "company", "responsibilities", "requirements")):
                        return title_candidate

        # Never invent a generic role title; return empty string to indicate unknown
        return ""

    def _slugify(self, text: str) -> str:
        """Create a clean identifier from a text snippet."""
        clean = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[-\s]+", "_", clean) or "requirement"
