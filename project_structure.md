zipline-algo/
├── .agent/                                    # AI Agent Instructions
│   ├── README.md                              # "Read this first" for any agent
│   ├── strategy_creator.md                    # How to create strategies
│   ├── backtest_runner.md                     # How to execute backtests
│   ├── optimizer.md                           # How to optimize parameters
│   ├── analyst.md                             # How to analyze results
│   └── conventions.md                         # Naming, structure, style rules
│
├── config/
│   ├── settings.yaml                          # Global settings (capital, dates, etc.)
│   ├── data_sources.yaml                      # Data source configurations
│   ├── strategies/                            # Strategy parameter files
│   │   ├── btc_sma_cross.yaml                # BTC SMA crossover parameters
│   │   └── ...                                # Other strategy configs
│   └── assets/
│       ├── crypto.yaml                        # BTC, ETH, SOL pairs
│       ├── forex.yaml                         # EUR/USD, GBP/JPY, etc.
│       └── equities.yaml                      # SPY, QQQ, individual stocks
│
├── data/
│   ├── bundles/
│   │   ├── yahoo_crypto_daily/                # Yahoo Finance crypto bundle
│   │   ├── yahoo_forex_daily/                 # Yahoo Finance forex bundle
│   │   └── yahoo_equities_daily/              # Yahoo Finance equities bundle
│   ├── cache/
│   │   └── yahoo_2024_12_18.parquet          # Cached API responses
│   ├── processed/                             # Staging area for CSV files before bundle ingestion
│   │   ├── 1m/                                # 1-minute timeframe CSV files
│   │   │   └── {symbol}_{timeframe}_{start}_{end}_ready.csv
│   │   ├── 5m/                                # 5-minute timeframe CSV files
│   │   ├── 15m/                               # 15-minute timeframe CSV files
│   │   ├── 30m/                               # 30-minute timeframe CSV files
│   │   ├── 1h/                                # 1-hour timeframe CSV files
│   │   ├── 4h/                                # 4-hour timeframe CSV files
│   │   └── 1d/                                # Daily timeframe CSV files
│   └── exports/
│       ├── btc_sma_cross_returns.csv
│       └── eurusd_breakout_trades.csv
│
├── strategies/
│   ├── _template/
│   │   ├── strategy.py                        # Canonical starting point
│   │   ├── hypothesis.md                      # REQUIRED: What are we testing?
│   │   └── parameters.yaml                    # Default parameters
│   │
│   ├── crypto/
│   │   ├── btc_sma_cross/
│   │   │   ├── strategy.py
│   │   │   ├── hypothesis.md                  # "BTC trends persist >20 days"
│   │   │   ├── parameters.yaml                # fast: 10, slow: 50
│   │   │   └── results -> ../../results/btc_sma_cross/
│   │   │
│   │   ├── eth_mean_reversion/
│   │   │   ├── strategy.py
│   │   │   ├── hypothesis.md                  # "ETH reverts from 2σ bands"
│   │   │   ├── parameters.yaml
│   │   │   └── results -> ../../results/eth_mean_reversion/
│   │   │
│   │   └── sol_momentum_breakout/
│   │       ├── strategy.py
│   │       ├── hypothesis.md
│   │       ├── parameters.yaml
│   │       └── results -> ../../results/sol_momentum_breakout/
│   │
│   ├── forex/
│   │   ├── eurusd_london_breakout/
│   │   │   ├── strategy.py
│   │   │   ├── hypothesis.md                  # "London open creates directional moves"
│   │   │   ├── parameters.yaml
│   │   │   └── results -> ../../results/eurusd_london_breakout/
│   │   │
│   │   ├── gbpjpy_carry_momentum/
│   │   │   ├── strategy.py
│   │   │   ├── hypothesis.md
│   │   │   ├── parameters.yaml
│   │   │   └── results -> ../../results/gbpjpy_carry_momentum/
│   │   │
│   │   └── usdjpy_rsi_divergence/
│   │       ├── strategy.py
│   │       ├── hypothesis.md
│   │       ├── parameters.yaml
│   │       └── results -> ../../results/usdjpy_rsi_divergence/
│   │
│   └── equities/
│       ├── spy_dual_momentum/
│       │   ├── strategy.py
│       │   ├── hypothesis.md
│       │   ├── parameters.yaml
│       │   └── results -> ../../results/spy_dual_momentum/
│       │
│       └── qqq_volatility_regime/
│           ├── strategy.py
│           ├── hypothesis.md
│           ├── parameters.yaml
│           └── results -> ../../results/qqq_volatility_regime/
│
├── results/                                   # Centralized results storage
│   ├── btc_sma_cross/
│   │   ├── backtest_20241215_143022/
│   │   │   ├── returns.csv
│   │   │   ├── positions.csv
│   │   │   ├── transactions.csv
│   │   │   ├── metrics.json                   # Sharpe, Sortino, MaxDD, etc.
│   │   │   ├── parameters_used.yaml
│   │   │   └── equity_curve.png
│   │   ├── backtest_20241218_091547/
│   │   │   └── ...
│   │   ├── optimization_20241219_160033/
│   │   │   ├── grid_results.csv               # All param combinations tested
│   │   │   ├── best_params.yaml
│   │   │   ├── heatmap_sharpe.png
│   │   │   └── overfit_score.json             # Walk-forward validation
│   │   └── latest -> backtest_20241218_091547/
│   │
│   ├── eth_mean_reversion/
│   │   ├── backtest_20241216_102211/
│   │   │   └── ...
│   │   └── latest -> backtest_20241216_102211/
│   │
│   ├── eurusd_london_breakout/
│   │   ├── backtest_20241217_083012/
│   │   │   └── ...
│   │   ├── walkforward_20241220_141500/
│   │   │   ├── in_sample_results.csv
│   │   │   ├── out_sample_results.csv
│   │   │   ├── robustness_score.json
│   │   │   └── regime_breakdown.png
│   │   └── latest -> walkforward_20241220_141500/
│   │
│   └── spy_dual_momentum/
│       ├── backtest_20241214_171033/
│       │   └── ...
│       ├── montecarlo_20241219_220145/
│       │   ├── simulation_paths.csv           # 1000 equity curves
│       │   ├── confidence_intervals.json      # 5th, 50th, 95th percentile
│       │   └── distribution.png
│       └── latest -> montecarlo_20241219_220145/
│
├── notebooks/
│   ├── 01_backtest.ipynb                      # Single strategy backtest
│   ├── 02_optimize.ipynb                      # Grid/random search + validation
│   ├── 03_analyze.ipynb                       # Deep dive on single result
│   ├── 04_compare.ipynb                       # Multi-strategy comparison
│   ├── 05_walkforward.ipynb                   # Anti-overfit validation
│   └── _sandbox/                              # Experimental (gitignored)
│       ├── ml_signal_test.ipynb
│       └── regime_detection.ipynb
│
├── lib/
│   ├── __init__.py                            # Public API exports
│   ├── backtest/
│   │   ├── __init__.py                        # run_backtest, save_results exports
│   │   ├── runner.py                          # Zipline wrapper with calendar validation
│   │   ├── slippage.py                        # Custom slippage models
│   │   └── commission.py                      # Custom commission models
│   ├── bundles/
│   │   ├── __init__.py                        # ingest_bundle, register_bundle exports
│   │   ├── registry.py                        # Bundle registry and discovery
│   │   ├── yahoo.py                           # Yahoo Finance bundle implementation
│   │   └── validation.py                      # Bundle data validation
│   ├── calendars/
│   │   ├── __init__.py                        # Calendar registration exports
│   │   ├── crypto.py                          # 24/7 crypto calendar
│   │   ├── forex.py                           # Forex trading calendar
│   │   └── registry.py                        # Calendar discovery and registration
│   ├── config/
│   │   ├── __init__.py                        # load_settings, load_asset_config exports
│   │   ├── loader.py                          # Configuration loading from YAML
│   │   ├── settings.py                        # Settings dataclasses
│   │   ├── assets.py                          # Asset configuration parsing
│   │   └── strategy.py                        # Strategy parameter loading
│   ├── data/
│   │   ├── __init__.py                        # Data utilities exports
│   │   ├── aggregation.py                     # OHLCV aggregation utilities
│   │   ├── filtering.py                       # Data filtering and cleaning
│   │   ├── normalization.py                   # Data normalization utilities
│   │   └── forex.py                           # Forex-specific data handling
│   ├── logging/
│   │   ├── __init__.py                        # configure_logging, get_logger exports
│   │   ├── config.py                          # Logging configuration
│   │   ├── context.py                         # LogContext for structured logging
│   │   ├── formatters.py                      # Custom log formatters
│   │   ├── loggers.py                         # Specialized loggers (data, strategy, etc.)
│   │   └── utils.py                           # Logging utility functions
│   ├── metrics/
│   │   ├── __init__.py                        # calculate_metrics export
│   │   ├── core.py                            # Sharpe, Sortino, Calmar, etc.
│   │   ├── risk.py                            # MaxDD, VaR, CVaR, volatility
│   │   ├── trade.py                           # Win rate, profit factor, etc.
│   │   └── rolling.py                         # Rolling metric calculations
│   ├── optimize/
│   │   ├── __init__.py                        # grid_search, random_search exports
│   │   ├── grid.py                            # Grid search optimization
│   │   ├── random.py                          # Random search optimization
│   │   ├── split.py                           # Data splitting utilities
│   │   └── overfit.py                         # Overfit detection utilities
│   ├── plots/
│   │   ├── __init__.py                        # plot_equity_curve, plot_drawdown exports
│   │   ├── equity.py                          # Equity curve plots
│   │   ├── drawdown.py                        # Drawdown visualization
│   │   ├── returns.py                         # Returns distribution plots
│   │   └── trades.py                          # Trade analysis plots
│   ├── reports/
│   │   ├── __init__.py                        # generate_report export
│   │   ├── generator.py                       # Report generation
│   │   ├── templates.py                       # Report templates
│   │   └── catalog.py                         # Report catalog management
│   ├── validate/
│   │   ├── __init__.py                        # walk_forward, monte_carlo exports
│   │   ├── walkforward.py                     # Walk-forward validation
│   │   ├── montecarlo.py                      # Monte Carlo simulation
│   │   ├── overfit.py                         # Overfit probability calculation
│   │   └── efficiency.py                      # Walk-forward efficiency metrics
│   ├── validation/
│   │   ├── __init__.py                        # DataValidator, ValidationResult exports
│   │   ├── data.py                            # DataValidator implementation
│   │   ├── result.py                          # ValidationResult dataclass
│   │   ├── config.py                          # ValidationConfig settings
│   │   └── composite.py                       # Composite validation patterns
│   ├── paths.py                               # get_project_root, ProjectRootNotFoundError
│   └── extension.py                           # Wrapper for .zipline/extension.py
│
├── scripts/
│   ├── __init__.py                            # Scripts package init
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── run.py                             # python -m scripts.backtest.run --strategy btc_sma_cross
│   │   └── compare.py                         # python -m scripts.backtest.compare --strategies btc_sma_cross,eth_mean_reversion
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest.py                          # python -m scripts.data.ingest --source yahoo --assets crypto
│   │   ├── validate.py                        # python -m scripts.data.validate --bundle yahoo_crypto_daily
│   │   └── export.py                          # python -m scripts.data.export --strategy btc_sma_cross --format csv
│   ├── optimize/
│   │   ├── __init__.py
│   │   ├── grid.py                            # python -m scripts.optimize.grid --strategy btc_sma_cross
│   │   ├── random.py                          # python -m scripts.optimize.random --strategy btc_sma_cross --iterations 100
│   │   └── walkforward.py                     # python -m scripts.optimize.walkforward --strategy btc_sma_cross
│   ├── report/
│   │   ├── __init__.py
│   │   ├── generate.py                        # python -m scripts.report.generate --strategy btc_sma_cross
│   │   └── weekly.py                          # python -m scripts.report.weekly
│   └── strategy/
│       ├── __init__.py
│       ├── create.py                          # python -m scripts.strategy.create --name my_strategy --asset-class crypto
│       ├── list.py                            # python -m scripts.strategy.list [--asset-class crypto]
│       └── validate.py                        # python -m scripts.strategy.validate --strategy btc_sma_cross
│
├── reports/
│   ├── btc_sma_cross_report_20241218.md
│   ├── eurusd_london_breakout_report_20241220.md
│   └── weekly_summary_2024W51.md
│
├── docs/
│   ├── quickstart.md                          # 5-minute setup guide
│   ├── workflow.md                            # How to use the system
│   ├── strategy_catalog.md                    # Index of all strategies + status
│   └── code_patterns/                         # Your existing Zipline docs
│       ├── 00_getting_started/
│       ├── 01_core/
│       └── ...
│
├── .zipline/
│   └── extension.py                           # Custom calendar, slippage models
│
├── .gitignore
├── requirements.txt
└── README.md
