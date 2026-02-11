# Validation Suite

Comprehensive validation testing framework for The Researcher's Cockpit.

**Location:** `scripts/validation_suite.py`

**Purpose:** End-to-end validation of system integrity, data quality, and component functionality.

---

## Overview

The Validation Suite provides automated testing of all critical system components:

1. **Configuration Validation** - Settings and configuration files
2. **Data Validation** - OHLCV data quality and integrity
3. **Bundle Validation** - Zipline bundle integrity and availability
4. **Component Validation** - Individual module functionality
5. **Integration Validation** - End-to-end workflows

---

## Quick Start

```bash
# Run complete validation suite
python scripts/validation_suite.py

# Run quick checks only (skip integration tests)
python scripts/validation_suite.py --quick

# Run specific validation component
python scripts/validation_suite.py --data-only
python scripts/validation_suite.py --bundles-only
python scripts/validation_suite.py --component=metrics

# Generate detailed report
python scripts/validation_suite.py --report

# Verbose output
python scripts/validation_suite.py --verbose
```

---

## Validation Components

### 1. Configuration Validation

Validates system configuration files and settings:

- **Settings File**: `config/settings.yaml` loads successfully
- **Required Sections**: Common sections present (data, backtest, logging)
- **Structure**: Configuration has expected structure

**What It Checks:**
- File existence and readability
- YAML parsing
- Section presence
- Basic structure

**Does NOT Check:**
- Detailed value validation (that's done at runtime)
- Schema compliance (flexible configuration)

### 2. Data Validation

Validates OHLCV data quality using sample data:

- **Schema Validation**: Required columns present (open, high, low, close, volume)
- **OHLC Consistency**: High ≥ Low, Close/Open within range
- **Data Quality**: No NaN, negative prices, or invalid values
- **Timeframe**: Appropriate bar count for timeframe

**Sample Data:**
- 10 days of daily equity data
- Valid OHLCV structure
- Timezone-aware index

**What It Checks:**
- Data validator functionality
- Asset-specific validation rules
- Configuration options (strict vs lenient)

### 3. Bundle Validation

Validates existing Zipline bundles:

- **Bundle Existence**: Bundle data files exist on disk
- **Metadata**: Bundle metadata is accessible
- **Integrity**: Bundle structure is valid

**What It Checks:**
- All registered bundles
- Bundle data availability
- Bundle metadata consistency

**Note:** Fresh installations with no bundles will skip this (normal).

### 4. Component Validation

Validates individual library components:

- **Metrics Module**: Sharpe ratio, Sortino ratio calculations
- **Logging Module**: Logger configuration and functionality
- **Config Module**: Settings loading

**What It Checks:**
- Module imports
- Basic functionality
- Sample calculations

**Does NOT Check:**
- Comprehensive functionality (that's in unit tests)
- Performance benchmarks
- Edge cases

### 5. Integration Validation

Validates end-to-end workflows:

- **Pre-Ingestion Workflow**: Data validation → Quality checks
- **Post-Backtest Workflow**: Results validation → Metrics verification
- **Complete Pipeline**: Pre-ingest → Backtest → Post-validation

**What It Checks:**
- Workflow orchestration
- Data flow between components
- Result consistency

---

## Command-Line Options

### Basic Options

| Option | Description |
|--------|-------------|
| `--quick` | Run quick checks only (skip integration tests) |
| `--data-only` | Run data validation only |
| `--bundles-only` | Run bundle validation only |
| `--component TEXT` | Run specific component validation |
| `--report` | Generate detailed JSON report |
| `-v, --verbose` | Enable verbose output |

### Component Options

Valid values for `--component`:

- `config` - Configuration validation
- `data` - Data validation
- `bundles` - Bundle validation
- `components` - Component validation
- `integration` - Integration validation

---

## Output Format

### Console Output

```
================================================================================
RESEARCHER'S COCKPIT - COMPREHENSIVE VALIDATION SUITE
================================================================================

────────────────────────────────────────────────────────────────────────────────
1. CONFIGURATION VALIDATION
────────────────────────────────────────────────────────────────────────────────
  ✓ config/settings.yaml loaded successfully
  ✓ Section 'data' present
  ✓ Section 'backtest' present
  ✓ Configuration has 2 common sections

────────────────────────────────────────────────────────────────────────────────
2. DATA VALIDATION
────────────────────────────────────────────────────────────────────────────────
  ✓ Equity data validation passed

... (additional sections) ...

================================================================================
VALIDATION SUMMARY
================================================================================
Total validation runs: 6
Passed: 6
Failed: 0

Total checks performed: 45
Errors found: 0
Warnings found: 0

Execution time: 0.15s

================================================================================
✓ ALL VALIDATION CHECKS PASSED
================================================================================
```

### JSON Report

Generated with `--report` flag:

```json
{
  "timestamp": "2026-02-09T10:30:45.123456",
  "summary": {
    "total_results": 6,
    "passed": 6,
    "failed": 0,
    "total_checks": 45,
    "total_errors": 0,
    "total_warnings": 0
  },
  "results": {
    "data_validation_equity": {
      "passed": true,
      "checks": 12,
      "errors": 0,
      "warnings": 0,
      "error_messages": [],
      "warning_messages": []
    },
    ...
  }
}
```

**Location:** `results/validation_report.json`

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All validation checks passed |
| `1` | Some validation checks failed or error occurred |

---

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Run Validation Suite
  run: python scripts/validation_suite.py --quick --report

- name: Upload Validation Report
  uses: actions/upload-artifact@v3
  with:
    name: validation-report
    path: results/validation_report.json
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run quick validation before commit
python scripts/validation_suite.py --quick

if [ $? -ne 0 ]; then
    echo "Validation failed. Commit aborted."
    exit 1
fi
```

---

## Troubleshooting

### Configuration Validation Fails

**Symptom:** Missing required sections

**Solution:**
1. Check `config/settings.yaml` exists
2. Verify YAML syntax is valid
3. Ensure common sections present (data, backtest, logging)

### Bundle Validation Fails

**Symptom:** Bundle integrity errors

**Common Causes:**
1. Fresh installation (no bundles ingested yet) - NORMAL
2. Corrupted bundle data
3. Missing bundle metadata

**Solution:**
1. Fresh installation: Ignore or run `--data-only`
2. Corrupted: Re-ingest bundle with `scripts/ingest_data.py`
3. Use `scripts/validate_bundles.py --fix` for metadata issues

### Integration Validation Fails

**Symptom:** Workflow validation errors

**Common Causes:**
1. Component API changes
2. Data format incompatibility
3. Missing dependencies

**Solution:**
1. Run individual component tests first
2. Check for API changes in recent commits
3. Verify all dependencies installed

---

## Related Tools

### Unit Tests

```bash
# Run all validation unit tests
python -m pytest tests/validation/ -v

# Run specific test module
python -m pytest tests/validation/test_data_validator.py -v
```

### Bundle Validation

```bash
# Validate specific bundle
python scripts/validate_bundles.py --bundle my_bundle

# Auto-fix bundle issues
python scripts/validate_bundles.py --fix
```

### Integration Tests

```bash
# Run integration tests
python -m pytest tests/validation/test_validation_integration.py -v
```

---

## Best Practices

### When to Run

**Required:**
- Before major releases
- After dependency updates
- After significant refactoring

**Recommended:**
- After adding new strategies
- After data ingestion
- Weekly as part of maintenance

**Optional:**
- Before each commit (quick mode)
- In CI/CD pipeline
- After configuration changes

### Interpreting Results

**All Passed:** System is healthy, proceed with confidence

**Some Failed:**
1. Review error messages
2. Determine if issue is critical
3. Fix critical issues before proceeding
4. Document non-critical warnings

**Multiple Failures:**
1. Run individual component tests
2. Isolate failing components
3. Check recent changes
4. Review logs for details

### Performance Considerations

- **Quick Mode:** ~0.1s (suitable for frequent runs)
- **Full Suite:** ~0.2-0.5s (reasonable for pre-commit)
- **With Report:** +0.05s (minimal overhead)

---

## Development

### Adding New Validation

1. **Add to ValidationSuite class:**
   ```python
   def run_new_validation(self) -> bool:
       """Validate new component."""
       with LogContext(phase="new_validation"):
           try:
               # Validation logic
               return True
           except Exception as e:
               logger.error(f"New validation failed: {e}")
               return False
   ```

2. **Update run_all() method:**
   ```python
   def run_all(self) -> bool:
       # ... existing validations ...
       self.run_new_validation()
       # ... rest of code ...
   ```

3. **Add command-line option (optional):**
   ```python
   @click.option('--new-only', is_flag=True, help='Run new validation only')
   def main(new_only, ...):
       if new_only:
           success = suite.run_new_validation()
   ```

4. **Add tests:**
   ```python
   # tests/validation/test_validation_integration.py
   def test_new_validation():
       """Test new validation component."""
       # Test implementation
   ```

### Testing Changes

```bash
# Run validation suite
python scripts/validation_suite.py --verbose

# Run integration tests
python -m pytest tests/validation/test_validation_integration.py -v

# Generate report
python scripts/validation_suite.py --report
```

---

## See Also

- [Validation API](../api/validation.md) - Data validation API
- [Validate API](../api/validate.md) - Strategy validation API
- [Bundle Validation](../troubleshooting/data_validation.md) - Bundle troubleshooting
- [Testing](../testing/quick_validations.md) - Quick validation checks

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** Production Ready
