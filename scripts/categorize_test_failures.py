"""
Categorize pytest failures into actionable buckets.

This module is intentionally lightweight and primarily exists to support
local developer workflows and the accompanying unit tests.
"""

from __future__ import annotations

# Standard library imports
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TestFailure:
    """Represents a single failing test case parsed from pytest output."""

    test_name: str
    failure_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    traceback: List[str] = field(default_factory=list)


@dataclass
class FailureCategory:
    """Aggregated failures for a given exception type."""

    exception_type: str
    count: int
    failures: List[TestFailure]
    common_patterns: List[str] = field(default_factory=list)


class TestFailureCategorizer:
    """Parse pytest output, categorize failures, and generate a short report."""

    _TEST_LINE_RE = re.compile(r"^(?P<name>.+?)\s+(?P<status>PASSED|FAILED|SKIPPED|ERROR)\s*$")
    _EXC_RE = re.compile(
        r"\b(?P<exc>AssertionError|ImportError|TypeError|AttributeError|ModuleNotFoundError)\b"
    )
    _FILE_LINE_RE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):\s+(?P<exc>.+?)\s*$")

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.categories: Dict[str, FailureCategory] = {}
        self.skipped_tests: List[str] = []
        self.passed_tests: int = 0
        self.total_tests: int = 0

    def run_tests(self, target: str, timeout_seconds: int = 300) -> str:
        """Run pytest for a target path and return stdout (or a TIMEOUT marker)."""
        try:
            result = subprocess.run(
                ["pytest", target],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return (result.stdout or "") + (result.stderr or "")
        except subprocess.TimeoutExpired:
            return "TIMEOUT: pytest exceeded allotted time"

    def parse_pytest_output(self, output: str) -> List[TestFailure]:
        """
        Parse pytest output to extract failures and basic pass/skip counts.

        This is a best-effort parser designed for human-friendly reporting,
        not a fully general pytest log parser.
        """
        self.passed_tests = 0
        self.total_tests = 0
        self.skipped_tests = []

        failed_or_errored_tests: List[str] = []

        # Only parse the per-test status lines that appear before the
        # detailed FAILURES/ERRORS sections to avoid double-counting.
        for line in output.splitlines():
            if line.strip().startswith("===="):
                break
            m = self._TEST_LINE_RE.match(line.strip())
            if not m:
                continue
            name = m.group("name")
            status = m.group("status")
            if status == "PASSED":
                self.passed_tests += 1
                self.total_tests += 1
            elif status in {"FAILED", "ERROR"}:
                self.total_tests += 1
                failed_or_errored_tests.append(name)
            elif status == "SKIPPED":
                self.skipped_tests.append(name)

        # Extract a best-effort exception type and message from the output.
        failure_type = self._infer_failure_type(output)
        message = self._infer_message(output)
        file_path, line_number = self._infer_file_location(output)

        failures: List[TestFailure] = []
        for test_name in list(dict.fromkeys(failed_or_errored_tests)):
            failures.append(
                TestFailure(
                    test_name=test_name,
                    failure_type=failure_type,
                    message=message,
                    file_path=file_path,
                    line_number=line_number,
                )
            )

        return failures

    def categorize_failures(self, failures: List[TestFailure]) -> Dict[str, FailureCategory]:
        """Group failures by `failure_type` and extract simple common patterns."""
        grouped: Dict[str, List[TestFailure]] = {}
        for f in failures:
            grouped.setdefault(f.failure_type, []).append(f)

        categories: Dict[str, FailureCategory] = {}
        for exc_type, exc_failures in grouped.items():
            patterns = self._extract_common_patterns([f.message for f in exc_failures])
            categories[exc_type] = FailureCategory(
                exception_type=exc_type,
                count=len(exc_failures),
                failures=exc_failures,
                common_patterns=patterns,
            )

        self.categories = categories
        return categories

    def generate_report(self) -> str:
        """Run tests, parse failures, categorize them, and render a short report."""
        output = self.run_tests("tests/")
        failures = self.parse_pytest_output(output)

        header = (
            f"Passed: {self.passed_tests}/{self.total_tests}\nSkipped: {len(self.skipped_tests)}\n"
        )

        if not failures:
            skipped = "\n".join(self.skipped_tests)
            return (
                header
                + "All tests passed.\n"
                + ("Skipped tests:\n" + skipped + "\n" if skipped else "")
            )

        categories = self.categorize_failures(failures)
        lines = [header, "Failures by category:"]
        for exc_type, category in sorted(categories.items(), key=lambda kv: kv[0]):
            lines.append(f"- {exc_type}: {category.count}")
            for f in category.failures:
                lines.append(f"  - {f.test_name}: {f.message}")
        return "\n".join(lines) + "\n"

    def _infer_failure_type(self, output: str) -> str:
        # Prefer ImportError over ModuleNotFoundError for simpler grouping.
        if "ImportError" in output:
            return "ImportError"
        m = self._EXC_RE.search(output)
        if m:
            exc = m.group("exc")
            if exc == "ModuleNotFoundError":
                return "ImportError"
            return exc
        return "UnknownError"

    def _infer_message(self, output: str) -> str:
        # Take the first "E   ..." line if present, otherwise the first "...Error:" line.
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("E   "):
                return stripped.replace("E   ", "", 1)
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.endswith("Error:") or "Error:" in stripped:
                return stripped
        return ""

    def _infer_file_location(self, output: str) -> tuple[Optional[str], Optional[int]]:
        for line in output.splitlines():
            m = self._FILE_LINE_RE.match(line.strip())
            if not m:
                continue
            try:
                return m.group("file"), int(m.group("line"))
            except ValueError:
                return m.group("file"), None
        return None, None

    def _extract_common_patterns(self, messages: List[str]) -> List[str]:
        counts: Dict[str, int] = {}
        for msg in messages:
            msg_norm = (msg or "").strip()
            if not msg_norm:
                continue
            counts[msg_norm] = counts.get(msg_norm, 0) + 1
        # Return patterns that appear more than once, most frequent first.
        common = [m for m, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])) if c > 1]
        return common[:5]


__all__ = [
    "TestFailure",
    "FailureCategory",
    "TestFailureCategorizer",
]
