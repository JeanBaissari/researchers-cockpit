"""
Generate test coverage report for lib/ using pytest-cov.

Runs pytest with coverage on the lib package and writes:
- Terminal report with missing lines (term-missing)
- HTML report to htmlcov/

Usage:
    python scripts/coverage_report.py [pytest args...]

Examples:
    python scripts/coverage_report.py
    python scripts/coverage_report.py tests/config/ -q
"""

import subprocess
import sys
from pathlib import Path

# Project root for resolving paths
project_root = Path(__file__).resolve().parent.parent


def main() -> int:
    tests_dir = project_root / "tests"
    htmlcov_dir = project_root / "htmlcov"
    args = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",
        "--cov=lib",
        "--cov-report=term-missing",
        f"--cov-report=html:{htmlcov_dir}",
        "--cov-fail-under=0",  # Report only; do not fail on low coverage
    ]
    args.extend(sys.argv[1:])
    result = subprocess.run(args, cwd=str(project_root))
    if result.returncode == 0:
        print(f"\nHTML report: {htmlcov_dir / 'index.html'}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
