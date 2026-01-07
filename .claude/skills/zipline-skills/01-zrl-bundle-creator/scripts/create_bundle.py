#!/usr/bin/env python3
"""
Generate Zipline bundle registration code from data source.
Creates extension.py snippet and validates source structure.
"""
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

BUNDLE_TEMPLATE = '''
# Add this to ~/.zipline/extension.py
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
import pandas as pd

register(
    '{bundle_name}',
    csvdir_equities(
        ['daily'],
        '{source_path}',
    ),
    calendar_name='{calendar}',
    start_session=pd.Timestamp('{start}', tz='utc'),
    end_session=pd.Timestamp('{end}', tz='utc'),
)
'''

CUSTOM_TEMPLATE = '''
# Add this to ~/.zipline/extension.py
import pandas as pd
from zipline.data import bundles

@bundles.register('{bundle_name}')
def {func_name}_ingest(environ, asset_db_writer, minute_bar_writer,
                        daily_bar_writer, adjustment_writer, calendar,
                        start_session, end_session, cache, show_progress,
                        output_dir):
    """Custom ingest function for {bundle_name}."""
    
    # Configure source
    source_path = '{source_path}'
    symbols = {symbols}
    
    # Build asset metadata
    assets = pd.DataFrame({{
        'symbol': symbols,
        'asset_name': symbols,  # Update with actual names
        'start_date': pd.Timestamp('{start}', tz='utc'),
        'end_date': pd.Timestamp('{end}', tz='utc'),
        'exchange': '{calendar}',
    }})
    
    # Write assets to database
    asset_db_writer.write(equities=assets)
    
    # Daily bar generator
    def daily_bar_generator():
        import os
        for sid, symbol in enumerate(symbols):
            filepath = os.path.join(source_path, f'{{symbol.lower()}}.csv')
            df = pd.read_csv(filepath, parse_dates=['date'], index_col='date')
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index
            yield sid, df
    
    daily_bar_writer.write(daily_bar_generator(), show_progress=show_progress)
    
    # Write empty adjustments (update if you have splits/dividends)
    adjustment_writer.write()
'''


def discover_source(source_path: Path) -> dict:
    """Discover data source properties."""
    info = {'symbols': [], 'start': None, 'end': None, 'rows': 0}
    
    for csv_file in source_path.glob('*.csv'):
        symbol = csv_file.stem.upper()
        info['symbols'].append(symbol)
        
        try:
            df = pd.read_csv(csv_file, parse_dates=['date'])
            info['rows'] += len(df)
            
            file_start = df['date'].min()
            file_end = df['date'].max()
            
            if info['start'] is None or file_start < info['start']:
                info['start'] = file_start
            if info['end'] is None or file_end > info['end']:
                info['end'] = file_end
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
    
    return info


def generate_bundle_code(args, source_info: dict) -> str:
    """Generate bundle registration code."""
    start = args.start or source_info['start'].strftime('%Y-%m-%d')
    end = args.end or source_info['end'].strftime('%Y-%m-%d')
    
    if args.custom:
        func_name = args.name.replace('-', '_').replace('.', '_')
        return CUSTOM_TEMPLATE.format(
            bundle_name=args.name,
            func_name=func_name,
            source_path=str(args.source.absolute()),
            calendar=args.calendar,
            start=start,
            end=end,
            symbols=source_info['symbols'],
        )
    else:
        return BUNDLE_TEMPLATE.format(
            bundle_name=args.name,
            source_path=str(args.source.absolute()),
            calendar=args.calendar,
            start=start,
            end=end,
        )


def main():
    parser = argparse.ArgumentParser(description='Generate Zipline bundle registration')
    parser.add_argument('--source', type=Path, required=True, help='Path to CSV directory')
    parser.add_argument('--name', required=True, help='Bundle name')
    parser.add_argument('--calendar', default='NYSE', help='Trading calendar')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD), auto-detected if not set')
    parser.add_argument('--end', help='End date (YYYY-MM-DD), auto-detected if not set')
    parser.add_argument('--custom', action='store_true', help='Generate custom ingest function')
    parser.add_argument('--output', type=Path, help='Output file (prints to stdout if not set)')
    args = parser.parse_args()
    
    if not args.source.is_dir():
        print(f"Error: Source directory not found: {args.source}")
        return 1
    
    print(f"Discovering source data in {args.source}...")
    source_info = discover_source(args.source)
    
    print(f"Found {len(source_info['symbols'])} symbols, {source_info['rows']:,} total rows")
    print(f"Date range: {source_info['start']} to {source_info['end']}")
    
    code = generate_bundle_code(args, source_info)
    
    if args.output:
        args.output.write_text(code)
        print(f"\nBundle code written to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("GENERATED BUNDLE CODE:")
        print("=" * 60)
        print(code)
    
    print("\nNext steps:")
    print("1. Add the generated code to ~/.zipline/extension.py")
    print(f"2. Run: zipline ingest -b {args.name}")
    print(f"3. Verify: zipline bundles")
    
    return 0


if __name__ == '__main__':
    exit(main())
