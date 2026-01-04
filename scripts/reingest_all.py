#!/usr/bin/env python3
"""
Re-ingest all bundles from registry.

This script reads the bundle registry and re-ingests all (or selected) bundles
with their original parameters. Useful for:
- Updating data after bug fixes
- Refreshing stale data
- Rebuilding bundles after schema changes

Usage Examples:
    # Re-ingest all bundles
    python scripts/reingest_all.py

    # Re-ingest specific bundles
    python scripts/reingest_all.py --bundles yahoo_equities_daily,yahoo_crypto_1h

    # Re-ingest only daily bundles
    python scripts/reingest_all.py --timeframe daily

    # Re-ingest only crypto bundles
    python scripts/reingest_all.py --assets crypto

    # Dry run (show what would be re-ingested)
    python scripts/reingest_all.py --dry-run

    # Force re-ingest (skip confirmation)
    python scripts/reingest_all.py --force
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from typing import Optional, List, Dict, Any

from lib.data_loader import (
    _load_bundle_registry,
    ingest_bundle,
    VALID_TIMEFRAMES,
)


def parse_bundle_name(bundle_name: str) -> Dict[str, str]:
    """
    Parse bundle name to extract source and asset class.

    Bundle naming convention: {source}_{asset}_{timeframe}
    Examples:
        yahoo_equities_daily -> source='yahoo', assets='equities', timeframe='daily'
        yahoo_crypto_1h -> source='yahoo', assets='crypto', timeframe='1h'

    Args:
        bundle_name: Bundle name string

    Returns:
        Dict with 'source', 'assets', and 'timeframe_from_name' keys
    """
    parts = bundle_name.split('_')

    if len(parts) < 3:
        # Fallback for non-standard names
        return {
            'source': parts[0] if parts else 'yahoo',
            'assets': parts[1] if len(parts) > 1 else 'equities',
            'timeframe_from_name': parts[2] if len(parts) > 2 else 'daily',
        }

    return {
        'source': parts[0],
        'assets': parts[1],
        'timeframe_from_name': '_'.join(parts[2:]),  # Handle multi-part timeframes
    }


def filter_bundles(
    registry: Dict[str, Any],
    bundle_names: Optional[List[str]] = None,
    timeframe_filter: Optional[str] = None,
    assets_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Filter bundles based on criteria.

    Args:
        registry: Full bundle registry
        bundle_names: Specific bundle names to include (None = all)
        timeframe_filter: Only include bundles with this timeframe
        assets_filter: Only include bundles with this asset class
        source_filter: Only include bundles from this source

    Returns:
        Filtered registry dict
    """
    filtered = {}

    for name, meta in registry.items():
        # Filter by specific bundle names
        if bundle_names and name not in bundle_names:
            continue

        # Parse bundle name for source/assets
        parsed = parse_bundle_name(name)

        # Filter by timeframe (use registry metadata, fallback to parsed name)
        bundle_timeframe = meta.get('timeframe', parsed['timeframe_from_name'])
        if timeframe_filter and bundle_timeframe != timeframe_filter:
            continue

        # Filter by asset class
        if assets_filter and parsed['assets'] != assets_filter:
            continue

        # Filter by source
        if source_filter and parsed['source'] != source_filter:
            continue

        filtered[name] = meta

    return filtered


def reingest_bundle(
    bundle_name: str,
    meta: Dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """
    Re-ingest a single bundle using its registry metadata.

    Args:
        bundle_name: Name of the bundle
        meta: Bundle metadata from registry
        dry_run: If True, only print what would happen

    Returns:
        True if successful, False otherwise
    """
    # Parse bundle name to get source and assets
    parsed = parse_bundle_name(bundle_name)

    # Extract parameters from metadata
    symbols = meta.get('symbols', [])
    calendar_name = meta.get('calendar_name')
    start_date = meta.get('start_date')
    end_date = meta.get('end_date')
    timeframe = meta.get('timeframe', 'daily')

    # Validate end_date (some old entries may have 'daily' as end_date by mistake)
    if end_date and not _is_valid_date(end_date):
        end_date = None

    if dry_run:
        click.echo(f"  Would re-ingest: {bundle_name}")
        click.echo(f"    Source: {parsed['source']}")
        click.echo(f"    Assets: {parsed['assets']}")
        click.echo(f"    Symbols: {', '.join(symbols)}")
        click.echo(f"    Timeframe: {timeframe}")
        click.echo(f"    Calendar: {calendar_name}")
        click.echo(f"    Start: {start_date}")
        click.echo(f"    End: {end_date or 'today'}")
        return True

    try:
        click.echo(f"  Re-ingesting: {bundle_name}...")
        ingest_bundle(
            source=parsed['source'],
            assets=[parsed['assets']],
            bundle_name=bundle_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            calendar_name=calendar_name,
            timeframe=timeframe,
            force=True,  # Force re-registration with new parameters
        )
        click.echo(f"  ✓ {bundle_name} - success")
        return True

    except Exception as e:
        click.echo(f"  ✗ {bundle_name} - failed: {e}", err=True)
        return False


def _is_valid_date(date_str: str) -> bool:
    """Check if string is a valid YYYY-MM-DD date."""
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


@click.command()
@click.option('--bundles', '-b', default=None,
              help='Comma-separated list of bundle names to re-ingest')
@click.option('--timeframe', '-t', default=None,
              type=click.Choice(VALID_TIMEFRAMES, case_sensitive=False),
              help='Only re-ingest bundles with this timeframe')
@click.option('--assets', '-a', default=None,
              type=click.Choice(['crypto', 'forex', 'equities']),
              help='Only re-ingest bundles with this asset class')
@click.option('--source', '-s', default=None,
              type=click.Choice(['yahoo', 'binance', 'oanda']),
              help='Only re-ingest bundles from this source')
@click.option('--dry-run', is_flag=True,
              help='Show what would be re-ingested without actually doing it')
@click.option('--force', '-f', is_flag=True,
              help='Skip confirmation prompt')
@click.option('--list', 'list_only', is_flag=True,
              help='List all bundles in registry and exit')
def main(bundles, timeframe, assets, source, dry_run, force, list_only):
    """
    Re-ingest all bundles from the registry.

    Reads bundle metadata from ~/.zipline/bundle_registry.json and re-ingests
    each bundle with its original parameters. Useful for refreshing data or
    applying fixes to existing bundles.

    \b
    Examples:
        # Re-ingest all bundles
        python scripts/reingest_all.py

        # Re-ingest only crypto bundles
        python scripts/reingest_all.py --assets crypto

        # Re-ingest only hourly bundles
        python scripts/reingest_all.py --timeframe 1h

        # Preview what would be re-ingested
        python scripts/reingest_all.py --dry-run
    """
    # Load registry
    registry = _load_bundle_registry()

    if not registry:
        click.echo("No bundles found in registry.")
        click.echo("Registry location: ~/.zipline/bundle_registry.json")
        click.echo("\nTo ingest data, use:")
        click.echo("  python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY")
        return

    # List mode
    if list_only:
        click.echo(f"Bundles in registry ({len(registry)} total):\n")
        for name, meta in sorted(registry.items()):
            symbols = meta.get('symbols', [])
            timeframe_val = meta.get('timeframe', 'daily')
            calendar = meta.get('calendar_name', 'unknown')
            click.echo(f"  {name}")
            click.echo(f"    Symbols: {', '.join(symbols)}")
            click.echo(f"    Timeframe: {timeframe_val}, Calendar: {calendar}")
            click.echo()
        return

    # Parse bundle names if provided
    bundle_list = None
    if bundles:
        bundle_list = [b.strip() for b in bundles.split(',')]

    # Filter bundles
    filtered = filter_bundles(
        registry,
        bundle_names=bundle_list,
        timeframe_filter=timeframe,
        assets_filter=assets,
        source_filter=source,
    )

    if not filtered:
        click.echo("No bundles match the specified filters.")
        return

    # Show summary
    click.echo(f"\nBundles to re-ingest: {len(filtered)}")
    click.echo("-" * 40)
    for name in sorted(filtered.keys()):
        meta = filtered[name]
        symbols = meta.get('symbols', [])
        tf = meta.get('timeframe', 'daily')
        click.echo(f"  {name} ({tf}, {len(symbols)} symbol(s))")
    click.echo("-" * 40)

    # Dry run mode
    if dry_run:
        click.echo("\n[DRY RUN] Would perform the following:\n")
        for name, meta in sorted(filtered.items()):
            reingest_bundle(name, meta, dry_run=True)
            click.echo()
        return

    # Confirm unless forced
    if not force:
        click.confirm(
            f"\nProceed with re-ingesting {len(filtered)} bundle(s)?",
            abort=True
        )

    # Re-ingest bundles
    click.echo("\nRe-ingesting bundles...\n")
    success_count = 0
    fail_count = 0

    for name, meta in sorted(filtered.items()):
        if reingest_bundle(name, meta, dry_run=False):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    click.echo("\n" + "=" * 40)
    click.echo(f"Re-ingestion complete:")
    click.echo(f"  ✓ Successful: {success_count}")
    if fail_count:
        click.echo(f"  ✗ Failed: {fail_count}")
    click.echo("=" * 40)

    if fail_count:
        sys.exit(1)


if __name__ == '__main__':
    main()
