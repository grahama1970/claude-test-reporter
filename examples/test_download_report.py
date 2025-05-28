#!/usr/bin/env python3
"""Test the markdown report generation with existing download data."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sparta.downloaders import EnhancedSpartaDownloader

def test_report_generation():
    """Test report generation with existing data."""
    print("Testing markdown report generation...")
    
    # Create downloader instance
    downloader = EnhancedSpartaDownloader(output_dir="sparta_download_test/resources")
    
    # Manually set some test data if no downloads exist
    if len(downloader.downloaded_urls) == 0:
        print("No existing download data, creating test data...")
        downloader.downloaded_urls = {
            "https://sparta.aerospace.org/technique/REC-0001/",
            "https://www.spacesafetymagazine.com/aerospace-engineering/cyber-security/example.html",
            "https://jwillbold.com/paper/willbold2023spaceodyssey.pdf",
            "https://spacenews.com/north-korea-linked-hackers-accessed-souths-rocket-developer/",
            "https://www.dw.com/en/germanys-dlr-research-center-cyber-attack/a-17564342"
        }
        downloader.failed_urls = {
            "https://www.cpomagazine.com/cyber-security/spacex-third-party-vendor/": "403 Forbidden",
            "https://www.2-spyware.com/nasas-contractor-digital-management/": "403 Forbidden",
            "https://www.bloomberg.com/news/articles/network-security-breaches-plague-nasa": "Paywall"
        }
    
    # Generate the report
    downloader.generate_markdown_report()
    
    # Check if report was created
    report_path = Path("sparta_download_test/download_report.md")
    if report_path.exists():
        print(f"✅ Report generated successfully: {report_path}")
        
        # Show first 50 lines of report
        with open(report_path, 'r') as f:
            lines = f.readlines()
            print("\n📄 Report Preview:")
            print("=" * 80)
            for line in lines[:50]:
                print(line.rstrip())
            if len(lines) > 50:
                print(f"\n... ({len(lines) - 50} more lines)")
    else:
        print("❌ Report generation failed")

if __name__ == "__main__":
    test_report_generation()