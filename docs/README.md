# Documentation Index

This folder is organized for **discoverability** and **small, focused docs**.

**🗺️ New here? Check out the [Documentation Map](doc_map.md) for visual navigation!**

## Core Documentation

- **Documentation Map**: `doc_map.md`
  - Visual navigation guide for all documentation (start here!).
- **Project Description**: `project_description.md`
  - High-level project overview and value proposition.
- **Scripts Reference**: `scripts_reference.md`
  - Complete command-line interface guide for all scripts.
- **Value-Add Modules**: `value_add_modules.md`
  - What belongs in `lib/` vs what should be direct Zipline-Reloaded usage (NO WRAPPERS).
- **Agent Integration**: `docs/AGENT_INTEGRATION.md`
  - How AI agents should work in this repo (v1.12.0+ NO WRAPPERS).
- **Strategy Catalog**: `strategy_catalog.md`
  - Active catalog of implemented strategies.

## Documentation Sections

- **API Documentation**: `api/`
  - Public usage guides for the `lib/` modules.
  - See `api/README.md` for complete module index.

- **Code Patterns**: `code_patterns/`
  - Recipes and short patterns for common tasks.
  - Includes CSV ingestion, position sizing, and risk management guides.
  - See `code_patterns/README.md` for complete pattern index.

- **Notebooks**: `notebooks/`
  - Comprehensive guide to all Jupyter notebooks for interactive research.
  - Includes data exploration, backtesting, optimization, and validation workflows.
  - See `notebooks/README.md` for complete notebook guide.

- **Troubleshooting**: `troubleshooting/`
  - Symptom → cause → fix guides.
  - See `troubleshooting/README.md` for issue index.

- **Testing**: `testing/`
  - Test suite organization and coverage targets.
  - See `testing/README.md` for testing guidelines.

- **Verification**: `verification/`
  - Proofs that we verified key architectural claims.
  - See `verification/README.md` for verification reports.

- **Walkthrough**: `walkthrough/`
  - Step-by-step guides for complex workflows.
  - See `walkthrough/README.md` for available walkthroughs.

- **Analysis**: `analysis/`
  - Architectural analysis and wrapper analysis reports.
  - See `analysis/README.md` for analysis index.

- **Validation**: `validation/`
  - Data validation architecture and patterns.
  - See `validation/README.md` for validation documentation.

- **Archive**: `archive/`
  - Historical documents from v1.0-v1.11 development.
  - See `archive/implementation-guides/README.md` and `archive/reports/README.md`.
  - All archived docs include replacement links to current documentation.

## Standards

- Prefer **granular docs** (small, focused files).
- Every new doc must be linked from an index (this file or a sectional README).
- Docs must match the current architecture (v1.12.0+ NO WRAPPERS).
- Use lowercase filenames with underscores (e.g., `my_doc.md`, not `MY_DOC.md`).
- README.md files use uppercase (standard convention).

