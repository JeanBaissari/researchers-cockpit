# Factors

> Pipeline expressions that produce numerical outputs.

## Factor Class

```python
class zipline.pipeline.Factor(
    inputs=NotSpecified,
    outputs=NotSpecified,
    window_length=NotSpecified,
    mask=NotSpecified,
    domain=NotSpecified
)
```

Factors are the most common Pipeline term. They compute numerical results that can be combined with mathematical operators.

---

## Mathematical Operations

### Arithmetic

```python
f1 = SomeFactor()
f2 = AnotherFactor()

combined = f1 + f2
difference = f1 - f2
product = f1 * f2
ratio = f1 / f2
average = (f1 + f2) / 2.0
```

### Comparisons (Return Filters)

```python
filter1 = f1 > f2
filter2 = f1 >= 10.0
filter3 = f1.eq(f2)  # f1 == f2
filter4 = f1 != 0
```

---

## Key Methods

### rank()

Convert to cross-sectional ranks.

```python
factor.rank(method='ordinal', ascending=True, mask=NotSpecified, groupby=NotSpecified)
```

```python
# Rank all assets by momentum (1 = lowest)
momentum = Returns(window_length=10)
ranked = momentum.rank()

# Descending (1 = highest)
ranked_desc = momentum.rank(ascending=False)
```

### zscore()

Normalize to z-scores (mean=0, std=1).

```python
factor.zscore(mask=NotSpecified, groupby=NotSpecified)
```

```python
# Normalize momentum across all assets
normalized = momentum.zscore()
```

### demean()

Subtract cross-sectional mean.

```python
factor.demean(mask=NotSpecified, groupby=NotSpecified)
```

```python
# Remove market average
demeaned = momentum.demean()
```

### top() / bottom()

Select top or bottom N assets.

```python
factor.top(N, mask=NotSpecified, groupby=NotSpecified)
factor.bottom(N, mask=NotSpecified, groupby=NotSpecified)
```

```python
# Top 100 by volume
volume = AverageDollarVolume(window_length=20)
top_100 = volume.top(100)  # Returns Filter
```

### percentile_between()

Select assets in percentile range.

```python
factor.percentile_between(min_percentile, max_percentile, mask=NotSpecified)
```

```python
# Middle 50% by volume
mid_volume = volume.percentile_between(25, 75)
```

---

## Missing Data Methods

### isnull() / notnull()

Check for missing values.

```python
has_data = factor.notnull()  # Returns Filter
missing = factor.isnull()    # Returns Filter
```

### isnan() / notnan()

Check for NaN values.

```python
valid = factor.notnan()  # Returns Filter
```

### fillna()

Replace missing values.

```python
factor.fillna(fill_value)
factor.fillna(other_factor)
```

```python
# Replace NaN with 0
filled = momentum.fillna(0)

# Replace with another factor
filled = momentum.fillna(other_momentum)
```

### clip()

Clip values to range.

```python
factor.clip(min_bound, max_bound)
```

```python
# Limit momentum to [-0.5, 0.5]
clipped = momentum.clip(-0.5, 0.5)
```

---

## Windowed Computations

### winsorize()

Clip to percentile boundaries.

```python
factor.winsorize(min_percentile, max_percentile, mask=NotSpecified, groupby=NotSpecified)
```

```python
# Remove outliers (1st and 99th percentile)
winsorized = momentum.winsorize(0.01, 0.99)
```

---

## Example: Multi-Factor Model

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume
from zipline.pipeline.data import USEquityPricing

def make_pipeline():
    # Factors
    momentum = Returns(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    # Normalize factors
    momentum_z = momentum.zscore()
    volume_z = volume.zscore()
    
    # Combine (simple alpha)
    alpha = 0.7 * momentum_z + 0.3 * volume_z
    
    # Filters
    liquid = volume.top(1000)
    valid = momentum.notnull() & volume.notnull()
    
    # Top 50 by combined alpha
    longs = alpha.top(50, mask=liquid & valid)
    shorts = alpha.bottom(50, mask=liquid & valid)
    
    return Pipeline(
        columns={
            'alpha': alpha,
            'momentum': momentum,
            'volume': volume,
            'longs': longs,
            'shorts': shorts,
        },
        screen=liquid & valid
    )
```

---

## Factor with Groupby

```python
from zipline.pipeline.classifiers import Classifier

# Sector classifier (example)
sector = SomeClassifier()

# Rank within sector
sector_rank = momentum.rank(groupby=sector)

# Z-score within sector
sector_zscore = momentum.zscore(groupby=sector)
```

---

## See Also

- [Pipeline Overview](pipeline_overview.md)
- [Custom Factors](custom_factors.md)
- [Built-in Factors](builtin_factors.md)
- [Filters](filters.md)
