# The Researcher's Cockpit

[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)](https://github.com/JeanBaissari/researchers-cockpit)
[![Powered by](https://img.shields.io/badge/powered%20by-Zipline--Reloaded%203.1.0-green.svg)](https://github.com/stefan-jansen/zipline-reloaded)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

> **Philosophy:** Maximum clarity, minimum friction. If it doesn't serve the hypothesis→backtest→optimize loop, it doesn't exist.

**Author:** [Jean Baissari](https://github.com/JeanBaissari) — Algorithmic Trader & Software Engineer

---

## Project Identity

**Name:** researchers-cockpit
**Version:** 1.0.3
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

### `.agent/` — AI Agent Instructions

This folder contains explicit instructions that any AI agent (Claude Code, Cursor, GPT-based tools) reads before touching any code. This is the single most important folder for automation.

| File | Purpose |
|------|---------|
| `README.md` | Entry point: "Read this first before doing anything" |
| `strategy_creator.md` | Step-by-step guide for creating new strategies |
| `backtest_runner.md` | How to execute backtests correctly |
| `optimizer.md` | Parameter optimization procedures |
| `analyst.md` | Results analysis and interpretation |
| `conventions.md` | Naming rules, file formats, style standards |

**Why This Matters:** Without this folder, every AI agent interaction starts from zero. With it, agents have institutional knowledge.

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
└── exports/               # Extracted results for external use
    ├── btc_sma_cross_returns.csv
    └── eurusd_breakout_trades.csv
```

**Bundle vs Cache vs Export:**
- **Bundles** = Permanent, Zipline-formatted, ready for `run_algorithm()`
- **Cache** = Temporary, raw API responses, can be deleted safely
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

```
lib/
├── __init__.py
├── data_loader.py         # Bundle ingestion, API fetching
├── backtest.py            # Thin Zipline wrapper
├── metrics.py             # Empyrical + custom metrics
├── plots.py               # Standard visualizations
├── optimize.py            # Grid search, random search
└── validate.py            # Walk-forward, Monte Carlo, overfit detection
```

**Design Principle:** Each file is under 150 lines. If a file grows beyond that, it's doing too much.

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
- All metrics calculations in `lib/metrics.py`
- Standardized output format in `metrics.json`

### Jupyter
- Notebooks import from `lib/`
- Results saved to `results/`
- No state stored in notebooks themselves

### AI Agents
- Read `.agent/` before any operation
- Follow conventions in `.agent/conventions.md`
- Create strategies by copying `strategies/_template/`

---

## Quick Reference

| Task | Location |
|------|----------|
| Create new strategy | Copy `strategies/_template/` to `strategies/{asset_class}/{name}/` |
| Run backtest | `python scripts/run_backtest.py --strategy {name}` or `notebooks/01_backtest.ipynb` |
| View latest results | `results/{strategy_name}/latest/` |
| Add new data source | `config/data_sources.yaml` + implement in `lib/data_loader.py` |
| Check strategy status | `docs/strategy_catalog.md` |
| AI agent instructions | `.agent/` directory |

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
