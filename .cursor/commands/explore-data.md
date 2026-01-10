# Explore Data

## Overview

Explore bundle contents, detect data gaps, summarize available data, and check data freshness for research and strategy development.

## Steps

1. **List Bundle Contents** - Display symbols, date ranges, and bar counts
2. **Detect Data Gaps** - Identify missing dates or symbols
3. **Summarize Available Data** - Create summary of what's available
4. **Check Data Freshness** - Verify data is up-to-date
5. **Identify Missing Symbols** - Find symbols not in bundle
6. **Check Timeframe Coverage** - Verify timeframe availability

## Checklist

- [ ] Bundle contents listed (symbols, date ranges)
- [ ] Data gaps detected and documented
- [ ] Available data summarized
- [ ] Data freshness verified
- [ ] Missing symbols identified
- [ ] Timeframe coverage checked

## Exploration Patterns

**List bundle contents:**
```python
from lib.bundles import get_bundle_symbols, list_bundles
from lib.utils import get_project_root

# List all available bundles
bundles = list_bundles()
print("Available bundles:")
for bundle in bundles:
    print(f"  - {bundle}")

# Get symbols in a bundle
symbols = get_bundle_symbols('yahoo_crypto_daily')
print(f"\nSymbols in yahoo_crypto_daily: {len(symbols)}")
for symbol in sorted(symbols):
    print(f"  - {symbol}")
```

**Use CLI script for detailed info:**
```bash
# Show info for a specific bundle
python scripts/bundle_info.py yahoo_crypto_daily

# List all bundles
python scripts/bundle_info.py --list

# Verbose output with health check
python scripts/bundle_info.py yahoo_crypto_daily --verbose
```

**Detect data gaps:**
```python
from lib.bundles import load_bundle
import pandas as pd

bundle = load_bundle('yahoo_crypto_daily')
data = bundle.load_data('BTC-USD', start_date='2020-01-01', end_date='2024-12-31')
date_range = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
missing_dates = date_range.difference(data.index)

if len(missing_dates) > 0:
    print(f"Missing {len(missing_dates)} dates")
else:
    print("No gaps detected")
```

**Summarize available data:**
```python
from lib.bundles import get_bundle_symbols, load_bundle_registry

registry = load_bundle_registry()
for bundle_name, bundle_info in registry.items():
    symbols = get_bundle_symbols(bundle_name)
    print(f"{bundle_name}: {len(symbols)} symbols, {bundle_info.get('timeframe', 'unknown')}")
```

**Check data freshness:**
```python
from lib.bundles import load_bundle
from datetime import datetime, timedelta

bundle = load_bundle('yahoo_crypto_daily')
data = bundle.load_data('BTC-USD', start_date='2024-12-01', end_date='2024-12-31')
latest_date = data.index.max()
cutoff = datetime.now() - timedelta(days=2)

if latest_date >= cutoff:
    print(f"Data is fresh: {latest_date.date()}")
else:
    print(f"Data may be stale: {latest_date.date()}")
```

## Key Information to Gather

- **Symbols** - What assets are available
- **Date Ranges** - Start and end dates for each symbol
- **Bar Counts** - Number of bars per symbol
- **Timeframes** - Available timeframes (daily, hourly, etc.)
- **Data Gaps** - Missing dates or periods
- **Freshness** - How recent is the data

## Notes

- Use `lib/bundles/` modules (don't duplicate bundle inspection)
- Reference `scripts/bundle_info.py` for CLI patterns
- Use existing bundle registry functions
- Check data gaps before backtesting to avoid surprises
- Verify data freshness for live trading strategies

## Related Commands

- validate-bundles.md - For validating bundle integrity
- reingest-bundles.md - For updating stale data

