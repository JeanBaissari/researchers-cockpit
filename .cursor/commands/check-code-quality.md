# Check Code Quality

## Overview

Run comprehensive code quality checks including linting, type checking, complexity analysis, and SOLID/DRY compliance.

## Steps

1. **Run Linters** - Execute ruff, pylint, flake8 on codebase
2. **Type Checking** - Run mypy or pyright for type validation
3. **Complexity Analysis** - Calculate cyclomatic complexity
4. **SOLID/DRY Compliance** - Check against project standards
5. **File Size Check** - Verify lib/ files < 150 lines
6. **Generate Report** - Create quality report with metrics and violations

## Checklist

- [ ] Linters run (ruff, pylint, flake8)
- [ ] Type checking completed (mypy/pyright)
- [ ] Complexity analysis run
- [ ] SOLID/DRY compliance checked
- [ ] File sizes validated (< 150 lines for lib/)
- [ ] Quality report generated
- [ ] Violations flagged with suggestions

## Quality Check Patterns

**Run linters:**
```bash
# Ruff (fast, modern)
ruff check .

# Pylint (comprehensive)
pylint lib/ strategies/

# Flake8 (style)
flake8 lib/ strategies/
```

**Type checking:**
```bash
# Mypy
mypy lib/ --ignore-missing-imports

# Pyright
pyright lib/
```

**Complexity analysis:**
```bash
# Using radon
radon cc lib/ -a

# Using xenon
xenon --max-average A --max-modules B --max-absolute A lib/
```

**Check file sizes:**
```python
from pathlib import Path

def check_file_sizes(directory: Path, max_lines: int = 150):
    """Check file sizes against threshold."""
    violations = []
    for file_path in directory.rglob('*.py'):
        line_count = len(file_path.read_text().splitlines())
        if line_count > max_lines:
            violations.append((file_path, line_count))
    return violations
```

**SOLID/DRY compliance:**
```bash
# Check hardcoded paths (DIP violation)
grep -r "/home/" lib/  # Should use lib/paths
```

## Quality Report Format

**Report structure:**
```markdown
# Code Quality Report
Date: 2024-02-20

## Linting Results
- Ruff: 5 errors, 12 warnings
- Pylint: 3 errors, 8 warnings
- Flake8: 2 errors, 5 warnings

## Type Checking
- Mypy: 2 type errors
  - lib/backtest.py:45: Missing return type annotation

## Complexity
- High complexity functions (> 10):
  - lib/metrics.py:calculate_metrics() - Complexity: 15

## SOLID/DRY Violations
- lib/config.py: 180 lines (exceeds 150 line limit)
  Recommendation: Split into lib/config/core.py and lib/config/loader.py

## File Size Violations
- lib/metrics.py: 180 lines
- lib/backtest.py: 165 lines
```

## Notes

- Run quality checks before commits
- Fix critical violations first (errors > warnings)
- Use pre-commit hooks for automatic checks
- Set complexity thresholds (A = excellent, B = good, C = acceptable)
- Keep lib/ files < 150 lines (SOLID compliance)

## Related Commands

- code-review.md - For reviewing code changes
- github-commit.md - For pre-commit quality checks

