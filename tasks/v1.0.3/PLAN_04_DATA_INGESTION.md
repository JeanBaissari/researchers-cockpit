# Data Ingestion Flow

Ensure proper bundle ingestion, registration, and loading for all data sources.

## Problem Statement

The current data ingestion implementation has several issues:

1. **Timezone Handling in yahoo_ingest():**
   - Complex timezone conversion chain that may produce incorrect results
   - Uses `tz_localize(calendar_obj.tz).tz_convert('UTC')` which assumes input is naive
   - yfinance returns data in different formats depending on interval

2. **Bundle Registration Persistence:**
   - `_register_yahoo_bundle()` creates closures but registration may not persist
   - Double registration call in `ingest_bundle()` is a code smell
   - `_auto_register_yahoo_bundle_if_exists()` has bare except clauses

3. **Calendar Integration:**
   - Uses `'24/7'` for crypto/forex but custom calendars use `'CRYPTO'`/`'FOREX'`
   - May fail if custom calendar not registered before ingestion

4. **Data Frequency Support:**
   - `data_frequency` parameter added but not fully integrated
   - yfinance minute data has different characteristics than daily

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Trace complete ingestion flow from script to bundle
- [ ] Identify yfinance data format variations

## Future Tasks

### Timezone Fixes
- [ ] Simplify `yahoo_ingest()` timestamp handling to use UTC throughout
- [ ] Handle yfinance timezone-aware returns correctly
- [ ] Test with both daily and minute data

### Bundle Registration Fixes
- [ ] Remove double registration call in `ingest_bundle()`
- [ ] Fix `_auto_register_yahoo_bundle_if_exists()` error handling
- [ ] Add bundle existence check before registration
- [ ] Ensure registration persists across module reloads

### Calendar Integration Fixes
- [ ] Align calendar names with extension.py (`'CRYPTO'`, `'FOREX'`)
- [ ] Register custom calendars before bundle ingestion
- [ ] Add calendar validation before ingestion

### Ingestion Script Improvements
- [ ] Add `--calendar` option to override auto-detection
- [ ] Add `--data-frequency` option for minute data
- [ ] Add progress bar for multi-symbol ingestion
- [ ] Add validation of ingested bundle

## Implementation Plan

### Step 1: Fix yahoo_ingest() Timestamp Handling

yfinance returns different formats:
- Daily data: DatetimeIndex with date only (no time), timezone-aware or naive
- Minute data: DatetimeIndex with datetime, usually exchange timezone

Correct approach:

```python
def yahoo_ingest(...):
    # ...
    
    def data_gen():
        for sid, symbol in enumerate(symbols_list):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(
                    start=start_session.strftime('%Y-%m-%d'),
                    end=end_session.strftime('%Y-%m-%d'),
                    interval='1d' if data_frequency == 'daily' else '1m'
                )
                
                if hist.empty:
                    print(f"Warning: No data for {symbol}")
                    continue
                
                # yfinance returns timezone-aware index
                # Convert to UTC, then strip timezone
                if hist.index.tz is not None:
                    hist.index = hist.index.tz_convert('UTC').tz_localize(None)
                else:
                    # Assume already UTC if no timezone
                    hist.index = pd.to_datetime(hist.index)
                
                # Prepare DataFrame
                bars_df = pd.DataFrame({
                    'open': hist['Open'],
                    'high': hist['High'],
                    'low': hist['Low'],
                    'close': hist['Close'],
                    'volume': hist['Volume'].fillna(0).astype(int),
                }, index=hist.index)
                
                yield sid, bars_df
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
```

### Step 2: Fix Bundle Registration

Remove double registration and add proper checks:

```python
def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    data_frequency: str = 'daily',
    **kwargs
) -> str:
    """Ingest data from a source into a Zipline bundle."""
    
    if symbols is None or len(symbols) == 0:
        raise ValueError("symbols parameter is required")
    
    # Get source config
    source_config = get_data_source(source)
    if not source_config.get('enabled', False):
        raise ValueError(f"Data source '{source}' is not enabled")
    
    # Auto-generate bundle name
    if bundle_name is None:
        asset_class = assets[0] if assets else 'equities'
        freq_suffix = 'minute' if data_frequency == 'minute' else 'daily'
        bundle_name = f"{source}_{asset_class}_{freq_suffix}"
    
    # Determine calendar - ALIGN WITH extension.py
    if calendar_name is None:
        if 'crypto' in assets:
            calendar_name = 'CRYPTO'  # Custom calendar from extension.py
        elif 'forex' in assets:
            calendar_name = 'FOREX'   # Custom calendar from extension.py
        else:
            calendar_name = 'XNYS'    # NYSE for equities
    
    # Register custom calendars if needed
    if calendar_name in ['CRYPTO', 'FOREX']:
        from .extension import register_custom_calendars
        register_custom_calendars(calendars=[calendar_name])
    
    # Set default dates
    if start_date is None:
        start_date = '2020-01-01'
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Ingest based on source
    if source == 'yahoo':
        return _ingest_yahoo_bundle(
            bundle_name=bundle_name,
            symbols=symbols,
            calendar_name=calendar_name,
            start_date=start_date,
            end_date=end_date,
            data_frequency=data_frequency
        )
    else:
        raise NotImplementedError(f"Source '{source}' not implemented")


def _ingest_yahoo_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    start_date: str,
    end_date: str,
    data_frequency: str
) -> str:
    """Ingest Yahoo Finance data into a bundle."""
    from zipline.data.bundles import ingest, bundles
    
    # Only register if not already registered
    if bundle_name not in bundles:
        _register_yahoo_bundle(
            bundle_name=bundle_name,
            symbols=symbols,
            calendar_name=calendar_name,
            start_date=start_date,
            data_frequency=data_frequency
        )
    
    # Ingest the bundle
    ingest(bundle_name, show_progress=True)
    return bundle_name
```

### Step 3: Fix Auto-Registration

```python
def _auto_register_yahoo_bundle_if_exists():
    """Auto-register yahoo_equities_daily bundle if data was ingested."""
    import os
    from pathlib import Path
    
    zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
    if not zipline_data_dir.exists():
        return
    
    try:
        from zipline.data.bundles import bundles
        if 'yahoo_equities_daily' not in bundles:
            _register_yahoo_bundle('yahoo_equities_daily', ['SPY'], 'XNYS')
    except ImportError:
        # Zipline not installed, skip
        pass
    except Exception as e:
        # Log but don't crash on registration failure
        import logging
        logging.getLogger(__name__).warning(f"Auto-registration failed: {e}")
```

### Step 4: Update ingest_data.py Script

```python
@click.command()
@click.option('--source', required=True, type=click.Choice(['yahoo', 'binance', 'oanda']))
@click.option('--assets', required=True, type=click.Choice(['crypto', 'forex', 'equities']))
@click.option('--symbols', required=True, help='Comma-separated symbols')
@click.option('--bundle-name', default=None)
@click.option('--start-date', default=None)
@click.option('--end-date', default=None)
@click.option('--calendar', default=None, type=click.Choice(['XNYS', 'XNAS', 'CRYPTO', 'FOREX']))
@click.option('--frequency', default='daily', type=click.Choice(['daily', 'minute']))
def main(source, assets, symbols, bundle_name, start_date, end_date, calendar, frequency):
    """Ingest market data into a Zipline bundle."""
    symbol_list = [s.strip() for s in symbols.split(',')]
    
    click.echo(f"Ingesting {frequency} data from {source} for {len(symbol_list)} symbols...")
    
    bundle = ingest_bundle(
        source=source,
        assets=[assets],
        bundle_name=bundle_name,
        symbols=symbol_list,
        start_date=start_date,
        end_date=end_date,
        calendar_name=calendar,
        data_frequency=frequency,
    )
    
    click.echo(f"✓ Successfully ingested bundle: {bundle}")
```

## Relevant Files

- `lib/data_loader.py` - Main ingestion logic
- `scripts/ingest_data.py` - CLI script
- `lib/extension.py` - Custom calendars (for calendar registration)
- `config/data_sources.yaml` - Source configuration

## Testing Checklist

```bash
# Test equities ingestion
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY,AAPL

# Test crypto ingestion (after calendar fix)
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD,ETH-USD

# Verify bundle exists
python -c "from zipline.data.bundles import bundles; print(list(bundles.keys()))"

# Verify bundle data
python -c "
from lib.data_loader import load_bundle
b = load_bundle('yahoo_equities_daily')
print(b.equity_daily_bar_reader.sessions[:5])
"
```
