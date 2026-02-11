#!/usr/bin/env python3
"""
Apply standardized fixes to documentation files to meet compliance standards.

This script applies fixes to non-compliant docs identified by enforce_doc_standards.py.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


def find_project_root() -> Path:
    """Find the project root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no CLAUDE.md found)")


def add_metadata_footer(content: str) -> str:
    """Add standard metadata footer if missing."""
    footer = """
---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture"""

    # Check if already has footer
    if "**Last Updated:**" in content and "**Version:**" in content:
        # Already has footer, just ensure it's in standard format
        return content

    # Add footer at end
    return content.rstrip() + "\n" + footer + "\n"


def ensure_section_exists(content: str, section_name: str, section_content: str) -> str:
    """Ensure a section exists in the document."""
    pattern = f"^{re.escape(section_name)}$"

    if re.search(pattern, content, re.MULTILINE):
        # Section already exists
        return content

    # Find where to insert (after ---  and before first ## section)
    lines = content.split("\n")
    insert_pos = -1

    # Find first --- after the initial header block
    found_first_separator = False
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 0:
            if not found_first_separator:
                found_first_separator = True
            else:
                # Insert after second ---
                insert_pos = i + 1
                break

    if insert_pos == -1:
        # No suitable position found, add at end before footer
        if "**Last Updated:**" in content:
            # Insert before footer
            footer_pos = content.find("**Last Updated:**")
            return (
                content[:footer_pos]
                + section_name
                + "\n\n"
                + section_content
                + "\n\n"
                + content[footer_pos:]
            )
        else:
            return content + "\n\n" + section_name + "\n\n" + section_content + "\n"

    # Insert at found position
    lines.insert(insert_pos, "")
    lines.insert(insert_pos + 1, section_name)
    lines.insert(insert_pos + 2, "")
    lines.insert(insert_pos + 3, section_content)
    lines.insert(insert_pos + 4, "")

    return "\n".join(lines)


def fix_api_bundles(filepath: Path) -> str:
    """Fix api/bundles.md - add Main API section."""
    content = filepath.read_text()

    # Add Main API section after Quick Start
    main_api_section = """## Main API

### Core Functions

| Function | Purpose |
|----------|---------|
| `ingest_bundle()` | Ingest market data into Zipline bundle |
| `list_bundles()` | List all available bundles |
| `load_bundle()` | Load and verify bundle exists |
| `get_bundle_symbols()` | Get symbols available in bundle |

### Bundle Management

| Function | Purpose |
|----------|---------|
| `register_csv_bundle()` | Register CSV bundle (v1.12.0+: use csvdir_equities) |
| `unregister_bundle()` | Unregister a bundle |
| `get_bundle_metadata()` | Get bundle metadata (dates, symbols) |"""

    if "## Main API" not in content:
        # Insert after Quick Start section
        content = content.replace(
            "### Load and Use a Bundle", main_api_section + "\n\n---\n\n### Load and Use a Bundle"
        )

    return add_metadata_footer(content)


def fix_api_validation(filepath: Path) -> str:
    """Fix api/validation.md - add required sections."""
    content = filepath.read_text()

    # Add Overview if missing
    overview = """## Overview

The Validation API provides comprehensive data quality checks for OHLCV data, bundle integrity verification, and backtest result validation. It complements Zipline-Reloaded's runtime validation with business-rule checks, data quality analysis, and integrity verification.

**Key capabilities:**
- Pre-ingestion OHLCV validation (schema, OHLC consistency, outliers)
- Bundle integrity verification (existence, metadata, date coverage)
- Post-backtest result validation (metrics consistency, position alignment)
- Asset-specific validation rules (equity, forex, crypto)
- Actionable error messages with fix suggestions"""

    if "## Overview" not in content:
        # Insert after header block, before "How lib/validation" section
        content = content.replace(
            "## How lib/validation Complements",
            overview + "\n\n---\n\n## How lib/validation Complements",
        )

    # Add Installation section
    installation = """## Installation/Dependencies

**Required:**
- `zipline-reloaded` >= 3.1.0
- `pandas` >= 1.3.0
- `numpy` >= 1.20.0

**Optional:**
- `exchange-calendars` >= 4.0.0 (for calendar validation)

```bash
pip install zipline-reloaded pandas numpy exchange-calendars
```"""

    if "## Installation/Dependencies" not in content:
        content = content.replace(
            "---\n\n## Main API", f"---\n\n{installation}\n\n---\n\n## Main API"
        )

    # Add Examples section header
    if "## Examples" not in content:
        # Find first code block after Main API and add Examples header before it
        content = re.sub(
            r"(## Main API.*?\n\n.*?\n\n)(```python)",
            r"\1## Examples\n\n### Basic Validation\n\n\2",
            content,
            flags=re.DOTALL,
        )

    return add_metadata_footer(content)


def main():
    """Apply fixes to non-compliant documents."""
    project_root = find_project_root()

    fixes = {
        "docs/api/bundles.md": fix_api_bundles,
        "docs/api/validation.md": fix_api_validation,
    }

    print("Applying fixes to non-compliant documents...")
    print()

    for doc_path, fix_func in fixes.items():
        filepath = project_root / doc_path
        if not filepath.exists():
            print(f"⚠ Skipping {doc_path} (not found)")
            continue

        print(f"Fixing {doc_path}...")
        try:
            fixed_content = fix_func(filepath)
            filepath.write_text(fixed_content)
            print(f"  ✓ Fixed {doc_path}")
        except Exception as e:
            print(f"  ✗ Error fixing {doc_path}: {e}")

    print()
    print("✓ Fixes applied. Run enforce_doc_standards.py to verify.")


if __name__ == "__main__":
    main()
