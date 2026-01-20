#!/usr/bin/env python3
"""
Backtest execution script for The Researcher's Cockpit.

Runs a backtest for a strategy and saves results.
"""

import sys
from pathlib import Path

# Bootstrap: Add project root to path (scripts are in scripts/ subdirectory)
# This allows us to import lib.paths.get_project_root
_project_root_bootstrap = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root_bootstrap))

from lib.paths import get_project_root

# Use canonical path resolution
project_root = get_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import click
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params, validate_strategy_params, get_warmup_days
from lib.strategies import get_strategy_path
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging (console=False since we use click.echo for user output)
configure_logging(level='INFO', console=False, file=False)
logger = get_logger(__name__)


@click.command()
@click.option('--strategy', required=True, help='Strategy name (e.g., spy_sma_cross)')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
@click.option('--capital', type=float, default=None, help='Starting capital')
@click.option('--bundle', default=None, help='Data bundle name (auto-detected if not provided)')
@click.option('--asset-class', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class hint for strategy location')
@click.option('--data-frequency', default=None, type=click.Choice(['daily', 'minute']),
              help='Data frequency (auto-detected from bundle if not specified)')
@click.option('--skip-warmup-check', is_flag=True, default=False,
              help='Skip warmup period validation (use with caution)')
@click.option('--validate-calendar', is_flag=True, default=False,
              help='Strict calendar validation - raise error on session mismatch (v1.1.0)')
def main(strategy, start, end, capital, bundle, asset_class, data_frequency, skip_warmup_check, validate_calendar):
    """
    Run a backtest for a strategy.
    
    Example:
        python scripts/run_backtest.py --strategy spy_sma_cross
    """
    click.echo(f"Running backtest for strategy: {strategy}")

    # Use LogContext for structured logging
    with LogContext(phase='backtest', strategy=strategy, asset_type=asset_class):
        logger.info(f"Starting backtest for strategy: {strategy}")
        
        try:
            # Load and validate strategy parameters
            try:
                logger.info(f"Loading parameters for strategy: {strategy}")
                params = load_strategy_params(strategy, asset_class)
                is_valid, errors = validate_strategy_params(params, strategy)
                if not is_valid:
                    logger.error(f"Parameter validation failed for {strategy}: {errors}")
                    click.echo(f"✗ Parameter validation failed:", err=True)
                    for error in errors:
                        click.echo(f"  - {error}", err=True)
                    click.echo(f"  Fix: Edit parameters.yaml in strategies/{asset_class or '*'}/{strategy}/", err=True)
                    sys.exit(1)
            except FileNotFoundError as e:
                logger.error(f"Strategy not found: {strategy} (asset_class={asset_class})", exc_info=True)
                click.echo(f"✗ Error: Strategy '{strategy}' not found", err=True)
                click.echo(f"  Searched in: strategies/{asset_class or '*'}/", err=True)
                click.echo(f"  Create strategy: Copy strategies/_template/ to strategies/{asset_class or 'equities'}/{strategy}/", err=True)
                sys.exit(1)
            except ValueError as e:
                logger.error(f"Invalid parameters for {strategy}: {e}", exc_info=True)
                click.echo(f"✗ Error: {e}", err=True)
                sys.exit(1)

            # Display warmup information
            warmup_days = get_warmup_days(params)
            logger.info(f"Warmup period: {warmup_days} days required")
            click.echo(f"Warmup period: {warmup_days} days required for indicator initialization")

            # Temporarily disable warmup validation if requested
            if skip_warmup_check:
                logger.warning("Warmup validation disabled (--skip-warmup-check)")
                click.echo("⚠ Warmup validation disabled (--skip-warmup-check)")
                params.setdefault('backtest', {})['validate_warmup'] = False

            # Auto-detect data frequency from bundle registry if not specified
            if data_frequency is None:
                from lib.bundles import load_bundle_registry
                registry = load_bundle_registry()

                # Determine which bundle to check
                bundle_to_check = bundle
                if bundle_to_check is None:
                    # Try to infer bundle from strategy params
                    bundle_to_check = params.get('backtest', {}).get('bundle')

                if bundle_to_check and bundle_to_check in registry:
                    detected_freq = registry[bundle_to_check].get('data_frequency', 'daily')
                    detected_tf = registry[bundle_to_check].get('timeframe', 'daily')
                    logger.info(f"Auto-detected data frequency: {detected_freq} from bundle {bundle_to_check}")
                    click.echo(f"Auto-detected data frequency: {detected_freq} (from bundle {bundle_to_check}, timeframe: {detected_tf})")
                    data_frequency = detected_freq
                else:
                    logger.info("Data frequency not specified, defaulting to: daily")
                    click.echo("Data frequency not specified, defaulting to: daily")
                    data_frequency = 'daily'

            # Run backtest
            logger.info(f"Executing backtest (start={start}, end={end}, bundle={bundle})")
            click.echo("Executing backtest...")
            if validate_calendar:
                logger.info("Strict calendar validation enabled")
                click.echo("🔍 Strict calendar validation enabled (--validate-calendar)")
            perf, trading_calendar = run_backtest(
                strategy_name=strategy,
                start_date=start,
                end_date=end,
                capital_base=capital,
                bundle=bundle,
                data_frequency=data_frequency,
                asset_class=asset_class,
                validate_calendar=validate_calendar
            )

            # v1.11.0: Ensure capital_base is in params for portfolio_value reconstruction
            # (needed when metrics_set='none' is used for FOREX calendars)
            if capital is not None:
                if 'backtest' not in params:
                    params['backtest'] = {}
                params['backtest']['capital_base'] = capital
                logger.debug(f"Set capital_base in params: {capital}")
            elif 'backtest' not in params or 'capital_base' not in params.get('backtest', {}):
                # Try to get from settings as fallback
                from lib.config import load_settings
                settings = load_settings()
                default_capital = settings.get('backtest', {}).get('capital_base', 100000.0)
                if 'backtest' not in params:
                    params['backtest'] = {}
                params['backtest']['capital_base'] = default_capital
                logger.info(f"Using default capital_base from settings: {default_capital}")

            # Save results
            logger.info("Saving backtest results")
            click.echo("Saving results...")
            result_dir = save_results(
                strategy_name=strategy,
                perf=perf,
                params=params,
                trading_calendar=trading_calendar,
                result_type='backtest'
            )
            logger.info(f"Backtest complete, results saved to: {result_dir}")
            
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
                # v1.0.7: Metrics are now in percentage format, use .2f instead of .2%
                click.echo(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
                click.echo(f"  Annual Return: {metrics.get('annual_return', 0):.2f}%")
                click.echo(f"  Sharpe Ratio: {metrics.get('sharpe', 0):.2f}")
                click.echo(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            
            click.echo("=" * 60)
        
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            click.echo(f"✗ Error: {e}", err=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

