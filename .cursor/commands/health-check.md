# Health Check

## Overview

Perform comprehensive system health check including data integrity, configuration validation, and environment status.

## Steps

1. **Check Data Bundles** - Validate bundle integrity and completeness
2. **Validate Configuration** - Check config files for errors
3. **Verify Symlinks** - Ensure symlinks are valid and point to correct locations
4. **Check Disk Space** - Verify sufficient disk space available
5. **Validate Python Environment** - Check Python version and dependencies
6. **Check Logs** - Review recent log files for errors
7. **Generate Health Report** - Create comprehensive health status report

## Checklist

- [ ] Data bundles validated for integrity
- [ ] Configuration files checked for errors
- [ ] Symlinks verified (not broken)
- [ ] Disk space checked (sufficient available)
- [ ] Python version validated
- [ ] Dependencies installed and compatible
- [ ] Recent logs reviewed for errors
- [ ] Health report generated

## Health Check Patterns

**Validate data bundles:**
```python
from lib.bundles import validate_bundle
from lib.paths import get_data_dir

def check_bundles():
    """Check data bundle integrity."""
    data_dir = get_data_dir() / 'bundles'
    issues = []
    
    for bundle_dir in data_dir.iterdir():
        if bundle_dir.is_dir():
            try:
                validate_bundle(bundle_dir.name)
            except Exception as e:
                issues.append(f"Bundle {bundle_dir.name}: {e}")
    
    return issues
```

**Check configuration:**
```python
from lib.config import load_settings
try:
    load_settings()
except Exception as e:
    issues.append(f"Settings error: {e}")
```

**Verify symlinks:**
```python
from lib.utils import check_and_fix_symlinks
broken = check_and_fix_symlinks(get_results_dir())
```

**Check disk space:**
```python
import shutil
free_gb = shutil.disk_usage(path).free / (1024**3)
if free_gb < min_gb:
    return f"Low disk space: {free_gb:.2f} GB"
```

**Validate Python:**
```python
import sys
if sys.version_info < (3, 9, 0):
    return "Python version incompatible"
```

## Health Report Format

**Report structure:**
```markdown
# System Health Report
## Data Bundles: ✅ All valid
## Configuration: ✅ All valid
## Symlinks: ⚠️ 1 broken (fixed)
## Disk Space: ✅ 50.2 GB available
## Python: ✅ 3.11.0 (compatible)
```

## Notes

- Run health checks regularly (weekly recommended)
- Fix critical issues immediately
- Monitor disk space for data growth
- Validate bundles after data ingestion
- Check symlinks after result generation

## Related Commands

- validate-bundles.md - For detailed bundle validation
- audit-dependencies.md - For dependency health
- backup-results.md - For backup integrity checks

