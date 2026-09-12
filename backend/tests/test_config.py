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
    """Verify semantic thresholds are configurable with valid ordering."""
    custom = Settings(
        SEMANTIC_INFERRED_THRESHOLD=0.45,
        SEMANTIC_SIMILARITY_THRESHOLD=0.60,
        SEMANTIC_EXACT_THRESHOLD=0.90
    )
    assert custom.SEMANTIC_INFERRED_THRESHOLD == 0.45
    assert custom.SEMANTIC_SIMILARITY_THRESHOLD == 0.60
    assert custom.SEMANTIC_EXACT_THRESHOLD == 0.90


@pytest.mark.parametrize("inferred,similarity,exact", [
    (0.65, 0.65, 0.85),  # inferred == similarity
    (0.70, 0.65, 0.85),  # inferred > similarity
])
def test_semantic_thresholds_inferred_ge_similarity(inferred: float, similarity: float, exact: float):
    """Configuration must fail when inferred threshold >= similarity threshold."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            SEMANTIC_INFERRED_THRESHOLD=inferred,
            SEMANTIC_SIMILARITY_THRESHOLD=similarity,
            SEMANTIC_EXACT_THRESHOLD=exact
        )
    assert "Invalid semantic threshold ordering" in str(exc_info.value)


@pytest.mark.parametrize("inferred,similarity,exact", [
    (0.50, 0.85, 0.85),  # similarity == exact
    (0.50, 0.90, 0.85),  # similarity > exact
])
def test_semantic_thresholds_similarity_ge_exact(inferred: float, similarity: float, exact: float):
    """Configuration must fail when similarity threshold >= exact threshold."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            SEMANTIC_INFERRED_THRESHOLD=inferred,
            SEMANTIC_SIMILARITY_THRESHOLD=similarity,
            SEMANTIC_EXACT_THRESHOLD=exact
        )
    assert "Invalid semantic threshold ordering" in str(exc_info.value)


@pytest.mark.parametrize("field,value", [
    ("SEMANTIC_INFERRED_THRESHOLD", -0.1),
    ("SEMANTIC_INFERRED_THRESHOLD", 1.05),
    ("SEMANTIC_SIMILARITY_THRESHOLD", -0.01),
    ("SEMANTIC_SIMILARITY_THRESHOLD", 1.2),
    ("SEMANTIC_EXACT_THRESHOLD", -0.5),
    ("SEMANTIC_EXACT_THRESHOLD", 1.5),
])
def test_semantic_thresholds_outside_bounds(field: str, value: float):
    """Configuration must fail when any threshold is outside [0, 1]."""
    with pytest.raises(ValidationError):
        Settings(**{field: value})

