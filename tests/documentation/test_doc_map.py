"""Tests for documentation map."""

import pytest
from pathlib import Path


def test_doc_map_exists():
    """Verify doc_map.md exists."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"
    assert doc_map.exists(), "doc_map.md should exist in docs/"


def test_doc_map_linked_from_readme():
    """Verify doc_map.md is linked from docs/README.md."""
    project_root = Path(__file__).parent.parent.parent
    readme = project_root / "docs" / "README.md"

    assert readme.exists(), "docs/README.md should exist"

    content = readme.read_text()
    assert "doc_map.md" in content, "docs/README.md should link to doc_map.md"
    assert "Documentation Map" in content, "docs/README.md should mention Documentation Map"


def test_doc_map_has_required_sections():
    """Verify doc_map.md has all required sections."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"

    content = doc_map.read_text()

    # Check for major sections
    required_sections = [
        "# Documentation Map",
        "## 🎯 Getting Started",
        "## 📚 Main Documentation Sections",
        "## 🔍 Finding What You Need",
        "### By Task",
        "### By Role",
        "### By Problem",
        "## 📋 Core Documents",
        "## 📖 Documentation Standards",
    ]

    for section in required_sections:
        assert section in content, f"doc_map.md should have section: {section}"


def test_doc_map_references_main_sections():
    """Verify doc_map.md references all main documentation sections."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"

    content = doc_map.read_text()

    # Check for references to main sections
    sections = [
        "api/",
        "code_patterns/",
        "troubleshooting/",
        "testing/",
        "walkthrough/",
        "validation/",
        "verification/",
        "analysis/",
        "archive/",
    ]

    for section in sections:
        assert section in content, f"doc_map.md should reference {section}"


def test_doc_map_has_version_info():
    """Verify doc_map.md has version information."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"

    content = doc_map.read_text()

    # Check for version markers
    assert "Last Updated:" in content, "doc_map.md should have last updated date"
    assert "Version:" in content, "doc_map.md should have version info"
    assert "v1.12.0" in content, "doc_map.md should reference v1.12.0"
    assert "NO WRAPPERS" in content, "doc_map.md should mention NO WRAPPERS architecture"


def test_doc_map_links_to_key_documents():
    """Verify doc_map.md links to key documents."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"

    content = doc_map.read_text()

    # Key documents that should be linked
    key_docs = [
        "project_description.md",
        "value_add_modules.md",
        "agent_integration.md",
        "strategy_catalog.md",
        "api/README.md",
        "code_patterns/README.md",
        "troubleshooting/README.md",
    ]

    for doc in key_docs:
        assert doc in content, f"doc_map.md should link to {doc}"


def test_doc_map_markdown_formatting():
    """Verify doc_map.md has proper markdown formatting."""
    project_root = Path(__file__).parent.parent.parent
    doc_map = project_root / "docs" / "doc_map.md"

    content = doc_map.read_text()

    # Check for markdown elements
    assert content.startswith("# Documentation Map"), "Should start with H1 heading"
    assert "---" in content, "Should have horizontal rules for separation"
    assert "|" in content, "Should have tables"
    assert "[" in content and "]" in content, "Should have markdown links"
    assert "(" in content and ")" in content, "Should have markdown links with URLs"


def test_readme_doc_map_reference():
    """Verify README.md has prominent doc_map reference."""
    project_root = Path(__file__).parent.parent.parent
    readme = project_root / "docs" / "README.md"

    content = readme.read_text()

    # Check that doc_map is mentioned early in the README
    lines = content.split("\n")
    first_100_lines = "\n".join(lines[:100])

    assert "Documentation Map" in first_100_lines, (
        "Documentation Map should be mentioned in first 100 lines of README"
    )
    assert "doc_map.md" in first_100_lines, (
        "doc_map.md should be linked in first 100 lines of README"
    )
