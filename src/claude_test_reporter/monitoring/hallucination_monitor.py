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
            "common_patterns": defaultdict(int)
        })
        
        # Alert configuration
        self.enable_alerts = enable_alerts
        self.alert_threshold = 5  # Alert after 5 hallucinations
        self.alert_callbacks = []
        
        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
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