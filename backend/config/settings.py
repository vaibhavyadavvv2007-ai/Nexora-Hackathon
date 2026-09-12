from functools import lru_cache
from typing import List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application and ranking configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NEXORA_",
        env_file=".env",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Nexora Smart Shortlisting Engine"
    DEBUG: bool = False

    # Document Extraction & Constraints
    MIN_EXTRACTION_CHAR_COUNT: int = Field(
        default=100,
        description="Minimum character length for valid extracted document content",
        ge=10
    )
    MAX_RESUME_COUNT: int = Field(
        default=25,
        description="Maximum number of resumes processed in a single batch",
        ge=1,
        le=100
    )
    SUPPORTED_FILE_TYPES: List[str] = Field(
        default=[".pdf"],
        description="List of allowed document extensions"
    )

    # Embedding & Semantic Matching (Configurable placeholders)
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model tag for local sentence embedding"
    )
    SEMANTIC_SIMILARITY_THRESHOLD: float = Field(
        default=0.55,
        description="Baseline cosine similarity threshold for semantic candidate evidence",
        ge=0.0,
        le=1.0
    )
    SEMANTIC_EXACT_THRESHOLD: float = Field(
        default=0.85,
        description="Threshold for semantic equivalence to exact concept",
        ge=0.0,
        le=1.0
    )
    SEMANTIC_INFERRED_THRESHOLD: float = Field(
        default=0.45,
        description="Threshold for weak/inferred semantic correlation",
        ge=0.0,
        le=1.0
    )

    # Lexical / Fuzzy Matching
    FUZZY_MATCH_THRESHOLD: float = Field(
        default=85.0,
        description="RapidFuzz ratio cutoff for alias/spelling variations",
        ge=50.0,
        le=100.0
    )

    # Scoring Weights (Configurable placeholders, must sum to 1.0)
    WEIGHT_REQUIRED_SKILL_COVERAGE: float = Field(
        default=0.35,
        description="Weight for explicit named required skill coverage",
        ge=0.0,
        le=1.0
    )
    WEIGHT_SEMANTIC_ALIGNMENT: float = Field(
        default=0.35,
        description="Weight for semantic requirement-to-evidence alignment",
        ge=0.0,
        le=1.0
    )
    WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE: float = Field(
        default=0.20,
        description="Weight for BM25/lexical context relevance",
        ge=0.0,
        le=1.0
    )
    WEIGHT_PREFERRED_SKILL_COVERAGE: float = Field(
        default=0.10,
        description="Weight for explicit named preferred skill coverage",
        ge=0.0,
        le=1.0
    )

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "Settings":
        total = (
            self.WEIGHT_REQUIRED_SKILL_COVERAGE
            + self.WEIGHT_SEMANTIC_ALIGNMENT
            + self.WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE
            + self.WEIGHT_PREFERRED_SKILL_COVERAGE
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Scoring weights must sum to 1.0 (currently {total:.4f})")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton provider."""
    return Settings()
