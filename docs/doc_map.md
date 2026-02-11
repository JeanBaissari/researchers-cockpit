# Documentation Map

**Quick navigation guide for the Researcher's Cockpit documentation.**

Use this map to find the right document for your task. All paths are relative to `docs/`.

---

## 🎯 Getting Started

**New to the project?** Start here:

1. **[Project Description](project_description.md)** - What is this project and why use it?
2. **[Scripts Reference](scripts_reference.md)** - Command-line interface guide
3. **[API Reference](api/README.md)** - Quick start and module overview
4. **[Strategy Catalog](strategy_catalog.md)** - See what strategies exist
5. **[Walkthrough: Validation](walkthrough/validation.md)** - Step-by-step guide

---

## 📚 Main Documentation Sections

### 1. API Reference (`api/`)

**Complete reference for all `lib/` modules.**

**Quick access:**
- **Data & Config:** [bundles](api/bundles.md) · [validation](api/validation.md) · [data](api/data.md) · [calendars](api/calendars.md) · [config](api/config.md) · [strategies](api/strategies.md)
- **Execution:** [backtest](api/backtest.md) · [metrics](api/metrics.md) · [optimize](api/optimize.md) · [validate](api/validate.md) · [report](api/report.md)
- **Utilities:** [paths](api/paths.md) · [utils](api/utils.md) · [pipeline_utils](api/pipeline_utils.md) · [position_sizing](api/position_sizing.md) · [risk_management](api/risk_management.md) · [logging](api/logging.md) · [plots](api/plots.md)

**Inventory docs (deep reference):**
- [Performance DataFrame Integration](api/performance_dataframe_integration.md) - Zipline's 38+ column perf DataFrame
- [Metrics Inventory](api/metrics_inventory.md) - Complete metrics system reference
- [Metrics Provenance](api/metrics_provenance.md) - Zipline vs lib/metrics/
- [Pipeline Inventory](api/pipeline_inventory.md) - Complete Pipeline system reference
- [Bundle Inventory](api/bundle_inventory.md) - Complete Bundle system reference
- [Transaction Costs](api/transaction_costs.md) - Commission & slippage models

**[→ Full API Index](api/README.md)**

---

### 2. Code Patterns (`code_patterns/`)

**Recipes and best practices for common tasks.**

**Available patterns:**
- [CSV Ingestion Best Practices](code_patterns/csv_ingestion_best_practices.md) - Professional CSV data ingestion
- [Filters vs Validators](code_patterns/filters_vs_validators.md) - Data filtering vs validation
- [Position Sizing Decision Guide](code_patterns/position_sizing_decision_guide.md) - Choosing position sizing algorithms
- [Risk Management Guide](code_patterns/risk_management_guide.md) - Risk management patterns

**[→ Full Pattern Index](code_patterns/README.md)**

---

### 3. Troubleshooting (`troubleshooting/`)

**Symptom → cause → fix guides.**

**Common issues:**
- [Common Issues](troubleshooting/common_issues.md) - General troubleshooting
- [Data Ingestion](troubleshooting/data_ingestion.md) - Bundle ingestion problems
- [Data Validation](troubleshooting/data_validation.md) - Validation failures
- [Backtesting](troubleshooting/backtesting.md) - Backtest execution errors
- [Calendar Date Parsing](troubleshooting/calendar_date_parsing.md) - Calendar/date issues
- [Parameter Validation](troubleshooting/parameter_validation.md) - Strategy parameter errors

**Specific bugs:**
- [Zipline Metrics Bug](troubleshooting/zipline_metrics_bug.md)
- [Sharpe Ratio API Error](troubleshooting/sharpe_ratio_api_error.md)
- [Syntax Error Plots Import](troubleshooting/syntax_error_plots_import.md)
- [Broken Symlinks](troubleshooting/broken_symlinks.md)
- [Auto Repair Removal](troubleshooting/auto_repair_removal.md)

**[→ Full Troubleshooting Index](troubleshooting/README.md)**

---

### 4. Testing (`testing/`)

**Test suite organization and guidelines.**

**Available docs:**
- [Testing Guide](testing/README.md) - How to run tests, test structure
- [Quick Validations](testing/quick_validations.md) - Fast validation checks
- [Coverage Targets](testing/coverage_targets.md) - Test coverage goals

**[→ Full Testing Index](testing/README.md)**

---

### 5. Walkthrough (`walkthrough/`)

**Step-by-step guides for complex workflows.**

**Available walkthroughs:**
- [Validation Walkthrough](walkthrough/validation.md) - Complete validation workflow

**[→ Full Walkthrough Index](walkthrough/README.md)**

---

### 6. Validation (`validation/`)

**Validation architecture and patterns.**

**Available docs:**
- [Validation Architecture](validation/validation_architecture.md) - System design

**[→ Full Validation Index](validation/README.md)**

---

### 7. Verification (`verification/`)

**Formal verification reports proving architectural claims.**

**Available verifications:**
- [Zipline-Reloaded Targeting Verification](verification/zipline_reloaded_targeting_verification.md) - Proof of Zipline-Reloaded targeting
- [Pipeline Utils NO WRAPPERS Compliance](verification/pipeline_utils_no_wrappers.md) - No wrapper verification

**[→ Full Verification Index](verification/README.md)**

---

### 8. Analysis (`analysis/`)

**Architectural analysis and wrapper audit reports.**

**Available analyses:**
- [Backtest Wrapper Analysis](analysis/backtest_wrapper_analysis.md)
- [Bundles Wrapper Analysis](analysis/bundles_wrapper_analysis.md)
- [Metrics Duplication Analysis](analysis/metrics_duplication_analysis.md)
- [Pipeline Utils Wrapper Analysis](analysis/pipeline_utils_wrapper_analysis.md)
- [Position Sizing Wrapper Analysis](analysis/position_sizing_wrapper_analysis.md)
- [Risk Management Wrapper Analysis](analysis/risk_management_wrapper_analysis.md)

**[→ Full Analysis Index](analysis/README.md)**

---

### 9. Archive (`archive/`)

**Historical documents from v1.0-v1.11 development.**

**Archived sections:**
- [Implementation Guides](archive/implementation-guides/) - Phase-by-phase implementation docs
- [Legacy Agent Guides](archive/legacy-agent-guides/) - Old agent instructions
- [Reports](archive/reports/) - Old analysis reports
- [Code Patterns](archive/code_patterns/) - Archived patterns (replaced by current patterns)
- [Templates](archive/templates/) - Old templates
- [Analysis Duplicates](archive/analysis-duplicates/) - Redundant analysis docs

**All archived docs include replacement links to current documentation.**

---

## 🔍 Finding What You Need

### By Task

| Task | Start Here |
|------|------------|
| **First time setup** | [Project Description](project_description.md) → [API Quick Start](api/README.md#quick-start) |
| **Use CLI scripts** | [Scripts Reference](scripts_reference.md) - Complete command-line guide |
| **Ingest data** | [Scripts: ingest_data.py](scripts_reference.md#ingest_datapy) → [API: bundles](api/bundles.md) |
| **Create strategy** | [API: strategies](api/strategies.md) → [Strategy Catalog](strategy_catalog.md) |
| **Run backtest** | [Scripts: run_backtest.py](scripts_reference.md#run_backtestpy) → [API: backtest](api/backtest.md) |
| **Validate data** | [API: validation](api/validation.md) → [Walkthrough: Validation](walkthrough/validation.md) |
| **Calculate metrics** | [API: metrics](api/metrics.md) → [Metrics Inventory](api/metrics_inventory.md) |
| **Optimize parameters** | [Scripts: run_optimization.py](scripts_reference.md#run_optimizationpy) → [API: optimize](api/optimize.md) |
| **Fix errors** | [Troubleshooting Index](troubleshooting/README.md) |
| **Understand architecture** | [Value Add Modules](value_add_modules.md) → [Agent Integration](agent_integration.md) |
| **Verify compliance** | [Verification Index](verification/README.md) |

### By Role

| Role | Recommended Reading |
|------|---------------------|
| **Strategy Developer** | [Strategy Catalog](strategy_catalog.md) · [API: strategies](api/strategies.md) · [Position Sizing Guide](code_patterns/position_sizing_decision_guide.md) · [Risk Management Guide](code_patterns/risk_management_guide.md) |
| **Data Engineer** | [API: bundles](api/bundles.md) · [API: validation](api/validation.md) · [CSV Ingestion](code_patterns/csv_ingestion_best_practices.md) · [Bundle Inventory](api/bundle_inventory.md) |
| **Researcher/Analyst** | [API: metrics](api/metrics.md) · [API: optimize](api/optimize.md) · [API: validate](api/validate.md) · [Metrics Inventory](api/metrics_inventory.md) |
| **AI Agent** | [Agent Integration](agent_integration.md) · [Value Add Modules](value_add_modules.md) · [Code Patterns Index](code_patterns/README.md) |
| **Architect/Maintainer** | [Value Add Modules](value_add_modules.md) · [Verification Index](verification/README.md) · [Analysis Index](analysis/README.md) |

### By Problem

| Problem | Solution |
|---------|----------|
| **Bundle ingestion fails** | [Troubleshooting: Data Ingestion](troubleshooting/data_ingestion.md) |
| **Validation errors** | [Troubleshooting: Data Validation](troubleshooting/data_validation.md) |
| **Backtest errors** | [Troubleshooting: Backtesting](troubleshooting/backtesting.md) |
| **Calendar/date issues** | [Troubleshooting: Calendar Date Parsing](troubleshooting/calendar_date_parsing.md) · [API: calendars](api/calendars.md) |
| **Parameter errors** | [Troubleshooting: Parameter Validation](troubleshooting/parameter_validation.md) |
| **Metrics calculation issues** | [Troubleshooting: Zipline Metrics Bug](troubleshooting/zipline_metrics_bug.md) · [Metrics Provenance](api/metrics_provenance.md) |
| **Import errors** | [API Index](api/README.md#import-path-standards) |

---

## 📋 Core Documents

**High-level project understanding:**

- **[Project Description](project_description.md)** - Complete project overview
- **[Scripts Reference](scripts_reference.md)** - Command-line interface guide
- **[Value Add Modules](value_add_modules.md)** - Architecture principles (NO WRAPPERS)
- **[Agent Integration](agent_integration.md)** - How AI agents work in this repo
- **[Strategy Catalog](strategy_catalog.md)** - Active strategies

---

## 📖 Documentation Standards

All documentation follows these principles:

- **Granular** - Small, focused files (prefer 500 lines or less)
- **Indexed** - Every doc linked from a README
- **Current** - Matches v1.12.0+ NO WRAPPERS architecture
- **Discoverable** - Clear naming with underscores (e.g., `my_doc.md`)

**Naming conventions:**
- Content files: lowercase with underscores (`my_document.md`)
- Index files: uppercase (`README.md`)

---

## 🔗 Related Resources

- **Root:** [`CLAUDE.md`](../CLAUDE.md) - Implementation guide for AI agents
- **Root:** [`workflow.md`](../workflow.md) - Research workflow
- **Root:** [`pipeline.md`](../pipeline.md) - Data pipeline architecture
- **Strategies:** [`strategies/_template/`](../strategies/_template/) - Strategy template
- **Agent Instructions:** [`.claude/agents/`](../.claude/agents/) - Specialized agent guides
- **Skills:** [`.claude/skills/`](../.claude/skills/) - Agent skill modules

---

## 📊 Documentation Metrics

| Category | Files | Purpose |
|----------|-------|---------|
| API Reference | 30+ | Complete module documentation |
| Code Patterns | 4 | Reusable recipes |
| Troubleshooting | 14 | Problem-solution guides |
| Testing | 3 | Test guidelines |
| Walkthrough | 1 | Step-by-step guides |
| Validation | 1 | Architecture docs |
| Verification | 2 | Compliance proofs |
| Analysis | 6 | Architectural analysis |
| Archive | 50+ | Historical documents |
| **Total** | **142** | Complete documentation |

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
