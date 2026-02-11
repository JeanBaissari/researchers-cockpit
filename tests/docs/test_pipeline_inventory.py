"""
Tests for Pipeline inventory documentation.

Verifies that the Pipeline inventory document exists and contains
expected sections and information.
"""

from pathlib import Path
import pytest

from lib.paths import get_project_root


@pytest.fixture
def inventory_path():
    """Path to Pipeline inventory document."""
    project_root = get_project_root()
    return project_root / "docs" / "api" / "pipeline_inventory.md"


class TestPipelineInventory:
    """Test Pipeline inventory document structure and content."""

    def test_inventory_exists(self, inventory_path):
        """Verify inventory document exists."""
        assert inventory_path.exists(), f"Inventory not found at {inventory_path}"

    def test_inventory_readable(self, inventory_path):
        """Verify inventory document is readable."""
        content = inventory_path.read_text(encoding="utf-8")
        assert len(content) > 0, "Inventory document is empty"

    def test_inventory_has_table_of_contents(self, inventory_path):
        """Verify inventory has table of contents."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Table of Contents" in content, "Missing table of contents"

    def test_inventory_has_core_components(self, inventory_path):
        """Verify inventory documents core components."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Core Components" in content, "Missing core components section"
        assert "Pipeline Class" in content, "Missing Pipeline class documentation"
        assert "Term Types" in content, "Missing term types documentation"

    def test_inventory_has_builtin_factors(self, inventory_path):
        """Verify inventory documents built-in factors."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Built-in Factors" in content, "Missing built-in factors section"
        assert "Returns" in content, "Missing Returns factor"
        assert "SimpleMovingAverage" in content, "Missing SimpleMovingAverage factor"
        assert "BollingerBands" in content, "Missing BollingerBands factor"

    def test_inventory_has_builtin_filters(self, inventory_path):
        """Verify inventory documents built-in filters."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Built-in Filters" in content, "Missing built-in filters section"
        assert "StaticAssets" in content, "Missing StaticAssets filter"

    def test_inventory_has_common_filters_allpresent_isnan_notnan(self, inventory_path):
        """Verify inventory documents Common Filters: AllPresent, isnan, notnan."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "Common Filters: AllPresent, isnan, notnan" in content, (
            "Missing Common Filters section"
        )
        assert "AllPresent" in content, "Missing AllPresent filter example"
        assert "notnan()" in content or "notnan" in content, "Missing notnan filter example"
        assert "isnan()" in content or "isnan" in content, "Missing isnan filter example"
        assert "column availability" in content.lower() or "missing data" in content.lower(), (
            "Missing notes about column availability / missing data behavior"
        )

    def test_inventory_has_api_functions(self, inventory_path):
        """Verify inventory documents Pipeline API functions."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Pipeline API Functions" in content, "Missing API functions section"
        assert "attach_pipeline" in content, "Missing attach_pipeline()"
        assert "pipeline_output" in content, "Missing pipeline_output()"

    def test_inventory_has_factor_methods(self, inventory_path):
        """Verify inventory documents factor methods."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Factor Methods" in content, "Missing factor methods section"
        assert "rank()" in content, "Missing rank() method"
        assert "zscore()" in content, "Missing zscore() method"
        assert "top()" in content, "Missing top() method"

    def test_inventory_has_filter_operations(self, inventory_path):
        """Verify inventory documents filter operations."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Filter Operations" in content, "Missing filter operations section"
        assert "AND (&)" in content, "Missing AND operation"
        assert "OR (|)" in content, "Missing OR operation"

    def test_inventory_has_data_sources(self, inventory_path):
        """Verify inventory documents data sources."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Data Sources" in content, "Missing data sources section"
        assert "EquityPricing" in content, "Missing EquityPricing data source"

    def test_inventory_has_custom_factors(self, inventory_path):
        """Verify inventory documents custom factor creation."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Custom Factor Creation" in content, "Missing custom factors section"
        assert "CustomFactor" in content, "Missing CustomFactor class"

    def test_inventory_has_usage_patterns(self, inventory_path):
        """Verify inventory documents usage patterns."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Usage Patterns" in content, "Missing usage patterns section"
        assert "Momentum Strategy" in content, "Missing momentum strategy example"

    def test_inventory_has_best_practices(self, inventory_path):
        """Verify inventory documents best practices."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## Best Practices" in content, "Missing best practices section"

    def test_inventory_has_references(self, inventory_path):
        """Verify inventory has references section."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "## References" in content, "Missing references section"
        assert "zipline-reloaded" in content.lower(), "Missing Zipline-Reloaded reference"

    def test_inventory_mentions_zipline_reloaded(self, inventory_path):
        """Verify inventory mentions Zipline-Reloaded (not legacy Quantopian)."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "Zipline-Reloaded" in content, "Missing Zipline-Reloaded mention"
        assert "stefan-jansen" in content, "Missing stefan-jansen reference"

    def test_inventory_has_code_examples(self, inventory_path):
        """Verify inventory contains code examples."""
        content = inventory_path.read_text(encoding="utf-8")
        assert "```python" in content, "Missing Python code examples"
        assert "from zipline.pipeline" in content, "Missing Pipeline import examples"

    def test_inventory_structure_complete(self, inventory_path):
        """Verify inventory has all major sections."""
        content = inventory_path.read_text(encoding="utf-8")

        required_sections = [
            "Core Components",
            "Built-in Factors",
            "Built-in Filters",
            "Pipeline API Functions",
            "Factor Methods",
            "Filter Operations",
            "Data Sources",
            "Custom Factor Creation",
            "Usage Patterns",
            "Best Practices",
        ]

        for section in required_sections:
            assert f"## {section}" in content, f"Missing section: {section}"
