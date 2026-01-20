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
from lib.bundles import ingest_bundle, VALID_TIMEFRAMES, TIMEFRAME_DATA_LIMITS
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging (console=False since we use click.echo for user output)
configure_logging(level='INFO', console=False, file=False)
logger = get_logger(__name__)


def format_timeframe_help() -> str:
    """Generate help text showing timeframe options and their data limits."""
    lines = ["Available timeframes with Yahoo Finance data limits:"]
    for tf in VALID_TIMEFRAMES:
        limit = TIMEFRAME_DATA_LIMITS.get(tf)
        if limit:
            lines.append(f"  {tf:8s} - {limit} days")
        else:
            lines.append(f"  {tf:8s} - unlimited")
    return "\n".join(lines)


def generate_bundle_name(source: str, assets: str, timeframe: str, custom_name: str = None) -> str:
    """
    Generate a consistent bundle name that always includes the timeframe.

    Args:
        source: Data source (e.g., 'yahoo')
        assets: Asset class (e.g., 'equities')
        timeframe: Data timeframe (e.g., 'daily', '1h', '5m')
        custom_name: Optional custom base name

    Returns:
        Bundle name in format: {base}_{timeframe} or {source}_{assets}_{timeframe}

    Note:
        If custom_name already ends with the timeframe, it won't be duplicated.
    """
    if custom_name:
        # Avoid duplicating timeframe if already present in custom name
        if custom_name.endswith(f"_{timeframe}"):
            return custom_name
        return f"{custom_name}_{timeframe}"
    return f"{source}_{assets}_{timeframe}"


@click.command()
@click.option('--source', default=None, type=click.Choice(['yahoo', 'binance', 'oanda', 'csv']),
              help='Data source name (e.g., yahoo, binance, oanda, local_csv)')
@click.option('--assets', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class')
@click.option('--symbols', default=None, help='Comma-separated list of symbols (e.g., SPY,AAPL)')
@click.option('--bundle-name', default=None,
              help='Bundle name base. Timeframe will be appended (e.g., mydata -> mydata_daily)')
@click.option('--start-date', default=None,
              help='Start date (YYYY-MM-DD). Auto-adjusted for limited timeframes.')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
@click.option('--calendar', default=None,
              help='Trading calendar name (e.g., XNYS, CRYPTO, FOREX). Auto-detected from asset class if not provided.')
@click.option('--timeframe', '-t', default='daily',
              type=click.Choice(VALID_TIMEFRAMES, case_sensitive=False),
              help='Data timeframe. Use --list-timeframes to see options with limits.')
@click.option('--ingest-daily', is_flag=True, help='Ingest daily data bundle')
@click.option('--ingest-intraday', is_flag=True, help='Ingest intraday data bundle (uses --timeframe for granularity)')
@click.option('--force', is_flag=True, help='Force re-ingestion of the bundle, even if already registered')
@click.option('--list-timeframes', is_flag=True, help='Show available timeframes and their data limits')
def main(source, assets, symbols, bundle_name, start_date, end_date, calendar, timeframe, force, list_timeframes, ingest_daily, ingest_intraday):
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
        
        # Both daily and hourly data
        python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 1h --ingest-daily --ingest-intraday
    """
    # Handle --list-timeframes flag
    if list_timeframes:
        click.echo(format_timeframe_help())
        return

    # Validate required options for ingestion
    if source is None:
        logger.error("Missing required option: --source")
        click.echo("✗ Error: --source is required for ingestion.", err=True)
        click.echo("  Use --list-timeframes to see available timeframes without other options.", err=True)
        sys.exit(1)
    if assets is None:
        logger.error("Missing required option: --assets")
        click.echo("✗ Error: --assets is required for ingestion.", err=True)
        click.echo("  Example: --assets equities", err=True)
        sys.exit(1)
    if symbols is None:
        logger.error("Missing required option: --symbols")
        click.echo("✗ Error: --symbols is required for ingestion.", err=True)
        click.echo("  Example: --symbols SPY,AAPL", err=True)
        sys.exit(1)

    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',')]

    # Build list of bundles to ingest
    bundles_to_ingest = []
    if ingest_daily:
        bundles_to_ingest.append('daily')
    if ingest_intraday:
        # Use the provided timeframe for intraday data
        intraday_tf = timeframe.lower()
        if intraday_tf == 'daily':
            click.echo("Warning: --ingest-intraday with --timeframe daily is redundant. Use --ingest-daily instead.", err=True)
        else:
            bundles_to_ingest.append(intraday_tf)

    # If neither flag is specified, default to the provided timeframe
    if not bundles_to_ingest:
        bundles_to_ingest.append(timeframe.lower())

    # Use LogContext for structured logging
    with LogContext(phase='data_ingestion', source=source, assets=assets, timeframe=timeframe):
        logger.info(f"Starting data ingestion for {len(symbol_list)} symbols")
        
        ingested_bundles = []
        for current_timeframe in bundles_to_ingest:
            # Generate consistent bundle name that always includes timeframe
            current_bundle_name = generate_bundle_name(
                source=source,
                assets=assets,
                timeframe=current_timeframe,
                custom_name=bundle_name
            )
            
            # Get data limit info for the current timeframe (for display purposes)
            # Only show limits for API-based sources (Yahoo), not local CSV
            if source != 'csv':
                limit = TIMEFRAME_DATA_LIMITS.get(current_timeframe)
                limit_info = f" ({limit} days max)" if limit else " (unlimited)"
            else:
                limit_info = ""  # CSV has no limits - uses full available data

            click.echo(f"Ingesting {current_timeframe} data from {source} for {len(symbol_list)} symbols{limit_info}...")
            click.echo(f"Symbols: {', '.join(symbol_list)}")
            
            try:
                logger.info(f"Ingesting bundle: {current_bundle_name} with {len(symbol_list)} symbols")
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
                logger.info(f"Successfully ingested bundle: {bundle}")
                click.echo(f"✓ Successfully ingested bundle: {bundle}")
            except Exception as e:
                logger.error(f"Failed to ingest bundle {current_bundle_name}: {e}", exc_info=True)
                click.echo(f"✗ Error ingesting {current_timeframe} bundle {current_bundle_name}: {e}", err=True)
                click.echo(f"  Check bundle registry: python scripts/validate_bundles.py --bundle {current_bundle_name}", err=True)
                sys.exit(1)

    click.echo(f"\nAll specified bundles successfully ingested:")
    for b in ingested_bundles:
        click.echo(f"  - {b}")
    click.echo(f"Bundles are ready for backtesting.")

    # Show helpful next steps
    click.echo(f"\nNext steps:")
    for b in ingested_bundles:
        click.echo(f"  1. Run backtest: python scripts/run_backtest.py --strategy <name> --bundle {b}")
    click.echo(f"  2. Check bundle registry: cat ~/.zipline/bundle_registry.json | python -m json.tool")


if __name__ == '__main__':
    main()
