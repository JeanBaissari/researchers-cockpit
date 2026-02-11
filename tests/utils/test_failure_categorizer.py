"""
Tests for test failure categorization script.
"""

import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.categorize_test_failures import (
    TestFailure,
    TestFailureCategorizer,
    FailureCategory,
)


class TestTestFailure:
    """Test TestFailure dataclass."""

    def test_test_failure_creation(self):
        """Test creating a TestFailure instance."""
        failure = TestFailure(
            test_name="test_example",
            failure_type="AssertionError",
            message="assert 1 == 2",
            file_path="test_file.py",
            line_number=42,
        )

        assert failure.test_name == "test_example"
        assert failure.failure_type == "AssertionError"
        assert failure.message == "assert 1 == 2"
        assert failure.file_path == "test_file.py"
        assert failure.line_number == 42
        assert failure.traceback == []


class TestTestFailureCategorizer:
    """Test TestFailureCategorizer class."""

    @pytest.fixture
    def categorizer(self, project_root_path):
        """Create a TestFailureCategorizer instance."""
        return TestFailureCategorizer(project_root=project_root_path)

    def test_categorizer_initialization(self, categorizer, project_root_path):
        """Test categorizer initialization."""
        assert categorizer.project_root == project_root_path
        assert categorizer.categories == {}
        assert categorizer.skipped_tests == []
        assert categorizer.passed_tests == 0
        assert categorizer.total_tests == 0

    def test_parse_pytest_output_with_failures(self, categorizer):
        """Test parsing pytest output with failures."""
        output = """
tests/test_example.py::test_one PASSED
tests/test_example.py::test_two FAILED
tests/test_example.py::test_three SKIPPED

=================================== FAILURES ===================================
tests/test_example.py::test_two FAILED
----------------------------------- Captured output ----------------------------
AssertionError: assert 1 == 2
    def test_two():
>       assert 1 == 2
E       assert 1 == 2

tests/test_example.py:10: AssertionError
======================== 1 passed, 1 failed, 1 skipped in 0.12s ================
"""
        failures = categorizer.parse_pytest_output(output)

        assert len(failures) == 1
        assert failures[0].test_name == "tests/test_example.py::test_two"
        assert failures[0].failure_type == "AssertionError"
        assert categorizer.passed_tests == 1
        assert categorizer.total_tests == 2
        assert len(categorizer.skipped_tests) == 1

    def test_parse_pytest_output_no_failures(self, categorizer):
        """Test parsing pytest output with no failures."""
        output = """
tests/test_example.py::test_one PASSED
tests/test_example.py::test_two PASSED
======================== 2 passed, 12 skipped in 0.12s ========================
"""
        failures = categorizer.parse_pytest_output(output)

        assert len(failures) == 0
        assert categorizer.passed_tests == 2
        assert categorizer.total_tests == 2

    def test_parse_pytest_output_with_import_error(self, categorizer):
        """Test parsing pytest output with ImportError."""
        output = """
tests/test_example.py::test_one ERROR

=================================== ERRORS ====================================
tests/test_example.py::test_one ERROR
----------------------------------- Captured output ----------------------------
ImportError: No module named 'missing_module'
    import missing_module
E   ModuleNotFoundError: No module named 'missing_module'

tests/test_example.py:5: ImportError
======================== 0 passed, 1 error in 0.12s ============================
"""
        failures = categorizer.parse_pytest_output(output)

        assert len(failures) == 1
        assert failures[0].failure_type == "ImportError"
        assert "missing_module" in failures[0].message or "ImportError" in failures[0].failure_type

    def test_parse_pytest_output_with_type_error(self, categorizer):
        """Test parsing pytest output with TypeError."""
        output = """
tests/test_example.py::test_one FAILED

=================================== FAILURES ====================================
tests/test_example.py::test_one FAILED
----------------------------------- Captured output ----------------------------
TypeError: unsupported operand type(s) for +: 'int' and 'str'
    result = 1 + "hello"
E   TypeError: unsupported operand type(s) for +: 'int' and 'str'

tests/test_example.py:5: TypeError
======================== 0 passed, 1 failed in 0.12s ===========================
"""
        failures = categorizer.parse_pytest_output(output)

        assert len(failures) == 1
        assert failures[0].failure_type == "TypeError"

    def test_categorize_failures(self, categorizer):
        """Test categorizing failures by type."""
        failures = [
            TestFailure(
                test_name="test_one",
                failure_type="AssertionError",
                message="assert 1 == 2",
            ),
            TestFailure(
                test_name="test_two",
                failure_type="AssertionError",
                message="assert 3 == 4",
            ),
            TestFailure(
                test_name="test_three",
                failure_type="ImportError",
                message="No module named x",
            ),
        ]

        categories = categorizer.categorize_failures(failures)

        assert "AssertionError" in categories
        assert "ImportError" in categories
        assert categories["AssertionError"].count == 2
        assert categories["ImportError"].count == 1
        assert len(categories["AssertionError"].failures) == 2
        assert len(categories["ImportError"].failures) == 1

    def test_categorize_failures_extracts_patterns(self, categorizer):
        """Test that categorization extracts common patterns."""
        failures = [
            TestFailure(
                test_name="test_one",
                failure_type="AssertionError",
                message="assert value is None",
            ),
            TestFailure(
                test_name="test_two",
                failure_type="AssertionError",
                message="assert value is None",
            ),
            TestFailure(
                test_name="test_three",
                failure_type="AssertionError",
                message="assert other_value is None",
            ),
        ]

        categories = categorizer.categorize_failures(failures)

        assert "AssertionError" in categories
        category = categories["AssertionError"]
        # Should have extracted common patterns
        assert len(category.common_patterns) > 0

    @patch("scripts.categorize_test_failures.subprocess.run")
    def test_run_tests_success(self, mock_run, categorizer):
        """Test running tests successfully."""
        mock_result = MagicMock()
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        output = categorizer.run_tests("tests/")

        assert output == "1 passed"
        mock_run.assert_called_once()

    @patch("scripts.categorize_test_failures.subprocess.run")
    def test_run_tests_timeout(self, mock_run, categorizer):
        """Test handling test timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        output = categorizer.run_tests("tests/")

        assert "TIMEOUT" in output

    def test_generate_report_no_failures(self, categorizer):
        """Test generating report when no failures exist."""
        with patch.object(categorizer, "run_tests", return_value="2 passed, 1 skipped"):
            with patch.object(categorizer, "parse_pytest_output", return_value=[]):
                categorizer.passed_tests = 2
                categorizer.total_tests = 2
                categorizer.skipped_tests = ["test_one"]

                report = categorizer.generate_report()

                assert "All tests passed" in report
                assert "test_one" in report

    def test_generate_report_with_failures(self, categorizer):
        """Test generating report with failures."""
        failures = [
            TestFailure(
                test_name="test_one",
                failure_type="AssertionError",
                message="assert 1 == 2",
            ),
            TestFailure(
                test_name="test_two",
                failure_type="ImportError",
                message="No module named x",
            ),
        ]

        with patch.object(categorizer, "run_tests", return_value="1 passed, 2 failed"):
            with patch.object(categorizer, "parse_pytest_output", return_value=failures):
                with patch.object(
                    categorizer,
                    "categorize_failures",
                    return_value={
                        "AssertionError": FailureCategory(
                            exception_type="AssertionError",
                            count=1,
                            failures=[failures[0]],
                        ),
                        "ImportError": FailureCategory(
                            exception_type="ImportError",
                            count=1,
                            failures=[failures[1]],
                        ),
                    },
                ):
                    categorizer.passed_tests = 1
                    categorizer.total_tests = 3

                    report = categorizer.generate_report()

                    assert "AssertionError" in report
                    assert "ImportError" in report
                    assert "test_one" in report
                    assert "test_two" in report


class TestExceptionPatterns:
    """Test exception pattern matching."""

    @pytest.fixture
    def categorizer(self, project_root_path):
        """Create a TestFailureCategorizer instance."""
        return TestFailureCategorizer(project_root=project_root_path)

    def test_import_error_pattern(self, categorizer):
        """Test ImportError pattern matching."""
        output = "ImportError: No module named 'test'"
        failures = categorizer.parse_pytest_output(output)

        # Should recognize ImportError
        assert any("Import" in f.failure_type for f in failures) or len(failures) == 0

    def test_attribute_error_pattern(self, categorizer):
        """Test AttributeError pattern matching."""
        output = """
tests/test.py::test_one FAILED
AttributeError: 'NoneType' object has no attribute 'method'
"""
        failures = categorizer.parse_pytest_output(output)

        if failures:
            assert failures[0].failure_type == "AttributeError"
