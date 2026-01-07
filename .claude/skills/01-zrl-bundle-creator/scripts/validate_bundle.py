#!/usr/bin/env python3
"""
Validate source data before Zipline bundle ingestion.
Ensures data integrity, calendar alignment, and OHLCV consistency.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import numpy as np

class BundleValidator:
    """Validate data for Zipline bundle ingestion."""
    
    def __init__(self, calendar_name: str = 'NYSE'):
        self.calendar_name = calendar_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_dataframe(self, df: pd.DataFrame, symbol: str) -> bool:
        """Validate a single symbol's OHLCV data."""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        # Check required columns
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            self.errors.append(f"{symbol}: Missing columns: {missing}")
            return False
        
        # Check for NaN values
        for col in required_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                self.errors.append(f"{symbol}: {nan_count} NaN values in '{col}'")
        
        # Validate OHLC relationships
        invalid_high = df[df['high'] < df[['open', 'close']].max(axis=1)]
        if len(invalid_high) > 0:
            self.errors.append(f"{symbol}: {len(invalid_high)} rows where high < max(open, close)")
        
        invalid_low = df[df['low'] > df[['open', 'close']].min(axis=1)]
        if len(invalid_low) > 0:
            self.errors.append(f"{symbol}: {len(invalid_low)} rows where low > min(open, close)")
        
        # Check volume non-negative
        neg_vol = (df['volume'] < 0).sum()
        if neg_vol > 0:
            self.errors.append(f"{symbol}: {neg_vol} negative volume values")
        
        # Check for zero/negative prices
        for col in ['open', 'high', 'low', 'close']:
            bad_prices = (df[col] <= 0).sum()
            if bad_prices > 0:
                self.warnings.append(f"{symbol}: {bad_prices} zero/negative {col} prices")
        
        # Check date index
        if not isinstance(df.index, pd.DatetimeIndex):
            self.errors.append(f"{symbol}: Index must be DatetimeIndex")
        elif df.index.tz is None:
            self.warnings.append(f"{symbol}: Index not timezone-aware (should be UTC)")
        
        # Check for duplicates
        dup_dates = df.index.duplicated().sum()
        if dup_dates > 0:
            self.errors.append(f"{symbol}: {dup_dates} duplicate dates")
        
        # Check monotonic dates
        if not df.index.is_monotonic_increasing:
            self.warnings.append(f"{symbol}: Dates not sorted")
        
        return len(self.errors) == 0
    
    def validate_csv_directory(self, path: Path) -> Tuple[bool, dict]:
        """Validate all CSV files in a directory."""
        results = {'symbols': 0, 'rows': 0, 'date_range': None}
        all_dates = []
        
        csv_files = list(path.glob('*.csv'))
        if not csv_files:
            self.errors.append(f"No CSV files found in {path}")
            return False, results
        
        for csv_file in csv_files:
            symbol = csv_file.stem.upper()
            try:
                df = pd.read_csv(csv_file, parse_dates=['date'], index_col='date')
                self.validate_dataframe(df, symbol)
                results['symbols'] += 1
                results['rows'] += len(df)
                all_dates.extend(df.index.tolist())
            except Exception as e:
                self.errors.append(f"{symbol}: Failed to read - {e}")
        
        if all_dates:
            results['date_range'] = (min(all_dates), max(all_dates))
        
        return len(self.errors) == 0, results
    
    def report(self) -> str:
        """Generate validation report."""
        lines = ["=" * 60, "BUNDLE VALIDATION REPORT", "=" * 60]
        
        if self.errors:
            lines.append(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  • {err}")
        
        if self.warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  • {warn}")
        
        if not self.errors and not self.warnings:
            lines.append("\n✅ All validations passed!")
        elif not self.errors:
            lines.append("\n✅ No critical errors (warnings only)")
        
        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Validate data for Zipline bundle')
    parser.add_argument('path', help='Path to CSV directory or single file')
    parser.add_argument('--calendar', default='NYSE', help='Trading calendar name')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    args = parser.parse_args()
    
    validator = BundleValidator(calendar_name=args.calendar)
    path = Path(args.path)
    
    if path.is_dir():
        valid, results = validator.validate_csv_directory(path)
        print(f"\nValidated {results['symbols']} symbols, {results['rows']:,} total rows")
        if results['date_range']:
            print(f"Date range: {results['date_range'][0]} to {results['date_range'][1]}")
    elif path.is_file():
        df = pd.read_csv(path, parse_dates=['date'], index_col='date')
        valid = validator.validate_dataframe(df, path.stem.upper())
    else:
        print(f"Error: Path not found: {path}")
        sys.exit(1)
    
    print(validator.report())
    
    if args.strict and validator.warnings:
        valid = False
    
    sys.exit(0 if valid else 1)


if __name__ == '__main__':
    main()
