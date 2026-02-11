"""
Tests for 00_data_exploration.ipynb notebook.

Tests notebook structure, imports, and basic functionality.
"""

import json
from pathlib import Path

import pytest


def test_notebook_exists():
    """Test that the notebook file exists."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"
    assert notebook_path.exists(), "Notebook file not found"


def test_notebook_structure():
    """Test that the notebook has valid structure."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    # Check notebook format
    assert "cells" in nb, "Notebook missing cells"
    assert "metadata" in nb, "Notebook missing metadata"
    assert "nbformat" in nb, "Notebook missing nbformat"

    # Check we have cells
    assert len(nb["cells"]) > 0, "Notebook has no cells"


def test_notebook_has_markdown_intro():
    """Test that notebook starts with markdown introduction."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    first_cell = nb["cells"][0]
    assert first_cell["cell_type"] == "markdown", "First cell should be markdown"

    # Check for title
    source = "".join(first_cell["source"])
    assert "Data Exploration" in source, "Missing title"
    assert "v1.12.0" in source, "Missing version info"


def test_notebook_has_setup_cell():
    """Test that notebook has setup cell with imports."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find setup cell (should be early in notebook)
    setup_cells = [
        cell for cell in nb["cells"][:5]
        if cell["cell_type"] == "code" and any("import" in line for line in cell["source"])
    ]

    assert len(setup_cells) > 0, "No setup cell found"

    # Check for key imports
    setup_source = "".join(setup_cells[0]["source"])
    assert "from lib.bundles import" in setup_source, "Missing lib.bundles import"
    assert "from lib.validation import" in setup_source, "Missing lib.validation import"
    assert "from zipline" in setup_source, "Missing Zipline import"


def test_notebook_uses_no_wrappers_architecture():
    """Test that notebook uses v1.12.0 NO WRAPPERS architecture."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    # Get all code cells
    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    all_code = "\n".join("".join(cell["source"]) for cell in code_cells)

    # Check for direct Zipline imports
    assert "from zipline.data.bundles import" in all_code, "Missing direct Zipline bundle import"
    assert "from zipline.utils.calendar_utils import" in all_code, "Missing direct calendar import"

    # Check NO deprecated wrapper usage
    assert "from lib.bundles.csv import" not in all_code, "Using deprecated CSV wrapper"
    assert "from lib.calendars.sessions import" not in all_code, "Using deprecated SessionManager"


def test_notebook_has_key_sections():
    """Test that notebook has all key exploration sections."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    # Get all markdown headers
    markdown_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "markdown"]
    all_markdown = "\n".join("".join(cell["source"]) for cell in markdown_cells)

    # Check for key sections
    required_sections = [
        "List Available Bundles",
        "Bundle Metadata",
        "Validate Bundle",
        "Load Sample Data",
        "Visualize Price Data",
        "Data Quality Checks",
        "Trading Calendar Information",
        "Summary"
    ]

    for section in required_sections:
        assert section in all_markdown, f"Missing section: {section}"


def test_notebook_has_visualization_code():
    """Test that notebook includes visualization code."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    all_code = "\n".join("".join(cell["source"]) for cell in code_cells)

    # Check for plotting libraries
    assert "matplotlib" in all_code or "plt" in all_code, "Missing matplotlib"
    assert "plt.subplots" in all_code or "plt.plot" in all_code, "No plotting code found"


def test_notebook_has_data_quality_checks():
    """Test that notebook includes data quality analysis."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    all_code = "\n".join("".join(cell["source"]) for cell in code_cells)

    # Check for quality checks
    assert "missing" in all_code.lower() or "isnull" in all_code, "No missing data check"
    assert "gap" in all_code.lower() or "diff" in all_code, "No gap detection"
    assert "outlier" in all_code.lower() or "z_score" in all_code, "No outlier detection"


def test_notebook_error_handling():
    """Test that notebook includes proper error handling."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    all_code = "\n".join("".join(cell["source"]) for cell in code_cells)

    # Check for error handling
    assert "try:" in all_code, "No try-except blocks found"
    assert "except" in all_code, "No exception handling"

    # Check for user-friendly messages
    assert "⚠" in all_code or "warning" in all_code.lower(), "No warning messages"


def test_notebook_follows_project_conventions():
    """Test that notebook follows project coding conventions."""
    notebook_path = Path(__file__).parent.parent.parent / "notebooks" / "00_data_exploration.ipynb"

    with open(notebook_path) as f:
        nb = json.load(f)

    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    all_code = "\n".join("".join(cell["source"]) for cell in code_cells)

    # Check for get_project_root usage
    assert "get_project_root" in all_code, "Not using get_project_root"

    # Check NO hardcoded paths
    assert "/home/" not in all_code, "Contains hardcoded paths"
    assert "C:\\" not in all_code, "Contains hardcoded Windows paths"
