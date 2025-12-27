# AI Agent Instructions — The Researcher's Cockpit

> **READ THIS FIRST:** This directory contains explicit instructions for AI agents (Claude, Cursor, GPT-based tools) working on this project. Read the relevant instruction file before performing any operation.

---

## Quick Start

1. **Read this file** to understand the project structure
2. **Read `.agent/conventions.md`** for naming rules and standards
3. **Read the specific workflow file** for your task:
   - Creating strategies → `strategy_creator.md`
   - Running backtests → `backtest_runner.md`
   - Optimizing parameters → `optimizer.md`
   - Analyzing results → `analyst.md`

---

## Project Overview

**Name:** zipline-algo (The Researcher's Cockpit)  
**Type:** Research-First Minimalist + AI-Agent Optimized  
**Core Principle:** Every folder is a clear "handoff zone" between human and AI agents

This is a zipline-reloaded based algorithmic trading research environment designed for:
- Rapid hypothesis testing
- Systematic backtesting
- Parameter optimization with anti-overfit protocols
- Results analysis and validation

---

## Directory Structure Quick Reference

```
zipline-algo/
├── .agent/              ← YOU ARE HERE (read these files!)
├── config/              ← Single source of truth (YAML configs)
├── data/                ← Raw materials (bundles, cache, exports)
├── strategies/          ← The heart of research (one per strategy)
│   ├── _template/       ← Copy this to create new strategies
│   ├── crypto/          ← Crypto strategies
│   ├── forex/           ← Forex strategies
│   └── equities/        ← Equity strategies
├── results/             ← Centralized results archive
├── notebooks/           ← Interactive research (Jupyter)
├── lib/                 ← Shared code library
├── scripts/             ← CLI tools for automation
└── reports/             ← Human-readable outputs
```

---

## Workflow Summary

Every research cycle follows this pattern:

```
HYPOTHESIS → STRATEGY → BACKTEST → ANALYZE → OPTIMIZE → VALIDATE
```

1. **Hypothesis** (`hypothesis.md`) — What market behavior are we exploiting?
2. **Strategy** (`strategy.py`) — Code implementation
3. **Backtest** (`lib/backtest.py`) — Execute against historical data
4. **Analyze** (`lib/metrics.py`, `lib/plots.py`) — Understand results
5. **Optimize** (`lib/optimize.py`) — Find better parameters
6. **Validate** (`lib/validate.py`) — Walk-forward, Monte Carlo, overfit checks

---

## Agent Workflow Files

| File | When to Read |
|------|--------------|
| `conventions.md` | **Always** — Before any operation |
| `strategy_creator.md` | Creating new strategies |
| `backtest_runner.md` | Running backtests |
| `optimizer.md` | Parameter optimization |
| `analyst.md` | Analyzing backtest results |

---

## Key Principles

### 1. No Hardcoded Parameters
All tunable values live in `parameters.yaml`. Strategy code loads from there.

### 2. Hypothesis Required
Every strategy MUST have a `hypothesis.md` file. No exceptions.

### 3. Results Are Immutable
Every backtest creates a timestamped directory. Never overwrite results.

### 4. Symlinks for Convenience
Each strategy has a `results` symlink pointing to centralized results.

### 5. Configuration Hierarchy
1. Strategy `parameters.yaml` (highest priority)
2. Asset config (`config/assets/*.yaml`)
3. Global settings (`config/settings.yaml`)

---

## Common Tasks

### Create a New Strategy

```bash
# 1. Copy template
cp -r strategies/_template strategies/crypto/btc_new_idea

# 2. Edit hypothesis.md
# 3. Edit parameters.yaml
# 4. Implement strategy.py logic
# 5. Run backtest
python scripts/run_backtest.py --strategy btc_new_idea
```

**See:** `.agent/strategy_creator.md` for detailed steps

### Run a Backtest

```bash
python scripts/run_backtest.py --strategy {strategy_name} [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```

**See:** `.agent/backtest_runner.md` for pre-flight checks and execution

### Optimize Parameters

```bash
python scripts/run_optimization.py --strategy {strategy_name} --method grid
```

**See:** `.agent/optimizer.md` for anti-overfit protocols

### Analyze Results

```bash
# Results are in: results/{strategy_name}/latest/
cat results/{strategy_name}/latest/metrics.json
```

**See:** `.agent/analyst.md` for analysis checklist

---

## Error Handling

### Missing Data
- Check bundle exists: `ls data/bundles/`
- If missing: `python scripts/ingest_data.py --source yahoo --assets crypto`

### Strategy Errors
- Syntax check: `python -m py_compile strategies/{name}/strategy.py`
- Check imports match `requirements.txt`

### Configuration Errors
- Validate YAML: `python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"`
- Check for tabs (YAML hates tabs)

---

## File Locations Reference

| What | Where |
|------|-------|
| Strategy code | `strategies/{asset_class}/{name}/strategy.py` |
| Strategy params | `strategies/{asset_class}/{name}/parameters.yaml` |
| Strategy hypothesis | `strategies/{asset_class}/{name}/hypothesis.md` |
| Backtest results | `results/{name}/backtest_{timestamp}/` |
| Latest results | `results/{name}/latest/` (symlink) |
| Global config | `config/settings.yaml` |
| Asset configs | `config/assets/{asset_class}.yaml` |
| Data bundles | `data/bundles/{bundle_name}/` |

---

## Agent Response Format

When completing a task, always include:

1. **Action taken** — What you did
2. **Output location** — Where results are saved
3. **Summary metrics** — Key numbers (Sharpe, MaxDD, etc.)
4. **Recommendation** — Proceed, modify, or abandon
5. **Next suggested action** — What to do next

Example:
```
Backtest complete. Results saved to results/btc_sma_cross/backtest_20241220_143000/.
Sharpe: 1.23, MaxDD: -15.2%, Win Rate: 52%.
Recommendation: Proceed to optimization.
Next: Run grid search on fast_period (5-20) and slow_period (20-100).
```

---

## Questions?

- **Naming conventions?** → `conventions.md`
- **How to create strategies?** → `strategy_creator.md`
- **How to run backtests?** → `backtest_runner.md`
- **How to optimize?** → `optimizer.md`
- **How to analyze?** → `analyst.md`

---

## Remember

**This project is designed for research, not production trading.**  
Focus on hypothesis testing, not deployment infrastructure.

Every decision should serve the hypothesis→backtest→optimize loop.

