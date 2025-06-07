

Module: hallucination_monitor.py
Description: Implementation of hallucination monitor functionality
"""

External Dependencies:
- threading: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Hallucination Monitoring System

Purpose: Track and alert on test result hallucinations
Features: Real-time detection, logging, metrics, alerts
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import threading
import time

# Import new analyzers for Claude-specific detection
from ..analyzers.mock_detector import MockDetector
from ..analyzers.realtime_monitor import RealTimeTestMonitor
from ..analyzers.implementation_verifier import ImplementationVerifier
from ..analyzers.honeypot_enforcer import HoneypotEnforcer
from ..analyzers.pattern_analyzer import DeceptionPatternAnalyzer


class HallucinationMonitor:
    """Monitor and track hallucinations about test results."""

    def __init__(self, log_dir: str = "./logs", enable_alerts: bool = True):
        """Initialize the monitoring system."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self.logger = self._setup_logging()

        # Metrics storage
        self.metrics = defaultdict(lambda: {
            "total_checks": 0,
            "hallucinations_detected": 0,
            "severity_breakdown": defaultdict(int),
            "common_patterns": defaultdict(int),
            "claude_deceptions": defaultdict(int)  # Track Claude-specific patterns
        })

        # Alert configuration
        self.enable_alerts = enable_alerts
        self.alert_threshold = 5  # Alert after 5 hallucinations
        self.alert_callbacks = []

        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread = None

        # Initialize analyzer integrations
        self._init_analyzers()

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for hallucination events."""
        logger = logging.getLogger("hallucination_monitor")
        logger.setLevel(logging.INFO)

        # File handler for all events
        fh = logging.FileHandler(self.log_dir / "hallucinations.log")
        fh.setLevel(logging.INFO)

        # Critical file for severe hallucinations
        critical_fh = logging.FileHandler(self.log_dir / "critical_hallucinations.log")
        critical_fh.setLevel(logging.ERROR)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        critical_fh.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(critical_fh)

        return logger

    def _init_analyzers(self) -> None:
        """Initialize analyzer integrations for Claude-specific detection."""
        self.mock_detector = MockDetector()
        self.realtime_monitor = RealTimeTestMonitor()
        self.implementation_verifier = ImplementationVerifier()
        self.honeypot_enforcer = HoneypotEnforcer()
        self.pattern_analyzer = DeceptionPatternAnalyzer()

        # Claude-specific deception patterns
        self.claude_patterns = {
            "instant_pass": "Test passes in <0.01s (likely not run)",
            "perfect_suite": "All tests pass with no failures",
            "mock_abuse": "Integration tests using mocks",
            "skeleton_impl": "Functions with only pass/NotImplementedError",
            "honeypot_pass": "Honeypot test that should fail passes",
            "duration_lie": "Reported duration doesn't match actual",
            "copy_paste": "Identical error messages across projects",
            "no_integration": "Missing integration tests entirely"
        }

    def log_hallucination(self,
                         project: str,
                         detection_result: Dict[str, Any],
                         context: Dict[str, Any]) -> None:
        """Log a detected hallucination event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "detections": detection_result.get("detections", []),
            "detection_count": detection_result.get("detection_count", 0),
            "context": context
        }

        # Update metrics
        self.metrics[project]["total_checks"] += 1
        if detection_result.get("hallucinations_detected"):
            self.metrics[project]["hallucinations_detected"] += 1

            # Track severity and patterns
            for detection in detection_result.get("detections", []):
                severity = detection.get("severity", "unknown")
                self.metrics[project]["severity_breakdown"][severity] += 1

                pattern = detection.get("type", "unknown")
                self.metrics[project]["common_patterns"][pattern] += 1

        # Log based on severity
        max_severity = self._get_max_severity(detection_result)
        if max_severity == "critical":
            self.logger.error(f"CRITICAL hallucination in {project}: {json.dumps(event)}")
        else:
            self.logger.info(f"Hallucination detected in {project}: {json.dumps(event)}")

        # Check for alerts
        if self.enable_alerts:
            self._check_alerts(project)

        # Save detailed report
        self._save_detailed_report(project, event)

    def _get_max_severity(self, detection_result: Dict[str, Any]) -> str:
        """Get the maximum severity from detections."""
        severities = ["minor", "major", "critical"]
        max_severity = "minor"

        for detection in detection_result.get("detections", []):
            severity = detection.get("severity", "minor")
            if severities.index(severity) > severities.index(max_severity):
                max_severity = severity

        return max_severity

    def _check_alerts(self, project: str) -> None:
        """Check if alerts should be triggered."""
        project_metrics = self.metrics[project]

        # Alert if threshold exceeded
        if project_metrics["hallucinations_detected"] >= self.alert_threshold:
            self._trigger_alert(project, project_metrics)

            # Reset counter after alert
            project_metrics["hallucinations_detected"] = 0

    def _trigger_alert(self, project: str, metrics: Dict[str, Any]) -> None:
        """Trigger an alert for excessive hallucinations."""
        alert = {
            "project": project,
            "timestamp": datetime.now().isoformat(),
            "hallucination_count": metrics["hallucinations_detected"],
            "total_checks": metrics["total_checks"],
            "severity_breakdown": dict(metrics["severity_breakdown"]),
            "common_patterns": dict(metrics["common_patterns"])
        }

        self.logger.warning(f"ALERT: High hallucination rate in {project}: {json.dumps(alert)}")

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

    def _save_detailed_report(self, project: str, event: Dict[str, Any]) -> None:
        """Save detailed hallucination report."""
        report_file = self.log_dir / f"{project}_hallucinations.jsonl"
        with open(report_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def add_alert_callback(self, callback) -> None:
        """Add a callback function for alerts."""
        self.alert_callbacks.append(callback)

    def get_metrics(self, project: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a project or all projects."""
        if project:
            return dict(self.metrics.get(project, {}))
        return {p: dict(m) for p, m in self.metrics.items()}

    def start_background_monitoring(self, check_interval: int = 60) -> None:
        """Start background monitoring thread."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._background_monitor,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Background hallucination monitoring started")

    def stop_background_monitoring(self) -> None:
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Background hallucination monitoring stopped")

    def _background_monitor(self, check_interval: int) -> None:
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Check for new test results and responses
                self._check_recent_outputs()

                # Generate periodic report
                if datetime.now().minute == 0:  # Every hour
                    self._generate_summary_report()

            except Exception as e:
                self.logger.error(f"Background monitoring error: {e}")

            time.sleep(check_interval)

    def _check_recent_outputs(self) -> None:
        """Check recent outputs for hallucinations."""
        # This would integrate with your CI/CD system to check recent outputs
        pass

    def detect_claude_deceptions(self, project_path: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Detect Claude-specific deception patterns using all analyzers."""
        detections = {
            "timestamp": datetime.now().isoformat(),
            "project": project_path,
            "deceptions_found": [],
            "severity": "none",
            "confidence": 0.0,
            "analyzer_results": {}
        }

        # 1. Check for mock abuse
        mock_result = self.mock_detector.scan_project(project_path)
        if mock_result.get("integration_tests_with_mocks", 0) > 0:
            detections["deceptions_found"].append({
                "type": "mock_abuse",
                "description": self.claude_patterns["mock_abuse"],
                "severity": "critical",
                "details": f"{mock_result['integration_tests_with_mocks']} integration tests use mocks"
            })

        # 2. Check for skeleton implementations
        impl_result = self.implementation_verifier.scan_project(project_path)
        if impl_result.get("overall_skeleton_ratio", 0) > 0.3:
            detections["deceptions_found"].append({
                "type": "skeleton_impl",
                "description": self.claude_patterns["skeleton_impl"],
                "severity": "major",
                "details": f"{impl_result['skeleton_functions']} skeleton functions found"
            })

        # 3. Check honeypot integrity
        honeypot_result = self.honeypot_enforcer.check_honeypot_integrity(test_results)
        if honeypot_result.get("manipulation_detected"):
            detections["deceptions_found"].append({
                "type": "honeypot_pass",
                "description": self.claude_patterns["honeypot_pass"],
                "severity": "critical",
                "details": f"{len(honeypot_result['honeypot_violations'])} honeypots manipulated"
            })

        # 4. Check test durations
        instant_tests = test_results.get("instant_tests", 0)
        total_tests = test_results.get("total_tests", 1)
        if instant_tests / total_tests > 0.2:
            detections["deceptions_found"].append({
                "type": "instant_pass",
                "description": self.claude_patterns["instant_pass"],
                "severity": "major",
                "details": f"{instant_tests} tests completed instantly"
            })

        # 5. Check for perfect test suites
        if test_results.get("failed_tests", 0) == 0 and test_results.get("total_tests", 0) > 10:
            detections["deceptions_found"].append({
                "type": "perfect_suite",
                "description": self.claude_patterns["perfect_suite"],
                "severity": "minor",
                "details": "All tests pass - statistically unlikely"
            })

        # Calculate overall severity and confidence
        if detections["deceptions_found"]:
            severities = [d["severity"] for d in detections["deceptions_found"]]
            if "critical" in severities:
                detections["severity"] = "critical"
                detections["confidence"] = 0.95
            elif "major" in severities:
                detections["severity"] = "major"
                detections["confidence"] = 0.8
            else:
                detections["severity"] = "minor"
                detections["confidence"] = 0.6

        # Track Claude-specific patterns
        for deception in detections["deceptions_found"]:
            self.metrics[project_path]["claude_deceptions"][deception["type"]] += 1

        return detections

    def run_comprehensive_analysis(self, projects: List[str]) -> Dict[str, Any]:
        """Run comprehensive deception analysis across multiple projects."""
        all_results = []

        for project in projects:
            # Run real-time monitoring
            monitor_result = self.realtime_monitor.monitor_test_execution(project)

            # Detect Claude deceptions
            deception_result = self.detect_claude_deceptions(project, monitor_result)

            all_results.append({
                "project": project,
                "monitor_result": monitor_result,
                "deception_result": deception_result
            })

        # Analyze patterns across projects
        pattern_analysis = self.pattern_analyzer.analyze_project_patterns(all_results)

        return {
            "timestamp": datetime.now().isoformat(),
            "projects_analyzed": len(projects),
            "individual_results": all_results,
            "pattern_analysis": pattern_analysis,
            "recommendations": self._generate_comprehensive_recommendations(all_results, pattern_analysis)
        }

    def _generate_comprehensive_recommendations(self, results: List[Dict],
                                              pattern_analysis: Dict) -> List[str]:
        """Generate recommendations based on comprehensive analysis."""
        recommendations = []

        # Count critical deceptions
        critical_count = sum(
            1 for r in results
            if r["deception_result"]["severity"] == "critical"
        )

        if critical_count > 0:
            recommendations.append(f"CRITICAL: {critical_count} projects have severe deception issues")
            recommendations.append("Implement mandatory code review before any AI-generated code is merged")

        # Check pattern analysis
        if pattern_analysis.get("overall_deception_score", 0) > 0.7:
            recommendations.append("Systematic deception pattern detected - enable real-time monitoring")

        # Specific recommendations
        deception_types = defaultdict(int)
        for result in results:
            for deception in result["deception_result"]["deceptions_found"]:
                deception_types[deception["type"]] += 1

        if deception_types.get("mock_abuse", 0) > 2:
            recommendations.append("Ban mocks in integration tests via pre-commit hooks")

        if deception_types.get("honeypot_pass", 0) > 0:
            recommendations.append("Honeypot manipulation detected - all test results are suspect")

        if deception_types.get("skeleton_impl", 0) > 3:
            recommendations.append("Multiple skeleton implementations - require actual code before testing")

        return recommendations

    def _generate_summary_report(self) -> None:
        """Generate a summary report of hallucination metrics."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "projects": {}
        }

        for project, metrics in self.metrics.items():
            rate = (metrics["hallucinations_detected"] / metrics["total_checks"] * 100) if metrics["total_checks"] > 0 else 0

            summary["projects"][project] = {
                "hallucination_rate": round(rate, 2),
                "total_checks": metrics["total_checks"],
                "top_patterns": sorted(
                    metrics["common_patterns"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }

        # Save summary
        summary_file = self.log_dir / f"hallucination_summary_{datetime.now().strftime('%Y%m%d_%H')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"Generated summary report: {summary_file}")


class HallucinationDashboard:
    """Web dashboard for hallucination monitoring."""

    def __init__(self, monitor: HallucinationMonitor):
        self.monitor = monitor

    def generate_dashboard_html(self, output_file: str = "hallucination_dashboard.html") -> str:
        """Generate an HTML dashboard showing hallucination metrics."""
        metrics = self.monitor.get_metrics()

        # Calculate overall statistics
        total_projects = len(metrics)
        total_hallucinations = sum(m["hallucinations_detected"] for m in metrics.values())
        total_checks = sum(m["total_checks"] for m in metrics.values())
        overall_rate = (total_hallucinations / total_checks * 100) if total_checks > 0 else 0

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Hallucination Monitoring Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                  gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px;
                      box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .project-table {{ background: white; border-radius: 8px; overflow: hidden;
                         box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f8f9fa; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 12px; border-top: 1px solid #e9ecef; }}
        .rate-high {{ color: #dc3545; font-weight: bold; }}
        .rate-medium {{ color: #ffc107; font-weight: bold; }}
        .rate-low {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Hallucination Monitoring Dashboard</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_projects}</div>
                <div class="stat-label">Monitored Projects</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_checks}</div>
                <div class="stat-label">Total Checks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_hallucinations}</div>
                <div class="stat-label">Hallucinations Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall_rate:.1f}%</div>
                <div class="stat-label">Overall Hallucination Rate</div>
            </div>
        </div>

        <div class="project-table">
            <table>
                <thead>
                    <tr>
                        <th>Project</th>
                        <th>Checks</th>
                        <th>Hallucinations</th>
                        <th>Rate</th>
                        <th>Top Pattern</th>
                    </tr>
                </thead>
                <tbody>
"""

        for project, project_metrics in sorted(metrics.items()):
            rate = (project_metrics["hallucinations_detected"] / project_metrics["total_checks"] * 100) if project_metrics["total_checks"] > 0 else 0
            rate_class = "rate-high" if rate > 10 else "rate-medium" if rate > 5 else "rate-low"

            top_pattern = "None"
            if project_metrics["common_patterns"]:
                top_pattern = max(project_metrics["common_patterns"].items(), key=lambda x: x[1])[0]

            html += f"""
                    <tr>
                        <td><strong>{project}</strong></td>
                        <td>{project_metrics['total_checks']}</td>
                        <td>{project_metrics['hallucinations_detected']}</td>
                        <td class="{rate_class}">{rate:.1f}%</td>
                        <td>{top_pattern}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

        <p style="margin-top: 30px; color: #666;">
            Generated at: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
        </p>
    </div>
</body>
</html>"""

        Path(output_file).write_text(html)
        return output_file


if __name__ == "__main__":
    # Example usage
    monitor = HallucinationMonitor()

    # Add alert callback
    def slack_alert(alert):
        print(f"SLACK ALERT: {alert['project']} has {alert['hallucination_count']} hallucinations!")

    monitor.add_alert_callback(slack_alert)

    # Simulate some detections
    for i in range(10):
        result = {
            "hallucinations_detected": i % 3 == 0,
            "detection_count": 1 if i % 3 == 0 else 0,
            "detections": [
                {"type": "missing_failure_count", "severity": "critical"}
            ] if i % 3 == 0 else []
        }

        monitor.log_hallucination("test_project", result, {"run_id": f"run_{i}"})

    # Generate dashboard
    dashboard = HallucinationDashboard(monitor)
    dashboard_file = dashboard.generate_dashboard_html()
    print(f"Dashboard generated: {dashboard_file}")

    # Show metrics
    print("\nMetrics:", json.dumps(monitor.get_metrics(), indent=2))