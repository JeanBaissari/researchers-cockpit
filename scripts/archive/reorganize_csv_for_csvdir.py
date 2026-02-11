"""
Reorganize CSV files from data/processed/ to data/csvdir/ structure.

Transformations:
1. Merge multiple date-range files per symbol into single file
2. Remove dividend and split columns (FOREX/CRYPTO don't have these)
3. Rename to simple {SYMBOL}.csv format
4. Organize by timeframe directory

Usage:
    python scripts/reorganize_csv_for_csvdir.py --timeframe 1m --symbol EURUSD
    python scripts/reorganize_csv_for_csvdir.py --all  # Process all
"""

import argparse
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


def reorganize_symbol(symbol: str, timeframe: str, dry_run: bool = False):
    """
    Reorganize CSV files for a single symbol.

    Args:
        symbol: Symbol to reorganize (e.g., 'EURUSD')
        timeframe: Timeframe (e.g., '1m', 'daily')
        dry_run: If True, only print actions without executing
    """
    project_root = get_project_root()
    source_dir = project_root / "data" / "processed" / timeframe
    target_dir = project_root / "data" / "csvdir" / timeframe

    # Find all files for this symbol
    pattern = f"{symbol}_{timeframe}_*.csv"
    source_files = list(source_dir.glob(pattern))

    if not source_files:
        logger.warning(f"No files found for {symbol} {timeframe} (pattern: {pattern})")
        return False

    logger.info(f"Processing {symbol} {timeframe}: Found {len(source_files)} file(s)")

    # Read and merge all files
    dfs = []
    for file_path in source_files:
        logger.info(f"  Reading {file_path.name}")
        df = pd.read_csv(file_path, parse_dates=["date"], index_col="date")
        dfs.append(df)

    # Merge if multiple files
    if len(dfs) > 1:
        logger.info(f"  Merging {len(dfs)} files...")
        merged_df = pd.concat(dfs).sort_index()
        # Remove duplicates (keep first occurrence)
        merged_df = merged_df[~merged_df.index.duplicated(keep="first")]
    else:
        merged_df = dfs[0]

    # Remove dividend and split columns if present
    columns_to_remove = ["dividend", "split"]
    removed_cols = []
    for col in columns_to_remove:
        if col in merged_df.columns:
            merged_df = merged_df.drop(columns=[col])
            removed_cols.append(col)

    if removed_cols:
        logger.info(f"  Removed columns: {removed_cols}")

    # Verify required columns present
    required_cols = ["open", "high", "low", "close", "volume"]
    missing_cols = [col for col in required_cols if col not in merged_df.columns]
    if missing_cols:
        logger.error(f"  Missing required columns: {missing_cols}")
        return False

    # Ensure correct column order
    merged_df = merged_df[required_cols]

    # Output file
    target_file = target_dir / f"{symbol}.csv"

    if dry_run:
        logger.info(f"  [DRY RUN] Would write to: {target_file}")
        logger.info(f"  [DRY RUN] Rows: {len(merged_df)}, Columns: {list(merged_df.columns)}")
        logger.info(f"  [DRY RUN] Date range: {merged_df.index.min()} to {merged_df.index.max()}")
    else:
        # Write to target
        target_dir.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(target_file)
        logger.info(f"  ✅ Written to: {target_file}")
        logger.info(
            f"     Rows: {len(merged_df)}, Date range: {merged_df.index.min()} to {merged_df.index.max()}"
        )

    return True


def reorganize_all(dry_run: bool = False):
    """Reorganize all CSV files in data/processed/."""
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"

    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        return

    # Find all timeframes
    timeframes = [d.name for d in processed_dir.iterdir() if d.is_dir()]
    logger.info(f"Found timeframes: {timeframes}")

    # Process each timeframe
    for timeframe in timeframes:
        tf_dir = processed_dir / timeframe
        csv_files = list(tf_dir.glob("*.csv"))

        # Extract unique symbols
        symbols = set()
        for csv_file in csv_files:
            # Parse symbol from filename (e.g., EURUSD_1m_20200102_20250717_ready.csv)
            parts = csv_file.stem.split("_")
            if len(parts) >= 2:
                symbol = parts[0]
                symbols.add(symbol)

        logger.info(f"\n{timeframe}: Found {len(symbols)} unique symbols")

        # Process each symbol
        for symbol in sorted(symbols):
            reorganize_symbol(symbol, timeframe, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description="Reorganize CSV files for csvdir_equities()")
    parser.add_argument("--symbol", type=str, help="Symbol to reorganize (e.g., EURUSD)")
    parser.add_argument("--timeframe", type=str, help="Timeframe (e.g., 1m, daily)")
    parser.add_argument("--all", action="store_true", help="Process all symbols and timeframes")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")

    args = parser.parse_args()

    if args.all:
        reorganize_all(dry_run=args.dry_run)
    elif args.symbol and args.timeframe:
        reorganize_symbol(args.symbol, args.timeframe, dry_run=args.dry_run)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/reorganize_csv_for_csvdir.py --all --dry-run")
        print("  python scripts/reorganize_csv_for_csvdir.py --symbol EURUSD --timeframe 1m")


if __name__ == "__main__":
    main()
