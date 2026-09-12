"""Skill taxonomy: canonical aliases, related-skill graph, and surface normalisation.

Design policy
-------------
* **Aliases** are genuinely interchangeable names for the *same* technology.
  ``"k8s"`` ↔ ``"kubernetes"`` — matching either satisfies an explicit requirement
  for the canonical skill.
* **Related skills** are one-directional "provides evidence" edges.
  ``"express.js" → "node.js"`` means Express experience provides *semantic*
  evidence for Node.js competence, but does **not** satisfy an explicit
  Node.js requirement.
* Cross-domain databases (PostgreSQL / MongoDB) are **not** aliased and
  **not** related.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Canonical aliases  (canonical_key -> list of accepted surface forms)
# ---------------------------------------------------------------------------
# Surface forms are stored **lowercased**.  The canonical key itself is also
# a valid surface form (implicitly).

CANONICAL_ALIASES: Dict[str, List[str]] = {
    # Languages
    "python": ["py", "python3", "python 3"],
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "java": [],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp"],
    "go": ["golang"],
    "rust": [],
    "ruby": [],
    "php": [],
    "swift": [],
    "kotlin": [],
    "r": [],
    "scala": [],

    # Frontend frameworks
    "react": ["reactjs", "react.js"],
    "angular": ["angularjs", "angular.js"],
    "vue": ["vuejs", "vue.js"],
    "next.js": ["nextjs", "next"],
    "svelte": ["sveltejs"],

    # Backend frameworks
    "node.js": ["nodejs", "node"],
    "express.js": ["expressjs", "express"],
    "django": [],
    "flask": [],
    "fastapi": ["fast api"],
    "spring": ["spring boot", "springboot", "spring framework"],
    "rails": ["ruby on rails"],
    "asp.net": ["aspnet", "asp.net core"],

    # Databases
    "postgresql": ["postgres", "psql"],
    "mysql": ["my sql"],
    "mongodb": ["mongo"],
    "redis": [],
    "sqlite": [],
    "cassandra": [],
    "dynamodb": ["dynamo db", "amazon dynamodb"],
    "elasticsearch": ["elastic search", "elastic"],
    "neo4j": [],

    # Cloud & DevOps
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "docker": [],
    "kubernetes": ["k8s", "kube"],
    "terraform": [],
    "ansible": [],
    "jenkins": [],
    "github actions": ["gh actions"],
    "ci/cd": ["cicd", "ci cd", "continuous integration"],

    # Data & ML
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "pandas": [],
    "numpy": [],
    "spark": ["apache spark", "pyspark"],
    "kafka": ["apache kafka"],
    "airflow": ["apache airflow"],

    # Tools & Misc
    "git": [],
    "linux": [],
    "graphql": [],
    "rest api": ["restful api", "rest apis", "restful apis"],
    "grpc": [],
    "rabbitmq": ["rabbit mq"],
    "nginx": [],
    "html": ["html5"],
    "css": ["css3"],
    "sass": ["scss"],
    "webpack": [],
    "tailwind": ["tailwindcss", "tailwind css"],
    "bootstrap": [],
    "figma": [],
    "jira": [],
    "agile": ["scrum"],
}

# ---------------------------------------------------------------------------
# Related skills  (skill_A -> [skill_B, …])
# ---------------------------------------------------------------------------
# Means: experience with skill_A provides *related semantic evidence* for
# skill_B, but does NOT satisfy an explicit requirement for skill_B.

RELATED_SKILLS: Dict[str, List[str]] = {
    "express.js": ["node.js"],
    "next.js": ["react", "node.js"],
    "django": ["python"],
    "flask": ["python"],
    "fastapi": ["python"],
    "spring": ["java"],
    "rails": ["ruby"],
    "pytorch": ["python"],
    "tensorflow": ["python"],
    "react": ["javascript"],
    "angular": ["typescript", "javascript"],
    "vue": ["javascript"],
    "pandas": ["python"],
    "numpy": ["python"],
    "scikit-learn": ["python"],
    "pyspark": ["python", "spark"],
}

# ---------------------------------------------------------------------------
# Reverse-lookup caches (built once at import time)
# ---------------------------------------------------------------------------

# surface_form (lowered) -> canonical_key
_SURFACE_TO_CANONICAL: Dict[str, str] = {}

for _canon, _aliases in CANONICAL_ALIASES.items():
    _SURFACE_TO_CANONICAL[_canon] = _canon
    for _alias in _aliases:
        _SURFACE_TO_CANONICAL[_alias] = _canon

# canonical_key -> set of canonical_keys it is related to
_RELATED_CANONICAL: Dict[str, List[str]] = {}
for _src, _targets in RELATED_SKILLS.items():
    _src_canon = _SURFACE_TO_CANONICAL.get(_src, _src)
    resolved = []
    for _t in _targets:
        resolved.append(_SURFACE_TO_CANONICAL.get(_t, _t))
    _RELATED_CANONICAL[_src_canon] = resolved


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_COLLAPSE_RE = re.compile(r"[\s\-_]+")


def normalize_surface(token: str) -> str:
    """Lowercase, strip, and collapse whitespace / hyphens / underscores."""
    return _COLLAPSE_RE.sub(" ", token.strip().lower()).strip()


def resolve_canonical(surface: str) -> Optional[str]:
    """Return the canonical key for a surface form, or ``None``."""
    normed = normalize_surface(surface)
    return _SURFACE_TO_CANONICAL.get(normed)


def get_aliases(canonical_key: str) -> List[str]:
    """Return all known surface forms (including the canonical key itself)."""
    key = normalize_surface(canonical_key)
    if key not in CANONICAL_ALIASES:
        return [key]
    return [key] + CANONICAL_ALIASES[key]


def get_related_canonicals(canonical_key: str) -> List[str]:
    """Return canonical keys that *this* skill provides evidence for."""
    key = normalize_surface(canonical_key)
    return _RELATED_CANONICAL.get(key, [])
