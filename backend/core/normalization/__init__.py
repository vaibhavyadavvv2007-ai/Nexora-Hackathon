from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from backend.models.enums import SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.skill import Skill


class BaseNormalizer(ABC):
    """Abstract interface for text normalization, sectioning, and skill alias resolution."""

    @abstractmethod
    def segment_sections(self, raw_text: str) -> Dict[SectionType, str]:
        """Classify and partition document text into structural sections.

        Args:
            raw_text: Full unpartitioned document string.

        Returns:
            Mapping of recognized SectionType to raw section text.
        """
        raise NotImplementedError

    @abstractmethod
    def chunk_evidence(
        self,
        section_text: str,
        section_type: SectionType,
        source_file: str,
        base_page: int = 1
    ) -> List[EvidenceChunk]:
        """Segment section text into discrete evidence chunks (sentences/bullets).

        Args:
            section_text: Raw text of the given section.
            section_type: Section classification.
            source_file: Name of origin document.
            base_page: Approximate starting page.

        Returns:
            List of parsed EvidenceChunk instances with metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize_skill(self, surface_token: str) -> Optional[Skill]:
        """Resolve a raw skill mention against the canonical skill ontology/aliases.

        Args:
            surface_token: Raw text token or n-gram (e.g. 'k8s', 'ReactJS').

        Returns:
            Canonicalized Skill instance, or None if not recognized as a skill.
        """
        raise NotImplementedError
