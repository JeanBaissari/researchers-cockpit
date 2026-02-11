"""
Tests for sectional documentation indexes.

The docs standard in `docs/README.md` requires that each docs section has a
sectional README index linking all markdown docs in that section.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lib.paths import get_project_root


@pytest.mark.parametrize(
    "section_rel",
    [
        "analysis",
        "code_patterns",
        "troubleshooting",
        "validation",
        "verification",
        "walkthrough",
    ],
)
def test_docs_section_has_readme_index(section_rel: str) -> None:
    project_root = get_project_root()
    section_dir = project_root / "docs" / section_rel
    readme = section_dir / "README.md"

    assert section_dir.exists(), f"Missing docs section folder: {section_dir}"
    assert readme.exists(), f"Missing sectional index: {readme}"


@pytest.mark.parametrize(
    "section_rel",
    [
        "analysis",
        "code_patterns",
        "troubleshooting",
        "validation",
        "verification",
        "walkthrough",
    ],
)
def test_section_readme_links_all_docs_in_section(section_rel: str) -> None:
    project_root = get_project_root()
    section_dir = project_root / "docs" / section_rel
    readme = section_dir / "README.md"

    content = readme.read_text(encoding="utf-8")

    md_files = sorted(p for p in section_dir.glob("*.md") if p.name != "README.md")
    assert md_files, f"No markdown docs found in section: {section_dir}"

    for md in md_files:
        # We only require that the README contains a link target to the file.
        assert f"({md.name})" in content, f"README index missing link to {md.name}"
