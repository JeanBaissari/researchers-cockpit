"""
Verify test coverage for critical lib/ modules meets target (80%+).

Runs pytest with coverage, computes aggregate line coverage for critical
modules (as defined in this script and in docs/testing/coverage_targets.md),
and exits 0 if >= 80%, 1 otherwise.

Usage:
    python scripts/verify_critical_coverage.py [pytest args...]
    python scripts/verify_critical_coverage.py --dry-run
    python scripts/verify_critical_coverage.py --help
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Critical modules: path suffixes under project root (forward slashes).
# These are value-add and foundational modules per PRD (80%+ coverage target).
CRITICAL_MODULE_SUFFIXES = [
    "lib/paths.py",
    "lib/utils.py",
    "lib/config/core.py",
    "lib/config/strategy.py",
    "lib/logging/config.py",
    "lib/bundles/access.py",
    "lib/bundles/management.py",
    "lib/backtest/runner.py",
    "lib/backtest/preprocessing.py",
    "lib/validation/api.py",
    "lib/metrics/core.py",
]

COVERAGE_TARGET_PERCENT = 80.0


def _normalize_path(p: str) -> str:
    return str(Path(p).as_posix())


def _is_critical_file(file_path: str) -> bool:
    normalized = _normalize_path(file_path)
    # Match by suffix so we work with absolute or relative paths
    for suffix in CRITICAL_MODULE_SUFFIXES:
        if normalized.endswith(suffix):
            return True
    return False


def run_coverage_json(tests_dir: Path, extra_args: list) -> tuple[int, Path | None]:
    """Run pytest with coverage, write JSON to a temp file. Return (returncode, path)."""
    json_path = Path(tempfile.mkstemp(suffix=".json")[1])
    try:
        args = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_dir),
            "-q",
            "--no-cov-on-fail",
            "--cov=lib",
            f"--cov-report=json:{json_path}",
        ]
        args.extend(extra_args)
        result = subprocess.run(args, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        if not json_path.exists():
            return result.returncode, None
        return result.returncode, json_path
    except Exception:
        if json_path.exists():
            try:
                json_path.unlink()
            except OSError:
                pass
        raise


def compute_critical_coverage(json_path: Path) -> tuple[float, dict]:
    """
    Read coverage JSON and compute aggregate coverage for critical files.
    Returns (percent_covered, details_dict) where details has 'files' and 'total_covered', 'total_statements'.
    """
    with open(json_path) as f:
        data = json.load(f)
    files_data = data.get("files") or {}
    total_covered = 0
    total_statements = 0
    details_list = []
    for file_path, file_info in files_data.items():
        if not _is_critical_file(file_path):
            continue
        summary = file_info.get("summary") or {}
        num_statements = summary.get("num_statements") or 0
        covered_lines = summary.get("covered_lines") or summary.get("covered") or 0
        if num_statements == 0:
            continue
        total_covered += covered_lines
        total_statements += num_statements
        pct = 100.0 * covered_lines / num_statements if num_statements else 0
        details_list.append(
            {"path": file_path, "pct": pct, "covered": covered_lines, "total": num_statements}
        )
    percent = 100.0 * total_covered / total_statements if total_statements else 0.0
    return percent, {
        "files": details_list,
        "total_covered": total_covered,
        "total_statements": total_statements,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify 80%%+ test coverage for critical lib/ modules."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run coverage and print result; exit 0 regardless of target.",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Extra arguments passed to pytest (e.g. tests/config/).",
    )
    args = parser.parse_args()
    extra = list(args.pytest_args)

    tests_dir = PROJECT_ROOT / "tests"
    returncode, json_path = run_coverage_json(tests_dir, extra)
    if json_path is None:
        print("Coverage JSON was not produced; pytest may have failed.", file=sys.stderr)
        return returncode if returncode != 0 else 1
    percent, details = compute_critical_coverage(json_path)
    json_path.unlink(missing_ok=True)

    met = percent >= COVERAGE_TARGET_PERCENT
    if details["files"]:
        print(f"Critical modules coverage: {percent:.1f}% (target {COVERAGE_TARGET_PERCENT}%)")
        for f in details["files"]:
            print(f"  {f['path']}: {f['pct']:.1f}% ({f['covered']}/{f['total']})")
    else:
        print("No critical module files found in coverage report.", file=sys.stderr)
        return 1
    if args.dry_run:
        return 0
    return 0 if met else 1


if __name__ == "__main__":
    sys.exit(main())
