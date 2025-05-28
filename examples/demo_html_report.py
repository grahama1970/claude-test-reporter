#!/usr/bin/env python3
"""Demo the interactive HTML report generation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sparta.reports.html_report_generator import HtmlReportGenerator


def main():
    """Generate and serve a demo HTML report."""
    # Look for existing results or create demo data
    results_files = list(Path('.').glob('**/download_results.json'))
    
    if results_files:
        print(f"📊 Using existing results from: {results_files[0]}")
        import json
        with open(results_files[0], 'r') as f:
            data = json.load(f)
            
        # Convert format if needed
        if isinstance(data, list):
            # Old format - convert to new
            results = {
                'downloaded_urls': [item['url'] for item in data if item.get('status') == 'success'],
                'failed_urls': {item['url']: 'Download failed' for item in data if item.get('status') != 'success'}
            }
        else:
            results = data
    else:
        print("📊 Creating demo data...")
        results = {
            'downloaded_urls': [
                "https://sparta.aerospace.org/technique/REC-0001/",
                "https://sparta.aerospace.org/technique/REC-0002/", 
                "https://sparta.aerospace.org/threats/SV-MA-1",
                "https://jwillbold.com/paper/willbold2023spaceodyssey.pdf",
                "https://spacenews.com/article1.html",
                "https://www.dw.com/article2.html",
                "https://www.spacesafetymagazine.com/article3.html",
                "https://cromulence.com/blog/hack-a-sat-2022.html",
            ],
            'failed_urls': {
                "https://blocked.com/file1.pdf": "403 Forbidden",
                "https://timeout.com/file2.html": "Connection timeout",
                "https://www.cpomagazine.com/article.html": "403 Forbidden",
                "https://www.2-spyware.com/article.html": "403 Forbidden",
            }
        }
    
    # Generate report
    generator = HtmlReportGenerator()
    report_file = generator.generate_report(results, "sparta_demo_report.html")
    print(f"✅ Report generated: {report_file}")
    
    # Serve the report
    generator.serve_report(report_file, port=8080)


if __name__ == "__main__":
    main()