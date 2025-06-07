

Module: test_history_tracker.py
Description: Test suite for history_tracker functionality
"""

External Dependencies:
- statistics: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Test History Tracker

Purpose: Track test results over time to identify trends and flaky tests
Features: Historical data storage, trend analysis, flaky test detection
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
import statistics


class TestHistoryTracker:
    """Track and analyze test results over time."""

    def __init__(self, storage_dir: str = ".test_history"):
        """Initialize tracker with storage directory."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.history_file = self.storage_dir / "test_history.json"
        self.flaky_tests_file = self.storage_dir / "flaky_tests.json"
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load test history from storage."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                return json.load(f)
        return {}

    def _save_history(self) -> None:
        """Save test history to storage."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def add_test_run(self, project_name: str, test_results: Dict[str, Any],
                     run_id: Optional[str] = None) -> None:
        """Add a test run to history."""
        if project_name not in self.history:
            self.history[project_name] = []

        # Create run record
        run_record = {
            "run_id": run_id or datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": test_results.get("total", 0),
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "skipped": test_results.get("skipped", 0),
                "duration": test_results.get("duration", 0)
            },
            "tests": {}
        }

        # Store individual test results
        for test in test_results.get("tests", []):
            test_name = test.get("nodeid", test.get("name", "unknown"))
            run_record["tests"][test_name] = {
                "outcome": test.get("outcome", test.get("status", "unknown")),
                "duration": test.get("duration", 0),
                "error": test.get("error", None)
            }

        # Add to history (keep last 100 runs)
        self.history[project_name].append(run_record)
        self.history[project_name] = self.history[project_name][-100:]

        self._save_history()
        self._analyze_flaky_tests(project_name)

    def get_test_trends(self, project_name: str, test_name: str,
                       days: int = 7) -> Dict[str, Any]:
        """Get trends for a specific test over time."""
        if project_name not in self.history:
            return {"error": "Project not found"}

        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_runs = []

        for run in self.history[project_name]:
            run_time = datetime.fromisoformat(run["timestamp"])
            if run_time >= cutoff_date and test_name in run["tests"]:
                relevant_runs.append({
                    "timestamp": run["timestamp"],
                    "outcome": run["tests"][test_name]["outcome"],
                    "duration": run["tests"][test_name]["duration"]
                })

        if not relevant_runs:
            return {"error": "No data for this test in the specified period"}

        # Calculate trends
        outcomes = [r["outcome"] for r in relevant_runs]
        durations = [r["duration"] for r in relevant_runs if r["duration"] > 0]

        trends = {
            "test_name": test_name,
            "period_days": days,
            "total_runs": len(relevant_runs),
            "outcomes": {
                "passed": outcomes.count("passed"),
                "failed": outcomes.count("failed"),
                "skipped": outcomes.count("skipped")
            },
            "success_rate": (outcomes.count("passed") / len(outcomes) * 100) if outcomes else 0,
            "duration_stats": {
                "mean": statistics.mean(durations) if durations else 0,
                "median": statistics.median(durations) if durations else 0,
                "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0,
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0
            },
            "recent_runs": relevant_runs[-10:]  # Last 10 runs
        }

        # Detect performance regression
        if len(durations) >= 5:
            recent_avg = statistics.mean(durations[-5:])
            overall_avg = statistics.mean(durations)
            if recent_avg > overall_avg * 1.5:
                trends["performance_regression"] = True
                trends["regression_factor"] = recent_avg / overall_avg

        return trends

    def _analyze_flaky_tests(self, project_name: str) -> None:
        """Analyze and identify flaky tests."""
        if project_name not in self.history or len(self.history[project_name]) < 3:
            return

        # Analyze last 20 runs
        recent_runs = self.history[project_name][-20:]
        test_outcomes = defaultdict(list)

        # Collect outcomes for each test
        for run in recent_runs:
            for test_name, test_data in run["tests"].items():
                test_outcomes[test_name].append(test_data["outcome"])

        # Identify flaky tests
        flaky_tests = {}
        for test_name, outcomes in test_outcomes.items():
            if len(outcomes) < 3:
                continue

            unique_outcomes = set(outcomes)
            # Test is flaky if it has mixed results
            if len(unique_outcomes) > 1 and "passed" in unique_outcomes and "failed" in unique_outcomes:
                passed_count = outcomes.count("passed")
                failed_count = outcomes.count("failed")
                total_runs = len(outcomes)

                # Calculate flakiness score (0-1, higher is more flaky)
                flakiness = 1 - abs(passed_count - failed_count) / total_runs

                # Track recent pattern
                recent_pattern = "".join(
                    "P" if o == "passed" else "F" if o == "failed" else "S"
                    for o in outcomes[-10:]
                )

                flaky_tests[test_name] = {
                    "flakiness_score": round(flakiness, 3),
                    "pass_rate": round(passed_count / total_runs * 100, 1),
                    "fail_rate": round(failed_count / total_runs * 100, 1),
                    "total_runs": total_runs,
                    "recent_pattern": recent_pattern,
                    "last_outcome": outcomes[-1],
                    "detected_at": datetime.now().isoformat()
                }

        # Save flaky tests analysis
        if flaky_tests:
            all_flaky_tests = {}
            if self.flaky_tests_file.exists():
                with open(self.flaky_tests_file) as f:
                    all_flaky_tests = json.load(f)

            all_flaky_tests[project_name] = {
                "updated_at": datetime.now().isoformat(),
                "tests": flaky_tests
            }

            with open(self.flaky_tests_file, 'w') as f:
                json.dump(all_flaky_tests, f, indent=2)

    def get_flaky_tests(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get flaky tests for a project or all projects."""
        if not self.flaky_tests_file.exists():
            return {}

        with open(self.flaky_tests_file) as f:
            all_flaky_tests = json.load(f)

        if project_name:
            return all_flaky_tests.get(project_name, {})
        return all_flaky_tests

    def get_project_health_history(self, project_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get project health metrics over time."""
        if project_name not in self.history:
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        health_history = []

        for run in self.history[project_name]:
            run_time = datetime.fromisoformat(run["timestamp"])
            if run_time >= cutoff_date:
                summary = run["summary"]
                total = summary.get("total", 0)
                if total > 0:
                    health_history.append({
                        "timestamp": run["timestamp"],
                        "success_rate": (summary.get("passed", 0) / total) * 100,
                        "total_tests": total,
                        "failed_tests": summary.get("failed", 0),
                        "duration": summary.get("duration", 0)
                    })

        return health_history

    def generate_history_report(self, project_name: str, output_file: str = "test_history_report.html") -> str:
        """Generate HTML report showing test history and trends."""
        if project_name not in self.history:
            raise ValueError(f"No history found for project: {project_name}")

        # Get data
        health_history = self.get_project_health_history(project_name, days=30)
        flaky_tests = self.get_flaky_tests(project_name)

        # Generate charts data
        dates = [h["timestamp"][:10] for h in health_history[-14:]]  # Last 14 days
        success_rates = [h["success_rate"] for h in health_history[-14:]]

        # Generate HTML
        html_content = self._generate_history_html(project_name, health_history, flaky_tests, dates, success_rates)

        output_path = Path(output_file)
        output_path.write_text(html_content, encoding='utf-8')

        return str(output_path.resolve())

    def _generate_history_html(self, project_name: str, health_history: List[Dict],
                              flaky_tests: Dict, dates: List[str], success_rates: List[float]) -> str:
        """Generate the history report HTML."""
        # Flaky tests table
        flaky_tests_html = ""
        if flaky_tests and "tests" in flaky_tests:
            flaky_tests_html = "<h2>🎲 Flaky Tests</h2><table class='flaky-table'><thead><tr><th>Test Name</th><th>Flakiness Score</th><th>Pass Rate</th><th>Recent Pattern</th><th>Last Result</th></tr></thead><tbody>"
            for test_name, data in sorted(flaky_tests["tests"].items(), key=lambda x: x[1]["flakiness_score"], reverse=True):
                last_outcome_color = "#10b981" if data["last_outcome"] == "passed" else "#ef4444"
                flaky_tests_html += f"""
                <tr>
                    <td class='test-name'>{test_name}</td>
                    <td class='flakiness'>{data['flakiness_score']}</td>
                    <td>{data['pass_rate']}%</td>
                    <td class='pattern'>{data['recent_pattern']}</td>
                    <td style='color: {last_outcome_color}'>{data['last_outcome'].upper()}</td>
                </tr>
                """
            flaky_tests_html += "</tbody></table>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Test History Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; color: #111827; line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        h2 {{ font-size: 1.8em; margin: 30px 0 20px; color: #374151; }}
        .chart-container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .flaky-table {{ width: 100%; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .flaky-table th {{ background: #f9fafb; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb; }}
        .flaky-table td {{ padding: 12px; border-bottom: 1px solid #f3f4f6; }}
        .flaky-table tr:hover {{ background: #f9fafb; }}
        .test-name {{ font-family: monospace; font-size: 0.9em; }}
        .flakiness {{ font-weight: 600; color: #dc2626; }}
        .pattern {{ font-family: monospace; letter-spacing: 0.1em; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: 700; margin-bottom: 5px; }}
        .stat-label {{ color: #6b7280; font-size: 0.9em; }}
        .svg-chart {{ width: 100%; height: 300px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 {project_name} - Test History Report</h1>
        <p style="color: #6b7280; margin-bottom: 30px;">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{len(health_history)}</div>
                <div class="stat-label">Test Runs (30 days)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{round(statistics.mean([h['success_rate'] for h in health_history[-7:]]), 1) if health_history else 0}%</div>
                <div class="stat-label">Avg Success Rate (7 days)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(flaky_tests.get('tests', {}))}</div>
                <div class="stat-label">Flaky Tests Detected</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>📊 Success Rate Trend (Last 14 Days)</h2>
            <div class="svg-chart">
                {self._generate_svg_chart(dates, success_rates)}
            </div>
        </div>

        {flaky_tests_html}
    </div>

</body>
</html>"""

    def _generate_svg_chart(self, dates: List[str], values: List[float]) -> str:
        """Generate SVG line chart for success rates."""
        if not dates or not values:
            return '<p style="text-align: center; color: #6b7280;">No data available</p>'

        # Chart dimensions
        width = 800
        height = 300
        padding = 40
        chart_width = width - 2 * padding
        chart_height = height - 2 * padding

        # Calculate points
        points = []
        x_step = chart_width / (len(values) - 1) if len(values) > 1 else 0
        y_scale = chart_height / 100  # 0-100% scale

        for i, value in enumerate(values):
            x = padding + i * x_step
            y = padding + (100 - value) * y_scale
            points.append((x, y))

        # Create path
        path_data = f"M {points[0][0]},{points[0][1]}"
        for x, y in points[1:]:
            path_data += f" L {x},{y}"

        # Generate SVG
        svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <!-- Grid lines -->
            <g stroke="#e5e7eb" stroke-width="1">
                <!-- Horizontal lines -->
                <line x1="{padding}" y1="{padding}" x2="{width-padding}" y2="{padding}" />
                <line x1="{padding}" y1="{padding + chart_height/4}" x2="{width-padding}" y2="{padding + chart_height/4}" stroke-dasharray="5,5" />
                <line x1="{padding}" y1="{padding + chart_height/2}" x2="{width-padding}" y2="{padding + chart_height/2}" stroke-dasharray="5,5" />
                <line x1="{padding}" y1="{padding + 3*chart_height/4}" x2="{width-padding}" y2="{padding + 3*chart_height/4}" stroke-dasharray="5,5" />
                <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" />
                <!-- Vertical line -->
                <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" />
            </g>

            <!-- Y-axis labels -->
            <g fill="#6b7280" font-size="12" text-anchor="end">
                <text x="{padding-5}" y="{padding+4}">100%</text>
                <text x="{padding-5}" y="{padding + chart_height/4 + 4}">75%</text>
                <text x="{padding-5}" y="{padding + chart_height/2 + 4}">50%</text>
                <text x="{padding-5}" y="{padding + 3*chart_height/4 + 4}">25%</text>
                <text x="{padding-5}" y="{height-padding+4}">0%</text>
            </g>

            <!-- Line chart -->
            <path d="{path_data}" fill="none" stroke="#10b981" stroke-width="3" />

            <!-- Data points -->
            <g fill="#10b981">
        '''

        for i, (x, y) in enumerate(points):
            svg += f'<circle cx="{x}" cy="{y}" r="4" />'
            if i < len(dates) and i % max(1, len(dates) // 7) == 0:  # Show every nth date
                svg += f'<text x="{x}" y="{height-padding+20}" text-anchor="middle" font-size="11" fill="#6b7280">{dates[i]}</text>'

        svg += '''
            </g>
        </svg>'''

        return svg


if __name__ == "__main__":
    # Validation example
    print(f"Validating {__file__}...")

    # Create tracker
    tracker = TestHistoryTracker()

    # Add sample test runs
    for i in range(5):
        tracker.add_test_run("ExampleProject", {
            "total": 100,
            "passed": 95 - i,
            "failed": 3 + i,
            "skipped": 2,
            "duration": 45.2 + i * 2,
            "tests": [
                {"nodeid": "test_feature_a", "outcome": "passed", "duration": 1.2},
                {"nodeid": "test_feature_b", "outcome": "passed" if i % 2 == 0 else "failed", "duration": 0.8},
                {"nodeid": "test_feature_c", "outcome": "failed" if i < 2 else "passed", "duration": 2.1},
            ]
        })

    # Get trends
    trends = tracker.get_test_trends("ExampleProject", "test_feature_b", days=30)
    print(f"Test trends: {trends}")

    # Get flaky tests
    flaky = tracker.get_flaky_tests("ExampleProject")
    print(f"Flaky tests: {flaky}")

    print("✅ Test History Tracker validation passed")