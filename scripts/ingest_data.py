#!/usr/bin/env python3
"""
Data ingestion script for The Researcher's Cockpit.

Ingests market data from various sources into Zipline bundles.
Supports multiple timeframes with automatic data limit validation.

Usage Examples:
    # Daily data (default)
    python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY

    # Hourly data (730 days available)
    python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY --timeframe 1h

    # 5-minute data (60 days available)
    python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD --timeframe 5m

    # 1-minute data (7 days available)
    python scripts/ingest_data.py --source yahoo --assets equities --symbols AAPL --timeframe 1m
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from lib.data_loader import ingest_bundle, VALID_TIMEFRAMES, TIMEFRAME_DATA_LIMITS


def format_timeframe_help():
    """Generate help text showing timeframe options and their data limits."""
    lines = ["Available timeframes with Yahoo Finance data limits:"]
    for tf in VALID_TIMEFRAMES:
        limit = TIMEFRAME_DATA_LIMITS.get(tf)
        if limit:
            lines.append(f"  {tf:8s} - {limit} days")
        else:
            lines.append(f"  {tf:8s} - unlimited")
    return "\n".join(lines)


@click.command()
@click.option('--source', default=None, type=click.Choice(['yahoo', 'binance', 'oanda', 'csv']),
              help='Data source name (e.g., yahoo, binance, oanda, local_csv)')
@click.option('--assets', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class')
@click.option('--symbols', default=None, help='Comma-separated list of symbols (e.g., SPY,AAPL)')
@click.option('--bundle-name', default=None,
              help='Bundle name. Auto-generated as {source}_{asset}_{timeframe} if not provided')
@click.option('--start-date', default=None,
              help='Start date (YYYY-MM-DD). Auto-adjusted for limited timeframes.')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
@click.option('--calendar', default=None,
              help='Trading calendar name (e.g., XNYS, CRYPTO, FOREX). Auto-detected from asset class if not provided.')
@click.option('--timeframe', '-t', default='daily',
              type=click.Choice(VALID_TIMEFRAMES, case_sensitive=False),
              help='Data timeframe. Use --list-timeframes to see options with limits.')
@click.option('--ingest-daily', is_flag=True, help='Ingest daily data bundle')
@click.option('--ingest-minute', is_flag=True, help='Ingest minute data bundle')
@click.option('--force', is_flag=True, help='Force re-ingestion of the bundle, even if already registered')
@click.option('--list-timeframes', is_flag=True, help='Show available timeframes and their data limits')
def main(source, assets, symbols, bundle_name, start_date, end_date, calendar, timeframe, force, list_timeframes, ingest_daily, ingest_minute):
    """
    Ingest market data into a Zipline bundle.

    Supports multiple timeframes from 1-minute to monthly data.
    Data availability varies by timeframe (e.g., 1m data only available for last 7 days).

    \b
    Examples:
        # Daily equity data
        python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY

        # Hourly crypto data
        python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD -t 1h

        # 5-minute forex data
        python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD=X -t 5m
    """
    # Handle --list-timeframes flag
    if list_timeframes:
        click.echo(format_timeframe_help())
        return

    # Validate required options for ingestion
    if source is None:
        click.echo("Error: --source is required for ingestion.", err=True)
        click.echo("Use --list-timeframes to see available timeframes without other options.", err=True)
        sys.exit(1)
    if assets is None:
        click.echo("Error: --assets is required for ingestion.", err=True)
        sys.exit(1)
    if symbols is None:
        click.echo("Error: --symbols is required for ingestion.", err=True)
        sys.exit(1)

    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',')]

    # Get data limit info
    limit = TIMEFRAME_DATA_LIMITS.get(timeframe.lower())
    limit_info = f" ({limit} days max)" if limit else " (unlimited)"

    bundles_to_ingest = []
    if ingest_daily:
        bundles_to_ingest.append({'timeframe': 'daily', 'bundle_suffix': '_daily'})
    if ingest_minute:
        # Use the original timeframe provided for minute data
        bundles_to_ingest.append({'timeframe': timeframe.lower(), 'bundle_suffix': f'_{timeframe}'})

    # If neither --ingest-daily nor --ingest-minute is specified, default to the provided timeframe
    if not bundles_to_ingest:
        bundles_to_ingest.append({'timeframe': timeframe.lower(), 'bundle_suffix': ''}) # No suffix if it's the only one and already matches the given timeframe


    ingested_bundles = []
    for bundle_info in bundles_to_ingest:
        current_timeframe = bundle_info['timeframe']
        current_bundle_suffix = bundle_info['bundle_suffix']

        # Determine the bundle name based on whether a custom name was provided
        if bundle_name:
            # If a base bundle_name is provided, append the suffix
            current_bundle_name = f"{bundle_name}{current_bundle_suffix}"
        else:
            # Auto-generate bundle name including source, asset class, and timeframe
            # Ensure asset class is a string for f-string
            asset_class_str = assets
            current_bundle_name = f"{source}_{asset_class_str}{current_bundle_suffix}"
        
        # Get data limit info for the current timeframe (for display purposes)
        limit = TIMEFRAME_DATA_LIMITS.get(current_timeframe)
        limit_info = f" ({limit} days max)" if limit else " (unlimited)"

        click.echo(f"Ingesting {current_timeframe} data from {source} for {len(symbol_list)} symbols{limit_info}...")
        click.echo(f"Symbols: {', '.join(symbol_list)}")
        
        try:
            bundle = ingest_bundle(
                source=source,
                assets=[assets],
                bundle_name=current_bundle_name,
                symbols=symbol_list,
                start_date=start_date,
                end_date=end_date,
                calendar_name=calendar,
                timeframe=current_timeframe,
                force=force
            )
            ingested_bundles.append(bundle)
            click.echo(f"
✓ Successfully ingested bundle: {bundle}")
        except Exception as e:
            click.echo(f"✗ Error ingesting {current_timeframe} bundle {current_bundle_name}: {e}", err=True)
            sys.exit(1)

    click.echo(f"
All specified bundles successfully ingested:")
    for b in ingested_bundles:
        click.echo(f"  - {b}")
    click.echo(f"Bundles are ready for backtesting.")

    # Show helpful next steps
    click.echo(f"
Next steps:")
    for b in ingested_bundles:
        click.echo(f"  1. Run backtest: python scripts/run_backtest.py --strategy <name> --bundle {b}")
    click.echo(f"  2. Check bundle registry: cat ~/.zipline/bundle_registry.json | python -m json.tool")


if __name__ == '__main__':
    main()
