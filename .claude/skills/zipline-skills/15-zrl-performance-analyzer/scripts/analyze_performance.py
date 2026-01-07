#!/usr/bin/env python3
"""
Comprehensive performance analysis for Zipline backtest results.
Calculates risk-adjusted returns, drawdown metrics, and generates reports.
"""
import argparse
import pickle
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics."""
    # Returns
    total_return: float
    cagr: float
    daily_return_mean: float
    daily_return_std: float
    volatility: float
    
    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Drawdown
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    
    # Risk
    var_95: float
    cvar_95: float
    
    # Trading
    num_trades: int
    win_rate: float
    profit_factor: float


class PerformanceAnalyzer:
    """Comprehensive performance analysis for Zipline results."""
    
    def __init__(self, results: pd.DataFrame, 
                 benchmark_returns: Optional[pd.Series] = None,
                 risk_free_rate: float = 0.0):
        self.results = results
        self.benchmark_returns = benchmark_returns
        self.risk_free_rate = risk_free_rate
        
        # Extract returns
        self.returns = results['returns'].dropna()
        self.equity = results['portfolio_value']
        
        # Extract transactions if available
        self.transactions = self._extract_transactions()
    
    def _extract_transactions(self) -> pd.DataFrame:
        """Extract transactions from results."""
        if 'transactions' not in self.results.columns:
            return pd.DataFrame()
        
        txns = []
        for date, txn_list in self.results['transactions'].items():
            if txn_list:
                for txn in txn_list:
                    txn['date'] = date
                    txns.append(txn)
        
        return pd.DataFrame(txns) if txns else pd.DataFrame()
    
    # ==================== Return Metrics ====================
    
    def total_return(self) -> float:
        """Calculate total cumulative return."""
        return (self.equity.iloc[-1] / self.equity.iloc[0]) - 1
    
    def cagr(self) -> float:
        """Calculate compound annual growth rate."""
        total_days = (self.returns.index[-1] - self.returns.index[0]).days
        total_years = total_days / 365.25
        return (1 + self.total_return()) ** (1 / total_years) - 1
    
    def volatility(self) -> float:
        """Calculate annualized volatility."""
        return self.returns.std() * np.sqrt(252)
    
    # ==================== Risk-Adjusted Metrics ====================
    
    def sharpe_ratio(self) -> float:
        """Calculate annualized Sharpe ratio."""
        excess_returns = self.returns - self.risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def sortino_ratio(self) -> float:
        """Calculate Sortino ratio (downside risk adjusted)."""
        excess_returns = self.returns - self.risk_free_rate / 252
        downside_returns = self.returns[self.returns < 0]
        if len(downside_returns) == 0:
            return np.inf
        downside_std = np.sqrt(np.mean(downside_returns**2))
        if downside_std == 0:
            return np.inf
        return np.sqrt(252) * excess_returns.mean() / downside_std
    
    def calmar_ratio(self) -> float:
        """Calculate Calmar ratio (CAGR / MaxDD)."""
        max_dd = abs(self.max_drawdown())
        if max_dd == 0:
            return np.inf
        return self.cagr() / max_dd
    
    # ==================== Drawdown Metrics ====================
    
    def drawdown_series(self) -> pd.Series:
        """Calculate drawdown series."""
        rolling_max = self.equity.expanding().max()
        drawdowns = (self.equity - rolling_max) / rolling_max
        return drawdowns
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        return self.drawdown_series().min()
    
    def max_drawdown_duration(self) -> int:
        """Calculate max drawdown duration in days."""
        dd = self.drawdown_series()
        in_drawdown = dd < 0
        
        if not in_drawdown.any():
            return 0
        
        # Find drawdown periods
        dd_starts = in_drawdown & ~in_drawdown.shift(1).fillna(False)
        dd_ends = ~in_drawdown & in_drawdown.shift(1).fillna(False)
        
        max_duration = 0
        current_start = None
        
        for date in dd.index:
            if dd_starts.get(date, False):
                current_start = date
            elif dd_ends.get(date, False) and current_start:
                duration = (date - current_start).days
                max_duration = max(max_duration, duration)
                current_start = None
        
        # Handle ongoing drawdown
        if current_start:
            duration = (dd.index[-1] - current_start).days
            max_duration = max(max_duration, duration)
        
        return max_duration
    
    def top_drawdowns(self, n: int = 5) -> pd.DataFrame:
        """Get top N drawdown periods."""
        dd = self.drawdown_series()
        
        drawdowns = []
        in_dd = False
        start = None
        
        for date, val in dd.items():
            if val < 0 and not in_dd:
                start = date
                in_dd = True
                min_val = val
                min_date = date
            elif val < 0 and in_dd:
                if val < min_val:
                    min_val = val
                    min_date = date
            elif val >= 0 and in_dd:
                drawdowns.append({
                    'start': start,
                    'trough': min_date,
                    'end': date,
                    'depth': min_val,
                    'duration': (date - start).days
                })
                in_dd = False
        
        if not drawdowns:
            return pd.DataFrame()
        
        df = pd.DataFrame(drawdowns)
        return df.nsmallest(n, 'depth')
    
    # ==================== Risk Metrics ====================
    
    def var(self, confidence: float = 0.95) -> float:
        """Calculate Value at Risk."""
        return np.percentile(self.returns, (1 - confidence) * 100)
    
    def cvar(self, confidence: float = 0.95) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        var = self.var(confidence)
        return self.returns[self.returns <= var].mean()
    
    def beta(self) -> Optional[float]:
        """Calculate beta vs benchmark."""
        if self.benchmark_returns is None:
            return None
        
        aligned = pd.concat([self.returns, self.benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return None
        
        cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1]
        var = np.var(aligned.iloc[:, 1])
        return cov / var if var != 0 else 0
    
    def alpha(self) -> Optional[float]:
        """Calculate alpha vs benchmark (annualized)."""
        if self.benchmark_returns is None:
            return None
        
        beta = self.beta()
        if beta is None:
            return None
        
        strategy_return = self.returns.mean() * 252
        benchmark_return = self.benchmark_returns.mean() * 252
        
        return strategy_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
    
    # ==================== Trading Metrics ====================
    
    def num_trades(self) -> int:
        """Count total number of trades."""
        if self.transactions.empty:
            return 0
        return len(self.transactions)
    
    def win_rate(self) -> float:
        """Calculate win rate from transactions."""
        if self.transactions.empty:
            return 0.0
        
        # Simplified: use positive price changes as wins
        if 'amount' in self.transactions.columns and 'price' in self.transactions.columns:
            # Group by asset and calculate P&L
            pass
        
        return 0.0  # Placeholder
    
    def profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        positive_days = self.returns[self.returns > 0].sum()
        negative_days = abs(self.returns[self.returns < 0].sum())
        
        if negative_days == 0:
            return np.inf
        return positive_days / negative_days
    
    # ==================== Time-Based Analysis ====================
    
    def monthly_returns(self) -> pd.Series:
        """Calculate monthly returns."""
        return self.equity.resample('M').last().pct_change().dropna()
    
    def yearly_returns(self) -> pd.Series:
        """Calculate yearly returns."""
        return self.equity.resample('Y').last().pct_change().dropna()
    
    def rolling_sharpe(self, window: int = 252) -> pd.Series:
        """Calculate rolling Sharpe ratio."""
        rolling_mean = self.returns.rolling(window).mean()
        rolling_std = self.returns.rolling(window).std()
        return np.sqrt(252) * rolling_mean / rolling_std
    
    # ==================== Aggregate Methods ====================
    
    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics."""
        return {
            # Returns
            'total_return': self.total_return(),
            'cagr': self.cagr(),
            'volatility': self.volatility(),
            
            # Risk-adjusted
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'calmar_ratio': self.calmar_ratio(),
            
            # Drawdown
            'max_drawdown': self.max_drawdown(),
            'max_drawdown_duration': self.max_drawdown_duration(),
            
            # Risk
            'var_95': self.var(0.95),
            'cvar_95': self.cvar(0.95),
            'beta': self.beta(),
            'alpha': self.alpha(),
            
            # Trading
            'num_trades': self.num_trades(),
            'profit_factor': self.profit_factor(),
        }
    
    def summary_report(self) -> str:
        """Generate text summary report."""
        m = self.calculate_all_metrics()
        
        lines = [
            "=" * 60,
            "PERFORMANCE SUMMARY",
            "=" * 60,
            "",
            "Return Metrics:",
            f"  Total Return:     {m['total_return']:>12.2%}",
            f"  CAGR:             {m['cagr']:>12.2%}",
            f"  Volatility:       {m['volatility']:>12.2%}",
            "",
            "Risk-Adjusted Metrics:",
            f"  Sharpe Ratio:     {m['sharpe_ratio']:>12.2f}",
            f"  Sortino Ratio:    {m['sortino_ratio']:>12.2f}",
            f"  Calmar Ratio:     {m['calmar_ratio']:>12.2f}",
            "",
            "Drawdown Metrics:",
            f"  Max Drawdown:     {m['max_drawdown']:>12.2%}",
            f"  Max DD Duration:  {m['max_drawdown_duration']:>12} days",
            "",
            "Risk Metrics:",
            f"  VaR (95%):        {m['var_95']:>12.2%}",
            f"  CVaR (95%):       {m['cvar_95']:>12.2%}",
        ]
        
        if m['beta'] is not None:
            lines.extend([
                f"  Beta:             {m['beta']:>12.2f}",
                f"  Alpha:            {m['alpha']:>12.2%}",
            ])
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Analyze Zipline backtest performance')
    parser.add_argument('results', help='Path to pickled results DataFrame')
    parser.add_argument('--benchmark', help='Benchmark ticker symbol')
    parser.add_argument('--risk-free-rate', type=float, default=0.0, help='Annual risk-free rate')
    parser.add_argument('--output', help='Output file path for report')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text')
    args = parser.parse_args()
    
    # Load results
    results_path = Path(args.results)
    if results_path.suffix == '.pickle':
        with open(results_path, 'rb') as f:
            results = pickle.load(f)
    else:
        results = pd.read_pickle(results_path)
    
    # Load benchmark if specified
    benchmark_returns = None
    if args.benchmark:
        try:
            import yfinance as yf
            bench = yf.Ticker(args.benchmark)
            bench_data = bench.history(start=results.index[0], end=results.index[-1])
            benchmark_returns = bench_data['Close'].pct_change().dropna()
            benchmark_returns.index = benchmark_returns.index.tz_localize(None)
        except Exception as e:
            print(f"Warning: Could not load benchmark {args.benchmark}: {e}")
    
    # Analyze
    analyzer = PerformanceAnalyzer(results, benchmark_returns, args.risk_free_rate)
    
    if args.format == 'text':
        report = analyzer.summary_report()
        if args.output:
            Path(args.output).write_text(report)
        print(report)
    
    elif args.format == 'json':
        import json
        metrics = analyzer.calculate_all_metrics()
        output = json.dumps(metrics, indent=2, default=str)
        if args.output:
            Path(args.output).write_text(output)
        print(output)
    
    elif args.format == 'csv':
        metrics = analyzer.calculate_all_metrics()
        df = pd.DataFrame([metrics])
        if args.output:
            df.to_csv(args.output, index=False)
        print(df.to_string())
    
    return 0


if __name__ == '__main__':
    exit(main())
