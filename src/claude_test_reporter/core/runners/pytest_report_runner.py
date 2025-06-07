"""
Module: pytest_report_runner.py
Description: Test suite for pyreport_runner functionality

External Dependencies:
- None (uses only standard library)

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
SPARTA Pytest Report Runner - Orchestrates pytest plugins
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def run_pytest_reports(
    test_path: str = "tests/",
    report_types: Optional[List[str]] = None,
    report_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Run pytest with requested report plugins."""
    if report_types is None:
        report_types = ["html", "json"]
    
    if report_dir is None:
        report_dir = Path("docs/reports")
    
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    results = {}
    
    # Add report plugins
    if "html" in report_types:
        html_path = report_dir / f"test_report_{timestamp}.html"
        cmd.extend(["--html", str(html_path), "--self-contained-html"])
        results["html"] = html_path
    
    if "json" in report_types:
        json_path = report_dir / f"test_results_{timestamp}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_path}"])
        results["json"] = json_path
    
    if "coverage" in report_types:
        cov_html = report_dir / f"coverage_html_{timestamp}"
        cmd.extend(["--cov=src/sparta", f"--cov-report=html:{cov_html}"])
        results["coverage_html"] = cov_html

    
    # Run pytest
    print(f"🧪 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"{'✅ Tests passed!' if result.returncode == 0 else '❌ Tests failed'}")
    
    # Show output
    if result.stdout:
        print(result.stdout)
    
    return results


def get_latest_json_report(report_dir: Path = None) -> Optional[Path]:
    """Find the latest JSON test report."""
    if report_dir is None:
        report_dir = Path("docs/reports")
    
    json_reports = list(report_dir.glob("test_results_*.json"))
    if json_reports:
        return max(json_reports, key=lambda p: p.stat().st_mtime)
    return None


if __name__ == "__main__":
    # Example usage
    results = run_pytest_reports(report_types=["html", "json"])
    print("\n📄 Generated reports:")
    for report_type, path in results.items():
        print(f"  • {report_type}: {path}")
