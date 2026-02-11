"""
Unit tests for hypothesis lifecycle management.

Tests hypothesis creation, saving, loading, listing, and linking functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime

from lib.research import (
    HypothesisStatus,
    Hypothesis,
    create_hypothesis,
    save_hypothesis,
    load_hypothesis,
    list_hypotheses,
    link_backtest,
)


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

    return hypotheses_dir


def test_create_hypothesis_generates_valid_id():
    """Test that create_hypothesis generates a valid ID with date prefix."""
    hyp = create_hypothesis(
        title="BTC momentum persistence",
        asset_class="crypto",
    )

    # ID should be YYYY-MM_slug format
    assert hyp.id.startswith(datetime.now().strftime("%Y-%m"))
    assert "btc_momentum" in hyp.id
    assert hyp.status == HypothesisStatus.DRAFT


def test_create_hypothesis_with_all_fields():
    """Test creating hypothesis with all optional fields."""
    hyp = create_hypothesis(
        title="Test Hypothesis",
        asset_class="forex",
        description="Detailed description",
        symbols=["EURUSD", "GBPUSD"],
        timeframe="1h",
        tags=["momentum", "forex"],
    )

    assert hyp.title == "Test Hypothesis"
    assert hyp.asset_class == "forex"
    assert hyp.description == "Detailed description"
    assert hyp.symbols == ["EURUSD", "GBPUSD"]
    assert hyp.timeframe == "1h"
    assert hyp.tags == ["momentum", "forex"]
    assert hyp.created == datetime.now().strftime("%Y-%m-%d")
    assert hyp.updated == datetime.now().strftime("%Y-%m-%d")


def test_save_and_load_hypothesis_roundtrip(temp_hypotheses_dir):
    """Test that saving and loading a hypothesis preserves all data."""
    # Create hypothesis
    original = create_hypothesis(
        title="Test roundtrip",
        asset_class="equities",
        description="Test description",
        symbols=["SPY"],
        timeframe="daily",
        tags=["test"],
    )

    # Add additional fields
    original.why = "Test rationale"
    original.expected_sharpe = 1.5
    original.strategy_name = "test_strategy"

    # Save
    file_path = save_hypothesis(original)
    assert file_path.exists()
    assert file_path.name == f"{original.id}.yaml"

    # Load
    loaded = load_hypothesis(original.id)

    # Verify all fields match
    assert loaded.id == original.id
    assert loaded.title == original.title
    assert loaded.asset_class == original.asset_class
    assert loaded.description == original.description
    assert loaded.symbols == original.symbols
    assert loaded.timeframe == original.timeframe
    assert loaded.why == original.why
    assert loaded.expected_sharpe == original.expected_sharpe
    assert loaded.strategy_name == original.strategy_name
    assert loaded.tags == original.tags
    assert loaded.status == original.status


def test_load_nonexistent_hypothesis_raises_error(temp_hypotheses_dir):
    """Test that loading a nonexistent hypothesis raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_hypothesis("nonexistent_id")


def test_list_hypotheses_empty(temp_hypotheses_dir):
    """Test listing hypotheses when directory is empty."""
    hypotheses = list_hypotheses()
    assert hypotheses == []


def test_list_hypotheses_with_status_filter(temp_hypotheses_dir):
    """Test listing hypotheses with status filter."""
    # Create hypotheses with different statuses
    draft = create_hypothesis("Draft hypothesis", "crypto")
    draft.status = HypothesisStatus.DRAFT
    save_hypothesis(draft)

    testing = create_hypothesis("Testing hypothesis", "forex")
    testing.status = HypothesisStatus.TESTING
    save_hypothesis(testing)

    validated = create_hypothesis("Validated hypothesis", "equities")
    validated.status = HypothesisStatus.VALIDATED
    save_hypothesis(validated)

    # Test filtering
    all_hyps = list_hypotheses()
    assert len(all_hyps) == 3

    draft_hyps = list_hypotheses(HypothesisStatus.DRAFT)
    assert len(draft_hyps) == 1
    assert draft_hyps[0].status == HypothesisStatus.DRAFT

    testing_hyps = list_hypotheses(HypothesisStatus.TESTING)
    assert len(testing_hyps) == 1
    assert testing_hyps[0].status == HypothesisStatus.TESTING

    validated_hyps = list_hypotheses(HypothesisStatus.VALIDATED)
    assert len(validated_hyps) == 1
    assert validated_hyps[0].status == HypothesisStatus.VALIDATED


def test_list_hypotheses_skips_template_files(temp_hypotheses_dir):
    """Test that list_hypotheses skips files starting with underscore."""
    # Create regular hypothesis
    hyp = create_hypothesis("Regular hypothesis", "crypto")
    save_hypothesis(hyp)

    # Create template file (should be skipped)
    template_path = temp_hypotheses_dir / "_template.yaml"
    template_path.write_text("id: template\nstatus: draft")

    hypotheses = list_hypotheses()
    assert len(hypotheses) == 1
    assert hypotheses[0].id == hyp.id


def test_link_backtest_appends_to_list(temp_hypotheses_dir):
    """Test that link_backtest appends backtest ID to hypothesis."""
    hyp = create_hypothesis("Test linking", "crypto")
    save_hypothesis(hyp)

    # Link first backtest
    link_backtest(hyp.id, "backtest_001")
    loaded = load_hypothesis(hyp.id)
    assert "backtest_001" in loaded.backtest_ids
    assert len(loaded.backtest_ids) == 1

    # Link second backtest
    link_backtest(hyp.id, "backtest_002")
    loaded = load_hypothesis(hyp.id)
    assert "backtest_001" in loaded.backtest_ids
    assert "backtest_002" in loaded.backtest_ids
    assert len(loaded.backtest_ids) == 2


def test_link_backtest_prevents_duplicates(temp_hypotheses_dir):
    """Test that link_backtest doesn't add duplicate backtest IDs."""
    hyp = create_hypothesis("Test duplicates", "forex")
    save_hypothesis(hyp)

    # Link same backtest twice
    link_backtest(hyp.id, "backtest_001")
    link_backtest(hyp.id, "backtest_001")

    loaded = load_hypothesis(hyp.id)
    assert loaded.backtest_ids.count("backtest_001") == 1
    assert len(loaded.backtest_ids) == 1


def test_link_backtest_updates_timestamp(temp_hypotheses_dir):
    """Test that link_backtest updates the updated timestamp."""
    hyp = create_hypothesis("Test timestamp", "equities")
    original_updated = hyp.updated
    save_hypothesis(hyp)

    # Link backtest (may need to wait a moment to ensure different timestamp)
    import time

    time.sleep(0.1)

    link_backtest(hyp.id, "backtest_001")
    loaded = load_hypothesis(hyp.id)

    # Updated timestamp should be today
    assert loaded.updated == datetime.now().strftime("%Y-%m-%d")


def test_link_backtest_nonexistent_hypothesis_raises_error(temp_hypotheses_dir):
    """Test that linking to nonexistent hypothesis raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        link_backtest("nonexistent_id", "backtest_001")


def test_hypothesis_status_enum_values():
    """Test that HypothesisStatus enum has correct values."""
    assert HypothesisStatus.DRAFT.value == "draft"
    assert HypothesisStatus.TESTING.value == "testing"
    assert HypothesisStatus.VALIDATED.value == "validated"
    assert HypothesisStatus.REJECTED.value == "rejected"
