"""
Verify package exports are clean after v1.12.0 refactoring.

Checks for:
- No deleted module imports (specific to deleted modules, not docstrings)
- No wrapper function exports in __all__
"""

import sys
import re
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
lib_dir = project_root / "lib"

# Specific import patterns for DELETED modules only
DELETED_IMPORT_PATTERNS = [
    (r"from \.csv import", "lib/bundles/__init__.py"),  # csv module deleted from bundles
    (r"from \.\.bundles\.csv import", None),  # Any import from bundles.csv
    (r"from \.registry import", "lib/bundles/__init__.py"),  # registry deleted from bundles
    (r"from \.\.bundles\.registry import", None),  # Any import from bundles.registry
    (r"from \.guard import", "lib/bundles/__init__.py"),  # guard deleted from bundles
    (r"from \.\.bundles\.guard import", None),  # Any import from bundles.guard
    (r"from \.sessions import", "lib/calendars/__init__.py"),  # sessions deleted from calendars
    (r"from \.\.calendars\.sessions import", None),  # Any import from calendars.sessions
    (r"from \.aggregation import", "lib/data/__init__.py"),  # aggregation deleted from data
    (r"from \.\.data\.aggregation import", None),  # Any import from data.aggregation
]

# Deleted function names to check in __all__
DELETED_FUNCTIONS = [
    "aggregate_ohlcv",
    "SessionManager",
    "register_csv_bundle",
    "register_bundle_metadata",
    "add_registered_bundle",
    "validate_bundle_config",
    "load_and_process_csv",
    "write_minute_and_daily_bars",
]

errors = []

# Check all __init__.py files
init_files = list(lib_dir.rglob("__init__.py"))
for init_file in init_files:
    rel_path = init_file.relative_to(project_root)
    content = init_file.read_text()

    # Split into lines for checking
    lines = content.split("\n")
    in_docstring = False
    in_multiline_string = False

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track docstring state
        if '"""' in line:
            in_docstring = not in_docstring
            continue
        if "'''" in line:
            in_multiline_string = not in_multiline_string
            continue

        # Skip lines inside docstrings or comments
        if in_docstring or in_multiline_string or stripped.startswith("#"):
            continue

        # Check for deleted import patterns
        for pattern, specific_file in DELETED_IMPORT_PATTERNS:
            if re.search(pattern, line):
                # If specific_file is set, only flag for that file
                if specific_file is None or str(rel_path) == specific_file:
                    errors.append(
                        f"{rel_path}:{line_num}: Imports from deleted module: {line.strip()}"
                    )

    # Check __all__ for deleted functions
    if "__all__" in content:
        # Extract __all__ content
        all_match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if all_match:
            all_content = all_match.group(1)
            for func_name in DELETED_FUNCTIONS:
                # Check if function name appears in __all__ as a string
                if re.search(rf"['\"]" + func_name + rf"['\"]", all_content):
                    errors.append(f"{rel_path}: __all__ contains deleted function '{func_name}'")

# Print results
if errors:
    print("❌ EXPORT VERIFICATION FAILED\n")
    for error in errors:
        print(f"  ERROR: {error}")
    print(f"\nChecked {len(init_files)} __init__.py files")
    sys.exit(1)
else:
    print("✅ EXPORT VERIFICATION PASSED")
    print(f"   Checked {len(init_files)} __init__.py files")
    print("   No deleted module exports found")
    print("   No deleted functions in __all__ definitions")
    sys.exit(0)
