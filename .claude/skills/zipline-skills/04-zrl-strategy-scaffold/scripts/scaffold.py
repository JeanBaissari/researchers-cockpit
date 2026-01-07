#!/usr/bin/env python3
"""
Generate professional Zipline strategy scaffolds.
Creates complete strategy structure with templates.
"""
import argparse
from pathlib import Path
from datetime import datetime

STRATEGY_TEMPLATE = '''"""
{name}
Generated: {date}
Type: {strategy_type}
"""
from zipline.api import (
    order_target_percent, schedule_function,
    date_rules, time_rules, record, get_datetime
)
{pipeline_imports}
from config import StrategyConfig


def initialize(context):
    """Initialize strategy state and configuration."""
    context.config = StrategyConfig()
    context.config.validate()
    {pipeline_attach}
    schedule_function(
        rebalance,
        date_rule=context.config.rebalance_date_rule,
        time_rule=context.config.rebalance_time_rule
    )


{before_trading_start}

def rebalance(context, data):
    """Execute rebalancing logic."""
    {rebalance_logic}


def handle_data(context, data):
    """Process each bar."""
    record(
        portfolio_value=context.portfolio.portfolio_value,
        positions=len(context.portfolio.positions)
    )


def analyze(context, perf):
    """Post-backtest analysis."""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    perf['portfolio_value'].plot(ax=axes[0], title='Portfolio Value')
    perf['returns'].cumsum().plot(ax=axes[1], title='Cumulative Returns')
    plt.tight_layout()
    plt.savefig('results.png')
    print(f"Final portfolio value: ${{perf['portfolio_value'].iloc[-1]:,.2f}}")
'''

CONFIG_TEMPLATE = '''"""Configuration for {name}."""
from dataclasses import dataclass, field
from zipline.api import date_rules, time_rules

@dataclass
class StrategyConfig:
    """Strategy configuration."""
    
    name: str = "{name}"
    version: str = "1.0.0"
    
    # Universe parameters
    universe_size: int = 100
    min_price: float = 5.0
    min_volume: float = 1_000_000
    
    # Signal parameters
    lookback_window: int = 20
    
    # Position sizing
    max_position_size: float = 0.05
    max_leverage: float = 1.0
    
    # Scheduling
    rebalance_date_rule: object = field(default_factory=lambda: date_rules.week_start())
    rebalance_time_rule: object = field(default_factory=lambda: time_rules.market_open(hours=1))
    
    def validate(self):
        """Validate configuration."""
        assert 0 < self.max_position_size <= 1.0, "Invalid position size"
        assert self.universe_size > 0, "Invalid universe size"
        return True
'''

PIPELINE_TEMPLATE = '''"""Pipeline definition for {name}."""
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume


def make_pipeline(config):
    """Build the main pipeline."""
    returns = Returns(window_length=config.lookback_window)
    volume = AverageDollarVolume(window_length=20)
    
    universe = volume.top(config.universe_size)
    longs = returns.top(10, mask=universe)
    
    return Pipeline(
        columns={{
            'returns': returns,
            'longs': longs,
        }},
        screen=longs
    )
'''

TEST_TEMPLATE = '''"""Tests for {name}."""
import pytest
import pandas as pd


def test_config_validation():
    """Test configuration validation."""
    from config import StrategyConfig
    
    config = StrategyConfig()
    assert config.validate()


def test_strategy_imports():
    """Test all imports work."""
    from strategy import initialize, handle_data, rebalance
    assert callable(initialize)
    assert callable(handle_data)
'''


def create_strategy(name: str, strategy_type: str, output_dir: Path, include_tests: bool):
    """Create strategy scaffold."""
    strategy_dir = output_dir / name
    strategy_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine template variations
    pipeline_imports = ""
    pipeline_attach = ""
    before_trading = ""
    rebalance_logic = "pass  # Add rebalance logic"
    
    if strategy_type in ('pipeline', 'multi_asset'):
        pipeline_imports = """from zipline.api import attach_pipeline, pipeline_output
from pipeline import make_pipeline"""
        pipeline_attach = "attach_pipeline(make_pipeline(context.config), 'main')"
        before_trading = '''def before_trading_start(context, data):
    """Get pipeline output."""
    context.output = pipeline_output('main')
    context.longs = context.output[context.output['longs']].index.tolist()

'''
        rebalance_logic = '''weight = 1.0 / max(len(context.longs), 1)
    
    # Exit positions not in longs
    for asset in context.portfolio.positions:
        if asset not in context.longs:
            order_target_percent(asset, 0)
    
    # Enter new positions
    for asset in context.longs:
        if data.can_trade(asset):
            order_target_percent(asset, weight)'''
    
    # Generate strategy.py
    strategy_content = STRATEGY_TEMPLATE.format(
        name=name,
        date=datetime.now().strftime('%Y-%m-%d'),
        strategy_type=strategy_type,
        pipeline_imports=pipeline_imports,
        pipeline_attach=pipeline_attach,
        before_trading_start=before_trading,
        rebalance_logic=rebalance_logic
    )
    
    (strategy_dir / 'strategy.py').write_text(strategy_content)
    (strategy_dir / 'config.py').write_text(CONFIG_TEMPLATE.format(name=name))
    (strategy_dir / '__init__.py').write_text(f'"""{name} strategy package."""\n')
    
    if strategy_type in ('pipeline', 'multi_asset'):
        (strategy_dir / 'pipeline.py').write_text(PIPELINE_TEMPLATE.format(name=name))
    
    if include_tests:
        tests_dir = strategy_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / '__init__.py').write_text('')
        (tests_dir / 'test_strategy.py').write_text(TEST_TEMPLATE.format(name=name))
    
    return strategy_dir


def main():
    parser = argparse.ArgumentParser(description='Generate Zipline strategy scaffold')
    parser.add_argument('--name', required=True, help='Strategy name')
    parser.add_argument('--type', choices=['simple', 'pipeline', 'scheduled', 'multi_asset'],
                       default='pipeline', help='Strategy type')
    parser.add_argument('--output', type=Path, default=Path('.'), help='Output directory')
    parser.add_argument('--include-tests', action='store_true', help='Include test files')
    parser.add_argument('--include-notebooks', action='store_true', help='Include Jupyter notebooks')
    args = parser.parse_args()
    
    strategy_dir = create_strategy(args.name, args.type, args.output, args.include_tests)
    
    print(f"✅ Created strategy scaffold: {strategy_dir}")
    print(f"\nGenerated files:")
    for f in sorted(strategy_dir.rglob('*.py')):
        print(f"  • {f.relative_to(strategy_dir)}")
    
    print(f"\nNext steps:")
    print(f"1. Edit config.py with your parameters")
    print(f"2. Implement signal logic in strategy.py")
    print(f"3. Run backtest: zipline run -f {strategy_dir}/strategy.py")


if __name__ == '__main__':
    main()
