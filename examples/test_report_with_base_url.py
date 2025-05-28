#!/usr/bin/env python3
"""Test the report generator with custom base URL."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sparta.reports.universal_report_generator import UniversalReportGenerator

def main():
    """Generate a test report with the specified base URL."""
    
    # Sample data
    data = [
        {
            "File": "document1.pdf",
            "Status": "✅ Success", 
            "Size": "2.3 MB",
            "Processing Time": "1.2s",
            "Pages": 45
        },
        {
            "File": "report2.docx",
            "Status": "✅ Success",
            "Size": "1.1 MB", 
            "Processing Time": "0.8s",
            "Pages": 23
        },
        {
            "File": "data3.xlsx",
            "Status": "❌ Failed",
            "Size": "0 MB",
            "Processing Time": "0s",
            "Error": "Corrupted file"
        }
    ]
    
    # Create generator with your base URL
    generator = UniversalReportGenerator(
        title="Test Report with Base URL",
        theme_color="#10b981",
        logo="📊",
        base_url="http://192.168.86.49:8"  # Your specified base URL
    )
    
    # Generate report
    report_file = generator.generate(
        data=data,
        output_file="test_base_url_report.html",
        summary_stats={
            "Total Files": len(data),
            "Successful": sum(1 for d in data if "Success" in d["Status"]),
            "Failed": sum(1 for d in data if "Failed" in d["Status"]),
            "Total Pages": sum(d.get("Pages", 0) for d in data)
        },
        group_by="Status"
    )
    
    # Display the URL where report will be available
    report_url = generator.serve_report(report_file)
    
    print(f"\n✅ Report generated successfully!")
    print(f"📊 View your report at: {report_url}")
    print(f"\n💡 Note: Make sure your web server is running at {generator.base_url}")
    print(f"   If using Python's SimpleHTTPServer:")
    print(f"   cd {Path.cwd()}")
    print(f"   python -m http.server 8 --bind 192.168.86.49")

if __name__ == "__main__":
    main()