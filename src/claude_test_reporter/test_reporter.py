"""
Test Reporter - Main reporter class for test results

Purpose: Generate test reports in various formats
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .generators.html_generator import HTMLGenerator
from .generators.markdown_generator import MarkdownGenerator


class TestReporter:
    """Main test reporter class."""
    
    def __init__(self):
        self.html_generator = HTMLGenerator()
        self.markdown_generator = MarkdownGenerator()
    
    def generate_report(self, test_results: Dict[str, Any], format: str = "html") -> str:
        """Generate report in specified format."""
        if format == "html":
            return self.html_generator.generate(test_results)
        elif format == "markdown":
            return self.markdown_generator.generate(test_results)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def run_and_report(
        self,
        output_path: str = "test_report.html",
        include_coverage: bool = True,
        test_path: str = "tests/"
    ) -> str:
        """Run tests and generate report."""
        # Run pytest
        cmd = ["pytest", test_path, "--json-report", "--json-report-file=test_results.json"]
        if include_coverage:
            cmd.extend(["--cov", "--cov-report=html"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Load results
        with open("test_results.json") as f:
            test_results = json.load(f)
        
        # Generate HTML report
        html_content = self.html_generator.generate(test_results)
        
        # Write to file
        Path(output_path).write_text(html_content)
        
        return output_path
    
    def generate_from_results(
        self,
        test_results: Dict[str, Any],
        output_path: str = "test_report.html",
        include_coverage: bool = True
    ) -> str:
        """Generate report from existing test results."""
        # Generate HTML report
        html_content = self.html_generator.generate(test_results)
        
        # Write to file
        Path(output_path).write_text(html_content)
        
        return output_path


class ReportGenerator:
    """Generic report generator for various data types."""
    
    def __init__(self):
        self.html_generator = HTMLGenerator()
    
    def generate_html_report(
        self,
        data: Dict[str, Any],
        output_path: str,
        template: str = "default"
    ) -> str:
        """Generate HTML report from data."""
        # Create HTML based on template
        if template == "data":
            html = self._generate_data_report(data)
        elif template == "pipeline":
            html = self._generate_pipeline_report(data)
        else:
            html = self.html_generator.generate(data)
        
        # Write to file
        Path(output_path).write_text(html)
        
        return output_path
    
    def _generate_data_report(self, data: Dict[str, Any]) -> str:
        """Generate data table report."""
        title = data.get("title", "Data Report")
        items = data.get("data", [])
        columns = data.get("columns", [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <table>
                <tr>
        """
        
        for col in columns:
            html += f"<th>{col}</th>"
        html += "</tr>"
        
        for item in items:
            html += "<tr>"
            for col in columns:
                html += f"<td>{item.get(col, '')}</td>"
            html += "</tr>"
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _generate_pipeline_report(self, data: Dict[str, Any]) -> str:
        """Generate pipeline execution report."""
        title = data.get("title", "Pipeline Report")
        summary = data.get("summary", {})
        sections = data.get("sections", [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #e8f5e9; padding: 15px; margin: 20px 0; }}
                .section {{ margin: 20px 0; }}
                .metric {{ padding: 10px; margin: 5px 0; }}
                .success {{ color: #2e7d32; }}
                .failed {{ color: #c62828; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="summary">
                <h2>Summary</h2>
        """
        
        for key, value in summary.items():
            html += f"<p><strong>{key}:</strong> {value}</p>"
        
        html += "</div>"
        
        for section in sections:
            html += f"""
            <div class="section">
                <h3>{section.get('name', 'Section')}</h3>
                <pre>{json.dumps(section.get('data', {}), indent=2)}</pre>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html