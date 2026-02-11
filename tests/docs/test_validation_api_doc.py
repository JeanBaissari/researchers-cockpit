"""
Tests for data validation API documentation (docs/api/validation.md).

Verifies that the validation API doc exists and documents how lib/validation
complements Zipline runtime validation.
"""

from pathlib import Path


def _validation_doc_path() -> Path:
    """Return path to docs/api/validation.md."""
    return Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "validation.md"


def test_validation_api_doc_exists():
    """Test that data validation API document exists."""
    path = _validation_doc_path()
    assert path.exists(), "docs/api/validation.md should exist"


def test_validation_api_doc_has_zipline_runtime_complement_section():
    """Test that doc includes section on how lib/validation complements Zipline runtime validation."""
    path = _validation_doc_path()
    content = path.read_text()
    assert "How lib/validation Complements Zipline Runtime Validation" in content, (
        "Doc should include section 'How lib/validation Complements Zipline Runtime Validation'"
    )


def test_validation_api_doc_describes_zipline_runtime_validation():
    """Test that doc describes what Zipline validates at runtime."""
    path = _validation_doc_path()
    content = path.read_text()
    assert "Zipline" in content and "runtime" in content.lower(), (
        "Doc should describe Zipline and runtime validation"
    )
    assert "During ingestion" in content or "during ingestion" in content, (
        "Doc should describe Zipline ingestion validation"
    )
    assert "During backtest" in content or "during backtest" in content, (
        "Doc should describe Zipline backtest/runtime validation"
    )


def test_validation_api_doc_links_to_architecture():
    """Test that doc links to validation architecture for full pipeline."""
    path = _validation_doc_path()
    content = path.read_text()
    assert "validation_architecture.md" in content, (
        "Doc should link to docs/validation/validation_architecture.md"
    )


def test_validation_api_doc_lists_main_functions():
    """Test that doc lists main validation API functions."""
    path = _validation_doc_path()
    content = path.read_text()
    assert "validate_before_ingest" in content
    assert "validate_bundle" in content
    assert "validate_backtest_results" in content
    assert "verify_bundle_dates" in content
