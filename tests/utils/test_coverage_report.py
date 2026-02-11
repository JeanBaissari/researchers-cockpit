"""
Tests for coverage report feature.

Verifies that coverage and pytest-cov are available and that the
coverage report script exists with expected options.
"""

from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent


class TestCoverageAvailability:
    """Coverage and pytest-cov availability."""

    @pytest.mark.unit
    def test_coverage_module_available(self):
        """Coverage package is installed and has Coverage class."""
        coverage = pytest.importorskip("coverage")
        assert hasattr(coverage, "Coverage")

    @pytest.mark.unit
    def test_pytest_cov_available(self):
        """pytest-cov plugin is installed."""
        pytest.importorskip("pytest_cov")


class TestCoverageReportScript:
    """Coverage report script exists and has expected options."""

    @pytest.mark.unit
    def test_coverage_report_script_exists(self):
        """scripts/coverage_report.py exists."""
        script = project_root / "scripts" / "coverage_report.py"
        assert script.exists()
        assert script.read_text().find("--cov=lib") != -1

    @pytest.mark.unit
    def test_coverage_report_script_has_html_output(self):
        """Script configures HTML report to htmlcov/."""
        script = project_root / "scripts" / "coverage_report.py"
        content = script.read_text()
        assert "htmlcov" in content
        assert "term-missing" in content
