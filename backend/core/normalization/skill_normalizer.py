import re
from typing import Dict, List, Optional, Set, Tuple
from backend.models.enums import MatchType, SectionType
from backend.models.skill import Skill


class SkillNormalizer:
    """Conservative canonical skill normalizer and alias resolver.

    Maintains strict technology isolation (e.g. PostgreSQL != MongoDB, React Native != React, Express.js != Node.js),
    enforces deterministic section priority deduplication, and captures unknown technologies conservatively.
    """

    # Conservative Canonical Skill Ontology
    CANONICAL_SKILL_MAP: Dict[str, List[str]] = {
        "javascript": ["javascript", "js", "ecmascript", "es6", "es6+"],
        "typescript": ["typescript", "ts"],
        "python": ["python", "python3", "py"],
        "react": ["react", "react.js", "reactjs"],
        "react native": ["react native", "react-native"],
        "node.js": ["node.js", "nodejs", "node js", "node"],
        "express.js": ["express.js", "expressjs", "express js", "express"],
        "fastapi": ["fastapi", "fast api"],
        "flask": ["flask"],
        "django": ["django"],
        "postgresql": ["postgresql", "postgres", "psql"],
        "mongodb": ["mongodb", "mongo", "mongo db", "nosql/mongodb"],
        "mysql": ["mysql"],
        "sqlite": ["sqlite", "sqlite3"],
        "redis": ["redis"],
        "graphql": ["graphql", "gql"],
        "rest api": ["rest api", "rest apis", "restful api", "restful apis", "rest"],
        "docker": ["docker", "dockerfile", "docker compose", "containerization"],
        "kubernetes": ["kubernetes", "k8s"],
        "aws": ["aws", "amazon web services"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "git": ["git", "github", "gitlab", "version control"],
        "ci/cd": ["ci/cd", "cicd", "ci cd", "continuous integration", "continuous delivery"],
        "linux": ["linux", "unix", "bash", "shell scripting"],
        "sql": ["sql"],
        "html": ["html", "html5"],
        "css": ["css", "css3"],
        "tailwind css": ["tailwind", "tailwind css", "tailwindcss"],
        "next.js": ["next.js", "nextjs", "next js"],
        "scikit-learn": ["scikit-learn", "sklearn"],
        "pytorch": ["pytorch", "torch"],
        "tensorflow": ["tensorflow", "tf"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "jest": ["jest"],
        "mocha": ["mocha"],
        "agile": ["agile", "scrum", "agile/scrum"],
    }

    # Deterministic section hierarchy for deduplication: Experience/Projects > Skills > Certs > Summary > Education > Other
    SECTION_PRIORITY: Dict[SectionType, int] = {
        SectionType.EXPERIENCE: 5,
        SectionType.PROJECTS: 5,
        SectionType.SKILLS: 4,
        SectionType.CERTIFICATIONS: 3,
        SectionType.SUMMARY: 2,
        SectionType.EDUCATION: 1,
        SectionType.OTHER: 0,
        SectionType.HEADER: 0,
    }

    # Non-technical vocabulary to exclude from unknown-skill capture
    NON_TECH_STOPWORDS: Set[str] = {
        "and", "or", "the", "with", "in", "to", "for", "of", "by", "on", "at", "as", "an", "it",
        "years", "year", "month", "months", "experience", "strong", "excellent", "good",
        "knowledge", "proficient", "proficiency", "familiar", "familiarity", "basic",
        "intermediate", "advanced", "skills", "skill", "tools", "tool", "frameworks",
        "framework", "technologies", "technology", "languages", "language", "platforms",
        "platform", "various", "management", "communication", "team", "teams", "work",
        "developer", "engineer", "lead", "senior", "junior", "intern", "degree", "bachelor",
        "master", "phd", "university", "college", "school", "high", "building", "built",
        "developed", "maintaining", "maintained", "responsible", "responsibilities", "duties",
        "overview", "summary", "profile", "about", "me", "projects", "project", "education",
        "role", "title", "position", "qualifications", "requirements", "preferred",
    }

    def __init__(self):
        # Build reverse lookup and compiled regex patterns
        self.alias_to_canonical: Dict[str, str] = {}
        self._compiled_patterns: List[Tuple[re.Pattern, str, str]] = []

        # Sort aliases by length descending so multi-word aliases match before single-word substrings
        all_aliases = []
        for canonical, aliases in self.CANONICAL_SKILL_MAP.items():
            for alias in aliases:
                all_aliases.append((alias.lower(), canonical))
                self.alias_to_canonical[alias.lower()] = canonical

        all_aliases.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, canonical in all_aliases:
            # Escape for regex and enforce word boundaries while allowing sentence-ending punctuation
            escaped = re.escape(alias)
            pattern = re.compile(rf"(?<!\w)(?<!\w\.){escaped}(?!\w)(?!\.\w)", re.IGNORECASE)
            self._compiled_patterns.append((pattern, alias, canonical))

    def _clean_token(self, token: str) -> str:
        """Strip surrounding punctuation from a candidate skill token while preserving prefixes like .NET."""
        cleaned = token.strip()
        cleaned = re.sub(r"^[•\-\*–—▪▫►:;,\(\)\[\]{}]+", "", cleaned).strip()
        # Do not strip leading dot for .NET
        if not (cleaned.startswith(".") and len(cleaned) > 1 and cleaned[1:].isalpha()):
            cleaned = re.sub(r"^[\s.:;,\(\)\[\]{}]+", "", cleaned).strip()
        cleaned = re.sub(r"[\s.:;,\(\)\[\]{}]+$", "", cleaned).strip()
        return cleaned

    def _is_technology_like(self, token: str, in_skills_section: bool = False) -> bool:
        """Determine if a token represents an unknown technology conservatively."""
        cleaned = self._clean_token(token)
        if len(cleaned) < 2 or len(cleaned) > 35:
            return False
        if cleaned[0].isdigit():
            return False
        if cleaned.lower() in self.NON_TECH_STOPWORDS:
            return False

        # Known technology prefixes/symbols (e.g. .NET, C++, C#)
        if cleaned.startswith(".") and len(cleaned) > 1 and cleaned[1:].isalpha():
            return True
        if re.search(r"[A-Za-z]\+\+", cleaned) or re.search(r"[A-Za-z]#", cleaned):
            return True

        words = cleaned.split()
        if len(words) > 3:
            return False
        if any(w.lower() in self.NON_TECH_STOPWORDS for w in words):
            return False

        if in_skills_section:
            return True

        # In non-skills text (experience/projects), require title-case / uppercase / CamelCase
        if all(w[0].isupper() or w.isupper() for w in words if w):
            return True

        return False

    def normalize_token(
        self,
        token: str,
        section: SectionType = SectionType.SKILLS,
        source_page: int = 1,
        allow_unknown: bool = True,
    ) -> Optional[Skill]:
        """Normalize a single technology token against the canonical ontology or unknown-skill path.

        Args:
            token: Raw string token (e.g. 'Postgres', 'React.js', 'Terraform').
            section: Origin section.
            source_page: 1-indexed source PDF page number.
            allow_unknown: Whether to capture technology-like tokens not in curated ontology.

        Returns:
            Normalized Skill or None if not a recognized or technology-like skill.
        """
        cleaned = self._clean_token(token)
        cleaned_lower = cleaned.lower()

        if cleaned_lower in self.alias_to_canonical:
            canonical = self.alias_to_canonical[cleaned_lower]
            match_type = MatchType.EXACT if cleaned_lower == canonical else MatchType.ALIAS
            return Skill(
                canonical_name=canonical,
                surface_form=cleaned,
                match_type=match_type,
                confidence=1.0 if match_type == MatchType.EXACT else 0.95,
                section=section,
                source_page=source_page,
            )

        # Pattern-based matching for tokens containing punctuation (e.g. 'Node.js')
        for pattern, alias, canonical in self._compiled_patterns:
            if pattern.fullmatch(cleaned):
                match_type = MatchType.EXACT if alias == canonical else MatchType.ALIAS
                return Skill(
                    canonical_name=canonical,
                    surface_form=cleaned,
                    match_type=match_type,
                    confidence=1.0 if match_type == MatchType.EXACT else 0.95,
                    section=section,
                    source_page=source_page,
                )

        # Conservative unknown-skill capture path
        if allow_unknown and self._is_technology_like(cleaned, in_skills_section=(section == SectionType.SKILLS)):
            canonical_name = re.sub(r"[\s_-]+", "_", cleaned_lower) if " " in cleaned_lower else cleaned_lower
            return Skill(
                canonical_name=canonical_name,
                surface_form=cleaned,
                match_type=MatchType.LOW_CONFIDENCE,
                confidence=0.70,
                section=section,
                source_page=source_page,
            )

        return None

    def extract_skills_from_text(
        self,
        text: str,
        section: SectionType = SectionType.SKILLS,
        source_page: int = 1,
    ) -> List[Skill]:
        """Extract all recognized canonical and unknown technology skills from text.

        Args:
            text: Raw extracted text line, bullet, or block.
            section: Origin section.
            source_page: 1-indexed source page.

        Returns:
            List of detected Skill models with match metadata.
        """
        extracted: List[Skill] = []
        if not text.strip():
            return extracted

        matched_spans: List[Tuple[int, int]] = []

        # 1. Curated canonical skills
        for pattern, alias, canonical in self._compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                # Ensure no overlapping match on an already matched longer span
                if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
                    continue

                surface = match.group(0)
                matched_spans.append((start, end))

                match_type = MatchType.EXACT if surface.lower() == canonical else MatchType.ALIAS
                extracted.append(
                    Skill(
                        canonical_name=canonical,
                        surface_form=surface,
                        match_type=match_type,
                        confidence=1.0 if match_type == MatchType.EXACT else 0.95,
                        section=section,
                        source_page=source_page,
                    )
                )

        # 2. Conservative unknown-skill capture
        # If in skills section or text contains delimiter lists (commas, slashes, bullets)
        delimiters_present = bool(re.search(r"[,|;\n•▪▫►/()]", text)) or section == SectionType.SKILLS
        if delimiters_present:
            # Strip section header prefix if present (e.g. "Languages: Python, Go")
            content_to_split = text
            if ":" in text:
                header_part, rest = text.split(":", 1)
                if len(header_part.strip()) <= 30:
                    content_to_split = rest

            parts = re.split(r"[,|;\n•▪▫►/()]|\s+(?:and|&)\s+", content_to_split)
            for part in parts:
                cleaned_part = self._clean_token(part)
                if not cleaned_part:
                    continue

                # Check if already captured by curated matches
                already_matched = any(
                    s.surface_form.lower() == cleaned_part.lower() or s.canonical_name == cleaned_part.lower()
                    for s in extracted
                )
                if already_matched:
                    continue

                if self._is_technology_like(cleaned_part, in_skills_section=(section == SectionType.SKILLS)):
                    canonical_name = (
                        re.sub(r"[\s_-]+", "_", cleaned_part.lower())
                        if " " in cleaned_part
                        else cleaned_part.lower()
                    )
                    extracted.append(
                        Skill(
                            canonical_name=canonical_name,
                            surface_form=cleaned_part,
                            match_type=MatchType.LOW_CONFIDENCE,
                            confidence=0.70,
                            section=section,
                            source_page=source_page,
                        )
                    )

        return extracted

    def deduplicate_skills(self, skills: List[Skill]) -> List[Skill]:
        """Suppress duplicate skill mentions while enforcing deterministic section priority.

        Priority order:
            Experience / Projects (5) > Skills (4) > Certifications (3) > Summary (2) > Education (1) > Other (0).
        If priority is identical, the skill with higher confidence is preferred; otherwise first occurrence is preserved.
        """
        seen: Dict[str, Skill] = {}
        for skill in skills:
            canonical = skill.canonical_name
            if canonical not in seen:
                seen[canonical] = skill
            else:
                existing = seen[canonical]
                new_prio = self.SECTION_PRIORITY.get(skill.section, 0)
                existing_prio = self.SECTION_PRIORITY.get(existing.section, 0)
                if new_prio > existing_prio:
                    seen[canonical] = skill
                elif new_prio == existing_prio and skill.confidence > existing.confidence:
                    seen[canonical] = skill
        return list(seen.values())
