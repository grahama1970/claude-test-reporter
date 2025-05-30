"""Tests for the hallucination monitoring module."""
import pytest
from unittest.mock import Mock, patch
from claude_test_reporter.monitoring.hallucination_monitor import HallucinationMonitor


class TestHallucinationMonitor:
    def test_log_detection(self):
        """Test logging of hallucination detections."""
        monitor = HallucinationMonitor()
        
        detection = {
            "timestamp": "2025-01-30T12:00:00",
            "response": "All 100 tests passed",
            "actual_results": {"total": 10, "passed": 8, "failed": 2},
            "issues": ["Claimed 100 tests when only 10 exist"],
            "severity": "HIGH"
        }
        
        # Should not raise any exceptions
        monitor.log_detection(detection)
    
    def test_check_thresholds(self):
        """Test threshold checking for alerts."""
        monitor = HallucinationMonitor()
        
        # Add multiple detections
        for i in range(5):
            monitor.metrics["detections_count"] += 1
        
        monitor.metrics["detection_rate"] = 0.6  # 60% rate
        
        threshold_exceeded = monitor._check_thresholds()
        assert threshold_exceeded  # Should exceed default 50% threshold
    
    @patch('claude_test_reporter.monitoring.hallucination_monitor.smtplib')
    def test_send_alert(self, mock_smtp):
        """Test alert sending functionality."""
        monitor = HallucinationMonitor()
        
        alert_data = {
            "type": "THRESHOLD_EXCEEDED",
            "message": "Detection rate exceeded 50%",
            "current_rate": 0.6
        }
        
        # Should complete without errors even if email not configured
        monitor._send_alert(alert_data)