# Re-ingest Bundles

## Overview

Re-ingest bundles from registry to update stale data, fix issues, or rebuild after schema changes.

## Steps

1. **Select Bundles** - Choose bundles to re-ingest (all, specific, or filtered)
2. **Check Registry** - Verify bundle entries in registry
3. **Re-ingest Bundles** - Run ingestion with original parameters
4. **Verify Results** - Confirm bundles were successfully re-ingested
5. **Update Registry** - Ensure registry reflects updated bundles

## Checklist

- [ ] Bundles selected for re-ingestion
- [ ] Registry entries verified
- [ ] Re-ingestion completed successfully
- [ ] Results verified (bundle exists, data present)
- [ ] Registry updated if needed

## Re-ingestion Patterns

**Re-ingest all bundles:**
```bash
# Re-ingest all bundles from registry
python scripts/reingest_all.py
```

**Re-ingest specific bundles:**
```bash
# Re-ingest specific bundles
python scripts/reingest_all.py --bundles yahoo_equities_daily,yahoo_crypto_1h
```

**Re-ingest filtered bundles:**
```bash
# Re-ingest only daily bundles
python scripts/reingest_all.py --timeframe daily

# Re-ingest only crypto bundles
python scripts/reingest_all.py --assets crypto

# Re-ingest bundles from specific source
python scripts/reingest_all.py --source yahoo
```

**Dry run (preview):**
```bash
# Show what would be re-ingested without doing it
python scripts/reingest_all.py --dry-run
```

**Force re-ingest (skip confirmation):**
```bash
# Re-ingest without confirmation prompts
python scripts/reingest_all.py --force
```

**Re-ingest programmatically:**
```python
from lib.bundles import ingest_bundle, load_bundle_registry

registry = load_bundle_registry()
bundle_name = 'yahoo_crypto_daily'
bundle_info = registry[bundle_name]

result = ingest_bundle(
    source=bundle_info['source'],
    assets=bundle_info['assets'],
    timeframe=bundle_info['timeframe'],
    bundle_name=bundle_name,
    start_date=bundle_info.get('start_date'),
    end_date=bundle_info.get('end_date')
)
print(f"Re-ingested {bundle_name}")
```

**Re-ingest all bundles programmatically:**
```python
from lib.bundles import ingest_bundle, load_bundle_registry

registry = load_bundle_registry()
for bundle_name, bundle_info in registry.items():
    try:
        ingest_bundle(
            source=bundle_info['source'],
            assets=bundle_info['assets'],
            timeframe=bundle_info['timeframe'],
            bundle_name=bundle_name,
            start_date=bundle_info.get('start_date'),
            end_date=bundle_info.get('end_date')
        )
        print(f"✓ {bundle_name}")
    except Exception as e:
        print(f"✗ {bundle_name}: {e}")
```

## When to Re-ingest

- **Data Updates** - Refresh stale data with latest market data
- **Bug Fixes** - Re-ingest after fixing ingestion bugs
- **Schema Changes** - Rebuild bundles after data format changes
- **Missing Data** - Fill gaps in existing bundles
- **New Symbols** - Add new symbols to existing bundles

## Notes

- Use `lib/bundles/` ingestion functions (don't duplicate ingestion logic)
- Reference `scripts/reingest_all.py` for CLI patterns
- Use existing bundle registry for metadata
- Re-ingestion can take time for large bundles
- Verify bundles after re-ingestion with validate-bundles.md

## Related Commands

- validate-bundles.md - For validating bundles after re-ingestion
- explore-data.md - For exploring re-ingested bundle contents

