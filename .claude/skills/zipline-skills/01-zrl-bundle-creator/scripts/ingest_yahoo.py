#!/usr/bin/env python3
"""
Ingest OHLCV data from Yahoo Finance for Zipline bundle creation.
Downloads, validates, and formats data for bundle ingestion.
"""
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance not installed. Run: pip install yfinance")
    exit(1)


def download_symbol(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV data for a single symbol."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, auto_adjust=False)
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    
    # Rename columns to Zipline format
    df = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Dividends': 'dividend',
        'Stock Splits': 'split',
    })
    
    # Keep only needed columns
    cols = ['open', 'high', 'low', 'close', 'volume']
    if 'dividend' in df.columns:
        cols.append('dividend')
    if 'split' in df.columns:
        cols.append('split')
    
    df = df[cols]
    
    # Ensure UTC timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    
    # Reset index to have 'date' column
    df.index.name = 'date'
    
    return df


def save_csv(df: pd.DataFrame, symbol: str, output_dir: Path):
    """Save DataFrame to CSV in Zipline-compatible format."""
    filepath = output_dir / f"{symbol.lower()}.csv"
    df_out = df.reset_index()
    df_out['date'] = df_out['date'].dt.strftime('%Y-%m-%d')
    df_out.to_csv(filepath, index=False)
    return filepath


def main():
    parser = argparse.ArgumentParser(description='Download Yahoo Finance data for Zipline')
    parser.add_argument('--symbols', required=True, help='Comma-separated symbols (e.g., AAPL,MSFT)')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=Path, required=True, help='Output directory')
    parser.add_argument('--include-adjustments', action='store_true', help='Include dividends/splits')
    args = parser.parse_args()
    
    symbols = [s.strip().upper() for s in args.symbols.split(',')]
    args.output.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {len(symbols)} symbols from {args.start} to {args.end}")
    print(f"Output directory: {args.output}")
    print("-" * 50)
    
    success = []
    failed = []
    
    for symbol in symbols:
        try:
            print(f"Downloading {symbol}...", end=" ", flush=True)
            df = download_symbol(symbol, args.start, args.end)
            filepath = save_csv(df, symbol, args.output)
            print(f"✓ {len(df)} rows")
            success.append(symbol)
        except Exception as e:
            print(f"✗ {e}")
            failed.append((symbol, str(e)))
    
    print("-" * 50)
    print(f"Completed: {len(success)}/{len(symbols)} symbols")
    
    if failed:
        print("\nFailed symbols:")
        for sym, err in failed:
            print(f"  • {sym}: {err}")
    
    if success:
        print(f"\nData saved to: {args.output}")
        print("\nNext steps:")
        print(f"1. Validate: python validate_bundle.py {args.output}")
        print(f"2. Generate bundle: python create_bundle.py --source {args.output} --name yahoo-bundle")
    
    return 0 if len(failed) == 0 else 1


if __name__ == '__main__':
    exit(main())
