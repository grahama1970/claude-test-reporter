#!/usr/bin/env python3
"""Demo: Generate reports for all projects using configuration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sparta.reports.universal_report_generator import UniversalReportGenerator
from src.sparta.reports.report_config import get_report_config


def generate_sparta_report():
    """Generate SPARTA download report."""
    config = get_report_config("sparta")
    
    data = [
        {"URL": "https://sparta.aerospace.org/file1", "Status": "✅ Success", "Size": "1.2 MB"},
        {"URL": "https://blocked.com/file2", "Status": "❌ Failed", "Error": "403 Forbidden"}
    ]
    
    generator = UniversalReportGenerator(**config)
    report_file = generator.generate(data, "sparta_configured_report.html")
    return generator.serve_report(report_file)


def generate_marker_report():
    """Generate Marker extraction report."""
    config = get_report_config("marker")
    
    data = [
        {"Document": "report.pdf", "Pages": 45, "Tables": 12, "Status": "✅ Complete"},
        {"Document": "data.xlsx", "Pages": 10, "Tables": 8, "Status": "✅ Complete"}
    ]
    
    generator = UniversalReportGenerator(**config)
    report_file = generator.generate(data, "marker_configured_report.html")
    return generator.serve_report(report_file)


def generate_arangodb_report():
    """Generate ArangoDB graph report."""
    config = get_report_config("arangodb")
    
    data = [
        {"Collection": "nodes", "Count": 1250, "Type": "Vertex", "Status": "Active"},
        {"Collection": "edges", "Count": 3456, "Type": "Edge", "Status": "Active"}
    ]
    
    generator = UniversalReportGenerator(**config)
    report_file = generator.generate(data, "arangodb_configured_report.html")
    return generator.serve_report(report_file)


def main():
    """Generate all reports."""
    print("🚀 Generating configured reports for all projects...\n")
    
    # Generate reports
    sparta_url = generate_sparta_report()
    print(f"✅ SPARTA Report: {sparta_url}")
    
    marker_url = generate_marker_report()
    print(f"✅ Marker Report: {marker_url}")
    
    arango_url = generate_arangodb_report()
    print(f"✅ ArangoDB Report: {arango_url}")
    
    print(f"\n📊 All reports generated with base URL: http://192.168.86.49:8")
    print(f"💡 Make sure your web server is running at that address")


if __name__ == "__main__":
    main()