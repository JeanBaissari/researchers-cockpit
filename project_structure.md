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
│   ├── data_sources.yaml                      # API keys, endpoints
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
│   ├── __init__.py
│   ├── backtest.py                            # Zipline wrapper with calendar validation
│   ├── config.py                              # Configuration loading
│   ├── data_loader.py                         # Bundle ingestion with gap-filling
│   ├── extension.py                           # Wrapper for .zipline/extension.py
│   ├── logging_config.py                      # Centralized logging configuration
│   ├── metrics.py                             # Empyrical + custom metrics
│   ├── optimize.py                            # Grid search, random search
│   ├── paths.py                               # Marker-based project root discovery
│   ├── plots.py                               # Standard visualizations
│   ├── report.py                              # Report generation
│   ├── utils.py                               # Utility functions, timezone handling
│   └── validate.py                            # Walk-forward, Monte Carlo, overfit detection
│
├── scripts/
│   ├── ingest_data.py                         # python scripts/ingest_data.py --source yahoo --assets crypto [--calendar CRYPTO]
│   ├── run_backtest.py                        # python scripts/run_backtest.py --strategy btc_sma_cross
│   ├── run_optimization.py                    # python scripts/run_optimization.py --strategy btc_sma_cross --method grid
│   └── generate_report.py                     # python scripts/generate_report.py --strategy btc_sma_cross
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
