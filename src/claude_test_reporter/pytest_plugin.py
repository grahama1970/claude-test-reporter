"""
Module: pytest_plugin.py
Description: Test suite for pyplugin functionality

pytest plugin for claude-test-reporter
"""
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
        self.test_results = []

        if self.enabled:
            # Use model name as project key
            project_key = self.model_name or 'default'

            # Initialize the test reporter with project key
            report_config = get_report_config(project_key)
            report_config['model_name'] = self.model_name
            report_config['output_dir'] = str(self.output_dir)

            # Create output directory if it doesn't exist
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def pytest_runtest_protocol(self, item, nextitem):
        """Hook to track test execution"""
        # Let pytest handle the test execution
        return None

    def pytest_runtest_makereport(self, item, call):
        """Hook to capture test results"""
        if self.enabled and call.when == 'call':
            # Record test result
            outcome = 'passed' if call.excinfo is None else 'failed'
            self.test_results.append({
                'test_name': item.nodeid,
                'outcome': outcome,
                'duration': call.duration,
                'error': str(call.excinfo) if call.excinfo else None
            })

    def pytest_sessionfinish(self, session, exitstatus):
        """Hook called after test session finishes"""
        if self.enabled and self.test_results:
            # Create simple report
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['outcome'] == 'passed')
            failed_tests = total_tests - passed_tests

            report_path = self.output_dir / f"{self.model_name}_test_report.txt"

            with open(report_path, 'w') as f:
                f.write(f"Test Report for {self.model_name}\n")
                f.write(f"="*50 + "\n\n")
                f.write(f"Total Tests: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {failed_tests}\n")
                f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")

                if failed_tests > 0:
                    f.write("Failed Tests:\n")
                    for result in self.test_results:
                        if result['outcome'] == 'failed':
                            f.write(f"  - {result['test_name']}\n")
                            if result['error']:
                                f.write(f"    Error: {result['error']}\n")

            print(f"\nTest report saved to: {report_path}")


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
