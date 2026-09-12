import re
from typing import Dict, List, Optional, Tuple
from backend.core.exceptions import DocumentParsingError
from backend.core.normalization.skill_normalizer import SkillNormalizer
from backend.core.parsing.section_classifier import SectionClassifier
from backend.models.document import Resume
from backend.models.enums import ExtractionStatus, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.pdf_extraction import PDFExtractionResult
from backend.models.skill import Skill


class ResumeParser:
    """Parses a candidate resume PDFExtractionResult into a structured Resume model."""

    BULLET_PATTERN = re.compile(r"^([•\-\*–—▪▫►]|\d+\.|\([a-zA-Z0-9]+\))\s*")

    def __init__(self, skill_normalizer: Optional[SkillNormalizer] = None):
        self.normalizer = skill_normalizer or SkillNormalizer()

    def parse(self, extraction: PDFExtractionResult, candidate_id: str = "cand_001") -> Resume:
        """Parse structured sections, skills, and evidence chunks from PDFExtractionResult.

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

        candidate_name = self._extract_candidate_name(extraction, candidate_id)

        # Segment blocks into sections while preserving page numbers
        sections_dict: Dict[SectionType, List[Tuple[str, int]]] = {st: [] for st in SectionType}
        current_section: SectionType = SectionType.SUMMARY  # Initial default section before headers

        all_evidence_chunks: List[EvidenceChunk] = []
        chunk_counter = 1

        for block in extraction.text_blocks:
            page_num = block.page_number
            raw_lines = [ln.strip() for ln in block.text.split("\n") if ln.strip()]

            current_item: List[str] = []

            def flush_item():
                nonlocal chunk_counter
                if current_item:
                    combined = " ".join(current_item).strip()
                    current_item.clear()
                    if len(combined) >= 3 and not (combined.startswith("===") or combined.startswith("---")):
                        sections_dict[current_section].append((combined, page_num))
                        chunk_conf = 0.95 if current_section != SectionType.OTHER else 0.60
                        all_evidence_chunks.append(
                            EvidenceChunk(
                                id=f"chunk_{chunk_counter:04d}",
                                text=combined,
                                section=current_section,
                                page=page_num,
                                confidence=chunk_conf,
                                source_file=source_file,
                            )
                        )
                        chunk_counter += 1

            for line in raw_lines:
                detected_section = SectionClassifier.classify_resume_header(line)
                if detected_section is not None:
                    flush_item()
                    current_section = detected_section
                    continue

                if len(line) < 2 or line.startswith("===") or line.startswith("---"):
                    continue

                if self.BULLET_PATTERN.match(line):
                    flush_item()
                    current_item.append(line)
                else:
                    current_item.append(line)

            flush_item()

        # Flatten sections into combined text dict
        sections_text: Dict[SectionType, str] = {}
        for st, lines_with_page in sections_dict.items():
            if lines_with_page:
                sections_text[st] = "\n".join(ln for ln, _ in lines_with_page)

        # Extract structured category lists
        experience_bullets = [ln for ln, _ in sections_dict.get(SectionType.EXPERIENCE, [])]
        project_bullets = [ln for ln, _ in sections_dict.get(SectionType.PROJECTS, [])]
        education_bullets = [ln for ln, _ in sections_dict.get(SectionType.EDUCATION, [])]
        summary_text = sections_text.get(SectionType.SUMMARY)

        # Extract normalized skills across document
        raw_skills: List[Skill] = []
        for st, lines_with_page in sections_dict.items():
            for line, page_num in lines_with_page:
                found_skills = self.normalizer.extract_skills_from_text(
                    text=line,
                    section=st,
                    source_page=page_num,
                )
                raw_skills.extend(found_skills)

        # Suppress duplicate skill mentions with deterministic section priority
        deduplicated_skills = self.normalizer.deduplicate_skills(raw_skills)

        return Resume(
            candidate_id=candidate_id,
            name=candidate_name,
            source_file=source_file,
            raw_text=raw_text,
            sections=sections_text,
            skills=deduplicated_skills,
            experience=experience_bullets,
            projects=project_bullets,
            education=education_bullets,
            summary=summary_text,
            evidence_chunks=all_evidence_chunks,
        )

    def _extract_candidate_name(self, extraction: PDFExtractionResult, candidate_id: str) -> str:
        """Heuristically identify the candidate name from top blocks on page 1."""
        page_1_blocks = [b for b in extraction.text_blocks if b.page_number == 1]
        for block in page_1_blocks[:3]:
            for raw_line in block.text.split("\n"):
                line = raw_line.strip().strip(":,")
                # Exclude emails, phone numbers, URLs, and section headers
                if "@" in line or "http" in line or re.search(r"\d{3}[-\s]?\d{3}", line):
                    continue
                if SectionClassifier.classify_resume_header(line):
                    continue
                # Candidate names typically have 2-4 words, 3-40 chars, letters/initials/hyphens
                words = line.split()
                if 2 <= len(words) <= 4 and 3 <= len(line) <= 40:
                    if all(re.match(r"^[A-Za-z\.\-']+$", w) for w in words):
                        return line

        return f"Candidate_{candidate_id}"
