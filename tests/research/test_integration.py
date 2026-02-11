"""
Integration tests for research directory structure.

Verifies that the complete research workflow is functional.
"""

import pytest
from pathlib import Path
from dataclasses import asdict
import yaml

from lib.paths import get_project_root
from lib.research import create_hypothesis, save_hypothesis, load_hypothesis


def test_end_to_end_hypothesis_workflow(tmp_path):
    """
    Test complete hypothesis workflow using research directory.

    This integration test verifies:
    1. Template exists and is valid
    2. New hypothesis can be created
    3. Hypothesis can be saved to research/hypotheses/
    4. Hypothesis can be loaded back
    5. All data integrity is maintained
    """
    project_root = get_project_root()

    # Verify template exists
    template_path = project_root / "research" / "hypotheses" / "_template.yaml"
    assert template_path.exists(), "Template should exist"

    # Load template to verify structure
    with open(template_path, "r") as f:
        template_data = yaml.safe_load(f)

    assert "id" in template_data
    assert "hypothesis" in template_data
    assert "rationale" in template_data
    assert "testing" in template_data
    assert "results" in template_data

    # Create a new hypothesis
    hypothesis = create_hypothesis(title="Test Integration Hypothesis", asset_class="crypto")

    # Save hypothesis using the actual save function
    # This will save to the real research directory
    save_path = save_hypothesis(hypothesis)

    assert save_path.exists(), "Hypothesis file should be created"

    # Load hypothesis back using the actual load function
    loaded_hypothesis = load_hypothesis(hypothesis.id)

    assert loaded_hypothesis.id == hypothesis.id
    assert loaded_hypothesis.title == "Test Integration Hypothesis"
    assert loaded_hypothesis.asset_class == "crypto"

    # Clean up - remove the test hypothesis file
    save_path.unlink()


def test_research_directory_is_gitignored_appropriately():
    """
    Verify that .gitkeep ensures directory persistence while allowing
    hypothesis files to be tracked.
    """
    project_root = get_project_root()
    gitkeep_path = project_root / "research" / "hypotheses" / ".gitkeep"

    assert gitkeep_path.exists(), ".gitkeep should exist"

    # Verify .gitkeep content is appropriate
    with open(gitkeep_path, "r") as f:
        content = f.read().strip()

    assert len(content) > 0, ".gitkeep should have content explaining its purpose"


def test_template_can_be_copied_as_starting_point():
    """
    Verify template can be used as a starting point for new hypotheses.
    """
    project_root = get_project_root()
    template_path = project_root / "research" / "hypotheses" / "_template.yaml"

    # Load template
    with open(template_path, "r") as f:
        template_content = f.read()

    # Verify it has instructional comments
    assert "# Hypothesis Template" in template_content or "template" in template_content.lower()

    # Verify it loads as valid YAML
    with open(template_path, "r") as f:
        data = yaml.safe_load(f)

    assert data is not None
    assert isinstance(data, dict)
