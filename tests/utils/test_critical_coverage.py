"""
Tests for critical coverage verification feature.

Verifies that scripts/verify_critical_coverage.py exists, defines
critical modules, and that coverage computation behaves correctly.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
script_path = project_root / "scripts" / "verify_critical_coverage.py"


def _load_script_module():
    """Load scripts/verify_critical_coverage as a module."""
    spec = importlib.util.spec_from_file_location("verify_critical_coverage", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {script_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verify_critical_coverage"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCriticalCoverageScriptExists:
    """Script file and options."""

    @pytest.mark.unit
    def test_script_exists(self):
        """scripts/verify_critical_coverage.py exists."""
        assert script_path.exists()
        content = script_path.read_text()
        assert "80" in content or "critical" in content.lower()

    @pytest.mark.unit
    def test_script_has_help(self):
        """Script --help exits 0."""
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "80" in result.stdout or "coverage" in result.stdout.lower()

    @pytest.mark.unit
    def test_script_has_dry_run(self):
        """Script supports --dry-run."""
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--dry-run" in result.stdout


class TestCriticalModuleList:
    """Critical modules list is defined and non-empty."""

    @pytest.mark.unit
    def test_critical_suffixes_non_empty(self):
        """CRITICAL_MODULE_SUFFIXES is non-empty."""
        mod = _load_script_module()
        suffixes = getattr(mod, "CRITICAL_MODULE_SUFFIXES", None)
        assert suffixes is not None
        assert len(suffixes) > 0

    @pytest.mark.unit
    def test_critical_suffixes_include_paths(self):
        """Critical list includes lib/paths.py."""
        mod = _load_script_module()
        suffixes = mod.CRITICAL_MODULE_SUFFIXES
        assert "lib/paths.py" in suffixes

    @pytest.mark.unit
    def test_critical_suffixes_include_config_and_validation(self):
        """Critical list includes config and validation modules."""
        mod = _load_script_module()
        suffixes = mod.CRITICAL_MODULE_SUFFIXES
        assert any("config" in s for s in suffixes)
        assert any("validation" in s for s in suffixes)


class TestIsCriticalFile:
    """_is_critical_file matching behavior."""

    @pytest.mark.unit
    def test_matches_lib_paths(self):
        """Matches path ending with lib/paths.py."""
        mod = _load_script_module()
        assert mod._is_critical_file("lib/paths.py") is True
        assert mod._is_critical_file("/abs/path/to/lib/paths.py") is True

    @pytest.mark.unit
    def test_does_not_match_random_path(self):
        """Does not match unrelated path."""
        mod = _load_script_module()
        assert mod._is_critical_file("lib/other.py") is False
        assert mod._is_critical_file("tests/test_foo.py") is False


class TestComputeCriticalCoverage:
    """compute_critical_coverage with mock JSON."""

    @pytest.mark.unit
    def test_compute_aggregates_one_file(self, tmp_path):
        """compute_critical_coverage returns aggregate for one critical file."""
        mod = _load_script_module()
        json_file = tmp_path / "coverage.json"
        json_file.write_text(
            json.dumps(
                {
                    "files": {
                        "lib/paths.py": {
                            "summary": {"num_statements": 10, "covered_lines": 8},
                        },
                    },
                }
            )
        )
        percent, details = mod.compute_critical_coverage(json_file)
        assert percent == 80.0
        assert details["total_covered"] == 8
        assert details["total_statements"] == 10
        assert len(details["files"]) == 1
        assert details["files"][0]["path"] == "lib/paths.py"
        assert details["files"][0]["pct"] == 80.0

    @pytest.mark.unit
    def test_compute_ignores_non_critical(self, tmp_path):
        """compute_critical_coverage ignores non-critical files."""
        mod = _load_script_module()
        json_file = tmp_path / "coverage.json"
        json_file.write_text(
            json.dumps(
                {
                    "files": {
                        "lib/paths.py": {
                            "summary": {"num_statements": 10, "covered_lines": 10},
                        },
                        "tests/conftest.py": {
                            "summary": {"num_statements": 100, "covered_lines": 0},
                        },
                    },
                }
            )
        )
        percent, details = mod.compute_critical_coverage(json_file)
        assert percent == 100.0
        assert len(details["files"]) == 1

    @pytest.mark.unit
    def test_compute_empty_files_zero_percent(self, tmp_path):
        """compute_critical_coverage returns 0 when no critical files."""
        mod = _load_script_module()
        json_file = tmp_path / "coverage.json"
        json_file.write_text(
            json.dumps(
                {
                    "files": {
                        "tests/conftest.py": {
                            "summary": {"num_statements": 10, "covered_lines": 5},
                        },
                    },
                }
            )
        )
        percent, details = mod.compute_critical_coverage(json_file)
        assert percent == 0.0
        assert len(details["files"]) == 0
