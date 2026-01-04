#!/usr/bin/env python3
"""
Bundle information script for The Researcher's Cockpit.

Displays detailed information about Zipline data bundles including
symbols, date ranges, bar counts, and health status.

Usage Examples:
    # Show info for a specific bundle
    python scripts/bundle_info.py yahoo_equities_1h

    # List all available bundles
    python scripts/bundle_info.py --list

    # Show detailed health check
    python scripts/bundle_info.py yahoo_equities_daily --verbose
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from typing import Optional, Dict, Any

from lib.data_loader import (
    get_bundle_symbols,
    load_bundle,
    list_bundles,
    _load_bundle_registry,
)


def format_number(n: int) -> str:
    """Format number with thousands separator."""
    return f"{n:,}"


def get_bundle_info(bundle_name: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Gather comprehensive information about a bundle.

    Args:
        bundle_name: Name of the bundle
        verbose: Include additional diagnostic info

    Returns:
        Dictionary with bundle information
    """
    info = {
        'name': bundle_name,
        'symbols': [],
        'start_date': None,
        'end_date': None,
        'timeframe': 'daily',
        'calendar': 'XNYS',
        'daily_bars': 0,
        'minute_bars': 0,
        'data_frequency': 'daily',
        'health': 'unknown',
        'health_details': [],
        'errors': [],
    }

    # Load registry metadata
    registry = _load_bundle_registry()
    if bundle_name in registry:
        meta = registry[bundle_name]
        info['symbols'] = meta.get('symbols', [])
        info['start_date'] = meta.get('start_date')

        # Handle end_date - might be None or malformed (e.g., contains timeframe string)
        end_date = meta.get('end_date')
        if end_date and isinstance(end_date, str) and len(end_date) >= 10:
            # Validate it looks like a date (YYYY-MM-DD)
            if end_date[:4].isdigit() and end_date[4] == '-':
                info['end_date'] = end_date

        info['timeframe'] = meta.get('timeframe', 'daily')
        info['calendar'] = meta.get('calendar_name', 'XNYS')
        info['data_frequency'] = meta.get('data_frequency', 'daily')

    # Try to get symbols from bundle if not in registry
    if not info['symbols']:
        try:
            info['symbols'] = get_bundle_symbols(bundle_name)
        except Exception as e:
            info['errors'].append(f"Could not retrieve symbols: {e}")

    # Load bundle to get actual bar counts and validate
    try:
        bundle_data = load_bundle(bundle_name)
        health_issues = []

        # Get daily bar info
        if hasattr(bundle_data, 'equity_daily_bar_reader') and bundle_data.equity_daily_bar_reader is not None:
            daily_reader = bundle_data.equity_daily_bar_reader

            # Get sessions/dates
            if hasattr(daily_reader, 'sessions') and len(daily_reader.sessions) > 0:
                sessions = daily_reader.sessions
                info['daily_bars'] = len(sessions)

                # Update date range from actual data
                if info['start_date'] is None:
                    info['start_date'] = str(sessions[0].date())
                if info['end_date'] is None:
                    info['end_date'] = str(sessions[-1].date())

            # Check first_trading_day validity
            if hasattr(daily_reader, 'first_trading_day'):
                ftd = daily_reader.first_trading_day
                if ftd is None or (hasattr(ftd, 'value') and ftd != ftd):  # NaT check
                    health_issues.append("Daily bar reader has invalid first_trading_day (NaT)")
        else:
            if info['data_frequency'] == 'daily':
                health_issues.append("No daily bar reader found")

        # Get minute bar info
        if hasattr(bundle_data, 'equity_minute_bar_reader') and bundle_data.equity_minute_bar_reader is not None:
            minute_reader = bundle_data.equity_minute_bar_reader

            # Try to get minute bar count
            if hasattr(minute_reader, 'first_trading_day') and hasattr(minute_reader, 'last_available_dt'):
                try:
                    # Estimate minute bars from trading calendar
                    if hasattr(bundle_data, 'equity_daily_bar_reader'):
                        daily_sessions = len(bundle_data.equity_daily_bar_reader.sessions)
                        # Rough estimate based on calendar type
                        calendar_name = info['calendar'].upper()
                        if 'CRYPTO' in calendar_name:
                            minutes_per_day = 1440
                        elif 'FOREX' in calendar_name:
                            minutes_per_day = 1440
                        else:
                            minutes_per_day = 390  # NYSE

                        # Adjust for timeframe
                        tf = info['timeframe']
                        if tf == '1h':
                            bars_per_day = minutes_per_day // 60
                        elif tf == '30m':
                            bars_per_day = minutes_per_day // 30
                        elif tf == '15m':
                            bars_per_day = minutes_per_day // 15
                        elif tf == '5m':
                            bars_per_day = minutes_per_day // 5
                        elif tf == '1m':
                            bars_per_day = minutes_per_day
                        else:
                            bars_per_day = minutes_per_day // 60  # Default to hourly

                        info['minute_bars'] = daily_sessions * bars_per_day * len(info['symbols'])
                except Exception:
                    pass

            # Check minute reader validity
            if hasattr(minute_reader, 'first_trading_day'):
                ftd = minute_reader.first_trading_day
                if ftd is None or (hasattr(ftd, 'value') and ftd != ftd):
                    health_issues.append("Minute bar reader has invalid first_trading_day (NaT)")

        # Get calendar info from bundle if not in registry
        if hasattr(bundle_data, 'equity_daily_bar_reader') and bundle_data.equity_daily_bar_reader is not None:
            if hasattr(bundle_data.equity_daily_bar_reader, 'trading_calendar'):
                cal = bundle_data.equity_daily_bar_reader.trading_calendar
                if hasattr(cal, 'name'):
                    info['calendar'] = cal.name

        # Determine health status
        if health_issues:
            info['health'] = 'warning'
            info['health_details'] = health_issues
        else:
            info['health'] = 'ok'
            info['health_details'] = ['All checks passed']

    except FileNotFoundError as e:
        info['health'] = 'error'
        info['errors'].append(f"Bundle not found: {e}")
    except Exception as e:
        info['health'] = 'error'
        info['errors'].append(f"Failed to load bundle: {e}")

    return info


def print_bundle_info(info: Dict[str, Any], verbose: bool = False) -> None:
    """Print bundle information in a formatted way."""

    # Health icon
    health_icons = {
        'ok': '\u2705',      # ✅
        'warning': '\u26a0\ufe0f',  # ⚠️
        'error': '\u274c',   # ❌
        'unknown': '\u2753', # ❓
    }

    print(f"Bundle: {info['name']}")
    print(f"Symbols: {info['symbols']}")

    date_range = f"{info['start_date'] or 'N/A'} to {info['end_date'] or 'N/A'}"
    print(f"Date Range: {date_range}")

    print(f"Timeframe: {info['timeframe']}")
    print(f"Calendar: {info['calendar']}")

    if info['daily_bars'] > 0:
        print(f"Daily Bars: {format_number(info['daily_bars'])} rows")

    if info['minute_bars'] > 0:
        print(f"Minute Bars: {format_number(info['minute_bars'])} rows")

    health_icon = health_icons.get(info['health'], '?')
    health_text = info['health'].upper()
    print(f"Health: {health_icon} {health_text}")

    if verbose or info['health'] != 'ok':
        if info['health_details']:
            for detail in info['health_details']:
                print(f"  - {detail}")
        if info['errors']:
            for error in info['errors']:
                print(f"  - ERROR: {error}")


def list_all_bundles() -> None:
    """List all available bundles with summary info."""
    # Get registered bundles from Zipline
    registered = list_bundles()

    # Get bundles from our registry
    registry = _load_bundle_registry()

    # Combine and deduplicate
    all_bundles = set(registered) | set(registry.keys())

    if not all_bundles:
        print("No bundles found.")
        print("\nTo ingest data, run:")
        print("  python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY")
        return

    print("Available Bundles:")
    print("-" * 60)

    for bundle_name in sorted(all_bundles):
        # Get quick info from registry
        meta = registry.get(bundle_name, {})
        symbols = meta.get('symbols', [])
        timeframe = meta.get('timeframe', 'daily')
        calendar = meta.get('calendar_name', 'XNYS')

        symbols_str = ', '.join(symbols[:3])
        if len(symbols) > 3:
            symbols_str += f" (+{len(symbols)-3} more)"

        if symbols_str:
            print(f"  {bundle_name}")
            print(f"    Symbols: {symbols_str} | Timeframe: {timeframe} | Calendar: {calendar}")
        else:
            print(f"  {bundle_name}")

    print("-" * 60)
    print(f"Total: {len(all_bundles)} bundle(s)")
    print("\nFor detailed info: python scripts/bundle_info.py <bundle_name>")


@click.command()
@click.argument('bundle_name', required=False)
@click.option('--list', '-l', 'list_bundles_flag', is_flag=True,
              help='List all available bundles')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed health check information')
@click.option('--json', 'output_json', is_flag=True,
              help='Output in JSON format')
def main(bundle_name: Optional[str], list_bundles_flag: bool, verbose: bool, output_json: bool):
    """
    Display information about a Zipline data bundle.

    \b
    Examples:
        # Show info for a bundle
        python scripts/bundle_info.py yahoo_equities_daily

        # List all bundles
        python scripts/bundle_info.py --list

        # Verbose health check
        python scripts/bundle_info.py yahoo_equities_1h --verbose

        # JSON output
        python scripts/bundle_info.py yahoo_equities_daily --json
    """
    if list_bundles_flag:
        list_all_bundles()
        return

    if not bundle_name:
        click.echo("Error: Please provide a bundle name or use --list to see available bundles.")
        click.echo("\nUsage: python scripts/bundle_info.py <bundle_name>")
        click.echo("       python scripts/bundle_info.py --list")
        sys.exit(1)

    info = get_bundle_info(bundle_name, verbose=verbose)

    if output_json:
        import json
        print(json.dumps(info, indent=2, default=str))
    else:
        print_bundle_info(info, verbose=verbose)

    # Exit with error code if health check failed
    if info['health'] == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()
