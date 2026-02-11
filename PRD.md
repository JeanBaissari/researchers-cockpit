# Phases 2-6: Codebase Improvement & Zipline Alignment

> Implement Phase 1 research findings and align with Zipline-Reloaded built-in features

**Priority:** Critical  
**Estimated Duration:** 2-4 weeks  
**Dependencies:** Phase 1 Complete ✅

---

## Overview

**Purpose:** Remove duplications, align with Zipline built-ins, fix tests, update documentation, enhance value-add modules, improve agents.

**Key Principle:** Maximize Zipline-Reloaded value. Keep only modules that add research value beyond framework capabilities.

**Zipline Built-ins (Use Directly):**
- Data quality validation (isnan, AllPresent, validate_column_specs)
- Report generation (MetricsTracker, Performance DataFrame with 38+ columns)
- Position sizing (order_target_percent, order_target, order_target_value)
- Risk management (MaxPositionSize, MaxOrderSize, MaxLeverage, LongOnly)
- Configuration (SimulationParameters, set_commission, set_slippage)
- Logging (standard logging with named loggers)
- Strategy management (TradingAlgorithm lifecycle)
- Results persistence (pickle, bcolz, SQLite)

**Zipline Does NOT Provide (Our Value-Add):**
- Parameter optimization (grid/random search) → `lib/optimize/`
- Walk-forward validation → `lib/strategy_validation/walkforward.py`
- Monte Carlo simulation → `lib/strategy_validation/montecarlo.py`
- Pre-ingestion OHLCV validation → `lib/validation/`
- Custom calendars (FOREX 24/5, CRYPTO 24/7) → `lib/calendars/`
- Strategy report generation → `lib/report/`
- Advanced position sizing (volatility-scaled, Kelly) → `lib/position_sizing.py`
- Stop-loss, trailing stop → `lib/risk_management.py`
- YAML parameter loading → `lib/config/`
- Structured logging with context → `lib/logging/`
- Yahoo Finance bundle → `lib/bundles/yahoo/`

**Reference:** `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`

---

## Phase 2: Remove Duplications & Align with Zipline

- [x] Refactor all 3 strategy analyze() functions to use lib/metrics instead of empyrical (strategies/_template/strategy.py, strategies/forex/breakout_intraday/strategy.py, strategies/forex_breakout_test/strategy.py)
- [x] Review lib/position_sizing.py - ensure it complements Zipline's order_target_percent() API
- [x] Document when to use Zipline's order_target_percent() vs lib/position_sizing.py
- [x] Review lib/risk_management.py - ensure it complements Zipline's risk controls (MaxPositionSize, MaxOrderSize, etc.)
- [x] Document when to use Zipline's controls vs lib/risk_management.py utilities
- [x] Review lib/validation/ - ensure it complements Zipline's data quality validation (pre-ingestion vs runtime)
- [x] Document when to use Zipline's filters (isnan, AllPresent) vs lib/validation/ validators
- [x] Review lib/report/ - ensure it complements Zipline's metrics system (MetricsTracker, Performance DataFrame)
- [x] Document integration with Zipline's Performance DataFrame (38+ columns)
- [x] Review lib/config/ - ensure it complements Zipline's SimulationParameters
- [x] Document integration with Zipline's set_commission(), set_slippage() methods
- [x] Review lib/logging/ - ensure it enhances Zipline's standard logging (structured, context-aware)
- [x] Document integration with Zipline's named loggers (Blotter, ZiplineLog, DataPortal)
- [x] Verify lib/pipeline_utils.py doesn't wrap Zipline Pipeline APIs
- [x] Verify lib/bundles/ uses Zipline bundle APIs directly (v1.12.0 compliance)
- [x] Create lib/bundles/utils.validate_bundle_exists() function
- [ ] Replace duplicated bundle error handling in lib/bundles/access.py, lib/backtest/preprocessing.py, lib/validation/validators/bundle.py

**Reference:** `tasks/ralphy/research/duplication_analysis.md`, `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`

---

## Phase 3: Test Suite Rebuild

- [ ] Fix import errors in tests (update to current module structure, lib.* imports)
- [ ] Fix API change errors (update tests for direct Zipline usage, no wrapper functions)
- [x] Fix logic errors (update assertions for v1.12.0 behavior)
- [ ] Add tests for lib/bundles/management.py (bundle operations)
- [ ] Add tests for lib/bundles/access.py (bundle access patterns)
- [ ] Add tests for lib/bundles/yahoo/registration.py (Yahoo bundle registration)
- [ ] Add tests for direct csvdir_equities() usage in extension.py
- [ ] Add tests for lib/calendars/forex.py (FOREX calendar)
- [ ] Add tests for lib/calendars/registry.py (calendar registry)
- [ ] Add tests for lib/calendars/utils.py (calendar utilities)
- [ ] Add tests for lib/metrics/performance.py (performance metrics)
- [ ] Add tests for lib/metrics/risk.py (risk metrics)
- [ ] Add tests for lib/metrics/trade.py (trade metrics)
- [ ] Add tests for lib/metrics/rolling.py (rolling metrics)
- [ ] Add tests for lib/metrics/comparison.py (comparison metrics)
- [ ] Add tests for lib/optimize/random.py (random search)
- [ ] Add tests for lib/optimize/split.py (train/test splitting)
- [ ] Add tests for lib/optimize/overfit.py (overfitting detection)
- [ ] Add tests for lib/optimize/results.py (optimization results)
- [ ] Add tests for lib/strategy_validation/montecarlo.py (Monte Carlo simulation)
- [ ] Add tests for lib/strategy_validation/metrics.py (validation metrics)
- [ ] Add tests for lib/strategy_validation/results.py (validation results)
- [ ] Add tests for lib/config/assets.py (asset configuration)
- [ ] Add tests for lib/config/strategy.py (strategy configuration)
- [ ] Add tests for lib/config/validation*.py (validation configuration)
- [ ] Add tests for lib/logging/config.py (logging configuration)
- [ ] Add tests for lib/logging/context.py (log context management)
- [ ] Add tests for lib/logging/formatters.py (log formatters)
- [ ] Add tests for lib/report/catalog.py (strategy catalog)
- [ ] Add tests for lib/report/formatters.py (report formatters)
- [ ] Add tests for lib/report/sections.py (report sections)
- [ ] Add tests for lib/report/templates.py (report templates)
- [ ] Add tests for lib/report/weekly.py (weekly reports)
- [ ] Run full test suite: pytest tests/ -v
- [ ] Verify 100% pass rate
- [ ] Generate coverage report: pytest tests/ --cov=lib --cov-report=html
- [ ] Verify 80%+ coverage for critical modules

**Reference:** `tasks/ralphy/research/test_analysis.md`

---

## Phase 4: Architecture Alignment & Documentation

- [ ] Update pipeline.md with Zipline Pipeline patterns (direct Pipeline API usage, CustomFactor examples)
- [ ] Update workflow.md with Zipline execution flow (direct Zipline API usage, lifecycle methods)
- [ ] Update strategies/_template/strategy.py with Zipline best practices (Pipeline, order_target_percent, risk controls, set_commission, set_slippage, schedule_function)
- [ ] Update strategy template analyze() function to use lib/metrics (not empyrical)
- [ ] Create docs/ZIPLINE_INTEGRATION.md (comprehensive guide: built-in features, when to use Zipline vs our modules, integration patterns, extension points)
- [ ] Update .claude/agents/strategy_developer.md with Zipline built-in features knowledge
- [ ] Update .claude/agents/backtest_runner.md with Zipline execution patterns
- [ ] Update .claude/agents/codebase-architect.md with Zipline alignment principles
- [ ] Update .claude/agents/zipline-researcher.md with built-in features findings
- [ ] Update .claude/agents/maintainer.md with Zipline upgrade monitoring guidance
- [ ] Update CLAUDE.md with Zipline alignment section (built-in features we leverage, value-add modules rationale)

**Reference:** `tasks/ralphy/research/architecture_alignment.md`, `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`

---

## Phase 5: Value-Add Module Enhancement

- [ ] Verify lib/optimize/ uses Zipline's run_algorithm() API correctly
- [ ] Document lib/optimize/ integration with Zipline's Performance DataFrame
- [ ] Verify lib/strategy_validation/ uses Zipline's run_algorithm() API correctly
- [ ] Document lib/strategy_validation/ integration with Zipline's Performance DataFrame
- [ ] Document lib/validation/ complements Zipline's runtime validation (pre-ingestion vs runtime use cases)
- [ ] Add examples of Zipline's AllPresent filter and isnan/notnan filters in Pipeline
- [ ] Update lib/report/ to leverage Zipline's Performance DataFrame columns
- [ ] Document which metrics come from Zipline vs lib/metrics/
- [ ] Document lib/position_sizing.py complements Zipline's order_target_percent() (when to use each)
- [ ] Document lib/risk_management.py complements Zipline's risk controls (when to use each)
- [ ] Document lib/config/ integration with Zipline's SimulationParameters
- [ ] Document lib/logging/ integration with Zipline's named loggers
- [ ] Create docs/VALUE_ADD_MODULES.md (for each module: what Zipline provides, what we add, why we add it)

**Reference:** `tasks/ralphy/research/gap_analysis.md`, `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`

---

## Phase 6: Agent Improvement

- [ ] Update .claude/agents/strategy_developer.md with Zipline built-in features, Pipeline usage, order_target_percent examples, risk controls, set_commission/set_slippage, lib/metrics usage guidance
- [ ] Update .claude/agents/backtest_runner.md with Zipline execution patterns, Performance DataFrame usage, metrics system integration, SimulationParameters guidance
- [ ] Update .claude/agents/codebase-architect.md with Zipline alignment principles, pattern guidelines, when to use Zipline built-ins vs our modules, extension points documentation
- [ ] Update .claude/agents/zipline-researcher.md with built-in features knowledge, research methodology updates, output format with built-in comparison
- [ ] Update .claude/agents/maintainer.md with Zipline upgrade monitoring, new feature evaluation, NO WRAPPERS maintenance
- [ ] Create docs/AGENT_INTEGRATION.md (agent roles, collaboration patterns, knowledge sharing)

**Reference:** Phase 2-5 findings, `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`

---

## Acceptance Criteria

- [ ] All strategy analyze() functions use lib/metrics (not empyrical directly)
- [ ] All modules align with Zipline built-ins (complement, don't duplicate)
- [ ] Documentation clarifies when to use Zipline built-ins vs our modules
- [ ] Bundle validation utility extracted and used consistently
- [ ] All tests pass (100% pass rate)
- [ ] Test coverage 80%+ for critical modules
- [ ] All test gaps addressed
- [ ] Tests use direct Zipline APIs (no wrapper function tests)
- [ ] pipeline.md aligned with Zipline Pipeline patterns
- [ ] workflow.md aligned with Zipline execution flow
- [ ] Strategy template uses Zipline APIs directly with best practices
- [ ] Zipline integration guide created (docs/ZIPLINE_INTEGRATION.md)
- [ ] All agents updated with Zipline knowledge
- [ ] CLAUDE.md updated with Zipline alignment
- [ ] Value-add modules enhanced with Zipline integration
- [ ] Value-add module rationale documented (docs/VALUE_ADD_MODULES.md)

---

## Notes

**Dependencies:**
- Phase 2 → Phase 3 (test updates for code changes)
- Phase 2 → Phase 4 (documentation reflects code changes)
- Phase 2 → Phase 5 (module enhancements based on alignment)
- Phase 2-5 → Phase 6 (agents reflect all improvements)

**Execution Strategy:**
- Phase 2: Parallel execution (tasks 2.1-2.10 can run in parallel)
- Phase 3: Parallel execution (tasks 3.1-3.11 can run in parallel, 3.12 depends on all)
- Phase 4: Sequential execution (documentation builds on previous)
- Phase 5: Parallel execution (tasks 5.1-5.8 can run in parallel, 5.9 depends on all)
- Phase 6: Parallel execution (tasks 6.1-6.5 can run in parallel, 6.6 depends on all)

**Files to Modify:**
- Strategy files: strategies/_template/strategy.py, strategies/forex/breakout_intraday/strategy.py, strategies/forex_breakout_test/strategy.py
- Test files: Multiple test files in tests/ directory
- Documentation: pipeline.md, workflow.md, CLAUDE.md, new guides (docs/ZIPLINE_INTEGRATION.md, docs/VALUE_ADD_MODULES.md, docs/AGENT_INTEGRATION.md)
- Agent files: .claude/agents/*.md
- lib/ modules: Enhancements (lib/bundles/utils.py, lib/position_sizing.py, lib/risk_management.py, lib/validation/, lib/report/, lib/config/, lib/logging/)

**Files to Protect:**
- .zipline/extension.py (manual edits only)
- config/settings.yaml (manual edits only)
- config/data_sources.yaml (manual edits only)

**Testing Strategy:**
- Run tests after each phase: pytest tests/ -v
- Generate coverage: pytest tests/ --cov=lib --cov-report=html
- Verify Zipline integration: Test with actual Zipline backtests
- Validate no regressions: Run full test suite before and after changes

**Rollback Plan:**
- All changes in git (commit after each phase)
- Can revert individual phases if issues arise
- Test suite validates no regressions

---

**Reference Documents:**
- `tasks/ralphy/research/duplication_analysis.md`
- `tasks/ralphy/research/gap_analysis.md`
- `tasks/ralphy/research/test_analysis.md`
- `tasks/ralphy/research/architecture_alignment.md`
- `tasks/v1.12.x/Built-in_Features_in_Zipline-Reloaded.md`
