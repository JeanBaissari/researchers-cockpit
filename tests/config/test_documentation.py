"""
Tests for documentation configuration module.
"""

import pytest
from pathlib import Path

from lib.config.documentation import (
    load_documentation_config,
    get_doc_zones,
    get_required_sections,
    get_index_files,
    should_archive_instead_of_delete,
    validate_doc_structure,
    _get_default_config,
)
from lib.config import clear_config_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear config cache before each test."""
    clear_config_cache()
    yield
    clear_config_cache()


def test_load_documentation_config():
    """Test loading documentation configuration."""
    config = load_documentation_config()

    # Check that all expected sections are present
    assert "organization" in config
    assert "zones" in config
    assert "required_sections" in config
    assert "indexing" in config
    assert "cleanup" in config

    # Check organization settings
    org = config["organization"]
    assert org["prefer_granular"] is True
    assert org["require_indexing"] is True
    assert org["enforce_architecture_alignment"] is True
    assert org["prevent_stale_references"] is True


def test_load_documentation_config_caching():
    """Test that configuration is cached."""
    config1 = load_documentation_config()
    config2 = load_documentation_config()

    # Should return the same object (cached)
    assert config1 is config2


def test_get_default_config():
    """Test default configuration structure."""
    config = _get_default_config()

    # Verify structure
    assert isinstance(config, dict)
    assert "organization" in config
    assert "zones" in config
    assert "required_sections" in config
    assert "indexing" in config
    assert "cleanup" in config

    # Verify zones
    zones = config["zones"]
    assert zones["api"] == "docs/api/"
    assert zones["code_patterns"] == "docs/code_patterns/"
    assert zones["troubleshooting"] == "docs/troubleshooting/"
    assert zones["verification"] == "docs/verification/"
    assert zones["archive"] == "docs/archive/"


def test_get_doc_zones():
    """Test getting documentation zone paths."""
    zones = get_doc_zones()

    # Check that all expected zones are present
    assert "api" in zones
    assert "code_patterns" in zones
    assert "troubleshooting" in zones
    assert "verification" in zones
    assert "archive" in zones

    # Check that paths are absolute
    for path in zones.values():
        assert isinstance(path, Path)
        assert path.is_absolute()


def test_get_required_sections():
    """Test getting required sections list."""
    sections = get_required_sections()

    # Check expected sections
    assert isinstance(sections, list)
    assert "purpose" in sections
    assert "scope" in sections
    assert "repo_paths" in sections
    assert "examples" in sections
    assert "related_docs" in sections


def test_get_index_files():
    """Test getting index file paths."""
    indexes = get_index_files()

    # Check global index
    assert "global_index" in indexes
    assert isinstance(indexes["global_index"], Path)
    assert indexes["global_index"].name == "README.md"

    # Check section indexes
    assert "section_indexes" in indexes
    assert isinstance(indexes["section_indexes"], list)
    assert len(indexes["section_indexes"]) > 0


def test_should_archive_instead_of_delete():
    """Test archive-instead-of-delete flag."""
    should_archive = should_archive_instead_of_delete()

    assert isinstance(should_archive, bool)
    assert should_archive is True  # Default behavior


def test_validate_doc_structure_missing_file():
    """Test validation with non-existent file."""
    result = validate_doc_structure(Path("/nonexistent/file.md"))

    assert result["valid"] is False
    assert "error" in result
    assert result["error"] == "File does not exist"
    assert len(result["missing_sections"]) > 0
    assert len(result["found_sections"]) == 0


def test_validate_doc_structure_complete_doc(tmp_path):
    """Test validation with complete documentation."""
    # Create a complete doc with all required sections
    doc_path = tmp_path / "test_doc.md"
    doc_content = """
# Test Documentation

## Purpose
This is a test document.

## Scope
Covers testing scenarios.

## Repo_Paths
- lib/config/documentation.py

## Examples
```python
config = load_documentation_config()
```

## Related_Docs
- docs/README.md
"""
    doc_path.write_text(doc_content)

    result = validate_doc_structure(doc_path)

    assert result["valid"] is True
    assert len(result["missing_sections"]) == 0
    assert len(result["found_sections"]) == 5


def test_validate_doc_structure_incomplete_doc(tmp_path):
    """Test validation with incomplete documentation."""
    # Create a doc missing some sections
    doc_path = tmp_path / "incomplete_doc.md"
    doc_content = """
# Incomplete Documentation

## Purpose
This is incomplete.

## Examples
```python
# Some example
```
"""
    doc_path.write_text(doc_content)

    result = validate_doc_structure(doc_path)

    assert result["valid"] is False
    assert len(result["missing_sections"]) > 0
    assert "scope" in result["missing_sections"]
    assert "repo_paths" in result["missing_sections"]
    assert "related_docs" in result["missing_sections"]
    assert len(result["found_sections"]) == 2
    assert "purpose" in result["found_sections"]
    assert "examples" in result["found_sections"]


def test_doc_zones_exist():
    """Test that configured doc zones actually exist in the project."""
    zones = get_doc_zones()

    # Check that key zones exist
    assert zones["api"].exists(), "docs/api/ should exist"
    assert zones["code_patterns"].exists(), "docs/code_patterns/ should exist"
    assert zones["troubleshooting"].exists(), "docs/troubleshooting/ should exist"


def test_index_files_exist():
    """Test that configured index files actually exist."""
    indexes = get_index_files()

    # Check global index exists
    assert indexes["global_index"].exists(), "docs/README.md should exist"

    # Check section indexes (at least some should exist)
    existing_indexes = [idx for idx in indexes["section_indexes"] if idx.exists()]
    assert len(existing_indexes) > 0, "At least some section indexes should exist"


def test_configuration_matches_agent_standards():
    """Test that configuration matches .claude/agents/docs_maintainer.md standards."""
    config = load_documentation_config()

    # Check organization standards match agent requirements
    org = config["organization"]
    assert org["prefer_granular"] is True  # "Granular docs" requirement
    assert org["require_indexing"] is True  # "Discoverability" requirement
    assert org["enforce_architecture_alignment"] is True  # "No wrappers architecture" requirement
    assert org["prevent_stale_references"] is True  # "No stale paths" requirement

    # Check doc zones match agent layout rules
    zones = config["zones"]
    assert "api" in zones
    assert "code_patterns" in zones
    assert "troubleshooting" in zones
    assert "verification" in zones
    assert "archive" in zones

    # Check required sections match agent requirements
    required = config["required_sections"]
    assert "purpose" in required
    assert "scope" in required
    assert "repo_paths" in required  # "Where to look in the repo"
    assert "examples" in required
    assert "related_docs" in required

    # Check cleanup rules match agent standards
    cleanup = config["cleanup"]
    assert (
        cleanup["archive_instead_of_delete"] is True
    )  # "Never delete docs unless explicitly asked"
    assert cleanup["mark_archived_docs"] is True  # "Archived because..." note requirement
    assert cleanup["link_to_canonical"] is True  # Replacement link requirement
