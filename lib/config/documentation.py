"""
Documentation configuration and standards.

Provides access to documentation standards enforced by the docs-maintainer agent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, List

from .core import load_settings, get_config_cache
from ..utils import get_project_root


# Configure logging
logger = logging.getLogger(__name__)


def load_documentation_config() -> Dict[str, Any]:
    """
    Load documentation configuration from settings.

    Returns:
        dict: Documentation configuration dictionary with sections:
            - organization: Organization standards
            - zones: Doc zone directories
            - required_sections: Required sections for new docs
            - indexing: Index file paths
            - cleanup: Cleanup and refactoring rules

    Example:
        >>> config = load_documentation_config()
        >>> config['organization']['prefer_granular']
        True
        >>> config['zones']['api']
        'docs/api/'
    """
    cache_key = "documentation_config"
    cache = get_config_cache()

    if cache_key in cache:
        logger.debug("Returning cached documentation config")
        return cache[cache_key]

    settings = load_settings()
    doc_config = settings.get("documentation", {})

    if not doc_config:
        logger.warning("No documentation configuration found in settings.yaml")
        doc_config = _get_default_config()

    cache[cache_key] = doc_config
    return doc_config


def _get_default_config() -> Dict[str, Any]:
    """
    Get default documentation configuration.

    Returns:
        dict: Default configuration matching docs-maintainer standards
    """
    return {
        "organization": {
            "prefer_granular": True,
            "require_indexing": True,
            "enforce_architecture_alignment": True,
            "prevent_stale_references": True,
        },
        "zones": {
            "api": "docs/api/",
            "code_patterns": "docs/code_patterns/",
            "troubleshooting": "docs/troubleshooting/",
            "verification": "docs/verification/",
            "archive": "docs/archive/",
        },
        "required_sections": [
            "purpose",
            "scope",
            "repo_paths",
            "examples",
            "related_docs",
        ],
        "indexing": {
            "global_index": "docs/README.md",
            "section_indexes": [
                "docs/api/README.md",
                "docs/code_patterns/README.md",
                "docs/troubleshooting/README.md",
                "docs/verification/README.md",
                "docs/archive/README.md",
            ],
        },
        "cleanup": {
            "archive_instead_of_delete": True,
            "mark_archived_docs": True,
            "link_to_canonical": True,
        },
    }


def get_doc_zones() -> Dict[str, Path]:
    """
    Get documentation zone paths.

    Returns:
        dict: Mapping of zone names to absolute paths

    Example:
        >>> zones = get_doc_zones()
        >>> zones['api']
        PosixPath('/path/to/project/docs/api')
    """
    config = load_documentation_config()
    zones = config.get("zones", {})
    root = get_project_root()

    return {name: root / path for name, path in zones.items()}


def get_required_sections() -> List[str]:
    """
    Get list of required sections for new documentation.

    Returns:
        list: List of required section names

    Example:
        >>> sections = get_required_sections()
        >>> 'purpose' in sections
        True
    """
    config = load_documentation_config()
    return config.get("required_sections", [])


def get_index_files() -> Dict[str, Path]:
    """
    Get documentation index file paths.

    Returns:
        dict: Mapping of index names to absolute paths

    Example:
        >>> indexes = get_index_files()
        >>> indexes['global_index']
        PosixPath('/path/to/project/docs/README.md')
    """
    config = load_documentation_config()
    indexing = config.get("indexing", {})
    root = get_project_root()

    result = {}

    # Global index
    if "global_index" in indexing:
        result["global_index"] = root / indexing["global_index"]

    # Section indexes
    if "section_indexes" in indexing:
        result["section_indexes"] = [root / path for path in indexing["section_indexes"]]

    return result


def should_archive_instead_of_delete() -> bool:
    """
    Check if docs should be archived instead of deleted.

    Returns:
        bool: True if archiving is preferred over deletion
    """
    config = load_documentation_config()
    cleanup = config.get("cleanup", {})
    return cleanup.get("archive_instead_of_delete", True)


def validate_doc_structure(doc_path: Path) -> Dict[str, Any]:
    """
    Validate that a documentation file has required sections.

    Args:
        doc_path: Path to documentation file

    Returns:
        dict: Validation results with keys:
            - valid: True if all required sections present
            - missing_sections: List of missing section names
            - found_sections: List of found section names

    Example:
        >>> result = validate_doc_structure(Path('docs/api/example.md'))
        >>> result['valid']
        True
        >>> result['missing_sections']
        []
    """
    if not doc_path.exists():
        return {
            "valid": False,
            "missing_sections": get_required_sections(),
            "found_sections": [],
            "error": "File does not exist",
        }

    content = doc_path.read_text()
    content_lower = content.lower()
    required = get_required_sections()

    # Simple section detection (look for headers with section names)
    # Convert section names to title case and check case-insensitively
    found = []
    for section in required:
        # Normalize section name (replace underscores with spaces, title case)
        section_normalized = section.replace("_", " ").title()
        section_lower = section.lower()

        # Check for markdown headers with section name (case-insensitive)
        if (
            f"## {section_normalized}" in content
            or f"# {section_normalized}" in content
            or f"## {section_lower}" in content_lower
            or f"# {section_lower}" in content_lower
        ):
            found.append(section)

    missing = [s for s in required if s not in found]

    return {
        "valid": len(missing) == 0,
        "missing_sections": missing,
        "found_sections": found,
    }
