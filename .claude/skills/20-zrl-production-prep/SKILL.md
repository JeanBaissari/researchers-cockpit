---
name: zrl-production-prep
description: This skill should be used when preparing strategies for production deployment, implementing monitoring, logging, and failsafes. It provides patterns for transitioning from backtest to live trading with proper infrastructure.
---

# Zipline Production Prep

Prepare backtested strategies for production deployment with monitoring and safeguards.

## Purpose

Transform backtested strategies into production-ready systems with proper logging, monitoring, error handling, and operational safeguards.

## When to Use

- Transitioning from backtest to paper trading
- Deploying strategies to live trading
- Implementing monitoring and alerting
- Setting up operational safeguards
- Creating production deployment checklists

## Production Readiness Checklist

### Pre-Deployment

- [ ] Walk-forward validation completed
- [ ] Out-of-sample performance verified
- [ ] Parameter stability confirmed
- [ ] Risk limits defined and tested
- [ ] Commission/slippage models validated
- [ ] Data pipeline tested end-to-end
- [ ] Failover procedures documented

### Code Quality

- [ ] All functions have docstrings
- [ ] Type hints on critical functions
- [ ] Error handling for all external calls
- [ ] Logging at appropriate levels
- [ ] Configuration externalized
- [ ] Secrets management implemented
- [ ] Unit tests passing

### Operational

- [ ] Monitoring dashboards created
- [ ] Alerting rules configured
- [ ] Runbooks written
- [ ] Backup procedures tested
- [ ] Recovery procedures documented
- [ ] On-call rotation established

## Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Market     │    │   Strategy   │    │   Broker     │  │
│  │   Data Feed  │───▶│   Engine     │───▶│   Gateway    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │          │
│         ▼                   ▼                    ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    MONITORING LAYER                   │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐     │  │
│  │  │Logging │  │Metrics │  │Alerts  │  │Health  │     │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Workflow

### Step 1: Add Production Logging

```python
from production import ProductionLogger

logger = ProductionLogger(
    name='my_strategy',
    log_file='logs/strategy.log',
    level='INFO',
    rotation='daily'
)

def initialize(context):
    context.logger = logger
    context.logger.info("Strategy initialized")

def handle_data(context, data):
    context.logger.debug(f"Processing bar at {data.current_session}")
```

### Step 2: Implement Monitoring

```python
from production import MetricsCollector

metrics = MetricsCollector(
    strategy_name='my_strategy',
    export_interval=60  # seconds
)

def handle_data(context, data):
    metrics.record('orders_placed', len(context.orders))
    metrics.record('portfolio_value', context.portfolio.portfolio_value)
    metrics.record_timing('signal_generation')
```

### Step 3: Add Safeguards

```python
from production import SafetyMonitor

safety = SafetyMonitor(
    max_daily_loss=0.02,        # 2% max daily loss
    max_drawdown=0.10,          # 10% max drawdown
    max_position_size=0.15,     # 15% max per position
    max_daily_orders=100,       # Order limit
    circuit_breaker_threshold=0.05
)

def handle_data(context, data):
    if safety.check_halt_conditions(context):
        context.logger.critical("HALT: Safety limits breached")
        safety.halt_trading(context)
        return
```

## Script Reference

### validate_production.py

Validate strategy is production-ready:

```bash
python scripts/validate_production.py \
    --strategy strategy.py \
    --config production.yaml \
    --output validation_report.html
```

### generate_config.py

Generate production configuration:

```bash
python scripts/generate_config.py \
    --strategy strategy.py \
    --env production \
    --output config/production.yaml
```

### health_check.py

Run health checks on deployed system:

```bash
python scripts/health_check.py \
    --config production.yaml \
    --verbose
```

## ProductionLogger Class

```python
class ProductionLogger:
    """Production-grade logging with rotation and formatting."""
    
    def __init__(self, name: str,
                 log_file: str = None,
                 level: str = 'INFO',
                 rotation: str = 'daily',
                 retention_days: int = 30):
        """
        Parameters
        ----------
        name : str
            Logger name
        log_file : str
            Path to log file
        level : str
            Logging level
        rotation : str
            'daily', 'size', or 'hourly'
        retention_days : int
            Days to keep old logs
        """
    
    def info(self, msg: str, **kwargs)
    def warning(self, msg: str, **kwargs)
    def error(self, msg: str, exc_info=True, **kwargs)
    def critical(self, msg: str, **kwargs)
    def trade(self, order_id: str, asset: str, amount: int, price: float)
```

## SafetyMonitor Class

```python
class SafetyMonitor:
    """Monitor and enforce safety limits."""
    
    def __init__(self,
                 max_daily_loss: float = 0.02,
                 max_drawdown: float = 0.10,
                 max_position_size: float = 0.20,
                 max_daily_orders: int = 100,
                 max_leverage: float = 1.0,
                 circuit_breaker_threshold: float = 0.05):
        """
        Parameters
        ----------
        max_daily_loss : float
            Maximum allowed daily loss (fraction)
        max_drawdown : float
            Maximum allowed drawdown from peak
        max_position_size : float
            Maximum weight per position
        max_daily_orders : int
            Maximum orders per day
        max_leverage : float
            Maximum gross leverage
        circuit_breaker_threshold : float
            Market move that triggers circuit breaker
        """
    
    def check_halt_conditions(self, context) -> bool
    def check_order(self, context, asset, amount) -> Tuple[bool, str]
    def halt_trading(self, context)
    def reset_daily_counters(self)
```

## Configuration Management

### Production Configuration

```yaml
# production.yaml
strategy:
  name: momentum_strategy
  version: 1.2.3
  bundle: production-data
  capital_base: 1000000

execution:
  broker: interactive_brokers
  paper_trading: false
  max_slippage: 0.001

risk:
  max_daily_loss: 0.02
  max_drawdown: 0.10
  max_position_size: 0.15
  max_leverage: 1.0
  max_daily_orders: 100

monitoring:
  metrics_port: 9090
  log_level: INFO
  log_rotation: daily
  alert_channels:
    - slack
    - email

alerts:
  daily_loss_warning: 0.01
  drawdown_warning: 0.05
  order_failure_threshold: 3
```

### Environment-Specific Settings

```python
from production import ConfigManager

config = ConfigManager()
config.load('config/base.yaml')
config.load(f'config/{environment}.yaml', override=True)

# Access settings
max_position = config.get('risk.max_position_size')
broker = config.get('execution.broker')
```

## Error Handling

### Retry Logic

```python
from production import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=2)
def fetch_market_data(symbol):
    """Fetch data with automatic retry."""
    return data_provider.get_quote(symbol)

@retry_with_backoff(max_retries=5, exceptions=(ConnectionError, TimeoutError))
def submit_order(order):
    """Submit order with retry on connection issues."""
    return broker.submit(order)
```

### Graceful Degradation

```python
def handle_data(context, data):
    try:
        signals = generate_signals(context, data)
    except SignalGenerationError as e:
        context.logger.error(f"Signal generation failed: {e}")
        signals = context.last_valid_signals  # Use cached
        context.degraded_mode = True
    
    try:
        execute_trades(context, signals)
    except BrokerError as e:
        context.logger.critical(f"Broker error: {e}")
        context.safety.halt_trading(context)
        alert_operations(e)
```

## Monitoring & Alerting

### Metrics Collection

```python
class MetricsCollector:
    """Collect and export strategy metrics."""
    
    def record(self, metric: str, value: float)
    def record_timing(self, operation: str)
    def increment(self, counter: str)
    def export_prometheus(self, port: int)
    def export_cloudwatch(self)
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| portfolio_value | Current portfolio value | -5% daily |
| daily_pnl | Profit/loss for day | < -2% |
| max_drawdown | Current drawdown | > 10% |
| orders_placed | Orders submitted | > 100/day |
| order_failures | Failed orders | > 3/hour |
| latency_ms | Order latency | > 500ms |
| data_lag_seconds | Data feed lag | > 60s |

### Alert Configuration

```python
from production import AlertManager

alerts = AlertManager()

alerts.add_rule(
    name='daily_loss_alert',
    condition=lambda ctx: ctx.daily_pnl < -0.02,
    severity='critical',
    channels=['slack', 'pagerduty']
)

alerts.add_rule(
    name='drawdown_warning',
    condition=lambda ctx: ctx.drawdown < -0.05,
    severity='warning',
    channels=['slack']
)
```

## Deployment Patterns

### Blue-Green Deployment

```yaml
# Deploy new version alongside current
blue:
  strategy: momentum_v1.2
  capital: 500000
  status: active

green:
  strategy: momentum_v1.3
  capital: 100000
  status: shadow  # Paper trading
```

### Gradual Rollout

```python
def allocate_capital(version: str, context):
    rollout_pct = context.config.get(f'rollout.{version}')
    return context.total_capital * rollout_pct

# Week 1: 10% to new version
# Week 2: 25% to new version
# Week 3: 50% to new version
# Week 4: 100% to new version (if metrics good)
```

## Pre-Market Checklist

```python
def pre_market_checks(context) -> bool:
    """Run all pre-market validation checks."""
    checks = [
        ('Data feed connected', check_data_connection()),
        ('Broker connected', check_broker_connection()),
        ('Sufficient capital', check_capital_available()),
        ('Risk limits set', check_risk_limits()),
        ('No stale positions', check_position_staleness()),
        ('Warmup complete', check_warmup_period()),
    ]
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        logger.info(f"Pre-market check: {name} {status}")
        all_passed = all_passed and passed
    
    return all_passed
```

## Post-Trade Analysis

```python
def end_of_day_analysis(context):
    """Generate end-of-day report."""
    report = {
        'date': context.current_date,
        'pnl': context.daily_pnl,
        'trades': len(context.todays_trades),
        'win_rate': calculate_win_rate(context.todays_trades),
        'max_position': context.max_position_today,
        'max_drawdown': context.max_drawdown_today,
    }
    
    # Compare to backtest expectations
    expected = context.backtest_expectations
    if abs(report['pnl'] - expected['avg_daily_pnl']) > 2 * expected['std_daily_pnl']:
        alert('Significant deviation from backtest', severity='warning')
    
    # Save report
    save_daily_report(report)
    
    return report
```

## Complete Production Template

```python
from zipline.api import *
from production import (
    ProductionLogger, SafetyMonitor, MetricsCollector,
    ConfigManager, AlertManager
)

# Load configuration
config = ConfigManager()
config.load('config/production.yaml')

# Initialize components
logger = ProductionLogger('my_strategy')
safety = SafetyMonitor(**config.get('risk'))
metrics = MetricsCollector('my_strategy')
alerts = AlertManager()

def initialize(context):
    context.logger = logger
    context.safety = safety
    context.metrics = metrics
    
    # Your strategy setup
    context.assets = symbols(*config.get('strategy.symbols'))
    
    schedule_function(
        pre_market_checks,
        date_rules.every_day(),
        time_rules.market_open(minutes=-30)
    )
    
    schedule_function(
        end_of_day_analysis,
        date_rules.every_day(),
        time_rules.market_close(minutes=15)
    )
    
    logger.info("Strategy initialized", version=config.get('strategy.version'))

def handle_data(context, data):
    # Safety check
    if safety.check_halt_conditions(context):
        return
    
    try:
        # Your trading logic
        signals = generate_signals(context, data)
        execute_trades(context, data, signals)
        
        # Record metrics
        metrics.record('portfolio_value', context.portfolio.portfolio_value)
        
    except Exception as e:
        logger.error(f"Error in handle_data: {e}", exc_info=True)
        safety.halt_trading(context)
        alerts.trigger('strategy_error', str(e))
```

## References

See `references/deployment_checklist.md` for complete checklist.
See `references/monitoring_setup.md` for monitoring configuration.
See `references/incident_response.md` for incident procedures.
