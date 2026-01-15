# Audit Dependencies

## Overview

Audit Python dependencies for outdated packages, security vulnerabilities, and compatibility issues.

## Steps

1. **Parse Dependencies** - Read requirements.txt or pyproject.toml
2. **Check Versions** - Compare installed versions against latest available
3. **Security Scan** - Run security vulnerability scan (safety, pip-audit)
4. **Compatibility Check** - Verify Python version compatibility
5. **Identify Unused** - Find dependencies not imported anywhere
6. **Generate Report** - Create audit report with recommendations

## Checklist

- [ ] Dependencies parsed from requirements.txt/pyproject.toml
- [ ] Package versions checked against latest
- [ ] Security vulnerabilities scanned
- [ ] Python version compatibility verified
- [ ] Unused dependencies identified
- [ ] Audit report generated with recommendations
- [ ] Update recommendations prioritized

## Dependency Audit Patterns

**Check outdated packages:**
```bash
# Using pip list
pip list --outdated

# Using pip-review
pip-review --local --auto

# Manual check
pip index versions package_name
```

**Security vulnerability scan:**
```bash
# Using safety
safety check

# Using pip-audit
pip-audit

# Using pip check
pip check
```

**Check unused dependencies:**
```python
# Using pipreqs to find actual imports
pipreqs . --force

# Compare with requirements.txt
# Dependencies in requirements.txt but not in imports
```

**Parse requirements.txt:**
```python
from pathlib import Path

def parse_requirements(file_path: Path):
    """Parse requirements.txt file."""
    requirements = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements
```

## Audit Report Format

**Report structure:**
```markdown
# Dependency Audit Report
Date: 2024-02-20

## Outdated Packages
- package_name: 1.0.0 → 2.0.0 (major update available)
- another_package: 0.5.0 → 0.5.3 (patch update)

## Security Vulnerabilities
- package_name==1.0.0: CVE-2024-1234 (High severity)
  Recommendation: Update to 1.0.1

## Unused Dependencies
- unused_package: Not imported anywhere
  Recommendation: Remove from requirements.txt

## Compatibility Issues
- package_name requires Python >= 3.10
  Current: Python 3.9
  Recommendation: Upgrade Python or downgrade package
```

## Notes

- Run audit regularly (monthly recommended)
- Prioritize security vulnerabilities
- Test updates in development before production
- Document breaking changes in major updates
- Keep requirements.txt and pyproject.toml in sync

## Related Commands

- health-check.md - For overall system health
- check-code-quality.md - For code quality checks











