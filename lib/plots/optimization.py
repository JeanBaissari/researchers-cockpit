"""
Optimization visualization functions.

Provides heatmap and Monte Carlo distribution plotting.
"""

# Standard library imports
from pathlib import Path

# Third-party imports
import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def _plot_optimization_heatmap(
    results_df: pd.DataFrame,
    param_grid: dict,
    objective: str,
    save_dir: Path
) -> None:
    """
    Plot optimization heatmap for 2-parameter grid search.
    
    Args:
        results_df: DataFrame with optimization results
        param_grid: Parameter grid dictionary
        objective: Objective metric name
        save_dir: Directory to save plot
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    if len(param_grid) != 2:
        return
    
    param_names = list(param_grid.keys())
    test_obj_col = f'test_{objective}'
    
    if test_obj_col not in results_df.columns:
        return
    
    # Create pivot table
    pivot_data = results_df.pivot_table(
        values=test_obj_col,
        index=param_names[0],
        columns=param_names[1],
        aggfunc='mean'
    )
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(
        pivot_data,
        annot=True,
        fmt='.3f',
        cmap='RdYlGn',
        center=0,
        cbar_kws={'label': f'Test {objective.capitalize()}'},
        ax=ax,
        linewidths=0.5,
        linecolor='gray'
    )
    
    ax.set_xlabel(param_names[1], fontsize=12)
    ax.set_ylabel(param_names[0], fontsize=12)
    ax.set_title(f'Optimization Heatmap - {objective.capitalize()}', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_dir / f'heatmap_{objective}.png', dpi=150, bbox_inches='tight')
    plt.close()


def _plot_monte_carlo_distribution(
    simulation_results: dict,
    save_dir: Path
) -> None:
    """
    Plot Monte Carlo simulation distribution.
    
    Args:
        simulation_results: Dictionary with simulation results
        save_dir: Directory to save plot
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    if 'simulation_paths' not in simulation_results:
        return
    
    paths_df = simulation_results['simulation_paths']
    final_values = paths_df.iloc[-1].values if len(paths_df) > 0 else []
    
    if len(final_values) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.hist(final_values, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
    ax.axvline(np.mean(final_values), color='red', linestyle='--', linewidth=2, label='Mean')
    
    # Add confidence intervals
    if 'confidence_intervals' in simulation_results:
        ci = simulation_results['confidence_intervals']
        for key, value in ci.items():
            ax.axvline(value, color='green', linestyle='--', linewidth=1, alpha=0.7, label=f'{key}')
    
    ax.set_xlabel('Final Portfolio Value ($)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Monte Carlo Simulation - Final Value Distribution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / 'distribution.png', dpi=150, bbox_inches='tight')
    plt.close()















