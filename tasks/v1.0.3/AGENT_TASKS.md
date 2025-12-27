# AGENT_TASKS.md - Complete Realignment Execution Plan

This file contains all tasks for realigning v1_researchers_cockpit with Zipline-Reloaded 3.1.0 standards. Tasks are ordered for sequential execution by Claude Code agents.

## Agent Instructions

1. Execute tasks in order (Phase 1 → Phase 2 → Phase 3)
2. Mark tasks `[x]` when complete
3. If a task fails, note the error and continue to next task
4. After completing a phase, run the phase test before proceeding

---

## Phase 1: Foundation (Execute First)

### 1.1 Import Path Fix (PLAN_07)

**File:** `lib/backtest.py`

- [ ] Change line 33-36 from:
  ```python
  from v1_researchers_cockpit.zipline.extension import (
      register_custom_calendars,
      get_calendar_for_asset_class,
  )
  ```
  To:
  ```python
  from .extension import (
      register_custom_calendars,
      get_calendar_for_asset_class,
  )
  ```

**Test:** `python -c "from lib.backtest import run_backtest; print('OK')"`

---

### 1.2 UTC Timezone Standardization (PLAN_01)

**File:** `lib/utils.py`

- [ ] Replace `normalize_to_calendar_timezone()` function with:
  ```python
  def normalize_to_utc(dt: Union[pd.Timestamp, datetime, str]) -> pd.Timestamp:
      """
      Normalize a datetime to UTC timezone-naive timestamp.
      
      Zipline-Reloaded uses UTC internally. All timestamps should be:
      1. Converted to UTC if timezone-aware
      2. Made timezone-naive (Zipline interprets naive as UTC)
      
      Args:
          dt: Datetime (can be naive, aware, or string)
          
      Returns:
          Timezone-naive Timestamp in UTC
      """
      ts = pd.Timestamp(dt)
      
      if ts.tz is not None:
          ts = ts.tz_convert('UTC').tz_localize(None)
      
      return ts
  ```

- [ ] Keep `normalize_to_calendar_timezone()` as deprecated alias:
  ```python
  def normalize_to_calendar_timezone(
      dt: Union[pd.Timestamp, datetime],
      calendar_tz: str = 'America/New_York',
      time_of_day: str = '00:00:00'
  ) -> pd.Timestamp:
      """DEPRECATED: Use normalize_to_utc() instead."""
      import warnings
      warnings.warn("normalize_to_calendar_timezone is deprecated, use normalize_to_utc", DeprecationWarning)
      return normalize_to_utc(dt)
  ```

**File:** `lib/backtest.py`

- [ ] In `_validate_bundle_date_range()` (around line 222-223), change:
  ```python
  start_ts = normalize_to_calendar_timezone(start_date, calendar_tz=calendar_tz, time_of_day=time_of_day)
  end_ts = normalize_to_calendar_timezone(end_date, calendar_tz=calendar_tz, time_of_day=time_of_day)
  ```
  To:
  ```python
  from .utils import normalize_to_utc
  start_ts = normalize_to_utc(start_date)
  end_ts = normalize_to_utc(end_date)
  ```

- [ ] Remove time-of-day assertions (lines 444-447):
  ```python
  # DELETE THESE LINES:
  assert start_ts.time() == pd.Timestamp(time_of_day).time(), ...
  assert end_ts.time() == pd.Timestamp(time_of_day).time(), ...
  ```

- [ ] Update `_normalize_performance_dataframe()` (around line 486-491):
  ```python
  def _normalize_performance_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
      """Normalize performance DataFrame index to timezone-naive UTC."""
      perf_normalized = perf.copy()
      if perf_normalized.index.tz is not None:
          perf_normalized.index = perf_normalized.index.tz_convert('UTC').tz_localize(None)
      return perf_normalized
  ```

---

### 1.3 Calendar Integration (PLAN_02)

**File:** `lib/extension.py`

- [ ] Add calendar alias support after `_CALENDAR_REGISTRY`:
  ```python
  _CALENDAR_ALIASES = {
      '24/7': 'CRYPTO',
      'ALWAYS_OPEN': 'CRYPTO',
      'FX': 'FOREX',
      'CURRENCY': 'FOREX',
  }
  
  def resolve_calendar_name(name_or_alias: str) -> Optional[str]:
      """Resolve calendar name from alias."""
      upper = name_or_alias.upper()
      if upper in _CALENDAR_REGISTRY:
          return upper
      return _CALENDAR_ALIASES.get(upper)
  ```

**File:** `lib/data_loader.py`

- [ ] In `ingest_bundle()` (around line 256-262), change calendar detection:
  ```python
  # Auto-detect calendar using canonical names
  if calendar_name is None:
      if 'crypto' in assets:
          calendar_name = 'CRYPTO'
      elif 'forex' in assets:
          calendar_name = 'FOREX'
      else:
          calendar_name = 'XNYS'
  
  # Register custom calendars if needed
  if calendar_name in ['CRYPTO', 'FOREX']:
      from .extension import register_custom_calendars
      register_custom_calendars(calendars=[calendar_name])
  ```

**File:** `lib/backtest.py`

- [ ] In `run_backtest()` (around line 427-428), fix calendar registration:
  ```python
  # Register custom calendars before getting trading calendar
  if config.asset_class:
      calendar_name = get_calendar_for_asset_class(config.asset_class)
      if calendar_name:
          register_custom_calendars(calendars=[calendar_name])
  ```

**Phase 1 Test:**
```bash
python -c "
from lib.backtest import run_backtest
from lib.extension import register_custom_calendars, get_registered_calendars
from lib.utils import normalize_to_utc
import pandas as pd

# Test UTC normalization
ts = normalize_to_utc('2024-01-15')
assert ts.tz is None, 'Should be timezone-naive'
print('✓ UTC normalization')

# Test calendar registration
results = register_custom_calendars(['CRYPTO', 'FOREX'])
print(f'✓ Calendars registered: {get_registered_calendars()}')

print('Phase 1 Complete')
"
```

---

## Phase 2: Data Flow (Execute Second)

### 2.1 Data Ingestion Fixes (PLAN_04)

**File:** `lib/data_loader.py`

- [ ] Fix `yahoo_ingest()` timestamp handling (around line 177-179):
  ```python
  # Simplify to UTC conversion
  if hist.index.tz is not None:
      hist.index = hist.index.tz_convert('UTC').tz_localize(None)
  else:
      hist.index = pd.to_datetime(hist.index)
  ```

- [ ] Fix `_auto_register_yahoo_bundle_if_exists()` (around line 24-34):
  ```python
  def _auto_register_yahoo_bundle_if_exists():
      """Auto-register yahoo_equities_daily bundle if data was ingested."""
      from pathlib import Path
      import logging
      
      zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
      if not zipline_data_dir.exists():
          return
      
      try:
          from zipline.data.bundles import bundles
          if 'yahoo_equities_daily' not in bundles:
              _register_yahoo_bundle('yahoo_equities_daily', ['SPY'], 'XNYS')
      except ImportError:
          pass  # Zipline not installed
      except Exception as e:
          logging.getLogger(__name__).warning(f"Auto-registration failed: {e}")
  ```

- [ ] Remove duplicate registration in `ingest_bundle()` (remove lines 281-286)

---

### 2.2 Pipeline API Fix (PLAN_03)

**File:** `strategies/_template/strategy.py`

- [ ] Change Pipeline imports (around line 11-14):
  ```python
  # Optional Pipeline imports
  _PIPELINE_AVAILABLE = False
  try:
      from zipline.api import attach_pipeline, pipeline_output
      from zipline.pipeline import Pipeline
      from zipline.pipeline.data import EquityPricing  # Generic, not USEquityPricing
      from zipline.pipeline.factors import SimpleMovingAverage
      _PIPELINE_AVAILABLE = True
  except ImportError:
      pass
  ```

- [ ] Update `make_pipeline()` (around line 105-120):
  ```python
  def make_pipeline():
      """Create Pipeline with generic pricing data."""
      if not _PIPELINE_AVAILABLE:
          return None
      sma_30 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
      return Pipeline(columns={'sma_30': sma_30}, screen=sma_30.isfinite())
  ```

**File:** `strategies/_template/parameters.yaml`

- [ ] Add asset_class and use_pipeline fields:
  ```yaml
  strategy:
    asset_symbol: SPY
    asset_class: equities          # 'equities', 'crypto', 'forex'
    rebalance_frequency: daily
    minutes_after_open: 30
    use_pipeline: false            # Enable Pipeline API (default: false)
    lookback_period: 30
  ```

**Phase 2 Test:**
```bash
python -c "
from lib.data_loader import list_bundles, load_bundle
print(f'Available bundles: {list_bundles()}')

# Verify Pipeline import works
try:
    from zipline.pipeline.data import EquityPricing
    print('✓ EquityPricing import works')
except ImportError as e:
    print(f'✗ EquityPricing import failed: {e}')

print('Phase 2 Complete')
"
```

---

## Phase 3: Polish (Execute Last)

### 3.1 Debug Log Removal (PLAN_06)

**File:** `lib/backtest.py`

- [ ] Remove ALL blocks matching this pattern:
  ```python
  # #region agent log
  with open('/home/jeanbaissari/Documents/Programming/python-projects/algorithmic_trading/.cursor/debug.log', 'a') as f:
      f.write(json.dumps({...}) + '\n')
  # #endregion
  ```

- [ ] Search for `#region agent log` and delete from `# #region` to `# #endregion` inclusive

- [ ] Verify with: `grep -n "debug.log" lib/backtest.py` (should return nothing)

---

### 3.2 Error Handling Fixes (PLAN_06)

**File:** `lib/data_loader.py`

- [ ] Fix bare except at line 33:
  ```python
  # Change from:
  except:
      pass
  # To:
  except Exception:
      pass
  ```

- [ ] Fix bare except at line 39:
  ```python
  # Change from:
  except:
      pass
  # To:
  except Exception:
      pass
  ```

**File:** `lib/__init__.py`

- [ ] All try/except ImportError blocks are correct (no changes needed)

---

### 3.3 Logging Setup (PLAN_06)

**Create new file:** `lib/logging_config.py`

- [ ] Create file with content:
  ```python
  """Centralized logging configuration for The Researcher's Cockpit."""
  
  import logging
  import sys
  from pathlib import Path
  from typing import Optional
  
  
  def setup_logging(
      level: str = 'INFO',
      log_file: Optional[Path] = None
  ) -> logging.Logger:
      """Configure logging for the application."""
      format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      
      root_logger = logging.getLogger('researchers_cockpit')
      root_logger.setLevel(getattr(logging, level.upper()))
      
      if not root_logger.handlers:
          console_handler = logging.StreamHandler(sys.stdout)
          console_handler.setFormatter(logging.Formatter(format_string))
          root_logger.addHandler(console_handler)
          
          if log_file:
              file_handler = logging.FileHandler(log_file)
              file_handler.setFormatter(logging.Formatter(format_string))
              root_logger.addHandler(file_handler)
      
      return root_logger
  
  
  def get_logger(name: str) -> logging.Logger:
      """Get a child logger for a module."""
      return logging.getLogger(f'researchers_cockpit.{name}')
  ```

**Phase 3 Test:**
```bash
python -c "
# Verify no debug logs remain
import subprocess
result = subprocess.run(['grep', '-r', 'debug.log', 'lib/'], capture_output=True, text=True)
if result.stdout:
    print('✗ Debug logs still present')
    print(result.stdout)
else:
    print('✓ No debug logs found')

# Test logging config
from lib.logging_config import setup_logging, get_logger
setup_logging(level='DEBUG')
logger = get_logger('test')
logger.info('Test message')
print('✓ Logging works')

print('Phase 3 Complete')
"
```

---

## Final Validation

After all phases complete, run:

```bash
# Full import test
python -c "
from lib import (
    run_backtest, save_results,
    load_settings, load_strategy_params,
    calculate_metrics,
    register_custom_calendars,
)
print('✓ All imports successful')
"

# Verify no hardcoded paths
grep -r "v1_researchers_cockpit" lib/

# List of expected outputs:
# - No grep matches for hardcoded paths
# - All imports work without errors
```

---

## Summary Checklist

### Phase 1
- [x] 1.1 Import path fixed
- [x] 1.2 UTC timezone standardization complete
- [x] 1.3 Calendar integration aligned
- [x] Phase 1 test passes

### Phase 2
- [x] 2.1 Data ingestion fixes applied
- [x] 2.2 Pipeline API aligned
- [x] Phase 2 test passes

### Phase 3
- [x] 3.1 Debug logs removed
- [x] 3.2 Error handling fixed
- [x] 3.3 Logging config created
- [x] Phase 3 test passes

### Final
- [x] All imports work
- [x] No hardcoded paths
- [x] Ready for backtest execution

---

## Completion Notes

**Completed:** 2025-12-27

**Changes Made:**
1. Created `lib/extension.py` as wrapper for `.zipline/extension.py`
2. Added `normalize_to_utc()` function, deprecated `normalize_to_calendar_timezone()`
3. Added calendar aliases (`_CALENDAR_ALIASES`) and `resolve_calendar_name()`
4. Simplified timestamp handling in `yahoo_ingest()` to use UTC
5. Changed `USEquityPricing` to `EquityPricing` in strategy template
6. Made Pipeline imports optional with `_PIPELINE_AVAILABLE` flag
7. Removed all 18 debug log blocks from `lib/backtest.py`
8. Created `lib/logging_config.py` for centralized logging
9. Updated `lib/__init__.py` to export extension functions
