#!/usr/bin/env python3
"""
Backtest execution script for The Researcher's Cockpit.

Runs a backtest for a strategy and saves results.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import click
from v1_researchers_cockpit.lib.backtest import run_backtest, save_results
from v1_researchers_cockpit.lib.config import load_strategy_params, validate_strategy_params, get_warmup_days
from v1_researchers_cockpit.lib.utils import get_strategy_path


@click.command()
@click.option('--strategy', required=True, help='Strategy name (e.g., spy_sma_cross)')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
@click.option('--capital', type=float, default=None, help='Starting capital')
@click.option('--bundle', default=None, help='Data bundle name (auto-detected if not provided)')
@click.option('--asset-class', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class hint for strategy location')
@click.option('--skip-warmup-check', is_flag=True, default=False,
              help='Skip warmup period validation (use with caution)')
def main(strategy, start, end, capital, bundle, asset_class, skip_warmup_check):
    """
    Run a backtest for a strategy.
    
    Example:
        python scripts/run_backtest.py --strategy spy_sma_cross
    """
    click.echo(f"Running backtest for strategy: {strategy}")

    try:
        # Load and validate strategy parameters
        try:
            params = load_strategy_params(strategy, asset_class)
            is_valid, errors = validate_strategy_params(params, strategy)
            if not is_valid:
                click.echo(f"✗ Parameter validation failed:", err=True)
                for error in errors:
                    click.echo(f"  - {error}", err=True)
                sys.exit(1)
        except FileNotFoundError as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)
        except ValueError as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)

        # Display warmup information
        warmup_days = get_warmup_days(params)
        click.echo(f"Warmup period: {warmup_days} days required for indicator initialization")

        # Temporarily disable warmup validation if requested
        if skip_warmup_check:
            click.echo("⚠ Warmup validation disabled (--skip-warmup-check)")
            params.setdefault('backtest', {})['validate_warmup'] = False

        # Run backtest
        click.echo("Executing backtest...")
        perf, trading_calendar = run_backtest(
            strategy_name=strategy,
            start_date=start,
            end_date=end,
            capital_base=capital,
            bundle=bundle,
            asset_class=asset_class
        )

        # Save results
        click.echo("Saving results...")
        result_dir = save_results(
            strategy_name=strategy,
            perf=perf,
            params=params,
            trading_calendar=trading_calendar,
            result_type='backtest'
        )
        
        # Print summary
        click.echo("\n" + "=" * 60)
        click.echo("BACKTEST COMPLETE")
        click.echo("=" * 60)
        click.echo(f"Strategy: {strategy}")
        click.echo(f"Results saved to: {result_dir}")
        click.echo(f"Latest results: results/{strategy}/latest/")
        
        # Print basic metrics if available
        metrics_file = result_dir / 'metrics.json'
        if metrics_file.exists():
            import json
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            click.echo("\nPerformance Metrics:")
            click.echo(f"  Total Return: {metrics.get('total_return', 0):.2%}")
            click.echo(f"  Annual Return: {metrics.get('annual_return', 0):.2%}")
            click.echo(f"  Sharpe Ratio: {metrics.get('sharpe', 0):.2f}")
            click.echo(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        
        click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

