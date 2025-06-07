"""Report generators"""
Module: __init__.py
Description: Package initialization and exports

from .universal_report_generator import UniversalReportGenerator
from .simple_html_reporter import SimpleHTMLReporter
from .multi_project_dashboard import MultiProjectDashboard

__all__ = ["UniversalReportGenerator", "SimpleHTMLReporter", "MultiProjectDashboard"]
