#!/usr/bin/env python3
"""
Comprehensive data quality analysis for Zipline bundle data.
Generates detailed quality reports with actionable insights.
"""
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime

@dataclass
class QualityReport:
    """Data quality analysis results."""
    symbol: str
    total_rows: int = 0
    date_range: tuple = None
    issues: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    score: float = 100.0
    
    def add_issue(self, category: str, description: str, severity: str = 'error', count: int = 1):
        self.issues.append({'category': category, 'description': description, 'severity': severity, 'count': count})
        self.score -= 10 if severity == 'error' else 2
    
    def add_warning(self, category: str, description: str, count: int = 1):
        self.warnings.append({'category': category, 'description': description, 'count': count})
        self.score -= 1


class DataQualityAnalyzer:
    """Analyze data quality for Zipline backtesting."""
    
    def __init__(self, calendar_name: str = 'NYSE'):
        self.calendar_name = calendar_name
        self.reports: Dict[str, QualityReport] = {}
    
    def analyze_file(self, filepath: Path) -> QualityReport:
        """Analyze a single data file."""
        symbol = filepath.stem.upper()
        report = QualityReport(symbol=symbol)
        
        try:
            df = pd.read_csv(filepath, parse_dates=['date'], index_col='date')
        except Exception as e:
            report.add_issue('read_error', f'Failed to read file: {e}')
            return report
        
        report.total_rows = len(df)
        if len(df) > 0:
            report.date_range = (df.index.min(), df.index.max())
        
        # Run all quality checks
        self._check_required_columns(df, report)
        self._check_ohlc_relationships(df, report)
        self._check_price_continuity(df, report)
        self._check_volume_sanity(df, report)
        self._check_duplicates(df, report)
        self._check_missing_values(df, report)
        self._check_date_gaps(df, report)
        
        report.score = max(0, report.score)
        self.reports[symbol] = report
        return report
    
    def _check_required_columns(self, df: pd.DataFrame, report: QualityReport):
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [c for c in required if c not in df.columns]
        if missing:
            report.add_issue('schema', f'Missing columns: {missing}')
    
    def _check_ohlc_relationships(self, df: pd.DataFrame, report: QualityReport):
        if not all(c in df.columns for c in ['open', 'high', 'low', 'close']):
            return
        
        # High must be >= open and close
        invalid_high = (df['high'] < df[['open', 'close']].max(axis=1)).sum()
        if invalid_high > 0:
            report.add_issue('ohlc', f'High < max(open, close) in {invalid_high} rows')
        
        # Low must be <= open and close
        invalid_low = (df['low'] > df[['open', 'close']].min(axis=1)).sum()
        if invalid_low > 0:
            report.add_issue('ohlc', f'Low > min(open, close) in {invalid_low} rows')
    
    def _check_price_continuity(self, df: pd.DataFrame, report: QualityReport):
        if 'close' not in df.columns:
            return
        
        returns = df['close'].pct_change().abs()
        large_moves = (returns > 0.5).sum()  # >50% daily move
        if large_moves > 0:
            report.add_warning('continuity', f'{large_moves} days with >50% price change (check for splits)')
    
    def _check_volume_sanity(self, df: pd.DataFrame, report: QualityReport):
        if 'volume' not in df.columns:
            return
        
        negative = (df['volume'] < 0).sum()
        if negative > 0:
            report.add_issue('volume', f'{negative} negative volume values')
        
        zero = (df['volume'] == 0).sum()
        if zero > len(df) * 0.1:  # >10% zero volume
            report.add_warning('volume', f'{zero} zero volume days ({zero/len(df)*100:.1f}%)')
    
    def _check_duplicates(self, df: pd.DataFrame, report: QualityReport):
        dups = df.index.duplicated().sum()
        if dups > 0:
            report.add_issue('duplicates', f'{dups} duplicate dates')
    
    def _check_missing_values(self, df: pd.DataFrame, report: QualityReport):
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    report.add_issue('missing', f'{missing} NaN values in {col}')
    
    def _check_date_gaps(self, df: pd.DataFrame, report: QualityReport):
        if len(df) < 2:
            return
        
        # Simple gap detection (not calendar-aware for simplicity)
        date_diff = pd.Series(df.index).diff().dt.days
        large_gaps = (date_diff > 5).sum()  # >5 calendar days
        if large_gaps > 0:
            report.add_warning('gaps', f'{large_gaps} gaps > 5 days (check holidays/weekends)')
    
    def analyze_directory(self, path: Path) -> Dict[str, QualityReport]:
        """Analyze all CSV files in directory."""
        for csv_file in sorted(path.glob('*.csv')):
            self.analyze_file(csv_file)
        return self.reports
    
    def generate_summary(self) -> str:
        """Generate text summary of all reports."""
        lines = ["=" * 70, "DATA QUALITY SUMMARY", "=" * 70]
        
        total_symbols = len(self.reports)
        total_rows = sum(r.total_rows for r in self.reports.values())
        avg_score = np.mean([r.score for r in self.reports.values()]) if self.reports else 0
        
        lines.append(f"\nAnalyzed: {total_symbols} symbols, {total_rows:,} total rows")
        lines.append(f"Average Quality Score: {avg_score:.1f}/100")
        
        # Group by score
        excellent = [s for s, r in self.reports.items() if r.score >= 90]
        good = [s for s, r in self.reports.items() if 70 <= r.score < 90]
        poor = [s for s, r in self.reports.items() if r.score < 70]
        
        lines.append(f"\n✅ Excellent (≥90): {len(excellent)} symbols")
        lines.append(f"⚠️  Good (70-89): {len(good)} symbols")
        lines.append(f"❌ Poor (<70): {len(poor)} symbols")
        
        if poor:
            lines.append(f"\nSymbols needing attention: {', '.join(poor[:10])}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze data quality for Zipline')
    parser.add_argument('path', type=Path, help='Path to data directory or file')
    parser.add_argument('--calendar', default='NYSE', help='Trading calendar')
    parser.add_argument('--start', help='Start date filter')
    parser.add_argument('--end', help='End date filter')
    parser.add_argument('--report', help='Output report file (HTML or JSON)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    args = parser.parse_args()
    
    analyzer = DataQualityAnalyzer(calendar_name=args.calendar)
    
    if args.path.is_dir():
        analyzer.analyze_directory(args.path)
    else:
        analyzer.analyze_file(args.path)
    
    print(analyzer.generate_summary())
    
    if args.verbose:
        for symbol, report in sorted(analyzer.reports.items()):
            if report.issues or report.warnings:
                print(f"\n{symbol} (Score: {report.score:.1f}):")
                for issue in report.issues:
                    print(f"  ❌ {issue['category']}: {issue['description']}")
                for warn in report.warnings:
                    print(f"  ⚠️  {warn['category']}: {warn['description']}")
    
    # Determine exit code based on worst score
    min_score = min(r.score for r in analyzer.reports.values()) if analyzer.reports else 0
    return 0 if min_score >= 70 else 1


if __name__ == '__main__':
    exit(main())
