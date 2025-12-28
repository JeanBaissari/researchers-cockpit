# CLAUDE.md — The Researcher's Cockpit

> Implementation guide for AI agents (and humans) building this project from documentation to working reality.

---

## Project Overview

**Name:** zipline-algo  
**Type:** Research-First Minimalist + AI-Agent Optimized  
**Target User:** Algo trader focused on daily research cycles  
**Core Principle:** Every folder is a clear "handoff zone" between human and AI agents

This project creates a zipline-reloaded based algorithmic trading research environment. The structure treats trading research like a well-organized cockpit: every control is exactly where you need it.

---

## Current State

### ✅ Documentation Complete
- `README.md` — Project identity and architecture overview
- `workflow.md` — 7-phase research lifecycle
- `pipeline.md` — Workflow patterns and data flow
- `api-reference.md` — Full Zipline API documentation
- `maintenance.md` — Daily/weekly/monthly/quarterly maintenance guides
- `project.structure.md` — Complete directory tree

### ✅ Reference Materials Complete
- `docs/code_patterns/` — 30+ Zipline pattern documents across 12 categories
- `docs/templates/strategies/` — 10 production-ready strategy templates (basic + advanced)
- `docs/source/beginner_tutorial.md` — Getting started guide

### ✅ v1.0.3 Realignment Complete (2025-12-27)
The codebase has been realigned with Zipline-Reloaded 3.1.0 standards:
- UTC timezone standardization (`normalize_to_utc()`)
- Custom calendar system (CRYPTO, FOREX) with aliases
- Pipeline API uses generic `EquityPricing` (not US-specific)
- Debug logs removed, centralized logging added
- No hardcoded paths in source files

See `tasks/v1.0.3/AGENT_TASKS.md` for detailed completion notes.

### ✅ v1.0.5 Data Pipeline Fixes Complete (2025-12-28)
Comprehensive fixes for multi-asset class data ingestion and backtesting:
- **Path Resolution**: Marker-based `_find_project_root()` across all scripts/strategies
- **Timezone Handling**: `tz_convert(None)` pattern for calendar API calls
- **Bundle Registry**: `end_date` tracking in metadata persistence
- **Calendar Filtering**: FOREX Sunday sessions properly filtered to Mon-Fri
- **Gap-Filling**: Automatic fill for FOREX (5 days) and CRYPTO (3 days)
- **Calendar Validation**: Mismatch warning between bundle and backtest calendars
- **Ingestion CLI**: `--calendar` option for explicit calendar override
- **Metrics Consistency**: Empyrical-based Sharpe calculation in all strategies
- **Bundle Defaults**: Updated to `yahoo_*_daily` naming convention

See `tasks/v1.0.5/` for detailed implementation notes.

### 🚧 Implementation Needed
Everything described in `README.md` and `project.structure.md` needs to be created.

---

## Implementation Roadmap

The implementation is divided into **3 Stages**, each with multiple **Phases**. Each phase produces testable, working functionality.

```
STAGE 1: Foundation & Directory Structure
├── Phase 1.1: Environment Setup
├── Phase 1.2: Configuration System
├── Phase 1.3: Directory Scaffolding
└── Phase 1.4: AI Agent Instructions

STAGE 2: Core Library & Strategy System
├── Phase 2.1: Library Foundation (lib/)
├── Phase 2.2: Strategy Template System
├── Phase 2.3: Backtest Execution
└── Phase 2.4: First Working Backtest (MVP Checkpoint)

STAGE 3: Full Research Pipeline
├── Phase 3.1: Metrics & Analysis
├── Phase 3.2: Optimization System
├── Phase 3.3: Validation System
├── Phase 3.4: Reporting & Documentation
└── Phase 3.5: Notebooks & Scripts
```

---

## Stage 1: Foundation & Directory Structure

### Phase 1.1: Environment Setup
**Goal:** Establish Python environment and dependencies

**Deliverables:**
- [ ] `requirements.txt` with pinned versions
- [ ] `.gitignore` for Python/Jupyter/data artifacts
- [ ] `.zipline/extension.py` for custom calendars

**requirements.txt contents:**
```txt
# Core
zipline-reloaded>=3.0.0
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=14.0.0

# Metrics & Analysis
empyrical>=0.5.5
scipy>=1.11.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.18.0

# Data Sources
yfinance>=0.2.30
pandas-datareader>=0.10.0

# Utilities
pyyaml>=6.0.1
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0
tabulate>=0.9.0

# Development
ipykernel>=6.25.0
jupyter>=1.0.0
pytest>=7.4.0
```

**Files to create:**
```
.gitignore
requirements.txt
.zipline/
└── extension.py
```

---

### Phase 1.2: Configuration System
**Goal:** Single source of truth for all settings

**Deliverables:**
- [ ] `config/settings.yaml` — Global settings
- [ ] `config/data_sources.yaml` — API endpoints
- [ ] `config/assets/crypto.yaml`
- [ ] `config/assets/forex.yaml`
- [ ] `config/assets/equities.yaml`

**config/settings.yaml structure:**
```yaml
# Global Settings
capital:
  default_initial: 100000
  currency: USD

dates:
  default_start: "2020-01-01"
  default_end: null  # null = today

backtesting:
  data_frequency: daily
  benchmark: SPY

metrics:
  risk_free_rate: 0.04
  trading_days_per_year: 252

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Files to create:**
```
config/
├── settings.yaml
├── data_sources.yaml
└── assets/
    ├── crypto.yaml
    ├── forex.yaml
    └── equities.yaml
```

---

### Phase 1.3: Directory Scaffolding
**Goal:** Create empty directory structure with .gitkeep files

**Deliverables:**
- [ ] `data/bundles/` — For Zipline-ingested data
- [ ] `data/cache/` — Temporary API responses
- [ ] `data/exports/` — Processed outputs
- [ ] `strategies/_template/` — Strategy template
- [ ] `strategies/crypto/` — Crypto strategies
- [ ] `strategies/forex/` — Forex strategies
- [ ] `strategies/equities/` — Equity strategies
- [ ] `results/` — Centralized results storage
- [ ] `reports/` — Generated reports
- [ ] `logs/` — Execution logs

**Files to create:**
```
data/
├── bundles/.gitkeep
├── cache/.gitkeep
└── exports/.gitkeep

strategies/
├── _template/
│   ├── strategy.py
│   ├── hypothesis.md
│   └── parameters.yaml
├── crypto/.gitkeep
├── forex/.gitkeep
└── equities/.gitkeep

results/.gitkeep
reports/.gitkeep
logs/.gitkeep
```

---

### Phase 1.4: AI Agent Instructions
**Goal:** Create explicit instructions for AI agents

**Deliverables:**
- [ ] `.agent/README.md` — Entry point
- [ ] `.agent/strategy_creator.md` — How to create strategies
- [ ] `.agent/backtest_runner.md` — How to run backtests
- [ ] `.agent/optimizer.md` — How to optimize parameters
- [ ] `.agent/analyst.md` — How to analyze results
- [ ] `.agent/conventions.md` — Naming rules and standards

**Files to create:**
```
.agent/
├── README.md
├── strategy_creator.md
├── backtest_runner.md
├── optimizer.md
├── analyst.md
└── conventions.md
```

---

## Stage 2: Core Library & Strategy System

### Phase 2.1: Library Foundation
**Goal:** Create shared code library with core utilities

**Deliverables:**
- [ ] `lib/__init__.py` — Package initialization
- [ ] `lib/config.py` — Configuration loader
- [ ] `lib/data_loader.py` — Bundle and API data loading
- [ ] `lib/utils.py` — Common utilities

**lib/config.py key functions:**
```python
def load_settings() -> dict
def load_asset_config(asset_class: str) -> dict
def load_strategy_params(strategy_name: str) -> dict
def get_data_source(source_name: str) -> dict
```

**lib/data_loader.py key functions:**
```python
def list_bundles() -> list
def ingest_bundle(source: str, assets: list, **kwargs)
def load_bundle(bundle_name: str)
def cache_api_data(source: str, symbols: list, ...)
def clear_cache(older_than_days: int = 7)
```

**Files to create:**
```
lib/
├── __init__.py
├── config.py
├── data_loader.py
└── utils.py
```

---

### Phase 2.2: Strategy Template System
**Goal:** Production-ready strategy template

**Deliverables:**
- [ ] `strategies/_template/strategy.py` — Canonical structure
- [ ] `strategies/_template/hypothesis.md` — Template
- [ ] `strategies/_template/parameters.yaml` — Default params
- [ ] Copy script/function for creating new strategies

**strategies/_template/strategy.py structure:**
```python
"""
Strategy: [STRATEGY_NAME]
Asset: [ASSET_SYMBOL]
Type: [STRATEGY_TYPE]

See hypothesis.md for the trading rationale.
"""

from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
import yaml
from pathlib import Path


def load_params():
    """Load parameters from YAML file."""
    params_path = Path(__file__).parent / 'parameters.yaml'
    with open(params_path) as f:
        return yaml.safe_load(f)


def initialize(context):
    """Set up the strategy."""
    params = load_params()
    # Load params into context
    # Set commission/slippage
    # Schedule functions
    pass


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    pass
```

**Files to create:**
```
strategies/_template/
├── strategy.py
├── hypothesis.md
└── parameters.yaml
```

---

### Phase 2.3: Backtest Execution
**Goal:** Thin Zipline wrapper for consistent execution

**Deliverables:**
- [ ] `lib/backtest.py` — Core backtest runner
- [ ] Result directory creation with timestamps
- [ ] Automatic `latest` symlink management
- [ ] Standard output format (returns, positions, transactions)

**lib/backtest.py key functions:**
```python
def run_backtest(
    strategy_name: str,
    start_date: str = None,
    end_date: str = None,
    capital_base: float = None,
    bundle: str = None
) -> dict

def save_results(
    strategy_name: str,
    perf: pd.DataFrame,
    params: dict
) -> Path

def update_latest_symlink(strategy_name: str, result_dir: Path)
```

**Output structure:**
```
results/{strategy}/backtest_{YYYYMMDD}_{HHMMSS}/
├── returns.csv
├── positions.csv
├── transactions.csv
├── metrics.json
├── parameters_used.yaml
└── equity_curve.png
```

**Files to create:**
```
lib/
└── backtest.py
```

---

### Phase 2.4: First Working Backtest (MVP Checkpoint)
**Goal:** End-to-end backtest execution with sample strategy

**Deliverables:**
- [ ] Sample strategy in `strategies/equities/spy_sma_cross/`
- [ ] Working data ingestion (Yahoo Finance)
- [ ] Successful backtest execution
- [ ] Results saved to `results/spy_sma_cross/`
- [ ] Metrics calculated and saved

**Verification:**
```bash
# Create sample strategy
python -c "from lib.utils import create_strategy; create_strategy('spy_sma_cross', 'equities')"

# Run backtest
python scripts/run_backtest.py --strategy spy_sma_cross

# Check results
cat results/spy_sma_cross/latest/metrics.json
```

**This is the MVP — a working hypothesis→backtest→results pipeline.**

---

## Stage 3: Full Research Pipeline

### Phase 3.1: Metrics & Analysis
**Goal:** Comprehensive performance metrics via Empyrical

**Deliverables:**
- [ ] `lib/metrics.py` — Empyrical wrapper + custom metrics
- [ ] `lib/plots.py` — Standard visualizations

**lib/metrics.py key functions:**
```python
def calculate_metrics(returns: pd.Series) -> dict
# Returns: sharpe, sortino, max_dd, calmar, annual_return, 
#          annual_vol, win_rate, profit_factor, avg_trade_duration

def calculate_rolling_metrics(returns: pd.Series, window: int) -> pd.DataFrame

def compare_strategies(strategy_names: list) -> pd.DataFrame
```

**lib/plots.py key functions:**
```python
def plot_equity_curve(returns: pd.Series, save_path: Path = None)
def plot_drawdown(returns: pd.Series, save_path: Path = None)
def plot_monthly_returns(returns: pd.Series, save_path: Path = None)
def plot_trade_analysis(transactions: pd.DataFrame, save_path: Path = None)
```

**Files to create:**
```
lib/
├── metrics.py
└── plots.py
```

---

### Phase 3.2: Optimization System
**Goal:** Grid/random search with anti-overfit protocols

**Deliverables:**
- [ ] `lib/optimize.py` — Optimization engine
- [ ] Grid search implementation
- [ ] Random search implementation
- [ ] In-sample/out-of-sample splitting

**lib/optimize.py key functions:**
```python
def grid_search(
    strategy_name: str,
    param_grid: dict,
    start_date: str,
    end_date: str,
    objective: str = 'sharpe'
) -> pd.DataFrame

def random_search(
    strategy_name: str,
    param_distributions: dict,
    n_iter: int = 100,
    **kwargs
) -> pd.DataFrame

def split_data(
    start: str, end: str, 
    train_pct: float = 0.7
) -> tuple[tuple, tuple]
```

**Output structure:**
```
results/{strategy}/optimization_{timestamp}/
├── grid_results.csv
├── best_params.yaml
├── heatmap_sharpe.png
├── in_sample_metrics.json
├── out_sample_metrics.json
└── overfit_score.json
```

**Files to create:**
```
lib/
└── optimize.py
```

---

### Phase 3.3: Validation System
**Goal:** Walk-forward and Monte Carlo validation

**Deliverables:**
- [ ] `lib/validate.py` — Validation methods
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Overfit probability calculation

**lib/validate.py key functions:**
```python
def walk_forward(
    strategy_name: str,
    start_date: str,
    end_date: str,
    train_period: int = 252,  # days
    test_period: int = 63,    # days
    optimize_params: dict = None
) -> dict

def monte_carlo(
    returns: pd.Series,
    n_simulations: int = 1000
) -> dict

def calculate_overfit_probability(
    in_sample_sharpe: float,
    out_sample_sharpe: float,
    n_trials: int
) -> float
```

**Output structure:**
```
results/{strategy}/walkforward_{timestamp}/
├── in_sample_results.csv
├── out_sample_results.csv
├── robustness_score.json
└── regime_breakdown.png

results/{strategy}/montecarlo_{timestamp}/
├── simulation_paths.csv
├── confidence_intervals.json
└── distribution.png
```

**Files to create:**
```
lib/
└── validate.py
```

---

### Phase 3.4: Reporting & Documentation
**Goal:** Human-readable reports and catalog

**Deliverables:**
- [ ] `lib/report.py` — Report generator
- [ ] Report templates
- [ ] Strategy catalog updater
- [ ] `docs/strategy_catalog.md` — Index of all strategies

**lib/report.py key functions:**
```python
def generate_report(
    strategy_name: str,
    output_path: Path = None
) -> Path

def update_catalog(
    strategy_name: str,
    status: str,
    metrics: dict
)

def generate_weekly_summary() -> Path
```

**Report format:**
```markdown
# {Strategy Name} Research Report
Generated: {date}

## Hypothesis
{from hypothesis.md}

## Performance Summary
| Metric | Value |
|--------|-------|
| Sharpe | X.XX  |
| MaxDD  | -X.X% |
...

## Validation Results
- Walk-Forward Efficiency: X.XX
- Overfit Probability: X.XX

## Recommendations
{auto-generated based on results}
```

**Files to create:**
```
lib/
└── report.py

docs/
└── strategy_catalog.md
```

---

### Phase 3.5: Notebooks & Scripts
**Goal:** Interactive and automated execution paths

**Deliverables:**
- [ ] `notebooks/01_backtest.ipynb` — Single strategy backtest
- [ ] `notebooks/02_optimize.ipynb` — Parameter optimization
- [ ] `notebooks/03_analyze.ipynb` — Deep results analysis
- [ ] `notebooks/04_compare.ipynb` — Multi-strategy comparison
- [ ] `notebooks/05_walkforward.ipynb` — Walk-forward validation
- [ ] `notebooks/_sandbox/.gitkeep` — Experimental area
- [ ] `scripts/ingest_data.py` — Data ingestion CLI
- [ ] `scripts/run_backtest.py` — Backtest CLI
- [ ] `scripts/run_optimization.py` — Optimization CLI
- [ ] `scripts/generate_report.py` — Report generation CLI

**Notebook structure:**
Each notebook follows the pattern:
1. Configuration cell (strategy name, date range)
2. Execution cell
3. Results display
4. Save outputs

**Script CLI pattern:**
```bash
python scripts/run_backtest.py --strategy btc_sma_cross [--start 2020-01-01] [--end 2023-12-31]
python scripts/run_optimization.py --strategy btc_sma_cross --method grid [--param fast_period:5:20:5]
python scripts/ingest_data.py --source yahoo --assets crypto [--force]
python scripts/generate_report.py --strategy btc_sma_cross
```

**Files to create:**
```
notebooks/
├── 01_backtest.ipynb
├── 02_optimize.ipynb
├── 03_analyze.ipynb
├── 04_compare.ipynb
├── 05_walkforward.ipynb
└── _sandbox/.gitkeep

scripts/
├── ingest_data.py
├── run_backtest.py
├── run_optimization.py
└── generate_report.py
```

---

## Phase Completion Checklist

Use this to track progress:

### Stage 1: Foundation
- [ ] **1.1** Environment Setup complete
- [ ] **1.2** Configuration System complete
- [ ] **1.3** Directory Scaffolding complete
- [ ] **1.4** AI Agent Instructions complete

### Stage 2: Core Library
- [ ] **2.1** Library Foundation complete
- [ ] **2.2** Strategy Template System complete
- [ ] **2.3** Backtest Execution complete
- [ ] **2.4** First Working Backtest (MVP) ✓

### Stage 3: Full Pipeline
- [ ] **3.1** Metrics & Analysis complete
- [ ] **3.2** Optimization System complete
- [ ] **3.3** Validation System complete
- [ ] **3.4** Reporting & Documentation complete
- [ ] **3.5** Notebooks & Scripts complete

---

## Implementation Notes

### Conventions

**File Naming:**
- Strategy directories: `{asset}_{strategy_type}` (lowercase, underscores)
- Results directories: `{run_type}_{YYYYMMDD}_{HHMMSS}`
- Config files: `*.yaml` for human-editable, `*.json` for machine-generated

**Code Style:**
- Each `lib/` file < 150 lines (split if larger)
- All functions have docstrings
- Type hints on public functions
- Logging via standard library

**Error Handling:**
- Graceful failures with clear messages
- Missing data → suggest ingestion command
- Invalid config → show valid options

### Testing Each Phase

After completing each phase, verify with:

```bash
# Import test
python -c "from lib.{module} import *"

# Smoke test (phase-specific)
python scripts/{script}.py --help
```

### AI Agent Integration

When an AI agent works on this project:
1. Read `.agent/README.md` first
2. Follow conventions in `.agent/conventions.md`
3. Use appropriate instruction file for the task
4. Save all outputs to correct locations
5. Update symlinks as needed

---

## Quick Reference

| Task | Command/Location |
|------|------------------|
| Create strategy | Copy `strategies/_template/` |
| Run backtest | `python scripts/run_backtest.py --strategy {name}` |
| View results | `results/{strategy}/latest/` |
| Optimize | `python scripts/run_optimization.py --strategy {name}` |
| Generate report | `python scripts/generate_report.py --strategy {name}` |
| Check catalog | `docs/strategy_catalog.md` |
| Agent instructions | `.agent/` directory |

---

## Success Criteria

The project is complete when:

1. ✅ A new strategy can be created from template in < 1 minute
2. ✅ Backtest runs and saves standardized results
3. ✅ Metrics are calculated automatically
4. ✅ Optimization produces in/out sample results
5. ✅ Walk-forward validation runs end-to-end
6. ✅ Reports generate from results
7. ✅ AI agents can execute all workflows following `.agent/` instructions
8. ✅ The entire workflow from hypothesis to validated strategy works

**The Researcher's Cockpit is ready when it gets out of your way and lets you focus on what matters: finding profitable strategies.**

