"""
Tests for Report API documentation.

Verifies that docs/api/report.md exists and documents Performance DataFrame
integration, including columns used by report section builders.
"""

from pathlib import Path

import pytest

from lib.paths import get_project_root


@pytest.fixture
def report_api_path():
    """Path to Report API document."""
    return get_project_root() / "docs" / "api" / "report.md"


class TestReportApiDocExists:
    """Test Report API document exists and is readable."""

    def test_report_api_doc_exists(self, report_api_path):
        """Report API document exists."""
        assert report_api_path.exists(), f"Report API doc not found at {report_api_path}"

    def test_report_api_doc_readable(self, report_api_path):
        """Report API document is readable and non-empty."""
        content = report_api_path.read_text(encoding="utf-8")
        assert len(content) > 0, "Report API document is empty"


class TestReportApiPerformanceDataframeSection:
    """Test Report API documents Performance DataFrame integration."""

    def test_has_performance_dataframe_integration_section(self, report_api_path):
        """Report API has Performance DataFrame Integration section."""
        content = report_api_path.read_text(encoding="utf-8")
        assert "## Performance DataFrame Integration" in content

    def test_documents_data_sources(self, report_api_path):
        """Report API documents performance.pkl and returns.csv data sources."""
        content = report_api_path.read_text(encoding="utf-8")
        assert "performance.pkl" in content
        assert "returns.csv" in content
        assert "Data Source" in content or "Data source" in content

    def test_documents_perf_columns_used_by_reports(self, report_api_path):
        """Report API documents which Performance DataFrame columns are used."""
        content = report_api_path.read_text(encoding="utf-8")
        # Columns used by build_zipline_metrics_section and build_time_series_summary
        assert "alpha" in content
        assert "beta" in content
        assert "benchmark_period_return" in content
        assert "algorithm_period_return" in content
        assert "gross_leverage" in content
        assert "net_leverage" in content
        assert "sharpe" in content
        assert "sortino" in content
        assert "max_drawdown" in content
        assert "returns" in content

    def test_documents_section_builder_functions(self, report_api_path):
        """Report API documents load_performance_dataframe and section builders."""
        content = report_api_path.read_text(encoding="utf-8")
        assert "load_performance_dataframe" in content
        assert "build_zipline_metrics_section" in content
        assert "build_time_series_summary" in content

    def test_documents_column_to_section_mapping(self, report_api_path):
        """Report API documents column-to-report-section mapping."""
        content = report_api_path.read_text(encoding="utf-8")
        assert "Benchmark Comparison" in content
        assert "Leverage Analysis" in content
        assert "Time-Series Metrics" in content or "Time-Series Summary" in content

    def test_references_performance_dataframe_integration_doc(self, report_api_path):
        """Report API references performance_dataframe_integration.md."""
        content = report_api_path.read_text(encoding="utf-8")
        assert "performance_dataframe_integration.md" in content
        assert (
            "Performance DataFrame Integration" in content
            or "performance_dataframe_integration" in content
        )
