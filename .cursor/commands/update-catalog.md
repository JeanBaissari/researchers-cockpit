# Update Catalog

## Overview

Update strategy catalog with current status and metrics to maintain accurate strategy inventory and track strategy lifecycle.

## Steps

1. **Load Strategy Metrics** - Load latest metrics from results directory
2. **Determine Strategy Status** - Assess status (testing/validated/abandoned)
3. **Update Catalog Entry** - Add or update strategy entry in catalog
4. **Sync Metrics** - Refresh metrics from latest results
5. **Maintain Catalog Format** - Ensure catalog follows standard format

## Checklist

- [ ] Strategy metrics loaded from latest results
- [ ] Strategy status determined (testing/validated/abandoned)
- [ ] Catalog entry updated or created
- [ ] Metrics synced from latest results
- [ ] Catalog format maintained

## Catalog Update Patterns

**Update single strategy:**
```python
from lib.report.catalog import update_catalog
from lib.backtest.results import load_backtest_results
from pathlib import Path
import json

strategy_name = 'btc_sma_cross'
results_dir = Path(f'results/{strategy_name}/latest')

# Load metrics
with open(results_dir / 'metrics.json') as f:
    metrics = json.load(f)

# Determine status based on metrics
if metrics['sharpe'] > 1.0 and metrics['max_drawdown'] < 0.20:
    status = 'validated'
elif metrics['sharpe'] < 0.0:
    status = 'abandoned'
else:
    status = 'testing'

# Update catalog
update_catalog(
    strategy_name=strategy_name,
    status=status,
    metrics=metrics,
    asset_class='crypto'
)
```

**Update all strategies:**
```python
from lib.report.catalog import update_catalog
from lib.utils import get_project_root
from pathlib import Path
import json

root = get_project_root()
results_base = root / 'results'

for strategy_dir in results_base.iterdir():
    if not strategy_dir.is_dir():
        continue
    
    strategy_name = strategy_dir.name
    metrics_file = strategy_dir / 'latest' / 'metrics.json'
    
    if metrics_file.exists():
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        status = 'testing'
        if metrics.get('sharpe', 0) > 1.0:
            status = 'validated'
        elif metrics.get('sharpe', 0) < 0.0:
            status = 'abandoned'
        
        update_catalog(strategy_name, status, metrics)
        print(f"Updated {strategy_name}: {status}")
```

## Strategy Status Values

- **testing** - Strategy under development or evaluation
- **validated** - Strategy meets performance criteria
- **abandoned** - Strategy failed validation or deprecated

## Catalog Format

The catalog is maintained in `docs/strategy_catalog.md` with entries for each strategy including:
- Strategy name
- Status
- Key metrics (Sharpe, Sortino, MaxDD, etc.)
- Asset class
- Last updated timestamp

## Notes

- Use `lib/report/catalog.py:update_catalog()` (don't duplicate catalog logic)
- Use `lib/utils.get_project_root()` for paths
- Single responsibility: catalog updates only
- Update catalog after significant backtest results
- Maintain consistent status determination logic

## Related Commands

- analyze-results.md - For analyzing results before updating catalog
- run-backtest.md - For running backtests that generate metrics
- generate-weekly-summary.md - For weekly catalog updates

