# v1_researchers_cockpit Complete Realignment

Master planning document for aligning the research pipeline with Zipline-Reloaded 3.1.0 standards.

## Overview

This realignment addresses 7 key areas that require correction, improvement, or re-alignment to achieve a production-ready algorithmic trading research environment.

## Planning Files

| Area | File | Priority | Complexity |
|------|------|----------|------------|
| UTC Timezone Standardization | `PLAN_01_UTC_TIMEZONE.md` | P0 | Medium |
| Calendar & Asset Class Integration | `PLAN_02_CALENDARS.md` | P0 | High |
| Pipeline API Alignment | `PLAN_03_PIPELINE.md` | P1 | Medium |
| Data Ingestion Flow | `PLAN_04_DATA_INGESTION.md` | P0 | Medium |
| Strategy Template Modernization | `PLAN_05_STRATEGY_TEMPLATE.md` | P1 | Low |
| Code Cleanup & Standards | `PLAN_06_CODE_CLEANUP.md` | P2 | Low |
| Import Path Correction | `PLAN_07_IMPORTS.md` | P0 | Low |

## Execution Order

1. **Phase 1 (Foundation):** PLAN_07 → PLAN_01 → PLAN_02
2. **Phase 2 (Data Flow):** PLAN_04 → PLAN_03
3. **Phase 3 (Polish):** PLAN_05 → PLAN_06

## Success Criteria

- [x] All backtests run without timezone errors
- [x] CRYPTO/FOREX calendars register and work correctly
- [x] Pipeline factors compute for all asset classes
- [x] Data ingestion produces valid bundles for Yahoo source
- [x] Strategy template works across equities/crypto/forex
- [x] No debug logs or hardcoded paths in codebase

**Status: COMPLETE** (2025-12-27)

## Relevant Files

### Core Library (`lib/`)
- `lib/__init__.py` - Package exports ✅
- `lib/backtest.py` - Backtest execution ✅ (debug logs removed, UTC standardized)
- `lib/config.py` - Configuration loading ✅
- `lib/data_loader.py` - Bundle management ✅ (fixed timestamp handling, error handling)
- `lib/data_integrity.py` - Validation ✅
- `lib/extension.py` - Wrapper for .zipline/extension.py ✅ (NEW)
- `lib/logging_config.py` - Centralized logging ✅ (NEW)
- `lib/metrics.py` - Performance metrics ✅
- `lib/optimize.py` - Optimization ✅
- `lib/plots.py` - Visualization ✅
- `lib/report.py` - Report generation ✅
- `lib/utils.py` - Utilities ✅ (UTC normalization added)
- `lib/validate.py` - Walk-forward ✅

### Extension Module
- `.zipline/extension.py` - Custom calendars ✅ (calendar aliases added)

### Strategy Template
- `strategies/_template/strategy.py` - Template ✅ (Pipeline fixed, optional imports)
- `strategies/_template/parameters.yaml` - Default params ✅ (asset_class, use_pipeline added)
- `strategies/_template/hypothesis.md` - Template ✅

### Scripts
- `scripts/ingest_data.py` - Data ingestion ✅

### Documentation
- `pipeline.md` - Pipeline guide ✅
- `workflow.md` - Workflow guide ✅
