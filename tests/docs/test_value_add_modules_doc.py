"""
Tests for docs/value_add_modules.md.

This doc is the canonical reference for what belongs in `lib/` vs what should be
used directly from Zipline-Reloaded (v1.12.0+ NO WRAPPERS).
"""

from pathlib import Path


def _value_add_doc_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "value_add_modules.md"


def _docs_index_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "README.md"


def test_value_add_modules_doc_exists():
    assert _value_add_doc_path().exists(), "docs/value_add_modules.md should exist"


def test_value_add_modules_doc_structure():
    content = _value_add_doc_path().read_text(encoding="utf-8")

    # Core sections we want to keep stable
    assert "## Guiding Principle" in content
    assert "## What We Use Zipline-Reloaded For (No Project Wrappers)" in content
    assert "## Project Modules That Add Value" in content
    assert "## How to Decide if a New `lib/` Module is Allowed" in content

    # Guardrails
    assert "NO WRAPPERS" in content
    assert "Zipline-Reloaded" in content


def test_docs_index_links_value_add_modules_doc():
    content = _docs_index_path().read_text(encoding="utf-8")
    assert "value_add_modules.md" in content
