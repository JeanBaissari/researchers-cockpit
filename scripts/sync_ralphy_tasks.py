#!/usr/bin/env python3
"""
Sync `prd/` task checkboxes from `.ralphy/progress.txt`.

Why:
- Upstream Ralphy uses the PRD (markdown/YAML/JSON) as its task source.
- This repo treats `.ralphy/progress.txt` as the source of truth for completion.
- This script keeps them consistent so Ralph doesn't skip or repeat work.

How it works:
- Reads completed task titles from `.ralphy/progress.txt` lines like:
  - [✓] 2026-01-28 00:14 - Task title here
- For every markdown file in `prd/`, finds checklist items:
  - [ ] Task title here
  - [x] Task title here
- If the title matches a completed title, marks it `[x]`, otherwise `[ ]`.

Contract:
- Task titles must match exactly between `.ralphy/progress.txt` and `prd/*.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROGRESS_PATH = PROJECT_ROOT / ".ralphy" / "progress.txt"
PRD_DIR = PROJECT_ROOT / "prd"


@dataclass(frozen=True)
class ProgressTask:
    title: str


def _load_completed_titles(progress_path: Path) -> set[str]:
    completed: set[str] = set()

    if not progress_path.exists():
        raise FileNotFoundError(f"Missing progress file: {progress_path}")

    for raw_line in progress_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("- [✓] "):
            continue

        # Format: "- [✓] YYYY-MM-DD HH:MM - Title"
        parts = line.split(" - ", maxsplit=2)
        if len(parts) != 3:
            continue

        title = parts[2].strip()
        if title:
            completed.add(title)

    return completed


def _sync_prd_file(path: Path, completed_titles: set[str]) -> bool:
    """
    Returns True if file content changed.
    """
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=False)
    changed = False

    new_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()

        # Only sync checklist lines in the form "- [ ] Title" / "- [x] Title".
        if (
            stripped.startswith("- [ ] ")
            or stripped.startswith("- [x] ")
            or stripped.startswith("- [X] ")
        ):
            prefix, title = stripped.split("] ", maxsplit=1)
            title = title.strip()

            # Preserve indentation (rare, but keep it).
            leading_ws = line[: len(line) - len(stripped)]

            if title in completed_titles:
                new_line = f"{leading_ws}- [x] {title}"
            else:
                new_line = f"{leading_ws}- [ ] {title}"

            if new_line != line:
                changed = True
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    if not changed:
        return False

    path.write_text(
        "\n".join(new_lines) + ("\n" if original.endswith("\n") else ""), encoding="utf-8"
    )
    return True


def main() -> int:
    completed_titles = _load_completed_titles(PROGRESS_PATH)

    if not PRD_DIR.exists():
        raise FileNotFoundError(f"Missing PRD folder: {PRD_DIR}")

    md_files = sorted(p for p in PRD_DIR.glob("*.md") if p.is_file())
    if not md_files:
        raise FileNotFoundError(f"No .md files found in: {PRD_DIR}")

    changed_any = False
    for md in md_files:
        if _sync_prd_file(md, completed_titles):
            changed_any = True

    # Exit 0 regardless; prints are avoided to keep it automation-friendly.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
