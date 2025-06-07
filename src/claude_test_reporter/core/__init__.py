"""
Core functionality for Claude Test Reporter.

Module: __init__.py
Description: Package initialization and exports

Sample Input:
>>> from claude_test_reporter.core import TestReporter
>>> reporter = TestReporter()

Expected Output:
>>> print(reporter)
<TestReporter instance>

Example Usage:
>>> from claude_test_reporter.core import TestReporter
>>> reporter = TestReporter()
>>> reporter.run_tests('/path/to/project')
"""

# Export main classes
__all__ = [
    'TestReporter',
    'MultiProjectDashboard',
    'EnhancedMultiProjectDashboard',
    'UniversalReportGenerator',
    'TestResultVerifier'
]