#!/usr/bin/env python3
"""
Generate visualizations from Zipline backtest results.
Creates equity curves, drawdown charts, return analysis, and dashboards.
"""
import argparse
import pickle
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    print("Error: matplotlib not installed. Run: pip install matplotlib")
    exit(1)

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


class BacktestVisualizer:
    """Professional visualizations for backtest results."""
    
    COLORS = {
        'equity': '#1f77b4',
        'benchmark': '#7f7f7f', 
        'drawdown': '#d62728',
        'positive': '#2ca02c',
        'negative': '#d62728',
    }
    
    def __init__(self, results: pd.DataFrame,
                 benchmark_returns: Optional[pd.Series] = None,
                 style: str = 'seaborn-v0_8-whitegrid'):
        self.results = results
        self.benchmark_returns = benchmark_returns
        self.returns = results['returns'].dropna()
        self.equity = results['portfolio_value']
        
        try:
            plt.style.use(style)
        except:
            plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn' in plt.style.available else 'ggplot')
    
    def _setup_figure(self, figsize: Tuple[int, int] = (12, 6)) -> Tuple:
        """Create figure with standard formatting."""
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax
    
    def plot_equity_curve(self, log_scale: bool = False, 
                         figsize: Tuple[int, int] = (12, 6),
                         title: str = 'Portfolio Equity Curve') -> plt.Figure:
        """Plot portfolio equity curve."""
        fig, ax = self._setup_figure(figsize)
        
        ax.plot(self.equity.index, self.equity.values, 
               color=self.COLORS['equity'], linewidth=1.5, label='Portfolio')
        
        if self.benchmark_returns is not None:
            bench_equity = (1 + self.benchmark_returns).cumprod() * self.equity.iloc[0]
            ax.plot(bench_equity.index, bench_equity.values,
                   color=self.COLORS['benchmark'], linewidth=1, 
                   linestyle='--', label='Benchmark', alpha=0.7)
            ax.legend()
        
        if log_scale:
            ax.set_yscale('log')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value ($)')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        plt.tight_layout()
        return fig
    
    def plot_cumulative_returns(self, figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
        """Plot cumulative returns percentage."""
        fig, ax = self._setup_figure(figsize)
        
        cum_returns = (1 + self.returns).cumprod() - 1
        ax.plot(cum_returns.index, cum_returns.values * 100,
               color=self.COLORS['equity'], linewidth=1.5)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.fill_between(cum_returns.index, cum_returns.values * 100, 0,
                       where=cum_returns > 0, color=self.COLORS['positive'], alpha=0.2)
        ax.fill_between(cum_returns.index, cum_returns.values * 100, 0,
                       where=cum_returns < 0, color=self.COLORS['negative'], alpha=0.2)
        
        ax.set_title('Cumulative Returns', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Return (%)')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_drawdown(self, figsize: Tuple[int, int] = (12, 4)) -> plt.Figure:
        """Plot drawdown chart."""
        fig, ax = self._setup_figure(figsize)
        
        rolling_max = self.equity.expanding().max()
        drawdown = (self.equity - rolling_max) / rolling_max
        
        ax.fill_between(drawdown.index, drawdown.values * 100, 0,
                       color=self.COLORS['drawdown'], alpha=0.5)
        ax.plot(drawdown.index, drawdown.values * 100,
               color=self.COLORS['drawdown'], linewidth=1)
        
        ax.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(True, alpha=0.3)
        
        # Mark max drawdown
        max_dd_idx = drawdown.idxmin()
        max_dd_val = drawdown.min() * 100
        ax.annotate(f'Max DD: {max_dd_val:.1f}%',
                   xy=(max_dd_idx, max_dd_val),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, color=self.COLORS['drawdown'])
        
        plt.tight_layout()
        return fig
    
    def plot_returns_distribution(self, figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """Plot return distribution histogram."""
        fig, ax = self._setup_figure(figsize)
        
        returns_pct = self.returns * 100
        
        ax.hist(returns_pct, bins=50, color=self.COLORS['equity'], 
               alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Add vertical lines for mean and std
        mean_ret = returns_pct.mean()
        std_ret = returns_pct.std()
        
        ax.axvline(mean_ret, color='black', linestyle='-', linewidth=2, 
                  label=f'Mean: {mean_ret:.2f}%')
        ax.axvline(mean_ret + std_ret, color='gray', linestyle='--', 
                  label=f'+1 Std: {mean_ret + std_ret:.2f}%')
        ax.axvline(mean_ret - std_ret, color='gray', linestyle='--',
                  label=f'-1 Std: {mean_ret - std_ret:.2f}%')
        
        ax.set_title('Daily Returns Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Daily Return (%)')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_monthly_heatmap(self, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """Plot monthly returns heatmap."""
        # Calculate monthly returns
        monthly = self.returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Create pivot table
        monthly_df = monthly.to_frame('return')
        monthly_df['year'] = monthly_df.index.year
        monthly_df['month'] = monthly_df.index.month
        pivot = monthly_df.pivot(index='year', columns='month', values='return')
        
        # Month names
        pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.columns)]
        
        fig, ax = self._setup_figure(figsize)
        
        if HAS_SEABORN:
            sns.heatmap(pivot * 100, annot=True, fmt='.1f', cmap='RdYlGn',
                       center=0, ax=ax, cbar_kws={'label': 'Return (%)'})
        else:
            im = ax.imshow(pivot.values * 100, cmap='RdYlGn', aspect='auto')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            plt.colorbar(im, ax=ax, label='Return (%)')
        
        ax.set_title('Monthly Returns Heatmap', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def plot_rolling_sharpe(self, window: int = 252, 
                           figsize: Tuple[int, int] = (12, 4)) -> plt.Figure:
        """Plot rolling Sharpe ratio."""
        fig, ax = self._setup_figure(figsize)
        
        rolling_mean = self.returns.rolling(window).mean()
        rolling_std = self.returns.rolling(window).std()
        sharpe = np.sqrt(252) * rolling_mean / rolling_std
        
        ax.plot(sharpe.index, sharpe.values, 
               color=self.COLORS['equity'], linewidth=1.5)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Sharpe=1')
        ax.axhline(y=2, color='blue', linestyle='--', alpha=0.5, label='Sharpe=2')
        
        ax.fill_between(sharpe.index, sharpe.values, 0,
                       where=sharpe > 0, color=self.COLORS['positive'], alpha=0.2)
        ax.fill_between(sharpe.index, sharpe.values, 0,
                       where=sharpe < 0, color=self.COLORS['negative'], alpha=0.2)
        
        ax.set_title(f'Rolling {window}-Day Sharpe Ratio', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Sharpe Ratio')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_tearsheet(self, output_path: str = 'tearsheet.png'):
        """Create comprehensive tearsheet with multiple charts."""
        fig = plt.figure(figsize=(16, 20))
        
        # Layout: 4 rows, 2 columns
        gs = fig.add_gridspec(4, 2, height_ratios=[2, 1, 1.5, 1.5], hspace=0.3, wspace=0.2)
        
        # Equity curve (full width)
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(self.equity.index, self.equity.values, 
                color=self.COLORS['equity'], linewidth=1.5)
        ax1.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Value ($)')
        ax1.grid(True, alpha=0.3)
        
        # Drawdown (full width)
        ax2 = fig.add_subplot(gs[1, :])
        rolling_max = self.equity.expanding().max()
        drawdown = (self.equity - rolling_max) / rolling_max
        ax2.fill_between(drawdown.index, drawdown.values * 100, 0,
                        color=self.COLORS['drawdown'], alpha=0.5)
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        # Returns distribution
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.hist(self.returns * 100, bins=50, color=self.COLORS['equity'], 
                alpha=0.7, edgecolor='black', linewidth=0.5)
        ax3.set_title('Daily Returns Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Return (%)')
        ax3.grid(True, alpha=0.3)
        
        # Rolling Sharpe
        ax4 = fig.add_subplot(gs[2, 1])
        rolling_mean = self.returns.rolling(252).mean()
        rolling_std = self.returns.rolling(252).std()
        sharpe = np.sqrt(252) * rolling_mean / rolling_std
        ax4.plot(sharpe.index, sharpe.values, color=self.COLORS['equity'])
        ax4.axhline(y=1, color='green', linestyle='--', alpha=0.5)
        ax4.set_title('Rolling 1-Year Sharpe', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Monthly returns heatmap (approximate)
        ax5 = fig.add_subplot(gs[3, :])
        monthly = self.returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        ax5.bar(monthly.index, monthly.values * 100, 
               color=[self.COLORS['positive'] if x > 0 else self.COLORS['negative'] 
                     for x in monthly.values], width=20)
        ax5.set_title('Monthly Returns', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Return (%)')
        ax5.axhline(y=0, color='black', linewidth=0.5)
        ax5.grid(True, alpha=0.3)
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path


CHART_TYPES = ['equity', 'drawdown', 'monthly', 'distribution', 'sharpe', 'tearsheet']


def main():
    parser = argparse.ArgumentParser(description='Visualize Zipline backtest results')
    parser.add_argument('results', help='Path to pickled results')
    parser.add_argument('--charts', default='equity,drawdown', 
                       help=f'Comma-separated charts: {",".join(CHART_TYPES)}')
    parser.add_argument('--output', type=Path, default=Path('.'), help='Output directory')
    parser.add_argument('--format', default='png', choices=['png', 'pdf', 'svg'])
    parser.add_argument('--benchmark', help='Benchmark ticker for comparison')
    args = parser.parse_args()
    
    # Load results
    with open(args.results, 'rb') as f:
        results = pickle.load(f)
    
    # Load benchmark if specified
    benchmark = None
    if args.benchmark:
        try:
            import yfinance as yf
            bench = yf.Ticker(args.benchmark)
            bench_data = bench.history(start=results.index[0], end=results.index[-1])
            benchmark = bench_data['Close'].pct_change().dropna()
        except Exception as e:
            print(f"Warning: Could not load benchmark: {e}")
    
    # Create visualizer
    viz = BacktestVisualizer(results, benchmark)
    
    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Generate requested charts
    charts = [c.strip() for c in args.charts.split(',')]
    
    for chart in charts:
        print(f"Generating {chart}...", end=' ')
        
        if chart == 'equity':
            fig = viz.plot_equity_curve()
            fig.savefig(args.output / f'equity_curve.{args.format}', dpi=150)
        elif chart == 'drawdown':
            fig = viz.plot_drawdown()
            fig.savefig(args.output / f'drawdown.{args.format}', dpi=150)
        elif chart == 'monthly':
            fig = viz.plot_monthly_heatmap()
            fig.savefig(args.output / f'monthly_heatmap.{args.format}', dpi=150)
        elif chart == 'distribution':
            fig = viz.plot_returns_distribution()
            fig.savefig(args.output / f'returns_dist.{args.format}', dpi=150)
        elif chart == 'sharpe':
            fig = viz.plot_rolling_sharpe()
            fig.savefig(args.output / f'rolling_sharpe.{args.format}', dpi=150)
        elif chart == 'tearsheet':
            viz.create_tearsheet(str(args.output / f'tearsheet.{args.format}'))
        else:
            print(f"Unknown chart type: {chart}")
            continue
        
        print("✓")
        plt.close('all')
    
    print(f"\nCharts saved to: {args.output}")
    return 0


if __name__ == '__main__':
    exit(main())
