import pytest
from pydantic import ValidationError
from backend.config.settings import Settings


def test_default_settings():
    """Verify default settings instantiation and weight totals."""
    settings = Settings()
    assert settings.APP_NAME == "Nexora Smart Shortlisting Engine"
    assert settings.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.MIN_EXTRACTION_CHAR_COUNT == 100
    assert settings.MAX_RESUME_COUNT == 25
    assert ".pdf" in settings.SUPPORTED_FILE_TYPES

    # Verify weights sum
    total = (
        settings.WEIGHT_REQUIRED_SKILL_COVERAGE
        + settings.WEIGHT_SEMANTIC_ALIGNMENT
        + settings.WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE
        + settings.WEIGHT_PREFERRED_SKILL_COVERAGE
    )
    assert pytest.approx(total, 0.0001) == 1.0


def test_custom_valid_weights():
    """Verify customizable weights are accepted when summing to 1.0."""
    custom = Settings(
        WEIGHT_REQUIRED_SKILL_COVERAGE=0.40,
        WEIGHT_SEMANTIC_ALIGNMENT=0.30,
        WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE=0.20,
        WEIGHT_PREFERRED_SKILL_COVERAGE=0.10
    )
    assert custom.WEIGHT_REQUIRED_SKILL_COVERAGE == 0.40


def test_invalid_weights_sum():
    """Verify validation error is raised when weights do not sum to 1.0."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            WEIGHT_REQUIRED_SKILL_COVERAGE=0.50,
            WEIGHT_SEMANTIC_ALIGNMENT=0.50,
            WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE=0.20,
            WEIGHT_PREFERRED_SKILL_COVERAGE=0.10
        )
    assert "Scoring weights must sum to 1.0" in str(exc_info.value)


def test_configurable_thresholds():
    """Verify semantic thresholds are configurable."""
    custom = Settings(
        SEMANTIC_SIMILARITY_THRESHOLD=0.60,
        SEMANTIC_EXACT_THRESHOLD=0.90,
        SEMANTIC_INFERRED_THRESHOLD=0.45
    )
    assert custom.SEMANTIC_SIMILARITY_THRESHOLD == 0.60
    assert custom.SEMANTIC_EXACT_THRESHOLD == 0.90
    assert custom.SEMANTIC_INFERRED_THRESHOLD == 0.45
