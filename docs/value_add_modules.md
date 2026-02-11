# Value-Add Modules (Beyond Zipline-Reloaded)

This doc explains which project modules **add value beyond** Zipline-Reloaded, and which
areas are intentionally **NOT** implemented because Zipline-Reloaded already provides the
capability (per v1.12.0 **NO WRAPPERS**).


---

## Purpose

This document defines which project modules add value beyond Zipline-Reloaded's core functionality and which areas intentionally use Zipline-Reloaded APIs directly (NO WRAPPERS architecture). It serves as the architectural guide for deciding whether to implement custom code or use framework features.

---

## Scope

**What this covers:**
- Modules that add project-specific value (`lib/config/`, `lib/logging/`, etc.)
- Areas where we use Zipline-Reloaded directly (bundles, calendars, Pipeline)
- Decision criteria for implementing custom vs using framework
- Architecture compliance guidelines

**What this does NOT cover:**
- Detailed API documentation (see `docs/api/`)
- Implementation tutorials (see `.claude/skills/`)
- Zipline-Reloaded API reference (see stefan-jansen/zipline-reloaded)

---

## Guiding Principle

- Prefer **direct Zipline-Reloaded APIs** for trading/backtesting primitives.
- Add `lib/` modules only when they provide **project-specific composition**, **configuration**,
  **logging consistency**, **analysis/visualization utilities**, or **testable invariants**.
- Avoid duplicating Zipline-Reloaded capabilities (no wrapper layers over `zipline.*`).

## What We Use Zipline-Reloaded For (No Project Wrappers)

These are intentionally used **directly** (no wrappers in `lib/`):

- **Bundle management**: `zipline.data.bundles` and `zipline.data.bundles.csvdir.csvdir_equities`
- **Calendar access**: `exchange_calendars` and Zipline calendar utilities
- **Core algorithm API**: `zipline.api` (`symbol()`, `schedule_function()`, `data.history()`, etc.)
- **Pipeline**: `zipline.pipeline.*`
- **Performance tracking**: Zipline's performance DataFrame output and recorded variables (`record()`)

If you find a new `lib/` function that merely forwards arguments to Zipline, treat it as a
regression against this doc.

## Project Modules That Add Value

### `lib/config/` — Configuration Loading + Validation

**Why it exists**: Zipline-Reloaded does not define a project-wide convention for loading
strategy parameters from YAML or for config precedence.

**Value-add**:
- Loads `strategies/{name}/parameters.yaml` consistently.
- Enforces **config precedence** (args > strategy YAML > global settings > defaults).
- Validates parameter shapes/types and provides actionable error messages.

**What it must NOT do**:
- Wrap Zipline APIs (e.g., no `run_algorithm()` wrapper).

### `lib/paths.py` — Project Root + Path Safety

**Why it exists**: Research projects need robust root detection and consistent path resolution.

**Value-add**:
- Centralized project root discovery.
- Project-specific exception types for clear diagnostics.

### `lib/logging/` — Centralized Structured Logging

**Why it exists**: Zipline has logging, but the project needs consistent structured logging,
specialized loggers, and context-scoped fields across scripts, strategies, and analysis.

**Value-add**:
- `configure_logging()` and `get_logger()` to standardize format/handlers.
- Specialized logger instances (`data_logger`, `strategy_logger`, `backtest_logger`, etc.).
- `LogContext` for structured, scoped metadata.

### `lib/backtest/` — Orchestration (Not Wrapping)

**Why it exists**: Zipline-Reloaded provides the engine; this project provides the **workflow**
glue (load config, validate inputs, run backtest, store outputs in project structure).

**Value-add**:
- Orchestrates backtest execution with project conventions (results layout, metadata capture).
- Ensures deterministic and debuggable workflow steps.

**What it must NOT do**:
- Re-implement Zipline internals (simulation loop, performance tracking, blotter logic).

### `lib/validation/` — Data Quality Validation (Complementary)

**Why it exists**: Zipline validates bundle structure during ingestion, but research often needs
stronger data quality checks (OHLCV sanity, continuity, asset-type expectations).

**Value-add**:
- Data-quality validation utilities and profiles that **complement** Zipline ingestion checks.
- Actionable diagnostics for research workflows (e.g., gaps, NaNs, suspicious volumes).

### `lib/metrics/` — Research Metrics for Analysis

**Why it exists**: Zipline has metrics, but research frequently needs:
- Post-run analysis metrics computed from standardized perf outputs.
- Structured outputs for comparison, reporting, and plotting.

**Value-add**:
- Metrics functions that return structured data (`dict` / `DataFrame`) for downstream reuse.
- Consistent naming and aggregation across strategies.

### `lib/plots/` — Reusable Visualization Templates

**Why it exists**: Zipline does not provide a complete plotting layer for this project’s research
workflow and report needs.

**Value-add**:
- Matplotlib-based plot templates designed for both notebooks and scripts.
- Parameterized plotting functions (figsize, styles, output paths).

### `lib/optimize/` and `lib/strategy_validation/` — Research Workflow Extensions

**Why they exist**: Zipline runs a backtest; research workflows often require:
- Parameter search
- Overfitting checks
- Walk-forward validation and Monte Carlo

**Value-add**:
- Repeatable experiment patterns and reusable analysis artifacts.

### `lib/report/` — Report Generation

**Why it exists**: Zipline produces results; this project turns results into human-readable,
repeatable research artifacts (Markdown/HTML).

**Value-add**:
- Report sections and templates aligned with project result conventions.

## How to Decide if a New `lib/` Module is Allowed

Before adding a new module:

- **Check Zipline-Reloaded first**: If Zipline already provides it, use it directly.
- **Ask “what value is added?”**:
  - workflow orchestration?
  - config standardization?
  - data validation beyond ingestion?
  - reusable analysis/visualization?
  - logging consistency?
- **Avoid wrappers**: forwarding calls to `zipline.*` is not value-add.
- **Keep modules small**: prefer focused utilities over monolithic “manager” modules.

## Related Docs

- `docs/verification/zipline_reloaded_targeting_verification.md`
- `docs/api/` (module API docs)
- `docs/analysis/` (architecture decisions and wrapper removals)

---

## Related Documentation

- [Agent Integration](agent_integration.md) - How AI agents work in this repo
- [API Reference](api/README.md) - Complete API documentation
- [Project Description](project_description.md) - Project overview
- [Verification Reports](verification/) - Compliance verification proofs

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
