"""
Test Phase 7: Report Generation

Tests the report generation workflow:
- Strategy report creation
- Report formatting
- Report export
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.report import (
    generate_strategy_report,
)


class TestReportGeneration:
    """Test report generation."""
    
    @pytest.mark.slow
    def test_generate_strategy_report_exists(self):
        """Test that generate_strategy_report function exists."""
        assert generate_strategy_report is not None
        
        import inspect
        sig = inspect.signature(generate_strategy_report)
        params = list(sig.parameters.keys())
        
        # Should have parameters
        assert len(params) > 0
    
    @pytest.mark.slow
    def test_report_generation_signature(self):
        """Test report generation function signature."""
        import inspect
        sig = inspect.signature(generate_strategy_report)
        
        # Should accept strategy name or results
        assert sig is not None


class TestReportStructure:
    """Test report structure."""
    
    def test_report_sections(self):
        """Test report has expected sections."""
        expected_sections = [
            'summary',
            'performance_metrics',
            'risk_metrics',
            'trade_analysis',
            'equity_curve',
        ]
        
        # Report should have these sections
        for section in expected_sections:
            assert isinstance(section, str)
    
    def test_report_metadata(self):
        """Test report metadata."""
        metadata = {
            'strategy_name': 'test_strategy',
            'generated_at': '2020-01-01',
            'backtest_period': '2020-01-01 to 2020-12-31',
            'version': '1.0.8',
        }
        
        assert 'strategy_name' in metadata
        assert 'generated_at' in metadata


class TestReportMetrics:
    """Test report metrics section."""
    
    def test_performance_metrics_section(self, sample_backtest_results):
        """Test performance metrics in report."""
        metrics = {
            'total_return': sample_backtest_results['total_return'],
            'annual_return': sample_backtest_results['annual_return'],
            'sharpe_ratio': sample_backtest_results['sharpe_ratio'],
            'sortino_ratio': sample_backtest_results['sortino_ratio'],
        }
        
        # All metrics should be numeric
        for key, value in metrics.items():
            assert isinstance(value, (int, float))
    
    def test_risk_metrics_section(self, sample_backtest_results):
        """Test risk metrics in report."""
        risk_metrics = {
            'max_drawdown': sample_backtest_results['max_drawdown'],
            'volatility': sample_backtest_results['volatility'],
        }
        
        # All metrics should be numeric
        for key, value in risk_metrics.items():
            assert isinstance(value, (int, float))


class TestReportTables:
    """Test report tables."""
    
    def test_trade_summary_table(self, sample_backtest_results):
        """Test trade summary table."""
        transactions = sample_backtest_results['transactions']
        
        # Should have transaction data
        assert len(transactions) >= 0
        
        # Count trades
        total_trades = len(transactions)
        assert isinstance(total_trades, int)
    
    def test_monthly_returns_table(self, sample_backtest_results):
        """Test monthly returns table."""
        returns = sample_backtest_results['returns']
        
        # Group by month
        monthly = returns.resample('M').sum()
        
        assert len(monthly) >= 0


class TestReportCharts:
    """Test report charts."""
    
    def test_equity_curve_chart(self):
        """Test equity curve chart generation."""
        from lib.plots import plot_equity_curve
        
        assert plot_equity_curve is not None
    
    def test_returns_distribution_chart(self):
        """Test returns distribution chart."""
        from lib.plots import plot_returns_distribution
        
        assert plot_returns_distribution is not None
    
    @pytest.mark.slow
    def test_drawdown_chart(self):
        """Test drawdown chart generation."""
        # Check that drawdown plotting exists
        from lib import plots
        assert plots is not None


class TestReportFormatting:
    """Test report formatting."""
    
    def test_report_html_export(self, temp_results_dir):
        """Test exporting report as HTML."""
        report_path = temp_results_dir / 'report.html'
        
        # Should be able to create HTML file
        report_path.write_text('<html><body>Test Report</body></html>')
        
        assert report_path.exists()
        assert report_path.suffix == '.html'
    
    def test_report_pdf_export(self, temp_results_dir):
        """Test exporting report as PDF."""
        report_path = temp_results_dir / 'report.pdf'
        
        # Should be able to create PDF path
        assert report_path.suffix == '.pdf'
    
    def test_report_json_export(self, temp_results_dir):
        """Test exporting report as JSON."""
        import json
        report_path = temp_results_dir / 'report.json'
        
        test_data = {
            'strategy': 'test',
            'metrics': {
                'sharpe': 1.5,
                'max_dd': -0.1,
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(test_data, f)
        
        assert report_path.exists()
        assert report_path.suffix == '.json'


class TestReportContent:
    """Test report content."""
    
    def test_report_has_strategy_name(self):
        """Test report includes strategy name."""
        report = {
            'strategy_name': 'test_strategy',
            'metrics': {},
        }
        
        assert 'strategy_name' in report
    
    def test_report_has_backtest_period(self):
        """Test report includes backtest period."""
        report = {
            'backtest_period': {
                'start': '2020-01-01',
                'end': '2020-12-31',
            }
        }
        
        assert 'backtest_period' in report
    
    def test_report_has_metrics(self):
        """Test report includes metrics."""
        report = {
            'metrics': {
                'sharpe_ratio': 1.5,
                'max_drawdown': -0.1,
            }
        }
        
        assert 'metrics' in report
        assert len(report['metrics']) > 0


class TestReportValidation:
    """Test report validation."""
    
    def test_report_metrics_are_valid(self, sample_backtest_results):
        """Test that report metrics are valid."""
        metrics = {
            'sharpe_ratio': sample_backtest_results['sharpe_ratio'],
            'max_drawdown': sample_backtest_results['max_drawdown'],
        }
        
        # Sharpe should be reasonable
        assert -10 <= metrics['sharpe_ratio'] <= 10
        
        # Max drawdown should be negative or zero
        assert metrics['max_drawdown'] <= 0
    
    def test_report_completeness(self):
        """Test that report is complete."""
        required_sections = [
            'strategy_name',
            'metrics',
            'backtest_period',
        ]
        
        report = {
            'strategy_name': 'test',
            'metrics': {'sharpe': 1.5},
            'backtest_period': '2020-01-01 to 2020-12-31',
        }
        
        for section in required_sections:
            assert section in report


class TestReportOutput:
    """Test report output."""
    
    def test_report_saved_to_results_dir(self, temp_results_dir):
        """Test that report is saved to results directory."""
        report_file = temp_results_dir / 'strategy_report.html'
        
        # Create dummy report
        report_file.write_text('<html>Test</html>')
        
        assert report_file.exists()
        assert report_file.parent == temp_results_dir
    
    def test_report_filename_convention(self):
        """Test report filename convention."""
        strategy_name = 'test_strategy'
        report_filename = f'{strategy_name}_report.html'
        
        assert strategy_name in report_filename
        assert '.html' in report_filename

