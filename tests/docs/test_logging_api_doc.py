"""
Tests for logging API documentation (docs/api/logging.md).

These docs should describe how The Researcher's Cockpit integrates its logging
system with Zipline-Reloaded's named loggers.
"""

from pathlib import Path


def _logging_doc_path() -> Path:
    """Return path to docs/api/logging.md."""
    return Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "logging.md"


def test_logging_api_doc_exists():
    """Logging API document exists."""
    assert _logging_doc_path().exists(), "docs/api/logging.md should exist"


def test_logging_api_doc_mentions_zipline_named_loggers():
    """Doc mentions Zipline-Reloaded named loggers we integrate."""
    content = _logging_doc_path().read_text(encoding="utf-8")
    assert "## Zipline Logger Integration" in content
    assert "Blotter" in content
    assert "ZiplineLog" in content
    assert "DataPortal" in content
    assert "AlgoWarning" in content
