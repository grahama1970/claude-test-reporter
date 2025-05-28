"""
Claude Test Reporter - Universal test reporting for Claude companion projects
"""

from .report_config import get_report_config, REPORT_CONFIGS
from .test_reporter import TestReporter, ReportGenerator

__version__ = "0.2.1"
__all__ = ["get_report_config", "REPORT_CONFIGS", "TestReporter", "ReportGenerator"]
