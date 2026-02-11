"""
Sectional documentation indexes.

Goal:
- Keep docs discoverable by maintaining per-section `README.md` files
  that link to markdown docs in that section.

This module is intentionally lightweight and filesystem-driven; it does not
attempt to parse headings or generate a full site structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SectionDoc:
    """
    A single markdown doc within a docs section.

    Attributes:
        rel_path: Path relative to the section directory (POSIX style).
        title: Human-friendly title (derived from filename).
    """

    rel_path: str
    title: str


def _title_from_filename(path: Path) -> str:
    """
    Convert a markdown filename into a human-friendly title.
    """
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    if not stem:
        return "Untitled"
    return " ".join(word.capitalize() for word in stem.split())


def find_section_docs(
    section_dir: Path,
    *,
    max_depth: int = 2,
    ignore_dirs: tuple[str, ...] = ("archive",),
) -> list[SectionDoc]:
    """
    Find markdown docs within a section directory.

    Rules:
    - Includes `*.md` files up to `max_depth` (relative to `section_dir`).
    - Excludes any `README.md` found.
    - Skips directories listed in `ignore_dirs`.

    Args:
        section_dir: Directory under `docs/` (e.g., `docs/troubleshooting`).
        max_depth: Max depth to include, where 1 means direct children only.
        ignore_dirs: Directory names to skip anywhere in the subtree.

    Returns:
        Sorted list of SectionDoc entries.

    Raises:
        FileNotFoundError: If `section_dir` does not exist.
        ValueError: If `max_depth` is < 1.
    """
    if not section_dir.exists():
        raise FileNotFoundError(f"Section directory not found: {section_dir}")
    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")

    docs: list[SectionDoc] = []
    section_dir = section_dir.resolve()

    for md in section_dir.rglob("*.md"):
        if md.name.lower() == "readme.md":
            continue

        rel = md.relative_to(section_dir)
        if any(part in ignore_dirs for part in rel.parts):
            continue

        # Depth: e.g. "a.md" => 1, "sub/a.md" => 2
        depth = len(rel.parts)
        if depth > max_depth:
            continue

        docs.append(
            SectionDoc(
                rel_path=rel.as_posix(),
                title=_title_from_filename(md),
            )
        )

    # Stable ordering for deterministic READMEs/tests
    return sorted(docs, key=lambda d: (d.rel_path.count("/"), d.rel_path.lower()))


def build_section_index_markdown(
    section_name: str,
    docs: list[SectionDoc],
    *,
    intro: str | None = None,
) -> str:
    """
    Build a `README.md` sectional index.

    Args:
        section_name: Display name for the section (e.g., "Troubleshooting").
        docs: Docs within the section (use `find_section_docs()`).
        intro: Optional one-paragraph intro under the title.

    Returns:
        Markdown content for the section README.
    """
    lines: list[str] = [f"# {section_name}", ""]
    if intro:
        lines.extend([intro.strip(), ""])

    if not docs:
        lines.extend(
            [
                "No documents found in this section.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(["## Index", ""])
    for doc in docs:
        lines.append(f"- [{doc.title}]({doc.rel_path})")
    lines.append("")

    return "\n".join(lines)
