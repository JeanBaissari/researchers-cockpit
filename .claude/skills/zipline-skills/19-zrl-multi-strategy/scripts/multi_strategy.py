#!/usr/bin/env python3
"""
Multi-strategy management framework for Zipline.
Combines multiple strategies with various allocation methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
    
    def initialize(self, context):
        """Setup strategy state. Override in subclass."""
        pass
    
    @abstractmethod
    def generate_signals(self, context, data) -> Dict:
        """Generate trading signals for assets."""
        pass
    
    @abstractmethod
    def get_target_weights(self, context, data) -> Dict:
        """Get target portfolio weights for this strategy."""
        pass


class MomentumStrategy(BaseStrategy):
    """Simple momentum strategy."""
    
    def __init__(self, name: str = 'momentum', params: dict = None):
        default_params = {'period': 20, 'universe': [], 'top_n': 10}
        default_params.update(params or {})
        super().__init__(name, default_params)
    
    def initialize(self, context):
        setattr(context, f'{self.name}_universe', self.params.get('universe', []))
    
    def generate_signals(self, context, data) -> Dict:
        universe = getattr(context, f'{self.name}_universe', [])
        period = self.params.get('period', 20)
        signals = {}
        
        for asset in universe:
            try:
                if data.can_trade(asset):
                    prices = data.history(asset, 'price', period + 1, '1d')
                    momentum = (prices.iloc[-1] / prices.iloc[0]) - 1
                    signals[asset] = momentum
            except:
                continue
        
        return signals
    
    def get_target_weights(self, context, data) -> Dict:
        signals = self.generate_signals(context, data)
        if not signals:
            return {}
        
        # Rank by momentum
        ranked = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        top_n = self.params.get('top_n', 10)
        selected = ranked[:top_n]
        
        # Equal weight among selected
        weight = 1.0 / len(selected) if selected else 0
        return {asset: weight for asset, _ in selected}


class MeanReversionStrategy(BaseStrategy):
    """Simple mean reversion strategy."""
    
    def __init__(self, name: str = 'mean_rev', params: dict = None):
        default_params = {'period': 20, 'zscore_entry': 2.0, 'universe': []}
        default_params.update(params or {})
        super().__init__(name, default_params)
    
    def initialize(self, context):
        setattr(context, f'{self.name}_universe', self.params.get('universe', []))
    
    def generate_signals(self, context, data) -> Dict:
        universe = getattr(context, f'{self.name}_universe', [])
        period = self.params.get('period', 20)
        signals = {}
        
        for asset in universe:
            try:
                if data.can_trade(asset):
                    prices = data.history(asset, 'price', period, '1d')
                    mean = prices.mean()
                    std = prices.std()
                    if std > 0:
                        zscore = (prices.iloc[-1] - mean) / std
                        signals[asset] = -zscore  # Negative: buy oversold, sell overbought
            except:
                continue
        
        return signals
    
    def get_target_weights(self, context, data) -> Dict:
        signals = self.generate_signals(context, data)
        zscore_entry = self.params.get('zscore_entry', 2.0)
        
        weights = {}
        for asset, signal in signals.items():
            if signal > zscore_entry:  # Oversold (negative zscore flipped)
                weights[asset] = 0.1
            elif signal < -zscore_entry:  # Overbought
                weights[asset] = -0.1  # Short
        
        return weights


class BaseAllocator(ABC):
    """Base class for strategy allocators."""
    
    @abstractmethod
    def allocate(self, strategies: List[BaseStrategy], 
                context, data) -> Dict[str, float]:
        """Return allocation weights for each strategy."""
        pass


class EqualWeightAllocator(BaseAllocator):
    """Equal allocation across all strategies."""
    
    def allocate(self, strategies, context, data) -> Dict[str, float]:
        n = len(strategies)
        if n == 0:
            return {}
        return {s.name: 1.0 / n for s in strategies}


class RiskParityAllocator(BaseAllocator):
    """Risk parity allocation based on inverse volatility."""
    
    def __init__(self, lookback: int = 60, target_vol: float = 0.10):
        self.lookback = lookback
        self.target_vol = target_vol
    
    def allocate(self, strategies, context, data) -> Dict[str, float]:
        vols = {}
        
        for strat in strategies:
            returns = getattr(context, f'{strat.name}_returns', [])
            if len(returns) >= self.lookback:
                vol = np.std(returns[-self.lookback:]) * np.sqrt(252)
                vols[strat.name] = max(vol, 0.01)  # Floor at 1%
            else:
                vols[strat.name] = self.target_vol
        
        # Inverse volatility weights
        inv_vols = {k: 1/v for k, v in vols.items()}
        total = sum(inv_vols.values())
        
        if total == 0:
            return EqualWeightAllocator().allocate(strategies, context, data)
        
        return {k: v/total for k, v in inv_vols.items()}


class PerformanceAllocator(BaseAllocator):
    """Allocate based on recent risk-adjusted performance."""
    
    def __init__(self, lookback: int = 126, min_weight: float = 0.05):
        self.lookback = lookback
        self.min_weight = min_weight
    
    def allocate(self, strategies, context, data) -> Dict[str, float]:
        sharpes = {}
        
        for strat in strategies:
            returns = getattr(context, f'{strat.name}_returns', [])
            if len(returns) >= self.lookback:
                recent = returns[-self.lookback:]
                mean_ret = np.mean(recent)
                std_ret = np.std(recent)
                sharpe = np.sqrt(252) * mean_ret / std_ret if std_ret > 0 else 0
                sharpes[strat.name] = max(sharpe, 0)  # Floor negative
            else:
                sharpes[strat.name] = 0
        
        total = sum(sharpes.values())
        
        if total == 0:
            return EqualWeightAllocator().allocate(strategies, context, data)
        
        weights = {}
        for name, sharpe in sharpes.items():
            weights[name] = max(sharpe / total, self.min_weight)
        
        # Renormalize
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}


class MultiStrategyManager:
    """Manage multiple trading strategies."""
    
    def __init__(self, strategies: List[BaseStrategy],
                 allocator: BaseAllocator = None,
                 max_leverage: float = 1.0,
                 net_exposure_limit: float = 1.0):
        self.strategies = strategies
        self.allocator = allocator or EqualWeightAllocator()
        self.max_leverage = max_leverage
        self.net_exposure_limit = net_exposure_limit
        self.strategy_allocations = {}
    
    def initialize(self, context):
        """Initialize all strategies and tracking."""
        for strat in self.strategies:
            strat.initialize(context)
            setattr(context, f'{strat.name}_returns', [])
            setattr(context, f'{strat.name}_value', 1.0)
        
        # Initial equal allocation
        self.strategy_allocations = {
            s.name: 1.0 / len(self.strategies) 
            for s in self.strategies
        }
    
    def update_allocations(self, context, data):
        """Update strategy allocations."""
        self.strategy_allocations = self.allocator.allocate(
            self.strategies, context, data
        )
    
    def get_strategy_weights(self, context, data) -> Dict[str, float]:
        """Get current strategy allocation weights."""
        return self.strategy_allocations.copy()
    
    def get_combined_targets(self, context, data) -> Dict:
        """
        Get combined target weights across all strategies.
        Weights are scaled by strategy allocation.
        """
        combined = {}
        
        for strat in self.strategies:
            strat_alloc = self.strategy_allocations.get(strat.name, 0)
            if strat_alloc <= 0:
                continue
            
            targets = strat.get_target_weights(context, data)
            
            for asset, weight in targets.items():
                scaled_weight = weight * strat_alloc
                if asset in combined:
                    combined[asset] += scaled_weight
                else:
                    combined[asset] = scaled_weight
        
        # Apply constraints
        combined = self._apply_constraints(combined)
        
        return combined
    
    def _apply_constraints(self, weights: Dict) -> Dict:
        """Apply leverage and exposure constraints."""
        if not weights:
            return weights
        
        # Calculate gross and net exposure
        gross = sum(abs(w) for w in weights.values())
        net = sum(weights.values())
        
        # Scale down if gross > max leverage
        if gross > self.max_leverage:
            scale = self.max_leverage / gross
            weights = {k: v * scale for k, v in weights.items()}
        
        # Adjust if net exposure > limit
        net = sum(weights.values())
        if abs(net) > self.net_exposure_limit:
            # Scale net exposure
            adjustment = (self.net_exposure_limit - abs(net)) / len(weights)
            weights = {k: v + adjustment * np.sign(v) for k, v in weights.items()}
        
        return weights
    
    def track_performance(self, context, data):
        """Track hypothetical performance of each strategy."""
        for strat in self.strategies:
            targets = strat.get_target_weights(context, data)
            
            daily_return = 0.0
            for asset, weight in targets.items():
                try:
                    if data.can_trade(asset):
                        prices = data.history(asset, 'price', 2, '1d')
                        ret = prices.pct_change().iloc[-1]
                        daily_return += weight * ret
                except:
                    continue
            
            returns_list = getattr(context, f'{strat.name}_returns', [])
            returns_list.append(daily_return)
            setattr(context, f'{strat.name}_returns', returns_list[-252:])
            
            current_value = getattr(context, f'{strat.name}_value', 1.0)
            setattr(context, f'{strat.name}_value', current_value * (1 + daily_return))
    
    def get_strategy_stats(self, context) -> pd.DataFrame:
        """Get performance statistics for each strategy."""
        stats = []
        
        for strat in self.strategies:
            returns = getattr(context, f'{strat.name}_returns', [])
            if not returns:
                continue
            
            returns = np.array(returns)
            value = getattr(context, f'{strat.name}_value', 1.0)
            
            stats.append({
                'strategy': strat.name,
                'allocation': self.strategy_allocations.get(strat.name, 0),
                'total_return': value - 1,
                'volatility': np.std(returns) * np.sqrt(252),
                'sharpe': np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
            })
        
        return pd.DataFrame(stats)


def analyze_correlations(strategy_returns: Dict[str, List[float]]) -> pd.DataFrame:
    """Analyze correlations between strategy returns."""
    df = pd.DataFrame(strategy_returns)
    return df.corr()


def print_summary(manager: MultiStrategyManager, context):
    """Print multi-strategy summary."""
    print("\n" + "=" * 50)
    print("MULTI-STRATEGY SUMMARY")
    print("=" * 50)
    
    stats = manager.get_strategy_stats(context)
    print(stats.to_string(index=False))
    
    print("\nAllocations:")
    for name, alloc in manager.strategy_allocations.items():
        print(f"  {name}: {alloc:.1%}")
    
    print("\nCorrelations:")
    returns = {s.name: getattr(context, f'{s.name}_returns', []) 
               for s in manager.strategies}
    corr = analyze_correlations(returns)
    print(corr.to_string())


if __name__ == '__main__':
    # Example usage
    print("Multi-Strategy Framework")
    print("Import this module and use the classes in your Zipline algorithm.")
    print("\nExample:")
    print("""
from multi_strategy import (
    MultiStrategyManager, 
    MomentumStrategy,
    MeanReversionStrategy,
    RiskParityAllocator
)

manager = MultiStrategyManager(
    strategies=[
        MomentumStrategy('mom', {'period': 20}),
        MeanReversionStrategy('mr', {'period': 10}),
    ],
    allocator=RiskParityAllocator(target_vol=0.12),
)
""")
