"""pytest plugin for claude-test-reporter"""
import pytest
from pathlib import Path
from typing import Any, Dict, Optional
from claude_test_reporter.core.test_reporter import TestReporter
from claude_test_reporter.core.report_config import get_report_config


def pytest_addoption(parser):
    """Add claude-test-reporter command line options"""
    group = parser.getgroup('claude-test-reporter')
    group.addoption(
        '--claude-reporter',
        action='store_true',
        default=False,
        help='Enable Claude test reporter'
    )
    group.addoption(
        '--claude-model',
        action='store',
        default='default',
        help='Model name for Claude test reporter'
    )
    group.addoption(
        '--claude-output-dir',
        action='store',
        default='test_reports',
        help='Output directory for test reports'
    )


class ClaudeTestReporterPlugin:
    """pytest plugin implementation for Claude test reporter"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.getoption('--claude-reporter')
        self.model_name = config.getoption('--claude-model')
        self.output_dir = Path(config.getoption('--claude-output-dir'))
        self.reporter: Optional[TestReporter] = None
        
        if self.enabled:
            # Initialize the test reporter
            report_config = get_report_config()
            report_config['model_name'] = self.model_name
            report_config['output_dir'] = str(self.output_dir)
            self.reporter = TestReporter(report_config)
    
    def pytest_runtest_protocol(self, item, nextitem):
        """Hook to track test execution"""
        if self.enabled and self.reporter:
            # Record test start
            self.reporter.start_test(item.nodeid)
    
    def pytest_runtest_makereport(self, item, call):
        """Hook to capture test results"""
        if self.enabled and self.reporter and call.when == 'call':
            outcome = call.excinfo is None
            self.reporter.record_result(
                test_name=item.nodeid,
                passed=outcome,
                duration=call.duration,
                error=str(call.excinfo) if call.excinfo else None
            )
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Hook called after test session finishes"""
        if self.enabled and self.reporter:
            # Generate final report
            self.reporter.generate_report()


def pytest_configure(config):
    """Register the plugin"""
    config._claude_reporter = ClaudeTestReporterPlugin(config)
    config.pluginmanager.register(config._claude_reporter)
    
    # Add marker
    config.addinivalue_line(
        'markers', 
        'claude_report: mark test for inclusion in Claude test report'
    )


def pytest_unconfigure(config):
    """Unregister the plugin"""
    if hasattr(config, '_claude_reporter'):
        config.pluginmanager.unregister(config._claude_reporter)
        del config._claude_reporter
