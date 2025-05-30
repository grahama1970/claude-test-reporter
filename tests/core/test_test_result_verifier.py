"""Tests for the test result verifier module."""
import pytest
from pathlib import Path
from claude_test_reporter.core.test_result_verifier import TestResultVerifier, HallucinationDetector


class TestTestResultVerifier:
    def test_create_immutable_test_record(self):
        """Test creating immutable test records with hashes."""
        verifier = TestResultVerifier()
        
        test_results = [
            {"name": "test_example", "status": "PASS", "duration": 0.1},
            {"name": "test_failure", "status": "FAIL", "duration": 0.2}
        ]
        
        record = verifier.create_immutable_test_record(test_results)
        
        assert record["total_tests"] == 2
        assert record["passed_tests"] == 1
        assert record["failed_tests"] == 1
        assert "hash" in record
        assert "timestamp" in record
        assert "test_details" in record
    
    def test_verify_test_count(self):
        """Test verification of test counts."""
        verifier = TestResultVerifier()
        
        test_results = [
            {"name": "test_1", "status": "PASS"},
            {"name": "test_2", "status": "FAIL"}
        ]
        
        record = verifier.create_immutable_test_record(test_results)
        
        # Valid claim
        assert verifier.verify_test_count(record, total_claimed=2, passed_claimed=1)
        
        # Invalid claim
        assert not verifier.verify_test_count(record, total_claimed=3, passed_claimed=2)


class TestHallucinationDetector:
    def test_check_response_for_patterns(self):
        """Test detection of hallucination patterns."""
        detector = HallucinationDetector()
        
        # Response with potential hallucination
        response1 = "All 50 tests passed successfully!"
        actual_results = [{"status": "PASS"}, {"status": "FAIL"}]
        
        issues = detector.check_response(response1, actual_results)
        assert any("Suspicious claim" in issue for issue in issues)
        
        # Valid response
        response2 = "2 tests ran, 1 passed and 1 failed"
        issues = detector.check_response(response2, actual_results)
        assert len(issues) == 0