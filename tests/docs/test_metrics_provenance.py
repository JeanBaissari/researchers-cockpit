"""
Tests for metrics provenance documentation.

Verifies that docs/api/metrics_provenance.md exists and documents
Zipline-Reloaded vs lib/metrics/ provenance correctly.
"""

from pathlib import Path


def _provenance_path():
    """Path to metrics provenance document."""
    return Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "metrics_provenance.md"


def test_metrics_provenance_exists():
    """Metrics provenance document exists."""
    path = _provenance_path()
    assert path.exists(), "metrics_provenance.md should exist"


def test_metrics_provenance_structure():
    """Metrics provenance has expected sections."""
    path = _provenance_path()
    content = path.read_text(encoding="utf-8")

    assert "Metrics Provenance" in content
    assert "Zipline-Reloaded vs lib/metrics/" in content
    assert "Provenance Summary" in content
    assert "Zipline-Reloaded Metrics" in content
    assert "lib/metrics/ Metrics" in content
    assert "Overlapping Metrics" in content
    assert "Data Flow" in content
    assert "Recommendations" in content


def test_metrics_provenance_zipline_columns():
    """Provenance doc documents Zipline-produced columns."""
    path = _provenance_path()
    content = path.read_text(encoding="utf-8")

    assert "portfolio_value" in content
    assert "returns" in content
    assert "sharpe" in content
    assert "sortino" in content
    assert "max_drawdown" in content
    assert "alpha" in content
    assert "beta" in content


def test_metrics_provenance_lib_metrics_only():
    """Provenance doc documents metrics produced only by lib/metrics/."""
    path = _provenance_path()
    content = path.read_text(encoding="utf-8")

    assert "calmar" in content
    assert "omega" in content
    assert "tail_ratio" in content
    assert "win_rate" in content
    assert "profit_factor" in content
    assert "trade_count" in content or "trade-level" in content.lower()


def test_metrics_provenance_overlapping():
    """Provenance doc explains overlapping metrics (same name, different source)."""
    path = _provenance_path()
    content = path.read_text(encoding="utf-8")

    assert "rolling" in content or "full-period" in content
    assert "lib/metrics" in content or "lib/metrics/" in content
    assert "Zipline" in content or "zipline" in content


def test_metrics_provenance_references():
    """Provenance doc references related docs and Zipline-Reloaded."""
    path = _provenance_path()
    content = path.read_text(encoding="utf-8")

    assert "metrics_inventory" in content or "Metrics Inventory" in content
    assert "performance_dataframe_integration" in content or "Performance DataFrame" in content
    assert "metrics.md" in content
    assert "stefan-jansen/zipline-reloaded" in content or "zipline-reloaded" in content
