# Archived Scripts

This directory contains one-time scripts that are no longer needed for current project operations but are preserved for historical reference.

## Archived Scripts

### Documentation Compliance Scripts (Archived 2026-02-09)

These scripts were used to standardize documentation format during the v1.12.0 documentation cleanup initiative.

#### apply_doc_fixes.py
**Purpose:** Apply standardized fixes to documentation files
**What it did:**
- Added metadata footers (Last Updated, Version, Status)
- Ensured required sections exist
- Standardized header formats
**Why archived:** One-time documentation standardization complete. All docs now follow consistent format.

#### batch_fix_docs.sh
**Purpose:** Batch fix all non-compliant documentation files
**What it did:** Applied automated fixes to multiple documentation files in a single run
**Why archived:** One-time batch operation complete. Manual documentation updates preferred going forward.

#### enforce_doc_standards.py
**Purpose:** Validate documentation compliance with standards
**What it did:**
- Checked for required sections (Purpose, Scope, Examples, Related)
- Validated metadata footers
- Generated compliance reports
**Why archived:** Initial compliance validation complete. Standards are now established and documented.

#### finalize_guide_docs.sh
**Purpose:** Finalize guide documentation to meet compliance standards
**What it did:** Applied final touches to guide documentation (Purpose, Scope, Related sections)
**Why archived:** One-time finalization complete. Guides now follow standard structure.

**Current Alternative:** Manual documentation updates following established standards in `docs/` README files.

---

### Migration Scripts

### migrate_v110.py
**Purpose:** Migration script for v1.1.0 calendar alignment update
**What it did:** Automatically updated imports from old `csv_bundle` module to new `csv` package
**Why archived:** All codebase migrations to v1.1.0+ are complete. The csv_bundle module no longer exists as of v1.12.0
**Date archived:** 2026-02-09

### reingest_all.py
**Purpose:** Batch re-ingestion of all bundles from registry
**What it did:** Read bundle metadata from `~/.zipline/bundle_registry.json` and re-ingested bundles with original parameters
**Why archived:**
- Bundle registry system removed in v1.12.0 (NO WRAPPERS architecture)
- Direct Zipline API usage means bundle metadata is managed by Zipline natively
- Use `zipline bundles` command to list bundles
- Use `scripts/ingest_data.py` to ingest individual bundles as needed
**Date archived:** 2026-02-09

### reorganize_csv_for_csvdir.py
**Purpose:** Reorganize CSV files from `data/processed/` to `data/csvdir/` structure
**What it did:**
- Merged multiple date-range files per symbol into single file
- Removed dividend/split columns for FOREX/CRYPTO
- Renamed to `{SYMBOL}.csv` format for csvdir compatibility
**Why archived:**
- One-time migration completed during v1.12.0 transition
- All CSV data now follows csvdir structure in `data/csvdir/{symbol}/`
- New CSV data should be organized in csvdir format from the start
**Date archived:** 2026-02-09

## When to Use These Scripts

⚠️ **These scripts are for historical reference only.** Do not use them in current project operations unless:

**Documentation Scripts:**
- **apply_doc_fixes.py** / **batch_fix_docs.sh** / **enforce_doc_standards.py** / **finalize_guide_docs.sh** - Only if you need to see how automated documentation standardization was performed. Modern documentation should be updated manually following established patterns.

**Migration Scripts:**
1. **migrate_v110.py** - You are working with a fork/branch that pre-dates v1.1.0 and need to migrate old imports
2. **reingest_all.py** - You have a pre-v1.12.0 bundle registry and need to extract bundle metadata (manually adapt the code)
3. **reorganize_csv_for_csvdir.py** - You have old CSV data in `data/processed/` format and need to convert it to csvdir structure

## Current Alternatives

| Archived Script | Current Alternative |
|----------------|---------------------|
| **Documentation Scripts** | |
| `apply_doc_fixes.py` | Manual documentation updates |
| `batch_fix_docs.sh` | Manual documentation updates |
| `enforce_doc_standards.py` | Manual review (standards documented in `docs/`) |
| `finalize_guide_docs.sh` | Manual documentation updates |
| **Migration Scripts** | |
| `migrate_v110.py` | Manual import updates (if needed) |
| `reingest_all.py` | `scripts/ingest_data.py` + `zipline bundles` |
| `reorganize_csv_for_csvdir.py` | Organize CSV data in csvdir format from the start |

## Restoration

If you need to restore any of these scripts:
```bash
git mv scripts/archive/{script_name}.py scripts/
```

## Script Categories

**Documentation Compliance (4 scripts)** - One-time standardization of documentation format
**Migration & Data Organization (3 scripts)** - One-time migrations for v1.1.0 and v1.12.0

---
**Last Updated:** 2026-02-09
**Project Version:** v1.12.0+
**Architecture:** NO WRAPPERS (Direct Zipline API usage)
**Total Archived:** 7 scripts
