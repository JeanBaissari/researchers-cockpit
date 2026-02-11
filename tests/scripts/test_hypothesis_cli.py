"""
Tests for hypothesis CLI script.

Tests CLI commands for hypothesis management including create, list, update, link, search, and show.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

# Import CLI
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.hypothesis import cli
from lib.research import create_hypothesis, save_hypothesis, HypothesisStatus


@pytest.fixture
def temp_hypotheses_dir(tmp_path, monkeypatch):
    """Create a temporary hypotheses directory for testing."""
    hypotheses_dir = tmp_path / "research" / "hypotheses"
    hypotheses_dir.mkdir(parents=True)

    # Mock get_project_root to return temp directory
    def mock_get_project_root():
        return tmp_path

    from lib.research import hypothesis

    monkeypatch.setattr(hypothesis, "get_project_root", mock_get_project_root)

    # Also patch get_project_root in lib.paths for the CLI
    from lib import paths

    monkeypatch.setattr(paths, "get_project_root", mock_get_project_root)

    return hypotheses_dir


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that CLI help displays correctly."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Hypothesis" in result.output
    assert "create" in result.output
    assert "list" in result.output
    assert "update" in result.output
    assert "link" in result.output
    assert "search" in result.output
    assert "show" in result.output


def test_create_command(runner, temp_hypotheses_dir):
    """Test hypothesis create command."""
    result = runner.invoke(
        cli,
        [
            "create",
            "BTC momentum test",
            "--asset-class",
            "crypto",
            "--description",
            "Test description",
            "--timeframe",
            "daily",
        ],
    )

    assert result.exit_code == 0, f"Command failed with: {result.output}"
    assert "✓ Created hypothesis:" in result.output
    assert "Status: draft" in result.output

    # Verify file was created
    yaml_files = list(temp_hypotheses_dir.glob("*.yaml"))
    assert len(yaml_files) == 1
    assert "btc_momentum" in yaml_files[0].stem


def test_create_command_missing_asset_class(runner, temp_hypotheses_dir):
    """Test create command fails without asset-class."""
    result = runner.invoke(cli, ["create", "Test hypothesis"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_list_command_empty(runner, temp_hypotheses_dir):
    """Test list command with no hypotheses."""
    result = runner.invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "No hypotheses found" in result.output


def test_list_command_with_hypotheses(runner, temp_hypotheses_dir):
    """Test list command displays hypotheses."""
    # Create test hypotheses
    hyp1 = create_hypothesis("Test 1", "crypto", tags=["test"])
    hyp2 = create_hypothesis("Test 2", "forex", tags=["test"])
    save_hypothesis(hyp1)
    save_hypothesis(hyp2)

    result = runner.invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "Total: 2 hypothesis(es)" in result.output
    assert hyp1.id in result.output
    assert hyp2.id in result.output


def test_list_command_with_status_filter(runner, temp_hypotheses_dir):
    """Test list command with status filter."""
    # Create hypotheses with different statuses
    draft = create_hypothesis("Draft", "crypto")
    draft.status = HypothesisStatus.DRAFT
    save_hypothesis(draft)

    testing = create_hypothesis("Testing", "forex")
    testing.status = HypothesisStatus.TESTING
    save_hypothesis(testing)

    # List only testing
    result = runner.invoke(cli, ["list", "--status", "testing"])

    assert result.exit_code == 0
    assert "Total: 1 hypothesis(es)" in result.output
    assert testing.id in result.output
    assert draft.id not in result.output


def test_list_command_formats(runner, temp_hypotheses_dir):
    """Test list command output formats."""
    hyp = create_hypothesis("Test", "crypto")
    save_hypothesis(hyp)

    # Test table format
    result = runner.invoke(cli, ["list", "--format", "table"])
    assert result.exit_code == 0
    assert hyp.id in result.output

    # Test list format
    result = runner.invoke(cli, ["list", "--format", "list"])
    assert result.exit_code == 0
    assert hyp.id in result.output

    # Test detailed format
    result = runner.invoke(cli, ["list", "--format", "detailed"])
    assert result.exit_code == 0
    assert hyp.id in result.output


def test_update_command(runner, temp_hypotheses_dir):
    """Test hypothesis update command."""
    hyp = create_hypothesis("Test update", "crypto")
    save_hypothesis(hyp)

    result = runner.invoke(
        cli,
        [
            "update",
            hyp.id,
            "--status",
            "testing",
            "--strategy",
            "test_strategy",
            "--conclusion",
            "Test conclusion",
        ],
    )

    assert result.exit_code == 0
    assert "✓ Updated hypothesis:" in result.output
    assert "status → testing" in result.output
    assert "strategy → test_strategy" in result.output


def test_update_command_nonexistent(runner, temp_hypotheses_dir):
    """Test update command with nonexistent hypothesis."""
    result = runner.invoke(cli, ["update", "nonexistent_id", "--status", "testing"])

    assert result.exit_code == 1
    assert "not found" in result.output


def test_link_command(runner, temp_hypotheses_dir):
    """Test backtest link command."""
    hyp = create_hypothesis("Test link", "crypto")
    save_hypothesis(hyp)

    result = runner.invoke(cli, ["link", hyp.id, "backtest_20260210_143022"])

    assert result.exit_code == 0
    assert "✓ Linked backtest" in result.output


def test_link_command_nonexistent(runner, temp_hypotheses_dir):
    """Test link command with nonexistent hypothesis."""
    result = runner.invoke(cli, ["link", "nonexistent_id", "backtest_001"])

    assert result.exit_code == 1
    assert "not found" in result.output


def test_search_command_by_tag(runner, temp_hypotheses_dir):
    """Test search command by tag."""
    hyp1 = create_hypothesis("Momentum test", "crypto", tags=["momentum", "crypto"])
    hyp2 = create_hypothesis("Mean reversion", "forex", tags=["mean-reversion", "forex"])
    save_hypothesis(hyp1)
    save_hypothesis(hyp2)

    result = runner.invoke(cli, ["search", "--tags", "momentum"])

    assert result.exit_code == 0
    assert "Total: 1 hypothesis(es)" in result.output
    assert hyp1.id in result.output
    assert hyp2.id not in result.output


def test_search_command_by_asset_class(runner, temp_hypotheses_dir):
    """Test search command by asset class."""
    hyp1 = create_hypothesis("Crypto test", "crypto")
    hyp2 = create_hypothesis("Forex test", "forex")
    save_hypothesis(hyp1)
    save_hypothesis(hyp2)

    result = runner.invoke(cli, ["search", "--asset-class", "crypto"])

    assert result.exit_code == 0
    assert "Total: 1 hypothesis(es)" in result.output
    assert hyp1.id in result.output
    assert hyp2.id not in result.output


def test_search_command_multiple_tags(runner, temp_hypotheses_dir):
    """Test search command with multiple tags."""
    hyp1 = create_hypothesis("Test 1", "crypto", tags=["momentum", "crypto"])
    hyp2 = create_hypothesis("Test 2", "forex", tags=["momentum", "forex"])
    hyp3 = create_hypothesis("Test 3", "equities", tags=["mean-reversion"])
    save_hypothesis(hyp1)
    save_hypothesis(hyp2)
    save_hypothesis(hyp3)

    result = runner.invoke(cli, ["search", "--tags", "momentum", "--tags", "crypto"])

    assert result.exit_code == 0
    # Should find hypotheses with at least one matching tag
    assert hyp1.id in result.output
    assert hyp2.id in result.output
    assert hyp3.id not in result.output


def test_show_command(runner, temp_hypotheses_dir):
    """Test show command displays hypothesis details."""
    hyp = create_hypothesis(
        "Test show",
        "crypto",
        description="Detailed description",
        symbols=["BTC-USD"],
        timeframe="daily",
        tags=["momentum", "crypto"],
    )
    hyp.why = "Test rationale"
    hyp.expected_sharpe = 1.5
    save_hypothesis(hyp)

    result = runner.invoke(cli, ["show", hyp.id])

    assert result.exit_code == 0
    assert hyp.id in result.output
    assert "Test show" in result.output
    assert "crypto" in result.output
    assert "Detailed description" in result.output
    assert "BTC-USD" in result.output
    assert "daily" in result.output
    assert "Test rationale" in result.output
    assert "1.5" in result.output


def test_show_command_nonexistent(runner, temp_hypotheses_dir):
    """Test show command with nonexistent hypothesis."""
    result = runner.invoke(cli, ["show", "nonexistent_id"])

    assert result.exit_code == 1
    assert "not found" in result.output
