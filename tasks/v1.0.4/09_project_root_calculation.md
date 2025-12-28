# Detailed Solution Plan: Robust Project Root Resolution

## Problem Analysis

The current \_project\_root calculation in strategies/\_template/strategy.py uses fragile relative path traversal (e.g., Path(\_\_file\_\_).parent.parent.parent...). This breaks when:

* Strategies are nested at different depths  
* Files are copied/moved to different locations  
* Symlinks are involved (as documented in pipeline.md for results linking)  
* Running from different working directories

## Architectural Constraints

Based on workflow.md and pipeline.md, the solution must:

1. Work with the template copy pattern (cp \-r strategies/\_template strategies/crypto/btc\_new\_idea)  
2. Support the symlink pattern for results directories  
3. Be compatible with all three execution methods: notebooks, scripts, and library calls  
4. Allow AI agents to create strategies programmatically  
5. Not break existing strategies during migration

## Proposed Solution: Marker-Based Root Discovery with Caching

### Phase 1: Create Centralized Root Discovery Module

Location: lib/paths.py (new file)  
lib/  
├── \_\_init\_\_.py  
├── paths.py          \# NEW: Centralized path resolution  
├── backtest.py  
├── metrics.py  
└── ...  
Design:

1. Search upward from any starting point for project markers in priority order:  
* pyproject.toml (primary marker, already exists in Python projects)  
* .git/ directory  
* config/settings.yaml (project-specific marker per workflow.md)  
2. Cache result at module level to avoid repeated filesystem traversal  
3. Provide typed accessors for common paths

Key Functions:

* get\_project\_root() \-\> Path — Returns cached project root  
* get\_strategies\_dir() \-\> Path — Returns {root}/strategies  
* get\_results\_dir() \-\> Path — Returns {root}/results  
* get\_data\_dir() \-\> Path — Returns {root}/data  
* get\_config\_dir() \-\> Path — Returns {root}/config  
* resolve\_strategy\_path(name: str) \-\> Path — Handles {asset\_class}/{strategy\_name} resolution

Error Handling:

* Raise ProjectRootNotFoundError (custom exception) with clear message if no marker found  
* Include searched paths in error for debugging

### Phase 2: Create Project Marker File (Optional but Recommended)

Location: Project rootCreate .project\_root marker file (empty or containing project metadata). This provides:

* Explicit marker independent of git/pyproject  
* Works in distribution scenarios where .git may not exist  
* Self-documenting

### Phase 3: Update Strategy Template

File: strategies/\_template/[strategy.py](http://strategy.py)  
Replace:  
\_project\_root \= Path(\_\_file\_\_).parent.parent.parent  *\# fragile*  
With:  
*from* lib.paths *import* get\_project\_root, get\_strategies\_dir  
*\# Usage is now location-agnostic*  
Template Changes:

1. Add import at top  
2. Remove manual path calculation  
3. Update any path references to use lib.paths functions

### Phase 4: Update lib/backtest.py

Ensure backtest execution uses lib.paths for:

* Locating strategy directories  
* Creating results directories  
* Loading parameters.yaml

This ensures consistency whether called from notebook, script, or library.

### Phase 5: Migration Script for Existing Strategies

Location: scripts/migrate\_paths.py

1. Scan all strategies/\*/ directories  
1. Identify strategies using old path pattern (regex: Path\\(\_\_file\_\_\\).\*parent.\*parent)  
1. Generate diff/patch for each  
1. Apply changes (with backup)  
1. Report migration status

### Phase 6: Update Agent Instructions

Files to update:

* .agent/strategy\_creator.md — Instruct agents to use lib.paths  
* .agent/backtest\_runner.md — Document path resolution expectations

### Phase 7: Add Validation

Location: lib/paths.pyAdd validate\_project\_structure() function that checks:

* Required directories exist (strategies/, results/, data/, config/)  
* Required config files exist  
* Template exists at expected location

Call this on first import with warning (not error) for missing optional components.

## Implementation Order

1. lib/paths.py — Core module (no dependencies, can be tested in isolation)  
2. Unit tests for lib/paths.py — Verify marker search, caching, edge cases  
3. Update strategies/template/strategy.py — New strategies get correct pattern  
4. Update lib/backtest.py — Execution layer uses centralized paths  
5. Migration script — Batch update existing strategies  
6. Agent instructions — Document for AI agents  
7. Integration test — Full workflow: create → ingest → backtest → results

## Rollback Strategy

If issues arise:

1. lib/paths.py has fallback to environment variable PROJECT\_ROOT  
2. Old strategies continue working until explicitly migrated  
3. Migration script creates .bak files

## Testing Requirements

1. Unit: lib/paths.py with various starting directories  
2. Integration: Strategy created at different nesting depths  
3. Edge cases: Symlinked strategies, execution from different CWDs  
4. Regression: Existing spy\_sma\_cross continues to work

Draft me a very detailed, architecturally-consistent, and robust planning for the solution of the issue according to Zipline-reloaded code-example recommended patterns, and high-quality, consistent system engineering processes required for this. The end goal is that our @algorithmic\_trading/v1\_researchers\_cockpit/pipeline.md & @algorithmic\_trading/v1\_researchers\_cockpit/[workflow.md](http://workflow.md) can all run smoothly from beginning to end without any architectural inconsistency/errors. Don’t shy away from giving long-form but long-term solutions.