"""
Module: __init__.py
Report generators

Description: Package initialization and exports
"""

from .universal_report_generator import UniversalReportGenerator
from .simple_html_reporter import SimpleHTMLReporter
# from .multi_project_dashboard import MultiProjectDashboard  # Temporarily disabled due to Python 3.12 f-string issues
from .enhanced_multi_project_dashboard import EnhancedMultiProjectDashboard
# Temporarily use enhanced version as MultiProjectDashboard
MultiProjectDashboard = EnhancedMultiProjectDashboard

__all__ = ["UniversalReportGenerator", "SimpleHTMLReporter", "MultiProjectDashboard", "EnhancedMultiProjectDashboard"]
