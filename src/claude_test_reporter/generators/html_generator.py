"""
HTML Generator - Generate HTML reports from test data

Purpose: Create formatted HTML reports
"""

from typing import Dict, Any, List
from datetime import datetime


class HTMLGenerator:
    """Generate HTML reports from test results."""
    
    def generate(self, test_results: Dict[str, Any]) -> str:
        """Generate HTML report from test results."""
        # Extract data
        tests = test_results.get("tests", [])
        summary = test_results.get("summary", {})
        
        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 30px;
                }}
                .summary {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .summary-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                    text-align: center;
                }}
                .summary-card h3 {{
                    margin: 0 0 10px 0;
                    color: #666;
                    font-size: 14px;
                    text-transform: uppercase;
                }}
                .summary-card .value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #333;
                }}
                .passed {{ color: #28a745; }}
                .failed {{ color: #dc3545; }}
                .skipped {{ color: #ffc107; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e0e0e0;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #333;
                }}
                tr:hover {{
                    background: #f8f9fa;
                }}
                .status {{
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .status.passed {{
                    background: #d4edda;
                    color: #155724;
                }}
                .status.failed {{
                    background: #f8d7da;
                    color: #721c24;
                }}
                .status.skipped {{
                    background: #fff3cd;
                    color: #856404;
                }}
                .duration {{
                    color: #666;
                    font-size: 14px;
                }}
                .error {{
                    color: #dc3545;
                    font-size: 13px;
                    margin-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Test Report</h1>
                
                <div class="summary">
                    <div class="summary-card">
                        <h3>Total Tests</h3>
                        <div class="value">{summary.get('total', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Passed</h3>
                        <div class="value passed">{summary.get('passed', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed</h3>
                        <div class="value failed">{summary.get('failed', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Skipped</h3>
                        <div class="value skipped">{summary.get('skipped', 0)}</div>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add test rows
        for test in tests:
            status = test.get('status', 'unknown')
            duration = test.get('duration', 0)
            error = test.get('error', '')
            
            html += f"""
                        <tr>
                            <td>{test.get('name', 'Unknown Test')}</td>
                            <td><span class="status {status}">{status}</span></td>
                            <td class="duration">{duration:.2f}s</td>
                            <td>
            """
            
            if error:
                html += f'<div class="error">{error}</div>'
            
            html += """
                            </td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
                    Generated by claude-test-reporter • {timestamp}
                </div>
            </div>
        </body>
        </html>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return html