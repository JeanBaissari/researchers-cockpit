"""
Tests for scripts documentation completeness and accuracy.
"""

import re
from pathlib import Path
import pytest


def test_scripts_reference_exists():
    """Test that scripts reference documentation exists."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"
    assert scripts_ref.exists(), "scripts_reference.md should exist"


def test_scripts_reference_has_required_sections():
    """Test that scripts reference has all required sections."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    # Check for required sections per DOC_STANDARDS_SUMMARY.md
    required_sections = [
        "# Scripts Reference Guide",  # Title
        "## Purpose",  # Purpose section
        "## Scope",  # Scope section
        "## Related",  # Related section
    ]

    for section in required_sections:
        assert section in content, f"Missing required section: {section}"


def test_scripts_reference_has_metadata_footer():
    """Test that scripts reference has metadata footer."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    # Check for metadata footer
    assert "**Last Updated:**" in content, "Missing Last Updated in metadata footer"
    assert "**Version:**" in content, "Missing Version in metadata footer"
    assert "**Status:**" in content, "Missing Status in metadata footer"


def test_all_main_scripts_documented():
    """Test that all main scripts are documented in scripts_reference.md."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    # Main user-facing scripts that should be documented
    main_scripts = [
        "ingest_data.py",
        "run_backtest.py",
        "run_optimization.py",
        "generate_report.py",
        "validate_bundles.py",
        "bundle_info.py",
    ]

    for script in main_scripts:
        # Check that script is mentioned in the documentation
        assert script in content, f"Script {script} should be documented"

        # Check that script has a dedicated section (heading)
        # Pattern: ### script_name.py or ###ingest_data.py
        script_section = f"### {script.replace('.py', '').replace('_', '_')}"
        assert script_section in content or f"### {script}" in content, (
            f"Script {script} should have a dedicated section"
        )


def test_scripts_reference_linked_in_doc_map():
    """Test that scripts_reference.md is linked in doc_map.md."""
    docs_dir = Path(__file__).parent.parent / "docs"
    doc_map = docs_dir / "doc_map.md"

    content = doc_map.read_text()

    assert "scripts_reference.md" in content, "scripts_reference.md should be linked in doc_map.md"


def test_scripts_reference_linked_in_readme():
    """Test that scripts_reference.md is linked in docs/README.md."""
    docs_dir = Path(__file__).parent.parent / "docs"
    readme = docs_dir / "README.md"

    content = readme.read_text()

    assert "scripts_reference.md" in content, (
        "scripts_reference.md should be linked in docs/README.md"
    )


def test_scripts_reference_has_usage_examples():
    """Test that each documented script has usage examples."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    main_scripts = [
        "ingest_data.py",
        "run_backtest.py",
        "run_optimization.py",
        "generate_report.py",
    ]

    for script in main_scripts:
        # Look for usage examples section after each script heading
        # Pattern should include "Usage Examples" or "Examples" heading
        script_name = script.replace(".py", "")

        # Find the section for this script (look for next ### or end of doc)
        pattern = rf"### {re.escape(script_name)}.*?(?=\n### |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        assert match, f"Could not find section for {script}"
        section_content = match.group(0)

        # Check for usage examples
        assert "Usage Examples" in section_content or "Examples" in section_content, (
            f"Script {script} should have usage examples"
        )

        # Check for at least one code block
        assert "```bash" in section_content or "```" in section_content, (
            f"Script {script} should have code examples"
        )


def test_scripts_reference_has_options_table():
    """Test that main scripts have options tables."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    # Scripts that should have options tables
    scripts_with_options = [
        "ingest_data.py",
        "run_backtest.py",
        "run_optimization.py",
    ]

    for script in scripts_with_options:
        script_name = script.replace(".py", "")

        # Find the section for this script (look for next ### or end of doc)
        pattern = rf"### {re.escape(script_name)}.*?(?=\n### |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        assert match, f"Could not find section for {script}"
        section_content = match.group(0)

        # Check for options section with table
        assert "#### Options" in section_content, f"Script {script} should have Options section"

        # Check for table headers
        assert "| Option |" in section_content, f"Script {script} should have options table"


def test_scripts_reference_version_matches():
    """Test that scripts reference version matches CLAUDE.md version."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"
    claude_md = Path(__file__).parent.parent / "CLAUDE.md"

    scripts_content = scripts_ref.read_text()
    claude_content = claude_md.read_text()

    # Extract version from scripts_reference.md
    scripts_version_match = re.search(r"\*\*Version:\*\* (v[\d.]+)", scripts_content)
    assert scripts_version_match, "Could not find version in scripts_reference.md"
    scripts_version = scripts_version_match.group(1)

    # Extract version from CLAUDE.md
    claude_version_match = re.search(r"\*\*Current Version:\*\* (v[\d.]+)", claude_content)
    assert claude_version_match, "Could not find version in CLAUDE.md"
    claude_version = claude_version_match.group(1)

    assert scripts_version == claude_version, (
        f"Version mismatch: scripts_reference.md has {scripts_version}, "
        f"CLAUDE.md has {claude_version}"
    )


def test_scripts_reference_has_common_workflows():
    """Test that scripts reference includes common workflow examples."""
    docs_dir = Path(__file__).parent.parent / "docs"
    scripts_ref = docs_dir / "scripts_reference.md"

    content = scripts_ref.read_text()

    # Should have common workflows section
    assert "## Common Workflows" in content, (
        "scripts_reference.md should have Common Workflows section"
    )

    # Should include workflow examples
    workflows = [
        "Complete Research Pipeline",
        "Multi-Timeframe",
        "Bundle Maintenance",
    ]

    for workflow in workflows:
        assert workflow in content, f"Common Workflows should include {workflow} example"
