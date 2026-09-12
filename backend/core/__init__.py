"""Nexora Core Engine Package.

Contains modular engine abstractions:
- parsing: PDF extraction interfaces
- normalization: text segmentation and skill canonicalization interfaces
- matching: keyword and semantic matching interfaces
- ranking: score fusion and candidate ranking interfaces
- explanations: deterministic justification and pairwise comparison interfaces
- pipeline: end-to-end shortlisting pipeline orchestrator
"""

from backend.core.pipeline import ShortlistingPipeline, get_pipeline

__all__ = ["ShortlistingPipeline", "get_pipeline"]
