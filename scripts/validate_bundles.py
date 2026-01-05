#!/usr/bin/env python3
"""
Bundle validation utility for The Researcher's Cockpit.

Validates bundle registry integrity, checks for corrupted entries,
verifies bundle data exists on disk, and optionally auto-repairs issues.

Usage:
    python scripts/validate_bundles.py              # List and validate all bundles
    python scripts/validate_bundles.py --fix       # Auto-fix corrupted entries
    python scripts/validate_bundles.py --bundle X  # Validate specific bundle
"""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    """Find project root by searching for marker files."""
    markers = ['pyproject.toml', '.git', 'config/settings.yaml', 'CLAUDE.md']
    current = Path(__file__).resolve().parent
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    raise RuntimeError("Could not find project root. Missing marker files.")


# Add project root to path
project_root = _find_project_root()
sys.path.insert(0, str(project_root))

import json
import click
from datetime import datetime


def get_registry_path() -> Path:
    """Get path to bundle registry file."""
    return Path.home() / '.zipline' / 'bundle_registry.json'


def get_bundle_data_path(bundle_name: str) -> Path:
    """Get path to bundle data directory."""
    return Path.home() / '.zipline' / 'data' / bundle_name


def load_registry() -> dict:
    """Load bundle registry from disk."""
    registry_path = get_registry_path()
    if not registry_path.exists():
        return {}
    try:
        with open(registry_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_registry(registry: dict) -> None:
    """Save bundle registry to disk."""
    registry_path = get_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


def validate_date_field(value, field_name: str) -> tuple:
    """
    Validate a date field.

    Returns:
        (is_valid, error_message, suggested_fix)
    """
    if value is None:
        return True, None, None

    if not isinstance(value, str):
        return False, f"{field_name} should be string or null, got {type(value).__name__}", None

    # Check for common corruptions
    if value in ('daily', 'minute', '1h', '5m', '15m', '30m', 'weekly', 'monthly'):
        return False, f"{field_name} contains timeframe '{value}' instead of date", None

    # Try to parse as date
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True, None, None
    except ValueError:
        return False, f"{field_name} is not a valid date: '{value}'", None


def validate_bundle_entry(bundle_name: str, meta: dict) -> list:
    """
    Validate a single bundle registry entry.

    Returns:
        List of (issue_type, message, fix_action) tuples
    """
    issues = []

    # Required fields
    required_fields = ['symbols', 'calendar_name', 'data_frequency']
    for field in required_fields:
        if field not in meta:
            issues.append(('missing_field', f"Missing required field: {field}", None))

    # Validate symbols
    if 'symbols' in meta:
        if not isinstance(meta['symbols'], list):
            issues.append(('invalid_type', f"symbols should be a list, got {type(meta['symbols']).__name__}", None))
        elif len(meta['symbols']) == 0:
            issues.append(('empty_value', "symbols list is empty", None))

    # Validate calendar_name
    valid_calendars = ['XNYS', 'XNAS', 'CRYPTO', 'FOREX']
    if 'calendar_name' in meta and meta['calendar_name'] not in valid_calendars:
        issues.append(('invalid_value', f"Unknown calendar: {meta['calendar_name']}", None))

    # Validate data_frequency
    valid_frequencies = ['daily', 'minute']
    if 'data_frequency' in meta and meta['data_frequency'] not in valid_frequencies:
        issues.append(('invalid_value', f"Invalid data_frequency: {meta['data_frequency']}", None))

    # Validate date fields
    for date_field in ['start_date', 'end_date']:
        if date_field in meta:
            is_valid, error, fix = validate_date_field(meta[date_field], date_field)
            if not is_valid:
                issues.append(('corrupted_date', error, ('set_null', date_field)))

    # Validate timeframe consistency with bundle name
    # Note: Check longer patterns first to avoid substring matches (e.g., '15m' vs '5m')
    if 'timeframe' in meta:
        tf = meta['timeframe']
        # Extract timeframe from bundle name (last component after final underscore)
        name_parts = bundle_name.split('_')
        if len(name_parts) >= 3:
            name_tf = name_parts[-1]  # e.g., 'daily', '1h', '5m', '15m', '30m'
            if name_tf in ('1h', '5m', '15m', '30m', 'daily') and name_tf != tf:
                issues.append(('inconsistent', f"Bundle name suggests {name_tf} but timeframe is '{tf}'", ('set_timeframe', name_tf)))

    # Check if bundle data exists on disk
    bundle_path = get_bundle_data_path(bundle_name)
    if not bundle_path.exists():
        issues.append(('missing_data', f"Bundle data not found at {bundle_path}", None))

    return issues


def apply_fix(meta: dict, fix_action: tuple) -> bool:
    """
    Apply a fix to a bundle metadata entry.

    Returns:
        True if fix was applied, False otherwise
    """
    if fix_action is None:
        return False

    action, param = fix_action

    if action == 'set_null':
        meta[param] = None
        return True
    elif action == 'set_timeframe':
        meta['timeframe'] = param
        return True

    return False


@click.command()
@click.option('--fix', is_flag=True, help='Auto-fix corrupted entries')
@click.option('--bundle', default=None, help='Validate specific bundle only')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def main(fix, bundle, verbose):
    """
    Validate bundle registry integrity and optionally fix issues.

    Examples:
        python scripts/validate_bundles.py              # List and validate
        python scripts/validate_bundles.py --fix        # Auto-fix issues
        python scripts/validate_bundles.py --bundle X   # Check specific bundle
    """
    registry = load_registry()

    if not registry:
        click.echo("No bundles found in registry.")
        click.echo(f"Registry path: {get_registry_path()}")
        return

    # Filter to specific bundle if requested
    if bundle:
        if bundle not in registry:
            click.echo(f"Bundle '{bundle}' not found in registry.")
            click.echo(f"Available bundles: {', '.join(registry.keys())}")
            sys.exit(1)
        registry = {bundle: registry[bundle]}

    click.echo(f"Validating {len(registry)} bundle(s)...\n")

    total_issues = 0
    fixed_issues = 0
    bundles_with_issues = []

    for bundle_name, meta in registry.items():
        issues = validate_bundle_entry(bundle_name, meta)

        if issues:
            bundles_with_issues.append(bundle_name)
            click.echo(f"❌ {bundle_name}")
            for issue_type, message, fix_action in issues:
                total_issues += 1
                prefix = "  "

                if fix and fix_action:
                    if apply_fix(meta, fix_action):
                        click.echo(f"{prefix}⚠ {message} [FIXED]")
                        fixed_issues += 1
                    else:
                        click.echo(f"{prefix}✗ {message}")
                else:
                    click.echo(f"{prefix}✗ {message}")
        else:
            if verbose:
                click.echo(f"✓ {bundle_name}")
                click.echo(f"    symbols: {meta.get('symbols', [])}")
                click.echo(f"    calendar: {meta.get('calendar_name')}")
                click.echo(f"    frequency: {meta.get('data_frequency')}")
                click.echo(f"    timeframe: {meta.get('timeframe')}")
            else:
                click.echo(f"✓ {bundle_name}")

    # Save fixes if any were applied
    if fix and fixed_issues > 0:
        # Reload full registry if we filtered
        if bundle:
            full_registry = load_registry()
            full_registry[bundle] = meta
            save_registry(full_registry)
        else:
            save_registry(registry)
        click.echo(f"\nSaved {fixed_issues} fix(es) to registry.")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("VALIDATION SUMMARY")
    click.echo("=" * 50)
    click.echo(f"Total bundles: {len(registry)}")
    click.echo(f"Bundles with issues: {len(bundles_with_issues)}")
    click.echo(f"Total issues: {total_issues}")
    if fix:
        click.echo(f"Issues fixed: {fixed_issues}")
        click.echo(f"Issues remaining: {total_issues - fixed_issues}")

    if bundles_with_issues and not fix:
        click.echo("\nRun with --fix to auto-repair fixable issues.")

    # Exit with error code if unfixed issues remain
    if total_issues - fixed_issues > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
