"""
Documentation utilities.

This package supports maintaining small, discoverable docs by generating and
validating sectional indexes (README.md) under `docs/`.
"""

from lib.docs.section_index import build_section_index_markdown, find_section_docs

__all__ = [
    "build_section_index_markdown",
    "find_section_docs",
]
