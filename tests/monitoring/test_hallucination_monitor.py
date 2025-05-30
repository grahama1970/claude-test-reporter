"""Tests for the hallucination monitoring module."""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from claude_test_reporter.monitoring.hallucination_monitor import HallucinationMonitor, HallucinationDashboard


class TestHallucinationMonitor:
    def test_init(self):
        """Test monitor initialization."""
        monitor = HallucinationMonitor()
        assert monitor.log_dir.exists()
        assert monitor.alert_threshold == 5
        assert monitor.enable_alerts == True
    
    def test_log_hallucination(self):
        """Test logging a hallucination detection."""
        monitor = HallucinationMonitor()
        
        # Log a detection
        monitor.log_hallucination(
            project="test_project",
            detection_result={
                "detections": [{"type": "count_mismatch", "severity": "critical", "description": "Claimed 100 tests when only 10 exist"}],
                "detection_count": 1,
                "has_hallucination": True,
                "severity": "HIGH"
            },
            context={
                "test_results": {"total": 10, "passed": 8, "failed": 2},
                "llm_response": "All 100 tests passed"
            }
        )
        
        # Check metrics were updated
        metrics = monitor.get_metrics()
        assert "test_project" in metrics
    
    def test_get_metrics(self):
        """Test getting metrics."""
        monitor = HallucinationMonitor()
        
        # Log some data
        monitor.log_hallucination(
            project="test_project",
            detection_result={
                "detections": [{"type": "generic", "severity": "major", "description": "Test issue"}],
                "detection_count": 1,
                "severity": "MEDIUM"
            },
            context={
                "test_results": {"total": 5},
                "llm_response": "Test response"
            }
        )
        
        # Get metrics
        metrics = monitor.get_metrics("test_project")
        
        assert "total_checks" in metrics
        assert metrics["total_checks"] > 0
    
    def test_dashboard_generation(self):
        """Test dashboard HTML generation."""
        monitor = HallucinationMonitor()
        dashboard = HallucinationDashboard(monitor)
        
        # Generate dashboard (should create file)
        dashboard_path = dashboard.generate_dashboard_html()
        
        assert os.path.exists(dashboard_path)
        assert dashboard_path.endswith(".html")