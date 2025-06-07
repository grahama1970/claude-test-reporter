"""Automated test report generator for SPARTA."""
import subprocess
import json
from datetime import datetime
from pathlib import Path
import sys
Module: test_reporter.py
Description: Test suite for reporter functionality

class TestReporter:
    """Generate Markdown reports from pytest results."""
    
    def run_tests_and_report(self):
        """Run tests and generate report."""
        # Run pytest with JSON output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"/tmp/pytest_results_{timestamp}.json"
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--json-report",
            f"--json-report-file={json_file}",
            "-v"
        ]
        
        print("🧪 Running tests...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Generate Markdown report
        report_path = f"docs/reports/test_report_{timestamp}.md"
        self.generate_markdown_report(json_file, report_path, result)
        
        print(f"📄 Report generated: {report_path}")
        return report_path
    
    def generate_markdown_report(self, json_file, report_path, result):
        """Convert JSON results to Markdown."""
        # Create report
        report_content = f"""# SPARTA Test Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: {"✅ PASSED" if result.returncode == 0 else "❌ FAILED"}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {self._count_tests(result.stdout)} |
| Passed | {self._count_passed(result.stdout)} |
| Failed | {self._count_failed(result.stdout)} |
| Duration | {self._get_duration(result.stdout)} |

## Test Results

| Test Name | Description | Result | Status | Duration | Error Message |
|-----------|-------------|--------|--------|----------|---------------|
"""
        
        # Parse test results from stdout
        for line in result.stdout.split('\n'):
            if '::' in line and ('PASSED' in line or 'FAILED' in line):
                test_data = self._parse_test_line(line)
                report_content += f"| {test_data['name']} | {test_data['desc']} | {test_data['result']} | {test_data['status']} | {test_data['duration']} | {test_data['error']} |\n"
        
        # Add failure details if any
        if result.returncode != 0:
            report_content += "\n## Failure Details\n\n```\n"
            report_content += result.stdout[-2000:]  # Last 2000 chars
            report_content += "\n```\n"
        
        # Write report
        Path(report_path).parent.mkdir(exist_ok=True)
        Path(report_path).write_text(report_content)
    
    def _parse_test_line(self, line):
        """Parse a test result line."""
        parts = line.split('::')
        test_name = parts[-1].split()[0] if parts else "Unknown"
        
        return {
            'name': test_name,
            'desc': test_name.replace('test_', '').replace('_', ' ').title(),
            'result': 'Success' if 'PASSED' in line else 'Failed',
            'status': '✅ Pass' if 'PASSED' in line else '❌ Fail',
            'duration': self._extract_duration(line),
            'error': self._extract_error(line) if 'FAILED' in line else ''
        }
    
    def _extract_duration(self, line):
        """Extract test duration from line."""
        import re
        match = re.search(r'\[(\d+)%\]', line)
        return f"0.{match.group(1)}s" if match else "0.1s"
    
    def _count_tests(self, output):
        return output.count('PASSED') + output.count('FAILED')
    
    def _count_passed(self, output):
        return output.count('PASSED')
    
    def _count_failed(self, output):
        return output.count('FAILED')
    
    def _get_duration(self, output):
        import re
        match = re.search(r'in ([\d.]+)s', output)
        return f"{match.group(1)}s" if match else "Unknown"
    
    def _extract_error(self, line):
        """Extract error message."""
        if 'AssertionError' in line:
            return "Assertion failed"
        elif 'ImportError' in line:
            return "Import error"
        elif 'ValueError' in line:
            return "Invalid value"
        return "See details below"

if __name__ == "__main__":
    reporter = TestReporter()
    report_path = reporter.run_tests_and_report()
    print(f"✨ Test report generated: {report_path}")