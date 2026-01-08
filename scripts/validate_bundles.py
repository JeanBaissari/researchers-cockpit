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
import os


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
import exchange_calendars

# Import shared constants from lib modules to ensure consistency
from lib.data_loader import VALID_TIMEFRAMES, TIMEFRAME_DATA_LIMITS, VALID_SOURCES
from lib.extension import register_custom_calendars, CUSTOM_CALENDARS

# =============================================================================
# CONSTANTS
# =============================================================================

# Valid calendars: dynamically fetch standard calendars from exchange_calendars
# This ensures we stay in sync with the package
STANDARD_CALENDARS = sorted(exchange_calendars.get_calendar_names())

# Custom calendars registered by our extension module
# These are defined in lib/extension.py
CUSTOM_CALENDAR_NAMES = list(CUSTOM_CALENDARS.keys()) if CUSTOM_CALENDARS else []

# Combined valid calendars
VALID_CALENDARS = STANDARD_CALENDARS + CUSTOM_CALENDAR_NAMES

# Valid data frequencies for Zipline (these are Zipline's actual accepted values)
VALID_DATA_FREQUENCIES = ['daily', 'minute']

# Valid asset classes (aligned with lib/backtest.py BacktestConfig)
VALID_ASSET_CLASSES = ['equity', 'crypto', 'forex', None]


# =============================================================================
# PATH UTILITIES
# =============================================================================

def get_zipline_root() -> Path:
    """
    Get Zipline root directory, respecting ZIPLINE_ROOT environment variable.
    
    Zipline allows overriding the default ~/.zipline location via ZIPLINE_ROOT.
    """
    zipline_root = os.environ.get('ZIPLINE_ROOT')
    if zipline_root:
        return Path(zipline_root)
    return Path.home() / '.zipline'


def get_registry_path() -> Path:
    """Get path to bundle registry file."""
    return get_zipline_root() / 'bundle_registry.json'


def get_bundle_data_path(bundle_name: str) -> Path:
    """
    Get path to bundle data directory.
    
    Zipline stores bundles in versioned subdirectories under {ZIPLINE_ROOT}/bundles/{bundle_name}/
    Each ingestion creates a new timestamp-based version directory.
    """
    return get_zipline_root() / 'bundles' / bundle_name


def check_bundle_data_exists(bundle_name: str) -> tuple:
    """
    Check if bundle data exists on disk.
    
    Returns:
        (exists: bool, path: Path, details: str)
    """
    bundle_path = get_bundle_data_path(bundle_name)
    
    if not bundle_path.exists():
        return False, bundle_path, "Bundle directory does not exist"
    
    if not bundle_path.is_dir():
        return False, bundle_path, "Bundle path exists but is not a directory"
    
    # Check for versioned subdirectories (Zipline creates timestamp-based versions)
    versions = [d for d in bundle_path.iterdir() if d.is_dir()]
    if not versions:
        return False, bundle_path, "Bundle directory exists but contains no version data"
    
    # Check the latest version has actual data files
    latest_version = max(versions, key=lambda d: d.name)
    data_files = list(latest_version.glob('*'))
    if not data_files:
        return False, bundle_path, f"Latest version {latest_version.name} is empty"
    
    return True, bundle_path, f"{len(versions)} version(s), latest: {latest_version.name}"


# =============================================================================
# REGISTRY UTILITIES
# =============================================================================

def load_registry() -> dict:
    """Load bundle registry from disk."""
    registry_path = get_registry_path()
    if not registry_path.exists():
        return {}
    try:
        with open(registry_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Warning: Registry file is corrupted: {e}", err=True)
        return {}
    except IOError as e:
        click.echo(f"Warning: Could not read registry file: {e}", err=True)
        return {}


def save_registry(registry: dict) -> None:
    """Save bundle registry to disk."""
    registry_path = get_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_date_field(value, field_name: str) -> tuple:
    """
    Validate a date field.

    Returns:
        (is_valid, error_message, suggested_fix)
    """
    if value is None:
        return True, None, None

    if not isinstance(value, str):
        return False, f"{field_name} should be string or null, got {type(value).__name__}", ('set_null', field_name)

    # Check for common corruptions - timeframe values in date fields
    if value.lower() in [tf.lower() for tf in VALID_TIMEFRAMES]:
        return False, f"{field_name} contains timeframe '{value}' instead of date", ('set_null', field_name)

    # Try to parse as date
    try:
        datetime.strptime(value, '%Y-%m-%d')
        return True, None, None
    except ValueError:
        # Try other common date formats
        for fmt in ['%Y/%m/%d', '%d-%m-%Y', '%m/%d/%Y']:
            try:
                parsed = datetime.strptime(value, fmt)
                # Suggest converting to standard format
                correct_date = parsed.strftime('%Y-%m-%d')
                return False, f"{field_name} uses non-standard format: '{value}'", ('set_date', field_name, correct_date)
            except ValueError:
                continue
        return False, f"{field_name} is not a valid date: '{value}'", ('set_null', field_name)


def validate_timeframe_field(meta: dict, bundle_name: str) -> list:
    """
    Validate timeframe field and its consistency with bundle name.
    
    Returns:
        List of (issue_type, message, fix_action) tuples
    """
    issues = []
    
    # Extract timeframe from bundle name (last component after final underscore)
    name_parts = bundle_name.split('_')
    inferred_timeframe = None
    
    if len(name_parts) >= 2:
        potential_tf = name_parts[-1].lower()
        # Check if the last part matches any valid timeframe
        if potential_tf in [tf.lower() for tf in VALID_TIMEFRAMES]:
            inferred_timeframe = potential_tf
    
    # Check if timeframe field exists
    if 'timeframe' not in meta:
        if inferred_timeframe:
            issues.append((
                'missing_field',
                f"Missing 'timeframe' field (bundle name suggests '{inferred_timeframe}')",
                ('set_timeframe', inferred_timeframe)
            ))
        else:
            issues.append((
                'missing_field',
                "Missing 'timeframe' field and cannot infer from bundle name",
                None
            ))
    else:
        tf = meta['timeframe']
        
        # Validate timeframe value
        if tf is None:
            if inferred_timeframe:
                issues.append((
                    'null_value',
                    f"timeframe is null (bundle name suggests '{inferred_timeframe}')",
                    ('set_timeframe', inferred_timeframe)
                ))
        elif not isinstance(tf, str):
            issues.append((
                'invalid_type',
                f"timeframe should be string, got {type(tf).__name__}",
                ('set_timeframe', inferred_timeframe) if inferred_timeframe else None
            ))
        elif tf.lower() not in [t.lower() for t in VALID_TIMEFRAMES]:
            issues.append((
                'invalid_value',
                f"Invalid timeframe: '{tf}'. Valid options: {', '.join(VALID_TIMEFRAMES)}",
                ('set_timeframe', inferred_timeframe) if inferred_timeframe else None
            ))
        elif inferred_timeframe and tf.lower() != inferred_timeframe:
            # Timeframe exists but doesn't match bundle name
            issues.append((
                'inconsistent',
                f"Bundle name suggests '{inferred_timeframe}' but timeframe is '{tf}'",
                ('set_timeframe', inferred_timeframe)
            ))
    
    return issues


def validate_asset_class_field(meta: dict, bundle_name: str) -> list:
    """
    Validate asset_class field.
    
    Returns:
        List of (issue_type, message, fix_action) tuples
    """
    issues = []
    
    if 'asset_class' not in meta:
        # asset_class is optional, but we can try to infer it
        inferred_class = None
        bundle_lower = bundle_name.lower()
        
        if 'crypto' in bundle_lower or 'btc' in bundle_lower or 'eth' in bundle_lower:
            inferred_class = 'crypto'
        elif 'forex' in bundle_lower or 'fx' in bundle_lower:
            inferred_class = 'forex'
        elif any(x in bundle_lower for x in ['spy', 'aapl', 'msft', 'equity']):
            inferred_class = 'equity'
        
        if inferred_class:
            issues.append((
                'missing_field',
                f"Missing 'asset_class' field (bundle name suggests '{inferred_class}')",
                ('set_asset_class', inferred_class)
            ))
    else:
        asset_class = meta['asset_class']
        if asset_class is not None and asset_class not in VALID_ASSET_CLASSES:
            issues.append((
                'invalid_value',
                f"Invalid asset_class: '{asset_class}'. Valid: {', '.join(str(x) for x in VALID_ASSET_CLASSES if x)}",
                None
            ))
    
    return issues


def validate_source_field(meta: dict) -> list:
    """
    Validate source field.
    
    Returns:
        List of (issue_type, message, fix_action) tuples
    """
    issues = []
    
    if 'source' in meta:
        source = meta['source']
        if source is not None and source not in VALID_SOURCES:
            issues.append((
                'invalid_value',
                f"Invalid source: '{source}'. Valid: {', '.join(VALID_SOURCES)}",
                None
            ))
    
    return issues


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
        symbols = meta['symbols']
        if not isinstance(symbols, list):
            issues.append(('invalid_type', f"symbols should be a list, got {type(symbols).__name__}", None))
        elif len(symbols) == 0:
            issues.append(('empty_value', "symbols list is empty", None))
        else:
            # Check for invalid symbol entries
            for i, sym in enumerate(symbols):
                if not isinstance(sym, str):
                    issues.append(('invalid_type', f"symbols[{i}] should be string, got {type(sym).__name__}", None))
                elif not sym.strip():
                    issues.append(('empty_value', f"symbols[{i}] is empty string", None))

    # Validate calendar_name
    if 'calendar_name' in meta:
        cal = meta['calendar_name']
        if cal is None:
            issues.append(('null_value', "calendar_name is null", None))
        elif not isinstance(cal, str):
            issues.append(('invalid_type', f"calendar_name should be string, got {type(cal).__name__}", None))
        elif cal not in VALID_CALENDARS:
            # Provide helpful suggestion
            suggestion = ""
            cal_lower = cal.lower()
            if 'crypto' in cal_lower or 'btc' in cal_lower:
                suggestion = " (did you mean 'CRYPTO'?)"
            elif 'forex' in cal_lower or 'fx' in cal_lower:
                suggestion = " (did you mean 'FOREX'?)"
            elif 'nyse' in cal_lower or 'us' in cal_lower:
                suggestion = " (did you mean 'XNYS'?)"
            issues.append(('invalid_value', f"Unknown calendar: '{cal}'{suggestion}. Valid: {', '.join(CUSTOM_CALENDAR_NAMES)} (custom) + standard exchange calendars", None))

    # Validate data_frequency
    if 'data_frequency' in meta:
        freq = meta['data_frequency']
        if freq is None:
            issues.append(('null_value', "data_frequency is null", None))
        elif not isinstance(freq, str):
            issues.append(('invalid_type', f"data_frequency should be string, got {type(freq).__name__}", None))
        elif freq not in VALID_DATA_FREQUENCIES:
            # Try to suggest correct value
            suggested_fix = None
            if freq.lower() in ['daily', 'day', '1d', 'd']:
                suggested_fix = ('set_frequency', 'daily')
            elif freq.lower() in ['minute', 'min', '1m', 'm', 'intraday']:
                suggested_fix = ('set_frequency', 'minute')
            issues.append((
                'invalid_value',
                f"Invalid data_frequency: '{freq}'. Valid: {', '.join(VALID_DATA_FREQUENCIES)}",
                suggested_fix
            ))

    # Validate date fields
    for date_field in ['start_date', 'end_date']:
        if date_field in meta:
            is_valid, error, fix = validate_date_field(meta[date_field], date_field)
            if not is_valid:
                issues.append(('corrupted_date', error, fix))

    # Validate timeframe field and consistency
    timeframe_issues = validate_timeframe_field(meta, bundle_name)
    issues.extend(timeframe_issues)

    # Validate asset_class field
    asset_class_issues = validate_asset_class_field(meta, bundle_name)
    issues.extend(asset_class_issues)

    # Validate source field
    source_issues = validate_source_field(meta)
    issues.extend(source_issues)

    # Check if bundle data exists on disk
    exists, bundle_path, details = check_bundle_data_exists(bundle_name)
    if not exists:
        issues.append(('missing_data', f"Bundle data issue: {details} (path: {bundle_path})", None))

    return issues


def apply_fix(meta: dict, fix_action: tuple) -> bool:
    """
    Apply a fix to a bundle metadata entry.

    Returns:
        True if fix was applied, False otherwise
    """
    if fix_action is None:
        return False

    action = fix_action[0]

    if action == 'set_null':
        field = fix_action[1]
        meta[field] = None
        return True
    elif action == 'set_date':
        field = fix_action[1]
        value = fix_action[2]
        meta[field] = value
        return True
    elif action == 'set_timeframe':
        value = fix_action[1]
        meta['timeframe'] = value
        return True
    elif action == 'set_frequency':
        value = fix_action[1]
        meta['data_frequency'] = value
        return True
    elif action == 'set_asset_class':
        value = fix_action[1]
        meta['asset_class'] = value
        return True

    return False


# =============================================================================
# CLI COMMAND
# =============================================================================

@click.command()
@click.option('--fix', is_flag=True, help='Auto-fix corrupted entries')
@click.option('--bundle', default=None, help='Validate specific bundle only')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--check-disk/--no-check-disk', default=True, help='Check if bundle data exists on disk')
def main(fix, bundle, verbose, check_disk):
    """
    Validate bundle registry integrity and optionally fix issues.

    Examples:
        python scripts/validate_bundles.py              # List and validate
        python scripts/validate_bundles.py --fix        # Auto-fix issues
        python scripts/validate_bundles.py --bundle X   # Check specific bundle
        python scripts/validate_bundles.py --no-check-disk  # Skip disk checks
    """
    # Register custom calendars to ensure they're available
    try:
        register_custom_calendars()
    except Exception as e:
        click.echo(f"Warning: Could not register custom calendars: {e}", err=True)

    registry = load_registry()

    if not registry:
        click.echo("No bundles found in registry.")
        click.echo(f"Registry path: {get_registry_path()}")
        return

    # Filter to specific bundle if requested
    original_registry = registry.copy()
    if bundle:
        if bundle not in registry:
            click.echo(f"Bundle '{bundle}' not found in registry.")
            click.echo(f"Available bundles: {', '.join(sorted(registry.keys()))}")
            sys.exit(1)
        registry = {bundle: registry[bundle]}

    click.echo(f"Validating {len(registry)} bundle(s)...")
    click.echo(f"Using {len(VALID_TIMEFRAMES)} valid timeframes: {', '.join(VALID_TIMEFRAMES)}")
    click.echo(f"Using {len(CUSTOM_CALENDAR_NAMES)} custom calendars: {', '.join(CUSTOM_CALENDAR_NAMES)}")
    click.echo(f"Using {len(STANDARD_CALENDARS)} standard exchange calendars")
    click.echo(f"Zipline root: {get_zipline_root()}")
    click.echo()

    total_issues = 0
    fixed_issues = 0
    bundles_with_issues = []

    for bundle_name, meta in sorted(registry.items()):
        issues = validate_bundle_entry(bundle_name, meta)
        
        # Filter out disk check issues if --no-check-disk
        if not check_disk:
            issues = [i for i in issues if i[0] != 'missing_data']

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
                    fixable = " [fixable]" if fix_action else ""
                    click.echo(f"{prefix}✗ {message}{fixable}")
        else:
            if verbose:
                click.echo(f"✓ {bundle_name}")
                click.echo(f"    symbols: {meta.get('symbols', [])}")
                click.echo(f"    calendar: {meta.get('calendar_name')}")
                click.echo(f"    frequency: {meta.get('data_frequency')}")
                click.echo(f"    timeframe: {meta.get('timeframe')}")
                click.echo(f"    asset_class: {meta.get('asset_class')}")
                click.echo(f"    source: {meta.get('source')}")
                if check_disk:
                    exists, path, details = check_bundle_data_exists(bundle_name)
                    click.echo(f"    disk: {details}")
            else:
                click.echo(f"✓ {bundle_name}")

    # Save fixes if any were applied
    if fix and fixed_issues > 0:
        # Merge fixes back into full registry if we filtered
        if bundle:
            original_registry[bundle] = meta
            save_registry(original_registry)
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
        fixable_count = sum(
            1 for bn in bundles_with_issues
            for issue in validate_bundle_entry(bn, original_registry.get(bn, registry.get(bn, {})))
            if issue[2] is not None
        )
        if fixable_count > 0:
            click.echo(f"\n{fixable_count} issue(s) can be auto-fixed. Run with --fix to repair.")

    # Exit with error code if unfixed issues remain
    if total_issues - fixed_issues > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
