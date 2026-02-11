# Architectural Validation Checklist
## The Researcher's Cockpit — Codebase Architect Approval Template

> This checklist ensures all strategies comply with SOLID/DRY/modularity principles (v1.11.0+).

---

## SOLID Principles Compliance

### Single Responsibility
- [ ] Each file has ONE clear purpose
- [ ] Strategy.py only contains strategy logic (no data loading, no reporting)
- [ ] Parameters.yaml only contains configuration (no logic)
- [ ] Hypothesis.md only contains trading rationale (no code)

### Open/Closed Principle
- [ ] Strategy extends template pattern without modifying base template
- [ ] New strategies created by copying template, not modifying existing strategies
- [ ] lib/ modules used as-is without modification

### Liskov Substitution
- [ ] Strategy can be swapped with any other strategy in backtest runner
- [ ] All strategies follow same interface (initialize, handle_data, analyze)
- [ ] No special cases or conditional logic based on strategy name

### Interface Segregation
- [ ] Strategy only imports what it needs (no unused imports)
- [ ] Uses specific lib.config functions, not importing entire lib
- [ ] No bloated dependencies

### Dependency Inversion
- [ ] Strategy depends on abstractions (lib.config, lib.bundles)
- [ ] No hardcoded paths or values
- [ ] All configuration externalized to parameters.yaml

---

## DRY Principle Compliance

### Code Reuse
- [ ] NO duplicated code from template
- [ ] Uses lib.config.load_strategy_params() (not custom parameter loading)
- [ ] Uses lib.position_sizing functions (not custom position sizing)
- [ ] Uses lib.risk_management functions (not custom risk logic)
- [ ] Uses lib.bundles for data access (not direct file I/O)

### Configuration Reuse
- [ ] Uses canonical bundle names (csv_{symbol}_{timeframe})
- [ ] Uses standard FOREX calendar (no custom calendar per strategy)
- [ ] Reuses standard parameters (stop_loss_pct, trailing_stop_pct, etc.)

### Pattern Reuse
- [ ] Follows _template/strategy.py structure exactly
- [ ] Uses same hypothesis.md template format
- [ ] Uses same parameters.yaml structure

---

## Modularity Compliance

### File Size Limits
- [ ] strategy.py < 500 lines (ideally < 300)
- [ ] hypothesis.md < 400 lines (comprehensive but focused)
- [ ] parameters.yaml < 200 lines

### Function Complexity
- [ ] No function > 50 lines
- [ ] initialize() delegates to helper functions if complex
- [ ] handle_data() delegates to compute_signals() helper
- [ ] analyze() uses lib.metrics, not custom metric calculation

### Module Boundaries
- [ ] Clear separation: hypothesis (WHY) vs parameters (WHAT) vs strategy (HOW)
- [ ] No cross-boundary violations (no code in hypothesis.md, no prose in strategy.py)

---

## Import Path Compliance (v1.11.0+)

### Canonical Imports
- [ ] Uses `from lib.config import load_strategy_params` (not `lib.config.load_strategy_params()`)
- [ ] Uses `from lib.bundles import load_bundle` (not deprecated paths)
- [ ] Uses `from lib.validation import validate_bundle` (not lib.data_validation)
- [ ] Uses `from lib.calendars import get_calendar_for_asset_class` (not lib.extension)
- [ ] NO backward-compatibility imports (all removed in v1.11.0)

### Import Organization
```python
# Standard library
import sys
import warnings
from pathlib import Path

# Third-party
import numpy as np
import pandas as pd
from zipline.api import ...

# Local (v1.11.0+ canonical paths)
from lib.paths import get_project_root
from lib.config import load_strategy_params, get_warmup_days
from lib.position_sizing import compute_position_size
from lib.risk_management import check_exit_conditions
from lib.pipeline_utils import setup_pipeline
```

---

## Parameter Externalization

### Hardcoded Values Prohibited
- [ ] NO magic numbers in strategy.py (all parameters from YAML)
- [ ] NO hardcoded symbols (use parameters.yaml: asset_symbol)
- [ ] NO hardcoded bundle names (use parameters.yaml: backtest.bundle)
- [ ] NO hardcoded dates (use backtest runner CLI arguments)

### Required Parameters
- [ ] strategy.asset_symbol: Symbol to trade
- [ ] strategy.asset_class: 'forex', 'crypto', or 'equities'
- [ ] strategy.rebalance_frequency: 'daily', 'weekly', 'monthly'
- [ ] position_sizing.method: 'fixed', 'volatility_scaled', 'kelly'
- [ ] risk.stop_loss_pct: Stop loss percentage
- [ ] backtest.bundle: Bundle name
- [ ] backtest.warmup_days: Warmup period

---

## Bundle and Calendar Compliance

### Bundle Naming
- [ ] Follows convention: `csv_{symbol}_{timeframe}`
- [ ] Examples: `csv_eurusd_15m`, `csv_nzdjpy_1h`, `csv_eurusd_1d`
- [ ] NO duplicate timeframe suffixes (csv_eurusd_1h_1h)

### Calendar Selection
- [ ] Forex strategies use FOREX calendar (24/5 trading, 260 days/year)
- [ ] Auto-selected by asset_class: forex (no manual override needed)
- [ ] Timezone handling: All UTC internally (Zipline standard)

### Data Frequency
- [ ] Matches bundle timeframe: 1m/5m/15m/30m = 'minute', 1h/4h = 'minute', 1d = 'daily'
- [ ] Set in parameters.yaml: backtest.data_frequency

---

## Hypothesis Documentation Quality

### Required Sections
- [ ] The Belief: Clear statement of edge being exploited
- [ ] The Reasoning: Market mechanics explanation
- [ ] The Conditions: When strategy works / fails
- [ ] The Falsification: Concrete failure criteria
- [ ] Parameter Sensitivity: Which params matter most
- [ ] Data Requirements: Minimum history, warmup period
- [ ] Risk Regime: How strategy performs across volatility environments
- [ ] Optimization Bounds: Valid parameter ranges

### Content Quality
- [ ] Hypothesis is falsifiable (specific failure criteria)
- [ ] Reasoning explains WHY edge exists (not just WHAT strategy does)
- [ ] Conditions specify market regimes (trending vs ranging, high vs low vol)
- [ ] References v1.11.0+ module paths (lib/bundles/, lib/validation/, etc.)

---

## Testing Requirements

### Pre-Deployment
- [ ] Strategy imports successfully: `python -c "from strategies.forex.{name}.strategy import *"`
- [ ] Parameters load successfully: `lib.config.load_strategy_params('{name}')`
- [ ] Bundle exists: Verify with `scripts/ingest_data.py --list-bundles`
- [ ] Warmup period validated: Check warmup_days >= max(indicator_periods)

### Smoke Test (1-month backtest)
- [ ] Backtest runs without errors on 30 days of data
- [ ] Generates at least 1 trade (strategy isn't too restrictive)
- [ ] No divide-by-zero errors
- [ ] No NaN propagation in signals
- [ ] Results save to correct directory: `results/{name}/backtest_{timestamp}/`

---

## Results Structure Compliance

### Output Files
- [ ] returns.csv exists
- [ ] positions.csv exists
- [ ] transactions.csv exists
- [ ] metrics.json exists
- [ ] parameters_used.yaml exists (copy of parameters.yaml)

### Symlink
- [ ] `results/{name}/latest` → most recent backtest
- [ ] Symlink created automatically by backtest runner

---

## Documentation Standards

### File Headers
- [ ] strategy.py has docstring explaining purpose
- [ ] hypothesis.md has YAML frontmatter (optional, but recommended)
- [ ] parameters.yaml has comments explaining each section

### Code Comments
- [ ] Complex signal logic has inline comments
- [ ] ALL parameters reference parameters.yaml source: `# From parameters.yaml: strategy.rsi_period`
- [ ] Exit conditions documented: `# Exit: opposite signal or stop loss`

---

## Anti-Patterns (Violations)

### ❌ PROHIBITED
- [ ] NO print() statements (use logger from lib.logging)
- [ ] NO hardcoded paths (use lib.paths.get_project_root())
- [ ] NO try/except fallback imports (all removed in v1.11.0)
- [ ] NO monolithic functions > 50 lines
- [ ] NO duplicated logic from other strategies (extract to lib/)
- [ ] NO custom metric calculation (use lib.metrics)
- [ ] NO direct pd.read_csv() (use lib.bundles)

---

## Approval Checklist Summary

### Strategy: ______________________
### Reviewer: Codebase Architect
### Date: ______________________

| Category | Pass/Fail | Notes |
|----------|-----------|-------|
| SOLID Principles | [ ] | |
| DRY Compliance | [ ] | |
| Modularity | [ ] | |
| Import Paths (v1.11.0+) | [ ] | |
| Parameter Externalization | [ ] | |
| Bundle/Calendar | [ ] | |
| Hypothesis Quality | [ ] | |
| Testing | [ ] | |
| Results Structure | [ ] | |
| Documentation | [ ] | |
| Anti-Pattern Avoidance | [ ] | |

### Overall Assessment
- [ ] **APPROVED** — Strategy meets all architectural standards
- [ ] **NEEDS REVISION** — See notes above
- [ ] **REJECTED** — Fundamental architecture violations

### Architect Signature: _______________________

---

## References
- CLAUDE.md — Project overview and version history
- workflow.md — Research workflow phases
- pipeline.md — Data and results pipeline
- strategies/_template/ — Canonical strategy template
- lib/_exports.py — All public APIs (v1.11.0+)
- .claude/agents/codebase-architect.md — This agent's mandate
