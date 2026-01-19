# The Researcher's Cockpit

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/JeanBaissari/researchers-cockpit)
[![Powered by](https://img.shields.io/badge/powered%20by-Zipline--Reloaded%203.1.0-green.svg)](https://github.com/stefan-jansen/zipline-reloaded)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

> **Philosophy:** Maximum clarity, minimum friction. If it doesn't serve the hypothesis→backtest→optimize loop, it doesn't exist.

**Author:** [Jean Baissari](https://github.com/JeanBaissari) — Algorithmic Trader & Software Engineer

---

## Project Identity

**Name:** researchers-cockpit
**Version:** 1.1.0
**Type:** Research-First Minimalist + AI-Agent Optimized
**Target User:** Algo trader focused on daily research cycles
**Core Principle:** Every folder is a clear "handoff zone" between human and AI agents

---

## Architecture Overview

This structure treats your trading research like a well-organized cockpit: every control is exactly where you need it, nothing is hidden, and you can hand off the controls to an AI co-pilot at any moment without lengthy explanations.

### Mental Model

Think of this structure as a **restaurant kitchen**:

- `.agent/` = Recipe book for the kitchen staff (AI agents)
- `config/` = Pantry inventory and supplier contacts
- `data/` = Walk-in refrigerator (raw ingredients)
- `strategies/` = Prep stations (one per dish being developed)
- `results/` = Plating area (finished dishes, photographed and documented)
- `notebooks/` = Test kitchen (experimentation happens here)
- `lib/` = Kitchen tools (knives, pans, blenders)
- `scripts/` = Quick-access buttons (turn on oven, start dishwasher)
- `reports/` = Customer-facing menu descriptions
- `docs/` = Training manuals

---

## Directory Structure Explained

### `.agent/` & `.cursor/` — AI Agent Instructions

These folders contain explicit instructions that any AI agent (Claude Code, Cursor, GPT-based tools) reads before touching any code. This is the single most important folder for automation.

**`.agent/` — Legacy Agent Instructions:**
| File | Purpose |
|------|---------|
| `README.md` | Entry point: "Read this first before doing anything" |
| `strategy_creator.md` | Step-by-step guide for creating new strategies |
| `backtest_runner.md` | How to execute backtests correctly |
| `optimizer.md` | Parameter optimization procedures |
| `analyst.md` | Results analysis and interpretation |
| `conventions.md` | Naming rules, file formats, style standards |

**`.cursor/` — Cursor IDE Integration (v1.0.9+):**
- `commands/` - 30+ command templates for common tasks
- `rules/` - 30+ coding standards and patterns
- `.update_tracking.yaml` - Update cycle tracking

**Why This Matters:** Without these folders, every AI agent interaction starts from zero. With them, agents have institutional knowledge and standardized workflows.

---

### `config/` — Single Source of Truth

All configuration lives here. No scattered `.env` files, no hardcoded values.

```
config/
├── settings.yaml          # Global: capital, date ranges, defaults
├── data_sources.yaml      # API keys, endpoints, rate limits
└── assets/
    ├── crypto.yaml        # BTC-USD, ETH-USD, SOL-USD definitions
    ├── forex.yaml         # EUR/USD, GBP/JPY pair specifications
    └── equities.yaml      # SPY, QQQ, individual stock configs
```

**Design Decision:** Asset-specific configs are separated because crypto, forex, and equities have different trading hours, margin requirements, and data sources. An agent working on a forex strategy shouldn't need to parse crypto configurations.

---

### `data/` — Raw Materials Storage

```
data/
├── bundles/               # Zipline-ingested data (ready for backtesting)
│   ├── crypto_daily/
│   ├── forex_1h/
│   └── us_equities_daily/
├── cache/                 # Temporary API response storage
│   └── yahoo_2024_12_18.parquet
├── processed/             # Staging area for CSV files before bundle ingestion
│   ├── 1m/               # 1-minute timeframe CSV files
│   ├── 5m/               # 5-minute timeframe CSV files
│   ├── 15m/              # 15-minute timeframe CSV files
│   ├── 30m/              # 30-minute timeframe CSV files
│   ├── 1h/               # 1-hour timeframe CSV files
│   ├── 4h/               # 4-hour timeframe CSV files
│   └── 1d/               # Daily timeframe CSV files
└── exports/               # Extracted results for external use
    ├── btc_sma_cross_returns.csv
    └── eurusd_breakout_trades.csv
```

**Data Flow:**
1. **Cache** = Temporary, raw API responses, can be deleted safely
2. **Processed** = Cleaned/normalized CSV files organized by timeframe, ready for bundle ingestion
3. **Bundles** = Permanent, Zipline-formatted, ready for `run_algorithm()`
4. **Exports** = Processed outputs meant for sharing or external analysis

**Bundle vs Cache vs Processed vs Export:**
- **Cache** = Temporary, raw API responses, can be deleted safely
- **Processed** = Staging area for CSV files before bundle ingestion (organized by timeframe)
- **Bundles** = Permanent, Zipline-formatted, ready for `run_algorithm()`
- **Exports** = Processed outputs meant for sharing or external analysis

---

### `strategies/` — The Heart of Research

Each strategy is a self-contained unit with everything it needs:

```
strategies/
├── _template/                    # Copy this to create new strategies
│   ├── strategy.py               # Canonical Zipline algorithm
│   ├── hypothesis.md             # REQUIRED: What are we testing?
│   └── parameters.yaml           # Default parameter values
│
├── crypto/
│   └── btc_sma_cross/
│       ├── strategy.py           # The actual algorithm
│       ├── hypothesis.md         # "BTC trends persist >20 days"
│       ├── parameters.yaml       # fast: 10, slow: 50
│       └── results -> ../../results/btc_sma_cross/
│
├── forex/
│   └── eurusd_london_breakout/
│       └── ...
│
└── equities/
    └── spy_dual_momentum/
        └── ...
```

**The Hypothesis Requirement:**

Every strategy MUST have a `hypothesis.md` file. This is non-negotiable. The hypothesis file answers:

1. **What market behavior are we exploiting?**
2. **Why do we believe this behavior exists?**
3. **Under what conditions should this strategy fail?**
4. **What would falsify this hypothesis?**

Without a hypothesis, you're curve-fitting, not researching.

**The Symlink Pattern:**

Each strategy folder contains a `results` symlink pointing to its results in the centralized `results/` directory. This means:
- You can `cd` into any strategy and immediately see its results
- All results are also accessible from one central location
- No duplication, no sync issues

---

### `results/` — Centralized Results Archive

```
results/
├── btc_sma_cross/
│   ├── backtest_20241215_143022/
│   │   ├── returns.csv           # Daily/hourly returns series
│   │   ├── positions.csv         # Position history
│   │   ├── transactions.csv      # All trades executed
│   │   ├── metrics.json          # Sharpe, Sortino, MaxDD, etc.
│   │   ├── parameters_used.yaml  # Exact params for reproducibility
│   │   └── equity_curve.png      # Visual equity curve
│   │
│   ├── optimization_20241219_160033/
│   │   ├── grid_results.csv      # All parameter combinations
│   │   ├── best_params.yaml      # Winner
│   │   ├── heatmap_sharpe.png    # Parameter sensitivity
│   │   └── overfit_score.json    # Walk-forward validation results
│   │
│   └── latest -> backtest_20241218_091547/
```

**Naming Convention:** `{run_type}_{YYYYMMDD}_{HHMMSS}/`

This ensures:
- Chronological sorting works automatically
- No collisions between runs
- Easy to reference specific runs in discussions

**The `latest` Symlink:**

Always points to the most recent run. Agents and scripts can reference `results/btc_sma_cross/latest/metrics.json` without knowing the exact timestamp.

---

### `notebooks/` — Research Workbench

```
notebooks/
├── 01_backtest.ipynb        # Single strategy backtest
├── 02_optimize.ipynb        # Grid/random search + validation
├── 03_analyze.ipynb         # Deep dive on single result
├── 04_compare.ipynb         # Multi-strategy comparison
├── 05_walkforward.ipynb     # Anti-overfit validation
└── _sandbox/                # Experimental (gitignored)
    ├── ml_signal_test.ipynb
    └── regime_detection.ipynb
```

**Numbered Prefixes:** Notebooks are numbered to indicate workflow order. A typical research cycle follows 01→02→03, potentially looping back to 01 with new parameters.

**The Sandbox:** Anything in `_sandbox/` is experimental and not part of the official workflow. This is where you test crazy ideas before promoting them.

---

### `lib/` — Shared Code Library

Modular architecture with domain-organized packages (v1.0.8+):

```
lib/
├── __init__.py
├── paths.py               # Project root detection
├── utils.py              # Core utilities
├── pipeline_utils.py      # Pipeline API setup and validation (v1.0.9+)
├── position_sizing.py    # Position sizing calculations (v1.0.9+)
├── risk_management.py     # Exit condition checks (v1.0.9+)
│
├── backtest/             # Backtest execution (v1.1.0: modular)
│   ├── runner.py         # Main orchestrator (174 lines)
│   ├── preprocessing.py  # Validation, date checks (231 lines)
│   ├── execution.py      # Zipline algorithm setup (178 lines)
│   ├── config.py         # Configuration management
│   ├── strategy.py       # Strategy loading
│   ├── results.py        # Results handling
│   └── verification.py   # Verification utilities
│
├── bundles/               # Data bundle management (v1.1.0: source-specific)
│   ├── api.py            # Thin public interface (17 lines)
│   ├── management.py     # Bundle ingestion (200 lines)
│   ├── access.py         # Bundle loading/queries (164 lines)
│   ├── registry.py       # Bundle registry
│   ├── yahoo/            # Yahoo Finance subpackage
│   │   ├── fetcher.py    # API interaction (107 lines)
│   │   ├── processor.py  # Data processing (159 lines)
│   │   └── registration.py # Bundle registration (255 lines)
│   └── csv/              # CSV data subpackage
│       ├── parser.py     # CSV parsing (157 lines)
│       ├── ingestion.py  # Data loading (166 lines)
│       ├── writer.py     # Zipline writer (152 lines)
│       └── registration.py # Bundle registration (194 lines)
│
├── calendars/             # Trading calendars (v1.1.0: session alignment)
│   ├── crypto.py         # 24/7 crypto calendar
│   ├── forex.py          # 24/5 forex calendar
│   ├── registry.py       # Calendar registry
│   └── sessions/         # SessionManager for alignment (v1.1.0)
│       ├── manager.py    # SessionManager core (140 lines)
│       ├── strategies.py # Session loading strategies (116 lines)
│       └── validation.py # Mismatch reports (135 lines)
│
├── config/                # Configuration management (4 modules)
│   ├── core.py           # Core settings
│   ├── assets.py         # Asset configuration
│   ├── strategy.py       # Strategy parameters
│   └── validation.py     # Config validation
│
├── data/                  # Data processing (5 modules)
│   ├── normalization.py  # Data normalization
│   ├── aggregation.py    # Data aggregation
│   ├── forex.py          # FOREX data handling
│   └── ...
│
├── logging/               # Centralized logging (7 modules)
│   ├── config.py         # Logging configuration
│   ├── context.py        # Log context management
│   ├── formatters.py     # Log formatters
│   └── ...
│
├── metrics/               # Performance metrics (v1.1.0: concern separation)
│   ├── core.py           # Main orchestrator (242 lines)
│   ├── performance.py    # Sharpe, Sortino, returns (243 lines)
│   ├── risk.py           # Drawdown, alpha/beta, VaR (273 lines)
│   ├── trade.py          # Trade-level metrics
│   ├── rolling.py        # Rolling window metrics
│   └── comparison.py     # Strategy comparison
│
├── optimize/              # Parameter optimization (5 modules)
│   ├── grid.py           # Grid search
│   ├── random.py         # Random search
│   ├── split.py          # Train/test splitting
│   └── overfit.py        # Overfit detection
│
├── plots/                 # Visualization utilities (5 modules)
│   ├── equity.py         # Equity curve plots
│   ├── trade.py          # Trade analysis plots
│   ├── rolling.py        # Rolling metric plots
│   └── ...
│
├── report/                 # Report generation (6 modules)
│   ├── templates.py      # Report templates
│   ├── formatters.py     # Data formatters
│   ├── sections.py       # Report sections
│   └── ...
│
├── validate/               # Validation methods (4 modules)
│   ├── walkforward.py    # Walk-forward validation
│   ├── montecarlo.py     # Monte Carlo simulation
│   └── metrics.py        # Validation metrics
│
└── validation/             # Data validation framework (v1.1.0: strategy pattern)
    ├── api.py            # Public API functions (555 lines)
    ├── data_validator.py # Main orchestrator (925 lines)
    ├── validators/       # Asset-specific validators
    │   ├── equity.py     # Equity validation (307 lines)
    │   ├── forex.py      # FOREX validation (225 lines)
    │   ├── crypto.py     # Crypto validation (224 lines)
    │   └── reporting.py  # Report generation (236 lines)
    └── ...
```

**Design Principle:** Target 150-200 lines per module (v1.1.0: achieved 82% reduction in average size). Orchestrators may be larger (200-400 lines) but delegate to focused submodules following SOLID principles.

**New Utility Modules (v1.0.9+):**
- `pipeline_utils.py` - Pipeline API setup and validation
- `position_sizing.py` - Position sizing (fixed, volatility-scaled, Kelly Criterion)
- `risk_management.py` - Risk management (stop loss, trailing stop, take profit)

**What Goes Here vs. Strategy Files:**
- `lib/` = Reusable across ALL strategies
- `strategy.py` = Specific to ONE strategy

---

### `scripts/` — One-Command Operations

```
scripts/
├── ingest_data.py         # python scripts/ingest_data.py --source yahoo --assets crypto
├── run_backtest.py        # python scripts/run_backtest.py --strategy btc_sma_cross
├── run_optimization.py    # python scripts/run_optimization.py --strategy btc_sma_cross --method grid
└── generate_report.py     # python scripts/generate_report.py --strategy btc_sma_cross
```

These are CLI alternatives to notebooks. Use notebooks for interactive exploration, scripts for automation and scheduled runs.

---

### `reports/` — Human-Readable Outputs

```
reports/
├── btc_sma_cross_report_20241218.md
├── eurusd_london_breakout_report_20241220.md
└── weekly_summary_2024W51.md
```

Generated markdown reports that summarize research findings. These are what you share with others or review yourself to track progress.

---

### `docs/` — Reference Materials

```
docs/
├── quickstart.md          # 5-minute setup guide
├── workflow.md            # How to use the system
├── strategy_catalog.md    # Index of all strategies + status
└── code_patterns/         # Your existing Zipline documentation
    ├── 00_getting_started/
    ├── 01_core/
    └── ...
```

---

## File Naming Standards

### Strategies
- **Directory:** `{asset}_{strategy_type}` (e.g., `btc_sma_cross`)
- **Lowercase, underscores, no spaces**
- **Maximum 30 characters**

### Results
- **Directory:** `{run_type}_{YYYYMMDD}_{HHMMSS}`
- **Run types:** `backtest`, `optimization`, `walkforward`, `montecarlo`

### Config Files
- **YAML for data, JSON for metrics**
- YAML is human-readable and editable
- JSON is machine-generated and parsed

### Reports
- **Format:** `{strategy_name}_report_{YYYYMMDD}.md`
- **Weekly:** `weekly_summary_{YYYY}W{WW}.md`

---

## Asset Class Organization

Strategies are organized by asset class at the top level:

```
strategies/
├── crypto/        # 24/7 markets, high volatility
├── forex/         # Session-based, pairs trading
└── equities/      # Market hours, fundamentals-driven
```

**Why Separate?**
- Different trading calendars
- Different data sources
- Different slippage/commission models
- Different risk parameters

An agent working on forex strategies knows to look in `strategies/forex/` and use `config/assets/forex.yaml`.

---

## Integration Points

### Zipline-Reloaded
- Bundles stored in `data/bundles/`
- Custom calendars defined in `.zipline/extension.py`
- Strategies use standard `initialize()`, `handle_data()`, `analyze()` pattern

### Empyrical
- All metrics calculations in `lib/metrics/` modules
- Standardized output format in `metrics.json`

### Jupyter
- Notebooks import from `lib/`
- Results saved to `results/`
- No state stored in notebooks themselves

### AI Agents
- Read `.agent/` and `.cursor/` before any operation
- Follow conventions in `.agent/conventions.md` and `.cursor/rules/`
- Use `.cursor/commands/` for standardized workflows
- Create strategies by copying `strategies/_template/`

---

## Quick Reference

| Task | Location |
|------|----------|
| Create new strategy | Copy `strategies/_template/` to `strategies/{asset_class}/{name}/` |
| Run backtest | `python scripts/run_backtest.py --strategy {name}` or `notebooks/01_backtest.ipynb` |
| View latest results | `results/{strategy_name}/latest/` |
| Add new data source | `config/data_sources.yaml` + implement in `lib/bundles/` |
| Check strategy status | `docs/strategy_catalog.md` |
| AI agent instructions | `.agent/` and `.cursor/` directories |

---

## What This Structure Does NOT Include

Intentionally excluded for research-phase focus:

- **Live trading execution** — Out of scope
- **Kubernetes/Docker deployment** — Not needed for research
- **Real-time monitoring** — Future phase
- **Database backends** — File-based is sufficient
- **Complex IPC** — Single-process research environment
- **Multiple environment configs** — One environment, one config

These can be added later when transitioning from research to production.
