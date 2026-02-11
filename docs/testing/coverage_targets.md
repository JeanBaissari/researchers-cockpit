# Critical Coverage Targets

## Target

**80%+** aggregate line coverage for critical lib/ modules (as defined by the PRD).

## Critical Modules

Critical modules are value-add and foundational code paths:

| Module | Purpose |
|--------|--------|
| `lib/paths.py` | Project root detection |
| `lib/utils.py` | Core utilities |
| `lib/config/core.py` | Configuration loading |
| `lib/config/strategy.py` | Strategy parameter loading |
| `lib/logging/config.py` | Logging setup |
| `lib/bundles/access.py` | Bundle access |
| `lib/bundles/management.py` | Bundle management |
| `lib/backtest/runner.py` | Backtest orchestration |
| `lib/backtest/preprocessing.py` | Pre-flight validation |
| `lib/validation/api.py` | Data validation API |
| `lib/metrics/core.py` | Metrics orchestration |

## How to Verify

Run the verification script (requires pytest and pytest-cov):

```bash
python scripts/verify_critical_coverage.py
```

- **Exit 0**: Aggregate coverage for critical modules is ≥ 80%.
- **Exit 1**: Below target or coverage JSON could not be produced.

Dry run (print result, always exit 0):

```bash
python scripts/verify_critical_coverage.py --dry-run
```

## Exceptions and Next Steps

If coverage is below 80%, the script prints per-file coverage. Prioritize adding tests for the lowest-coverage critical modules. Full test suite:

```bash
pytest tests/ -v
```

Generate HTML coverage report:

```bash
python scripts/coverage_report.py
```
