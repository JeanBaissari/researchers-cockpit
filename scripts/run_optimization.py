#!/usr/bin/env python3
"""
Optimization script for The Researcher's Cockpit.

Runs grid search or random search optimization for strategy parameters.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
import numpy as np
from lib.optimize import grid_search, random_search
from lib.config import load_settings
from lib.paths import get_project_root
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging (console=False since we use click.echo for user output)
configure_logging(level='INFO', console=False, file=False)
logger = get_logger(__name__)


def parse_param_range(param_str: str) -> tuple[str, list]:
    """
    Parse parameter range string.
    
    Format: 'param.name:start:end:step' or 'param.name:value1,value2,value3'
    
    Examples:
        'strategy.fast_period:5:20:5' -> [5, 10, 15, 20]
        'strategy.slow_period:30,50,100' -> [30, 50, 100]
    """
    parts = param_str.split(':')
    if len(parts) < 2:
        raise ValueError(f"Invalid parameter format: {param_str}. Expected 'name:range' or 'name:start:end:step'")
    
    param_name = parts[0]
    range_parts = parts[1:]
    
    # Check if it's a comma-separated list (single part with commas)
    if len(range_parts) == 1 and ',' in range_parts[0]:
        values = [float(x.strip()) for x in range_parts[0].split(',')]
        # Convert to int if all are whole numbers
        if all(v.is_integer() for v in values):
            values = [int(v) for v in values]
        return param_name, values
    
    # Otherwise parse as start:end:step
    if len(range_parts) == 3:
        start, end, step = map(float, range_parts)
        values = list(np.arange(start, end + step, step))
        # Convert to int if all are whole numbers
        if all(v.is_integer() for v in values):
            values = [int(v) for v in values]
        return param_name, values
    else:
        raise ValueError(f"Invalid range format. Expected 'name:start:end:step' or 'name:val1,val2,val3'")


@click.command()
@click.option('--strategy', required=True, help='Strategy name (e.g., spy_sma_cross)')
@click.option('--method', type=click.Choice(['grid', 'random']), default='grid',
              help='Optimization method (grid or random)')
@click.option('--param', 'params', multiple=True, required=True,
              help='Parameter range in format: param.name:start:end:step or param.name:val1,val2,val3')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
@click.option('--objective', default='sharpe',
              type=click.Choice(['sharpe', 'sortino', 'total_return', 'calmar']),
              help='Objective metric to optimize')
@click.option('--train-pct', type=float, default=0.7, help='Training data percentage (default: 0.7)')
@click.option('--n-iter', type=int, default=100, help='Number of iterations for random search')
@click.option('--capital', type=float, default=None, help='Starting capital')
@click.option('--bundle', default=None, help='Data bundle name')
@click.option('--asset-class', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class hint')
def main(strategy, method, params, start, end, objective, train_pct, n_iter, capital, bundle, asset_class):
    """
    Run parameter optimization for a strategy.
    
    Examples:
        # Grid search
        python scripts/run_optimization.py \\
            --strategy spy_sma_cross \\
            --method grid \\
            --param strategy.fast_period:5:20:5 \\
            --param strategy.slow_period:30:100:10 \\
            --objective sharpe
        
        # Random search
        python scripts/run_optimization.py \\
            --strategy spy_sma_cross \\
            --method random \\
            --param strategy.fast_period:5,10,15,20 \\
            --param strategy.slow_period:30,50,100 \\
            --n-iter 50
    """
    click.echo(f"Running {method} optimization for strategy: {strategy}")
    
    # Use LogContext for structured logging
    with LogContext(phase='optimization', strategy=strategy, method=method):
        logger.info(f"Starting {method} optimization for strategy: {strategy}")
        
        try:
            # Get default dates if not provided
            if start is None or end is None:
                settings = load_settings()
                if start is None:
                    start = settings['dates']['default_start']
                if end is None:
                    from datetime import datetime
                    end = datetime.now().strftime('%Y-%m-%d')
        
            # Parse parameter ranges
            param_grid = {}
            for param_str in params:
                param_name, values = parse_param_range(param_str)
                param_grid[param_name] = values
            
            logger.info(f"Parameter grid: {param_grid}")
            click.echo(f"\nParameter grid:")
            for param_name, values in param_grid.items():
                click.echo(f"  {param_name}: {values}")
            
            # Run optimization
            if method == 'grid':
                logger.info("Running grid search optimization")
                click.echo(f"\nRunning grid search...")
                results_df = grid_search(
                strategy_name=strategy,
                param_grid=param_grid,
                start_date=start,
                end_date=end,
                objective=objective,
                train_pct=train_pct,
                capital_base=capital,
                bundle=bundle,
                asset_class=asset_class
                )
            else:  # random
                logger.info(f"Running random search optimization ({n_iter} iterations)")
                click.echo(f"\nRunning random search ({n_iter} iterations)...")
                results_df = random_search(
                strategy_name=strategy,
                param_distributions=param_grid,
                n_iter=n_iter,
                start_date=start,
                end_date=end,
                objective=objective,
                train_pct=train_pct,
                capital_base=capital,
                    bundle=bundle,
                    asset_class=asset_class
                )
            
            logger.info(f"Optimization complete: {len(results_df)} combinations tested")
            # Print summary
            click.echo("\n" + "=" * 60)
            click.echo("OPTIMIZATION COMPLETE")
            click.echo("=" * 60)
            click.echo(f"Strategy: {strategy}")
            click.echo(f"Method: {method}")
            click.echo(f"Objective: {objective}")
            click.echo(f"Total combinations tested: {len(results_df)}")
            
            # Find best result
            test_obj_col = f'test_{objective}'
            if test_obj_col in results_df.columns and len(results_df) > 0:
                best_idx = results_df[test_obj_col].idxmax()
                best_row = results_df.loc[best_idx]
                
                logger.info(f"Best parameters found: {dict(best_row[list(param_grid.keys())])}")
                click.echo(f"\nBest Parameters:")
                for param_name in param_grid.keys():
                    if param_name in best_row:
                        click.echo(f"  {param_name}: {best_row[param_name]}")
                
                click.echo(f"\nBest Performance:")
                click.echo(f"  Train {objective}: {best_row.get(f'train_{objective}', 0):.4f}")
                click.echo(f"  Test {objective}: {best_row.get(test_obj_col, 0):.4f}")
                click.echo(f"  Train Sharpe: {best_row.get('train_sharpe', 0):.4f}")
                click.echo(f"  Test Sharpe: {best_row.get('test_sharpe', 0):.4f}")
            
            # Load overfit score
            results_base = get_project_root() / 'results' / strategy / 'latest'
            overfit_file = results_base / 'overfit_score.json'
            if overfit_file.exists():
                import json
                with open(overfit_file) as f:
                    overfit = json.load(f)
                
                logger.info(f"Overfit analysis: efficiency={overfit.get('efficiency', 0):.2f}, pbo={overfit.get('pbo', 0):.2f}")
                click.echo(f"\nOverfit Analysis:")
                click.echo(f"  Efficiency: {overfit.get('efficiency', 0):.2f}")
                click.echo(f"  PBO: {overfit.get('pbo', 0):.2f}")
                click.echo(f"  Verdict: {overfit.get('verdict', 'unknown')}")
            
            click.echo(f"\nResults saved to: results/{strategy}/latest/")
            click.echo("=" * 60)
        
        except Exception as e:
            logger.error(f"Optimization failed: {e}", exc_info=True)
            click.echo(f"✗ Error: {e}", err=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

