---
name: zrl-position-sizer
description: This skill should be used when implementing position sizing logic for Zipline strategies. It provides algorithms for equal-weight, risk-parity, Kelly criterion, volatility-targeting, and other professional position sizing methods.
---

# Zipline Position Sizer

Professional position sizing algorithms for portfolio construction.

## Purpose

Determine optimal position sizes based on risk budgets, signal strength, volatility, and portfolio constraints. Convert trading signals into executable position weights.

## When to Use

- Implementing portfolio construction logic
- Managing position-level risk
- Optimizing capital allocation
- Building risk-adjusted portfolios

## Position Sizing Methods

### 1. Equal Weight

Simplest approach - equal allocation to all positions:

```python
class EqualWeightSizer:
    """Equal weight position sizing."""
    
    def __init__(self, max_positions: int = 20):
        self.max_positions = max_positions
    
    def calculate_weights(self, assets: list, context, data) -> dict:
        n = min(len(assets), self.max_positions)
        weight = 1.0 / n if n > 0 else 0
        return {asset: weight for asset in assets[:n]}
```

### 2. Signal-Weighted

Position size proportional to signal strength:

```python
class SignalWeightSizer:
    """Position size based on signal strength."""
    
    def __init__(self, max_position: float = 0.10, min_position: float = 0.01):
        self.max_position = max_position
        self.min_position = min_position
    
    def calculate_weights(self, signals: pd.Series, context, data) -> dict:
        # Normalize signals to sum to 1
        abs_signals = signals.abs()
        total = abs_signals.sum()
        
        if total == 0:
            return {}
        
        weights = {}
        for asset, signal in signals.items():
            raw_weight = abs(signal) / total
            # Apply bounds
            weight = np.clip(raw_weight, self.min_position, self.max_position)
            # Preserve sign for long/short
            weights[asset] = weight * np.sign(signal)
        
        return weights
```

### 3. Volatility-Targeted

Normalize by volatility for equal risk contribution:

```python
class VolatilityTargetSizer:
    """Target equal volatility contribution per position."""
    
    def __init__(self, target_vol: float = 0.02, lookback: int = 20):
        self.target_vol = target_vol  # Daily vol target per position
        self.lookback = lookback
    
    def calculate_weights(self, assets: list, context, data) -> dict:
        weights = {}
        
        for asset in assets:
            prices = data.history(asset, 'close', self.lookback + 1, '1d')
            returns = prices.pct_change().dropna()
            vol = returns.std()
            
            if vol > 0:
                # Weight inversely proportional to volatility
                weight = self.target_vol / vol
                weights[asset] = min(weight, 0.20)  # Cap at 20%
            else:
                weights[asset] = 0.0
        
        # Normalize to sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights
```

### 4. Risk Parity

Equal risk contribution from each position:

```python
class RiskParitySizer:
    """Risk parity position sizing."""
    
    def __init__(self, lookback: int = 60):
        self.lookback = lookback
    
    def calculate_weights(self, assets: list, context, data) -> dict:
        if len(assets) < 2:
            return {assets[0]: 1.0} if assets else {}
        
        # Get returns
        prices = data.history(assets, 'close', self.lookback + 1, '1d')
        returns = prices.pct_change().dropna()
        
        # Calculate volatilities
        vols = returns.std()
        
        # Inverse volatility weights
        inv_vols = 1 / vols.replace(0, 1e-6)
        weights = inv_vols / inv_vols.sum()
        
        return weights.to_dict()
```

### 5. Kelly Criterion

Optimal sizing based on expected returns and variance:

```python
class KellySizer:
    """Kelly criterion position sizing."""
    
    def __init__(self, lookback: int = 252, kelly_fraction: float = 0.25):
        self.lookback = lookback
        self.kelly_fraction = kelly_fraction  # Fractional Kelly for safety
    
    def calculate_weight(self, asset, context, data) -> float:
        prices = data.history(asset, 'close', self.lookback + 1, '1d')
        returns = prices.pct_change().dropna()
        
        mean_return = returns.mean()
        variance = returns.var()
        
        if variance == 0:
            return 0.0
        
        # Kelly formula: f = μ / σ²
        full_kelly = mean_return / variance
        
        # Apply fractional Kelly
        weight = full_kelly * self.kelly_fraction
        
        # Bound the result
        return np.clip(weight, -0.5, 0.5)
```

### 6. Maximum Diversification

Maximize diversification ratio:

```python
class MaxDiversificationSizer:
    """Maximize portfolio diversification."""
    
    def __init__(self, lookback: int = 60):
        self.lookback = lookback
    
    def calculate_weights(self, assets: list, context, data) -> dict:
        from scipy.optimize import minimize
        
        prices = data.history(assets, 'close', self.lookback + 1, '1d')
        returns = prices.pct_change().dropna()
        
        cov_matrix = returns.cov().values
        vols = returns.std().values
        n = len(assets)
        
        def neg_div_ratio(w):
            port_vol = np.sqrt(w @ cov_matrix @ w)
            weighted_vols = w @ vols
            return -weighted_vols / port_vol if port_vol > 0 else 0
        
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 0.3) for _ in range(n)]
        x0 = np.ones(n) / n
        
        result = minimize(neg_div_ratio, x0, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return dict(zip(assets, result.x))
```

## Portfolio Constraints

### Apply Constraints

```python
class ConstrainedSizer:
    """Apply portfolio constraints to weights."""
    
    def __init__(self, 
                 max_position: float = 0.10,
                 max_sector_weight: float = 0.30,
                 max_gross_exposure: float = 1.0,
                 max_net_exposure: float = 0.20):
        self.max_position = max_position
        self.max_sector = max_sector_weight
        self.max_gross = max_gross_exposure
        self.max_net = max_net_exposure
    
    def apply_constraints(self, weights: dict, sectors: dict = None) -> dict:
        # Position limit
        for asset, weight in weights.items():
            weights[asset] = np.clip(weight, -self.max_position, self.max_position)
        
        # Sector limit
        if sectors:
            sector_weights = {}
            for asset, weight in weights.items():
                sector = sectors.get(asset, 'Other')
                sector_weights[sector] = sector_weights.get(sector, 0) + abs(weight)
            
            for sector, total in sector_weights.items():
                if total > self.max_sector:
                    scale = self.max_sector / total
                    for asset, weight in weights.items():
                        if sectors.get(asset) == sector:
                            weights[asset] *= scale
        
        # Gross exposure limit
        gross = sum(abs(w) for w in weights.values())
        if gross > self.max_gross:
            scale = self.max_gross / gross
            weights = {k: v * scale for k, v in weights.items()}
        
        return weights
```

## Integration Pattern

```python
def initialize(context):
    context.sizer = VolatilityTargetSizer(target_vol=0.015)
    context.constraints = ConstrainedSizer(max_position=0.10)

def rebalance(context, data):
    # Get signal-selected assets
    assets = context.longs
    
    # Calculate raw weights
    raw_weights = context.sizer.calculate_weights(assets, context, data)
    
    # Apply constraints
    final_weights = context.constraints.apply_constraints(raw_weights)
    
    # Execute
    for asset in context.portfolio.positions:
        if asset not in final_weights:
            order_target_percent(asset, 0)
    
    for asset, weight in final_weights.items():
        if data.can_trade(asset):
            order_target_percent(asset, weight)
```

## Script Reference

### analyze_sizing.py

Analyze position sizing impact:

```bash
python scripts/analyze_sizing.py \
    --method volatility_target \
    --backtest results.csv \
    --output sizing_analysis.html
```

## References

See `references/sizing_formulas.md` for mathematical details.
See `references/constraint_specs.md` for constraint definitions.
