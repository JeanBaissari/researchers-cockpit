#!/usr/bin/env python3
"""
Enforce consistent documentation headers and required sections.

This script validates that key documentation files follow the standard structure:
- Clear title
- Purpose/Overview section
- Scope/Installation/Dependencies (where applicable)
- Examples/Quick Start
- Related documentation links
- Metadata footer (Last Updated, Version, Status)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Define the top 10 most important docs based on doc_map.md
TOP_10_DOCS = [
    "docs/project_description.md",
    "docs/api/README.md",
    "docs/strategy_catalog.md",
    "docs/walkthrough/validation.md",
    "docs/value_add_modules.md",
    "docs/agent_integration.md",
    "docs/api/bundles.md",
    "docs/api/validation.md",
    "docs/api/backtest.md",
    "docs/api/metrics.md",
]


# Required sections for different doc types
REQUIRED_SECTIONS = {
    "api": [
        "## Overview",
        "## Installation/Dependencies",  # OR "## Quick Start"
        "## Main API",  # OR "## Key Features"
        "## Examples",  # OR code blocks
        "## Related Documentation",  # OR "See Also"
    ],
    "guide": [
        "## Purpose",  # OR "## Overview"
        "## Scope",  # OR "## What This Covers"
        "## Related",  # OR "## See Also"
        # Note: Examples optional for guide docs
    ],
    "index": [
        "## Quick Navigation",  # OR table of contents
        "## Installation",  # OR "Quick Start"
    ],
}


def find_project_root() -> Path:
    """Find the project root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no CLAUDE.md found)")


def detect_doc_type(filepath: Path) -> str:
    """Detect document type based on path and filename."""
    if filepath.name == "README.md":
        return "index"
    elif "api/" in str(filepath):
        return "api"
    else:
        return "guide"


def extract_sections(content: str) -> List[str]:
    """Extract all section headers from markdown content."""
    # Match ## headers (not # title or ### subheaders)
    pattern = r"^## .+$"
    return re.findall(pattern, content, re.MULTILINE)


def check_metadata_footer(content: str) -> Tuple[bool, str]:
    """Check if document has metadata footer (Last Updated, Version, Status)."""
    # Check for footer pattern at end of document
    footer_pattern = r"\*\*Last Updated:\*\*.*\n\*\*Version:\*\*.*\n\*\*Status:\*\*"

    if re.search(footer_pattern, content):
        return True, "✓ Metadata footer present"

    # Check for alternative formats
    if "Last Updated:" in content or "Version:" in content:
        return True, "⚠ Metadata present but not in standard format"

    return False, "✗ Missing metadata footer (Last Updated, Version, Status)"


def check_title(content: str) -> Tuple[bool, str]:
    """Check if document has a clear title (# heading at start)."""
    lines = content.strip().split("\n")
    for line in lines:
        if line.strip():
            if line.startswith("# "):
                return True, f"✓ Title: {line[2:].strip()}"
            else:
                return False, "✗ First non-empty line is not a # title"
    return False, "✗ No content found"


def check_required_sections(content: str, doc_type: str) -> Tuple[bool, List[str]]:
    """Check if document has required sections for its type."""
    sections = extract_sections(content)
    required = REQUIRED_SECTIONS.get(doc_type, [])

    missing = []
    found_alternatives = []

    for req in required:
        # Check for exact match or common alternatives
        req_base = req.split()[1].lower()  # Get keyword from "## Keyword"

        # Check if any section matches the requirement (exact or alternative)
        matched = False
        for section in sections:
            section_lower = section.lower()

            # Check exact match
            if req.lower() in section_lower:
                matched = True
                break

            # Check alternatives based on keyword
            if req_base in section_lower:
                matched = True
                found_alternatives.append(f"{req} → {section}")
                break

            # Special case: "Quick Start" counts as "Installation"
            if "installation" in req_base and (
                "quick start" in section_lower or "getting started" in section_lower
            ):
                matched = True
                found_alternatives.append(f"{req} → {section}")
                break

            # Special case: "Main API" or "Key Features" counts as overview extension
            if "main api" in req_base and (
                "key features" in section_lower or "api reference" in section_lower
            ):
                matched = True
                found_alternatives.append(f"{req} → {section}")
                break

            # Special case: "Related" section can be "See Also" or "Related Documentation"
            if "related" in req_base and (
                "see also" in section_lower or "related" in section_lower
            ):
                matched = True
                found_alternatives.append(f"{req} → {section}")
                break

        if not matched:
            missing.append(req)

    if not missing:
        return True, found_alternatives
    else:
        return False, missing


def validate_document(filepath: Path) -> Dict:
    """Validate a single document against standards."""
    content = filepath.read_text()
    doc_type = detect_doc_type(filepath)

    results = {
        "path": str(filepath.relative_to(find_project_root())),
        "type": doc_type,
        "compliant": True,
        "checks": [],
    }

    # Check 1: Title
    has_title, title_msg = check_title(content)
    results["checks"].append(("Title", has_title, title_msg))
    if not has_title:
        results["compliant"] = False

    # Check 2: Required sections
    has_sections, section_info = check_required_sections(content, doc_type)
    if has_sections:
        if section_info:  # Has alternatives
            results["checks"].append(
                ("Required Sections", True, f"✓ All present (some via alternatives)")
            )
            for alt in section_info:
                results["checks"].append(("  Alternative", True, f"  {alt}"))
        else:
            results["checks"].append(("Required Sections", True, "✓ All present"))
    else:
        results["checks"].append(
            ("Required Sections", False, f"✗ Missing: {', '.join(section_info)}")
        )
        results["compliant"] = False

    # Check 3: Metadata footer
    has_footer, footer_msg = check_metadata_footer(content)
    results["checks"].append(("Metadata Footer", has_footer, footer_msg))
    if not has_footer and "⚠" not in footer_msg:
        results["compliant"] = False

    # Check 4: Examples (code blocks)
    code_blocks = len(re.findall(r"```", content))
    has_examples = code_blocks >= 2  # At least one complete code block (opening and closing)
    example_msg = (
        f"✓ {code_blocks // 2} code examples found"
        if has_examples
        else "⚠ No code examples (may not be required)"
    )
    results["checks"].append(("Examples", has_examples, example_msg))

    return results


def print_results(results: List[Dict]):
    """Print validation results in a readable format."""
    print("\n" + "=" * 80)
    print("DOCUMENTATION STANDARDS VALIDATION")
    print("=" * 80 + "\n")

    compliant_count = sum(1 for r in results if r["compliant"])
    total_count = len(results)

    for result in results:
        status = "✓ COMPLIANT" if result["compliant"] else "✗ NON-COMPLIANT"
        print(f"\n{result['path']}")
        print(f"  Type: {result['type']}")
        print(f"  Status: {status}")
        print()

        for check_name, passed, message in result["checks"]:
            symbol = "✓" if passed else "✗"
            print(f"    {symbol} {check_name}: {message}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {compliant_count}/{total_count} documents compliant")
    print("=" * 80 + "\n")

    return compliant_count == total_count


def main():
    """Main entry point."""
    project_root = find_project_root()

    print(f"Project root: {project_root}")
    print(f"Validating top {len(TOP_10_DOCS)} most important documents...")

    results = []
    missing_files = []

    for doc_path in TOP_10_DOCS:
        filepath = project_root / doc_path
        if not filepath.exists():
            missing_files.append(doc_path)
            continue

        results.append(validate_document(filepath))

    if missing_files:
        print("\n⚠ Warning: The following files were not found:")
        for f in missing_files:
            print(f"  - {f}")
        print()

    all_compliant = print_results(results)

    if not all_compliant:
        print("\nTo fix non-compliant documents:")
        print("  1. Add missing required sections")
        print("  2. Ensure clear # title at document start")
        print("  3. Add metadata footer: Last Updated, Version, Status")
        print("  4. Include code examples where applicable")
        print()
        sys.exit(1)
    else:
        print("\n✓ All top 10 documents meet standards!")
        sys.exit(0)


if __name__ == "__main__":
    main()
