"""
Test research directory structure.

Verifies that the research directory structure is properly set up
according to Phase 2 requirements of the Hypothesis Journal System.
"""

import pytest
from pathlib import Path
import yaml

from lib.paths import get_project_root


def test_research_directory_exists():
    """Verify research/ directory exists."""
    project_root = get_project_root()
    research_dir = project_root / "research"
    assert research_dir.exists(), "research/ directory should exist"
    assert research_dir.is_dir(), "research/ should be a directory"


def test_hypotheses_directory_exists():
    """Verify research/hypotheses/ directory exists."""
    project_root = get_project_root()
    hypotheses_dir = project_root / "research" / "hypotheses"
    assert hypotheses_dir.exists(), "research/hypotheses/ directory should exist"
    assert hypotheses_dir.is_dir(), "research/hypotheses/ should be a directory"


def test_gitkeep_exists():
    """Verify .gitkeep file exists to preserve empty directory."""
    project_root = get_project_root()
    gitkeep = project_root / "research" / "hypotheses" / ".gitkeep"
    assert gitkeep.exists(), "research/hypotheses/.gitkeep should exist"
    assert gitkeep.is_file(), ".gitkeep should be a file"


def test_template_exists():
    """Verify _template.yaml exists with example hypothesis."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"
    assert template.exists(), "research/hypotheses/_template.yaml should exist"
    assert template.is_file(), "_template.yaml should be a file"


def test_template_valid_yaml():
    """Verify _template.yaml is valid YAML."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "Template should be a YAML dictionary"


def test_template_has_required_keys():
    """Verify _template.yaml contains all required schema keys."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    required_keys = [
        "id",
        "created",
        "updated",
        "status",
        "hypothesis",
        "rationale",
        "testing",
        "results",
        "tags",
    ]

    for key in required_keys:
        assert key in data, f"Template should have '{key}' key"


def test_template_hypothesis_section():
    """Verify hypothesis section has required fields."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    hypothesis = data.get("hypothesis", {})
    required_fields = ["title", "description", "asset_class", "symbols", "timeframe"]

    for field in required_fields:
        assert field in hypothesis, f"Hypothesis section should have '{field}' field"


def test_template_rationale_section():
    """Verify rationale section has required fields."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    rationale = data.get("rationale", {})
    required_fields = ["why", "prior_evidence", "expected_sharpe", "expected_max_drawdown"]

    for field in required_fields:
        assert field in rationale, f"Rationale section should have '{field}' field"


def test_template_testing_section():
    """Verify testing section has required fields."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    testing = data.get("testing", {})
    required_fields = ["strategy_name", "backtest_ids", "parameter_ranges"]

    for field in required_fields:
        assert field in testing, f"Testing section should have '{field}' field"


def test_template_results_section():
    """Verify results section has required fields."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    results = data.get("results", {})
    required_fields = ["actual_sharpe", "actual_max_drawdown", "conclusion", "learnings"]

    for field in required_fields:
        assert field in results, f"Results section should have '{field}' field"


def test_template_status_valid():
    """Verify template status is one of the valid values."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    status = data.get("status")
    valid_statuses = ["draft", "testing", "validated", "rejected"]

    assert status in valid_statuses, f"Status '{status}' should be one of {valid_statuses}"


def test_template_tags_is_list():
    """Verify tags is a list."""
    project_root = get_project_root()
    template = project_root / "research" / "hypotheses" / "_template.yaml"

    with open(template, "r") as f:
        data = yaml.safe_load(f)

    tags = data.get("tags")
    assert isinstance(tags, list), "Tags should be a list"
    assert len(tags) > 0, "Template should have at least one tag as example"
