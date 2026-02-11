#!/usr/bin/env python3
"""
Generate/refresh sectional `README.md` indexes under `docs/`.

This script is intentionally conservative:
- It only writes README.md files for specific section folders.
- It does not modify the top-level `docs/README.md`.

Usage:
    python scripts/generate_docs_indexes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.docs.section_index import build_section_index_markdown, find_section_docs
from lib.logging.config import configure_logging, get_logger
from lib.logging.context import LogContext
from lib.paths import get_project_root

logger = get_logger(__name__)


def _write_if_changed(path: Path, content: str) -> bool:
    """
    Write content to `path` if it differs. Returns True if written.
    """
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return False
    path.write_text(content, encoding="utf-8")
    return True


def generate_indexes(docs_root: Path) -> dict[str, bool]:
    """
    Generate indexes for known docs sections.

    Returns:
        Dict mapping section relative path -> changed flag.
    """
    sections: dict[str, str] = {
        "analysis": "Analysis",
        "code_patterns": "Code Patterns",
        "troubleshooting": "Troubleshooting",
        "validation": "Validation",
        "verification": "Verification",
        "walkthrough": "Walkthrough",
    }

    changed: dict[str, bool] = {}
    for rel, title in sections.items():
        section_dir = docs_root / rel
        docs = find_section_docs(section_dir, max_depth=2)
        md = build_section_index_markdown(
            title,
            docs,
            intro="Section index (auto-generated).",
        )
        changed[rel] = _write_if_changed(section_dir / "README.md", md)
    return changed


def main() -> int:
    configure_logging(level="INFO")
    docs_root = get_project_root() / "docs"

    with LogContext(phase="docs", operation="generate_section_indexes"):
        changes = generate_indexes(docs_root)
        logger.info(
            "Generated docs section indexes",
            extra={"changed_sections": [k for k, v in changes.items() if v]},
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
