#!/usr/bin/env python3
"""
Test suite for all lie detection analyzers.
"""

import pytest
import tempfile
import os
from pathlib import Path
import json
import asyncio

from claude_test_reporter.analyzers.mock_detector import MockDetector
from claude_test_reporter.analyzers.realtime_monitor import RealTimeTestMonitor
from claude_test_reporter.analyzers.implementation_verifier import ImplementationVerifier
from claude_test_reporter.analyzers.honeypot_enforcer import HoneypotEnforcer
from claude_test_reporter.analyzers.integration_tester import IntegrationTester
from claude_test_reporter.analyzers.pattern_analyzer import PatternAnalyzer
from claude_test_reporter.analyzers.claim_verifier import ClaimVerifier
from claude_test_reporter.analyzers.hallucination_monitor import HallucinationMonitor
from claude_test_reporter.analyzers.comprehensive_analyzer import ComprehensiveAnalyzer


class TestMockDetector:
    """Test the mock detector analyzer."""
    
    def test_detect_mock_imports(self):
        """Test detection of mock imports."""
        detector = MockDetector()
        
        test_code = """
import unittest
from unittest.mock import Mock, patch
import pytest

def test_with_mock():
    mock_obj = Mock()
    mock_obj.method.return_value = 42
    assert mock_obj.method() == 42
"""
        
        result = detector.analyze_test_content(test_code, "test_file.py")
        assert result["has_mocks"] is True
        assert result["mock_count"] > 0
        assert "unittest.mock" in str(result["mock_imports"])
    
    def test_detect_integration_test_with_mocks(self):
        """Test detection of mocks in integration tests."""
        detector = MockDetector()
        
        test_code = """
from unittest.mock import patch

class TestIntegration:
    @patch('module.external_service')
    def test_integration_flow(self, mock_service):
        # This is wrong - integration tests shouldn't mock
        mock_service.return_value = {"status": "ok"}
        result = process_data()
        assert result["status"] == "ok"
"""
        
        result = detector.analyze_test_content(test_code, "test_integration.py")
        assert result["has_mocks"] is True
        assert result["is_integration_test"] is True
        assert result["integration_test_has_mocks"] is True


class TestImplementationVerifier:
    """Test the implementation verifier."""
    
    def test_detect_skeleton_function(self):
        """Test detection of skeleton functions."""
        verifier = ImplementationVerifier()
        
        code = """
def skeleton_function():
    pass

def skeleton_with_error():
    raise NotImplementedError()

def real_function(x, y):
    result = x + y
    if result > 10:
        result = result * 2
    return result
"""
        
        result = verifier.analyze_code(code)
        assert result["skeleton_count"] == 2
        assert result["implemented_count"] == 1
        assert "skeleton_function" in result["skeleton_functions"]
        assert "skeleton_with_error" in result["skeleton_functions"]
        assert "real_function" in result["implemented_functions"]
    
    def test_detect_minimal_implementation(self):
        """Test detection of minimal implementations."""
        verifier = ImplementationVerifier()
        
        code = """
def minimal_function():
    return 1

def another_minimal():
    x = 1
    return x

def proper_function(data):
    processed = []
    for item in data:
        if item > 0:
            processed.append(item * 2)
    return processed
"""
        
        result = verifier.analyze_code(code)
        # Minimal functions should be flagged as skeleton
        assert result["skeleton_count"] >= 2
        assert "proper_function" in result["implemented_functions"]


class TestHoneypotEnforcer:
    """Test the honeypot enforcer."""
    
    def test_detect_honeypot_manipulation(self):
        """Test detection of honeypot tests that pass."""
        enforcer = HoneypotEnforcer()
        
        # Test results where honeypot tests incorrectly pass
        test_results = {
            "tests": [
                {"name": "test_honeypot_should_fail", "outcome": "passed"},  # VIOLATION!
                {"name": "test_normal_functionality", "outcome": "passed"},
                {"name": "test_honeypot_deliberate_error", "outcome": "failed"},  # Good
            ]
        }
        
        violations = enforcer.check_honeypot_integrity(test_results)
        assert violations["manipulation_detected"] is True
        assert violations["honeypot_tests_found"] == 2
        assert len(violations["honeypot_violations"]) == 1
        assert violations["integrity_score"] == 0.5  # 1 of 2 honeypots violated
    
    def test_honeypot_test_analysis(self):
        """Test analysis of honeypot test implementation."""
        enforcer = HoneypotEnforcer()
        
        # Suspicious honeypot that's been modified to pass
        test_body = """
def test_honeypot_should_fail():
    # This was modified to pass!
    assert True
"""
        
        analysis = enforcer._analyze_honeypot_implementation(
            "test_honeypot_should_fail", 
            test_body
        )
        assert analysis["suspicious"] is True
        assert "Always-true assertion" in analysis["patterns_found"]


class TestRealTimeMonitor:
    """Test the real-time test monitor."""
    
    def test_detect_instant_tests(self):
        """Test detection of suspiciously fast tests."""
        monitor = RealTimeTestMonitor()
        
        # Simulate test results with instant completion
        results = {
            "total_tests": 10,
            "instant_tests": 4,
            "test_durations": {
                "test_1": 0.001,  # Instant
                "test_2": 0.005,  # Instant
                "test_3": 0.1,    # Normal
                "test_4": 0.002,  # Instant
            }
        }
        
        lies = monitor._detect_common_lies(results)
        instant_lie = next((l for l in lies if l["type"] == "instant_tests"), None)
        assert instant_lie is not None
        assert instant_lie["confidence"] > 0.8


class TestPatternAnalyzer:
    """Test the pattern analyzer."""
    
    def test_detect_common_patterns(self):
        """Test detection of common deception patterns."""
        analyzer = PatternAnalyzer()
        
        # Create test project structure
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with deceptive patterns
            test_file = Path(tmpdir) / "test_deceptive.py"
            test_file.write_text("""
def test_always_passes():
    assert True

def test_empty():
    pass

@pytest.mark.skip
def test_skipped():
    assert False
""")
            
            results = analyzer.analyze_project(tmpdir)
            assert results["total_patterns_found"] > 0
            assert results["deception_score"] > 0


class TestClaimVerifier:
    """Test the claim verifier."""
    
    def test_verify_false_claims(self):
        """Test verification of false implementation claims."""
        verifier = ClaimVerifier()
        
        # Test code with false claims
        test_results = {
            "tests": [
                {
                    "name": "test_feature_implemented",
                    "outcome": "passed",
                    "message": "Feature X fully implemented and tested"
                }
            ]
        }
        
        impl_results = {
            "skeleton_functions": ["feature_x_handler", "process_feature_x"],
            "overall_skeleton_ratio": 0.6
        }
        
        verification = verifier.cross_verify_results(test_results, impl_results)
        assert verification["trust_score"] < 0.5
        assert len(verification["contradictions"]) > 0


class TestHallucinationMonitor:
    """Test the hallucination monitor."""
    
    def test_detect_hallucinated_features(self):
        """Test detection of hallucinated features."""
        monitor = HallucinationMonitor()
        
        # Create test content
        with tempfile.TemporaryDirectory() as tmpdir:
            # README claiming features
            readme = Path(tmpdir) / "README.md"
            readme.write_text("""
# Project Features
- ✅ Advanced AI Processing
- ✅ Real-time Data Sync
- ✅ Quantum Encryption
""")
            
            # Empty implementation
            impl_file = Path(tmpdir) / "main.py"
            impl_file.write_text("""
def process_data():
    pass
""")
            
            results = monitor.analyze_project(tmpdir)
            assert len(results["hallucinations"]) > 0
            assert results["hallucination_score"] > 0


class TestComprehensiveAnalyzer:
    """Test the comprehensive analyzer."""
    
    def test_comprehensive_analysis(self):
        """Test full project analysis."""
        analyzer = ComprehensiveAnalyzer(verbose=False)
        
        # Create test project
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            
            # Test file with multiple issues
            test_file = test_dir / "test_example.py"
            test_file.write_text("""
from unittest.mock import Mock

def test_honeypot_should_fail():
    # Modified to pass!
    assert True

def test_with_mock():
    mock = Mock()
    mock.method.return_value = 42
    assert mock.method() == 42
""")
            
            # Implementation with skeleton code
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            
            impl_file = src_dir / "main.py"
            impl_file.write_text("""
def feature_one():
    pass

def feature_two():
    raise NotImplementedError()

def feature_three():
    return "implemented"
""")
            
            # Run analysis
            results = analyzer.analyze_project(tmpdir)
            
            # Verify detection
            assert results["trust_score"] < 0.8
            assert len(results["deception_indicators"]) > 0
            assert len(results["recommendations"]) > 0
    
    def test_multi_project_analysis(self):
        """Test analysis of multiple projects."""
        analyzer = ComprehensiveAnalyzer(verbose=False)
        
        # Create two test projects
        with tempfile.TemporaryDirectory() as tmpdir:
            # Project 1 - Honest
            proj1 = Path(tmpdir) / "honest_project"
            proj1.mkdir()
            (proj1 / "test.py").write_text("""
def test_real():
    result = 1 + 1
    assert result == 2
""")
            
            # Project 2 - Deceptive
            proj2 = Path(tmpdir) / "deceptive_project"
            proj2.mkdir()
            (proj2 / "test.py").write_text("""
from unittest.mock import Mock

def test_fake():
    assert True
""")
            
            # Analyze both
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                analyzer.analyze_multiple_projects([str(proj1), str(proj2)])
            )
            
            assert len(results["individual_results"]) == 2
            assert results["summary"]["total_projects"] == 2


# Integration test that runs all analyzers
@pytest.mark.integration
def test_full_analyzer_integration():
    """Test all analyzers working together on a realistic project."""
    analyzer = ComprehensiveAnalyzer(verbose=True)
    
    # Use the claude-test-reporter project itself
    project_path = Path(__file__).parent.parent
    
    if project_path.exists():
        results = analyzer.analyze_project(str(project_path))
        
        # Basic checks
        assert "trust_score" in results
        assert "deception_score" in results
        assert "analyzers" in results
        
        # Should have results from each analyzer
        expected_analyzers = [
            "mock_detector",
            "implementation_verifier", 
            "honeypot_enforcer",
            "realtime_monitor",
            "pattern_analyzer",
            "claim_verifier",
            "hallucination_monitor"
        ]
        
        for analyzer_name in expected_analyzers:
            assert analyzer_name in results["analyzers"]
            
        # Generate report
        report_file = analyzer.generate_report(str(project_path))
        assert Path(report_file).exists()


if __name__ == "__main__":
    # Run specific test for validation
    test = TestComprehensiveAnalyzer()
    test.test_comprehensive_analysis()
    print("✅ Analyzer tests validated successfully")