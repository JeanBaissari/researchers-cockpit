"""
Tests for Zipline-Reloaded metrics inventory documentation.

Verifies that the metrics inventory document exists and contains expected sections.
"""

from pathlib import Path


def test_metrics_inventory_exists():
    """Test that metrics inventory document exists."""
    inventory_path = Path(__file__).parent.parent.parent / "docs" / "api" / "metrics_inventory.md"
    assert inventory_path.exists(), "metrics_inventory.md should exist"


def test_metrics_inventory_structure():
    """Test that metrics inventory has expected sections."""
    inventory_path = Path(__file__).parent.parent.parent / "docs" / "api" / "metrics_inventory.md"
    content = inventory_path.read_text()

    # Check for key sections
    assert "Zipline-Reloaded Metrics System Inventory" in content
    assert "Performance DataFrame Columns" in content
    assert "Built-in Metrics Classes" in content
    assert "Metrics Sets" in content
    assert "Custom Metrics with record()" in content
    assert "Comparison with Project Metrics" in content
    assert "Usage Patterns" in content
    assert "Best Practices" in content


def test_metrics_inventory_columns():
    """Test that inventory documents expected DataFrame columns."""
    inventory_path = Path(__file__).parent.parent.parent / "docs" / "api" / "metrics_inventory.md"
    content = inventory_path.read_text()

    # Check for key columns
    assert "portfolio_value" in content
    assert "returns" in content
    assert "sharpe" in content
    assert "sortino" in content
    assert "max_drawdown" in content
    assert "alpha" in content
    assert "beta" in content


def test_metrics_inventory_zipline_references():
    """Test that inventory references Zipline-Reloaded correctly."""
    inventory_path = Path(__file__).parent.parent.parent / "docs" / "api" / "metrics_inventory.md"
    content = inventory_path.read_text()

    # Check for Zipline-Reloaded references
    assert "stefan-jansen/zipline-reloaded" in content
    assert "Zipline-Reloaded v3.0+" in content
    assert "zipline.finance.metrics" in content


def test_metrics_inventory_project_comparison():
    """Test that inventory compares with project metrics."""
    inventory_path = Path(__file__).parent.parent.parent / "docs" / "api" / "metrics_inventory.md"
    content = inventory_path.read_text()

    # Check for project metrics references
    assert "lib/metrics/" in content
    assert "calculate_metrics" in content
