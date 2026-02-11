"""
Tests for position sizing API documentation (docs/api/position_sizing.md).

Verifies that the doc exists and clearly explains how lib/position_sizing.py
COMPLEMENTS Zipline-Reloaded's order_target_percent() (calculation vs execution).
"""

from pathlib import Path


def _position_sizing_doc_path() -> Path:
    """Return path to docs/api/position_sizing.md."""
    return Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "position_sizing.md"


def test_position_sizing_api_doc_exists():
    """Position sizing API document exists."""
    path = _position_sizing_doc_path()
    assert path.exists(), "docs/api/position_sizing.md should exist"


def test_position_sizing_api_doc_mentions_order_target_percent_and_compute_position_size():
    """Doc should name the Zipline execution API and this project's sizing function."""
    content = _position_sizing_doc_path().read_text(encoding="utf-8")
    assert "order_target_percent" in content
    assert "compute_position_size" in content


def test_position_sizing_api_doc_has_use_zipline_vs_use_lib_section():
    """Doc must include the requested decision section."""
    content = _position_sizing_doc_path().read_text(encoding="utf-8")
    assert "## When to Use Zipline vs When to Use `lib/position_sizing`" in content
