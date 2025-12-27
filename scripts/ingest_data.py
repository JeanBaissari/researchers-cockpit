#!/usr/bin/env python3
"""
Data ingestion script for The Researcher's Cockpit.

Ingests market data from various sources into Zipline bundles.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from lib.data_loader import ingest_bundle


@click.command()
@click.option('--source', required=True, type=click.Choice(['yahoo', 'binance', 'oanda']),
              help='Data source name')
@click.option('--assets', required=True, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class')
@click.option('--symbols', required=True, help='Comma-separated list of symbols (e.g., SPY,AAPL)')
@click.option('--bundle-name', default=None, help='Bundle name (auto-generated if not provided)')
@click.option('--start-date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
def main(source, assets, symbols, bundle_name, start_date, end_date):
    """
    Ingest market data into a Zipline bundle.
    
    Example:
        python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY
    """
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',')]
    
    click.echo(f"Ingesting data from {source} for {len(symbol_list)} symbols...")
    click.echo(f"Symbols: {', '.join(symbol_list)}")
    
    try:
        bundle = ingest_bundle(
            source=source,
            assets=[assets],
            bundle_name=bundle_name,
            symbols=symbol_list,
            start_date=start_date,
            end_date=end_date,
        )
        
        click.echo(f"✓ Successfully ingested bundle: {bundle}")
        click.echo(f"Bundle is ready for backtesting.")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

