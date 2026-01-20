#!/usr/bin/env python3
"""
Migration script for v1.1.0 calendar alignment update.

Automatically updates imports from old csv_bundle module to new csv package.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Bootstrap: Add project root to path (scripts are in scripts/ subdirectory)
# This allows us to import lib.paths.get_project_root
_project_root_bootstrap = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root_bootstrap))

from lib.paths import get_project_root


def find_files_with_old_imports(root: Path) -> List[Path]:
    """
    Find Python files with old csv_bundle imports.

    Args:
        root: Project root directory

    Returns:
        List of files containing old imports
    """
    pattern = re.compile(r'from\s+lib\.bundles\.csv_bundle\s+import|import\s+lib\.bundles\.csv_bundle')
    files_to_update = []

    # Search in lib/, scripts/, tests/, notebooks/
    search_dirs = ['lib', 'scripts', 'tests']
    for dir_name in search_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob('*.py'):
            # Skip the compatibility wrapper itself
            if py_file.name == 'csv_bundle.py':
                continue

            try:
                content = py_file.read_text()
                if pattern.search(content):
                    files_to_update.append(py_file)
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")

    return files_to_update


def update_imports(file_path: Path, dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    Update old imports to new v1.1.0 imports.

    Args:
        file_path: Path to Python file
        dry_run: If True, don't modify files

    Returns:
        (modified: bool, changes: List[str])
    """
    try:
        content = file_path.read_text()
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    original_content = content
    changes = []

    # Pattern 1: from lib.bundles.csv_bundle import X
    pattern1 = re.compile(r'from\s+lib\.bundles\.csv_bundle\s+import\s+')
    if pattern1.search(content):
        content = pattern1.sub('from lib.bundles.csv import ', content)
        changes.append("Updated: from lib.bundles.csv_bundle import → from lib.bundles.csv import")

    # Pattern 2: import lib.bundles.csv_bundle
    pattern2 = re.compile(r'import\s+lib\.bundles\.csv_bundle')
    if pattern2.search(content):
        content = pattern2.sub('import lib.bundles.csv', content)
        changes.append("Updated: import lib.bundles.csv_bundle → import lib.bundles.csv")

    # Pattern 3: lib.bundles.csv_bundle.X (references)
    pattern3 = re.compile(r'lib\.bundles\.csv_bundle\.')
    if pattern3.search(content):
        content = pattern3.sub('lib.bundles.csv.', content)
        changes.append("Updated references: lib.bundles.csv_bundle.X → lib.bundles.csv.X")

    if content != original_content:
        if not dry_run:
            try:
                file_path.write_text(content)
                return True, changes
            except Exception as e:
                return False, [f"Error writing file: {e}"]
        else:
            return True, changes

    return False, []


def main():
    """Main migration entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Migrate codebase from v1.0.10 to v1.1.0 calendar alignment architecture'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Automatically fix all imports without confirmation'
    )
    args = parser.parse_args()

    try:
        root = get_project_root()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("=" * 60)
    print("v1.1.0 Calendar Alignment Migration Script")
    print("=" * 60)
    print()

    # Find files with old imports
    print("Scanning codebase for old csv_bundle imports...")
    files_to_update = find_files_with_old_imports(root)

    if not files_to_update:
        print("✓ No old imports found. Codebase is already v1.1.0 compatible!")
        sys.exit(0)

    print(f"Found {len(files_to_update)} file(s) with old imports:")
    for file_path in files_to_update:
        rel_path = file_path.relative_to(root)
        print(f"  - {rel_path}")
    print()

    # Dry run mode
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        print()

        for file_path in files_to_update:
            rel_path = file_path.relative_to(root)
            modified, changes = update_imports(file_path, dry_run=True)
            if modified:
                print(f"Would update {rel_path}:")
                for change in changes:
                    print(f"  • {change}")
                print()

        print("Run without --dry-run to apply changes.")
        sys.exit(0)

    # Confirm before proceeding
    if not args.auto_fix:
        response = input(f"Update {len(files_to_update)} file(s)? [y/N]: ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    # Update files
    print("Updating files...")
    success_count = 0
    error_count = 0

    for file_path in files_to_update:
        rel_path = file_path.relative_to(root)
        modified, changes = update_imports(file_path, dry_run=False)

        if modified:
            print(f"✓ Updated {rel_path}")
            for change in changes:
                print(f"  • {change}")
            success_count += 1
        else:
            if changes:  # Error occurred
                print(f"✗ Failed {rel_path}")
                for change in changes:
                    print(f"  • {change}")
                error_count += 1

    print()
    print("=" * 60)
    print(f"Migration complete!")
    print(f"  Files updated: {success_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run tests to verify: pytest tests/ -v")
    print("  2. Review changes: git diff")
    print("  3. Consider re-ingesting bundles for full v1.1.0 benefits")

    sys.exit(0 if error_count == 0 else 1)


if __name__ == '__main__':
    main()
