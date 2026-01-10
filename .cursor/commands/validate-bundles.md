# Validate Bundles

## Overview

Validate data bundle integrity, registry consistency, and detect corruption to ensure data quality for backtesting.

## Steps

1. **Check Bundle Registry** - Verify registry entries are valid and consistent
2. **Validate Bundle Existence** - Confirm bundle directories exist on disk
3. **Verify Bundle Metadata** - Check metadata files are valid JSON
4. **Check Asset Files** - Verify asset data files are present
5. **Detect Corruption** - Identify corrupted or incomplete bundles
6. **Auto-Repair** - Fix common issues automatically (if supported)
7. **Generate Health Report** - Create summary of bundle health status

## Checklist

- [ ] Bundle registry integrity checked
- [ ] Bundle directories verified on disk
- [ ] Metadata files validated
- [ ] Asset files presence confirmed
- [ ] Corruption detected and reported
- [ ] Auto-repair attempted (if applicable)
- [ ] Health status report generated

## Validation Patterns

**Validate a single bundle:**
```python
from lib.validation import validate_bundle, ValidationResult
from lib.utils import get_project_root

# Validate bundle
result = validate_bundle('yahoo_crypto_daily')

# Check results
if result.passed:
    print(f"Bundle 'yahoo_crypto_daily' is valid")
else:
    print(f"Bundle validation failed:")
    for check in result.checks:
        if not check.passed:
            print(f"  - {check.name}: {check.message}")
```

**Validate all bundles from registry:**
```python
from lib.validation import validate_bundle
from lib.bundles import load_bundle_registry

registry = load_bundle_registry()
for bundle_name in registry.keys():
    result = validate_bundle(bundle_name)
    if result.passed:
        print(f"✓ {bundle_name}")
    else:
        print(f"✗ {bundle_name}: {[c.message for c in result.checks if not c.passed]}")
```

**Use CLI script:**
```bash
# Validate all bundles
python scripts/validate_bundles.py

# Validate specific bundle
python scripts/validate_bundles.py yahoo_crypto_daily

# Auto-fix issues
python scripts/validate_bundles.py --fix

# Verbose output
python scripts/validate_bundles.py --verbose
```

**Bundle health report:**
```python
from lib.validation import validate_bundle
from lib.bundles import load_bundle_registry
import pandas as pd

registry = load_bundle_registry()
health_report = []

for bundle_name in registry.keys():
    result = validate_bundle(bundle_name)
    health_report.append({
        'bundle': bundle_name,
        'status': 'healthy' if result.passed else 'unhealthy',
        'checks_passed': sum(1 for c in result.checks if c.passed),
        'checks_total': len(result.checks)
    })

df = pd.DataFrame(health_report)
print(df.to_string(index=False))
```

## Validation Checks

- **Bundle exists** - Directory present on disk
- **Metadata valid** - JSON file is valid and parseable
- **Assets present** - Asset data files exist
- **Data integrity** - Files are not corrupted

## Notes

- Use `lib/validation/bundle_validator.py:BundleValidator` (don't duplicate validation)
- Reference `scripts/validate_bundles.py` for CLI patterns
- Use existing bundle registry functions from `lib/bundles/`
- Validation is automatically performed during bundle ingestion
- Fix issues before running backtests to avoid data errors

## Related Commands

- explore-data.md - For exploring bundle contents before validation
- reingest-bundles.md - For re-ingesting bundles after fixing issues

