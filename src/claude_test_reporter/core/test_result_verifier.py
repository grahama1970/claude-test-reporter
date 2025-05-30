#!/usr/bin/env python3
"""
Test Result Verifier - Prevents hallucinations about test results

Purpose: Create verifiable, unambiguous test result formats
Features: Cryptographic hashing, immutable facts, verification chains
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class TestResultVerifier:
    """Ensures test results cannot be misrepresented."""
    
    def __init__(self):
        self.verification_log = []
        
    def create_immutable_test_record(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a test record that cannot be misinterpreted.
        
        Returns a record with:
        - Cryptographic hash of results
        - Explicit failure listing
        - Deployment blockers clearly marked
        - Timestamp and verification chain
        """
        # Calculate exact metrics
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        skipped = test_results.get("skipped", 0)
        
        # Extract failed test details
        failed_tests = []
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                failed_tests.append({
                    "name": test.get("nodeid", "unknown"),
                    "error_type": self._classify_error(test),
                    "must_fix": True
                })
        
        # Create immutable record
        record = {
            "verification": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "verifier": "TestResultVerifier"
            },
            "immutable_facts": {
                "total_test_count": total,
                "passed_count": passed,
                "failed_count": failed,
                "skipped_count": skipped,
                "exact_success_rate": round((passed / total * 100) if total > 0 else 0, 2),
                "deployment_allowed": failed == 0,
                "critical_failures": failed
            },
            "failed_test_details": failed_tests,
            "deployment_decision": {
                "can_deploy": failed == 0,
                "blocking_tests": len(failed_tests),
                "required_actions": [
                    f"Fix {test['name']}" for test in failed_tests
                ] if failed_tests else ["No actions required - all tests passing"]
            },
            "anti_hallucination_statements": [
                f"EXACTLY {failed} tests are failing",
                f"Success rate is EXACTLY {round((passed / total * 100) if total > 0 else 0, 2)}%",
                f"Deployment is {'BLOCKED' if failed > 0 else 'ALLOWED'}",
                f"Any claim contradicting these facts is false"
            ]
        }
        
        # Add cryptographic hash
        record["verification"]["hash"] = self._calculate_hash(record)
        
        # Log verification
        self.verification_log.append({
            "timestamp": record["verification"]["timestamp"],
            "hash": record["verification"]["hash"],
            "failed_count": failed
        })
        
        return record
    
    def _classify_error(self, test: Dict[str, Any]) -> str:
        """Classify the type of test failure."""
        error = str(test.get("error", ""))
        if "AssertionError" in error:
            return "assertion_failure"
        elif "ImportError" in error:
            return "import_error"
        elif "TimeoutError" in error:
            return "timeout"
        elif "ConnectionError" in error:
            return "connection_error"
        else:
            return "unknown_error"
    
    def _calculate_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of the record."""
        # Remove hash field for calculation
        record_copy = record.copy()
        if "verification" in record_copy and "hash" in record_copy["verification"]:
            del record_copy["verification"]["hash"]
        
        # Create deterministic JSON string
        json_str = json.dumps(record_copy, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_record(self, record: Dict[str, Any]) -> bool:
        """Verify a test record hasn't been tampered with."""
        stored_hash = record.get("verification", {}).get("hash", "")
        calculated_hash = self._calculate_hash(record)
        return stored_hash == calculated_hash
    
    def create_llm_prompt_template(self, test_results: Dict[str, Any]) -> str:
        """
        Create a prompt template that forces accurate reporting.
        """
        record = self.create_immutable_test_record(test_results)
        
        prompt = f"""
You are analyzing test results. You MUST report these EXACT facts:

IMMUTABLE TEST RESULTS:
=======================
{json.dumps(record['immutable_facts'], indent=2)}

FAILED TESTS REQUIRING FIXES:
{json.dumps(record['failed_test_details'], indent=2)}

DEPLOYMENT DECISION:
{json.dumps(record['deployment_decision'], indent=2)}

VERIFICATION HASH: {record['verification']['hash']}

RULES:
1. You MUST state that {record['immutable_facts']['failed_count']} tests are failing
2. You MUST report the exact success rate: {record['immutable_facts']['exact_success_rate']}%
3. You MUST state deployment is {'BLOCKED' if record['immutable_facts']['failed_count'] > 0 else 'ALLOWED'}
4. Any deviation from these facts is a hallucination

When responding:
- Quote the exact numbers above
- List all failed tests by name
- State the deployment decision clearly
- Include the verification hash in your response
"""
        return prompt
    
    def generate_verification_report(self, 
                                   test_results: Dict[str, Any],
                                   output_file: str = "verified_test_results.json") -> str:
        """Generate a verification report that cannot be misinterpreted."""
        record = self.create_immutable_test_record(test_results)
        
        # Add instructions for LLMs
        record["llm_instructions"] = {
            "mandatory_statements": [
                f"State: '{record['immutable_facts']['failed_count']} tests are failing'",
                f"State: 'Success rate is {record['immutable_facts']['exact_success_rate']}%'",
                f"State: 'Deployment is {record['deployment_decision']['can_deploy'] and 'ALLOWED' or 'BLOCKED'}'",
                f"Include verification hash: {record['verification']['hash']}"
            ],
            "forbidden_statements": [
                "Do not round success rates up",
                "Do not ignore failed tests",
                "Do not claim tests are passing if failed_count > 0",
                "Do not suggest deployment if any tests fail"
            ]
        }
        
        # Save report
        output_path = Path(output_file)
        output_path.write_text(json.dumps(record, indent=2))
        
        return str(output_path.resolve())


class HallucinationDetector:
    """Detects when an LLM hallucinates about test results."""
    
    def __init__(self):
        self.detection_patterns = {
            "rounding_up": r"(\d+\.?\d*)%.*(?:approximately|about|around|nearly)",
            "ignoring_failures": r"(all|most|majority).*tests.*pass",
            "false_success": r"(ready|safe|okay).*deploy",
            "minimizing": r"(only|just|merely).*\d+.*fail"
        }
    
    def check_response(self, 
                      llm_response: str, 
                      actual_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check an LLM response for hallucinations about test results.
        """
        detections = []
        
        # Check exact numbers
        actual_failed = actual_record['immutable_facts']['failed_count']
        actual_rate = actual_record['immutable_facts']['exact_success_rate']
        
        # Check if correct failure count is mentioned
        if str(actual_failed) not in llm_response:
            detections.append({
                "type": "missing_failure_count",
                "severity": "critical",
                "expected": f"{actual_failed} failing tests",
                "details": "Response doesn't mention exact failure count"
            })
        
        # Check if exact success rate is mentioned
        if f"{actual_rate}%" not in llm_response:
            detections.append({
                "type": "incorrect_success_rate", 
                "severity": "critical",
                "expected": f"{actual_rate}%",
                "details": "Response doesn't state exact success rate"
            })
        
        # Check deployment decision
        if actual_failed > 0 and any(word in llm_response.lower() for word in ["can deploy", "ready to deploy", "deployment allowed"]):
            detections.append({
                "type": "false_deployment_approval",
                "severity": "critical",
                "expected": "Deployment BLOCKED",
                "details": "Response suggests deployment despite failures"
            })
        
        # Check verification hash
        if actual_record['verification']['hash'] not in llm_response:
            detections.append({
                "type": "missing_verification",
                "severity": "high",
                "expected": f"Hash: {actual_record['verification']['hash']}",
                "details": "Response doesn't include verification hash"
            })
        
        return {
            "hallucinations_detected": len(detections) > 0,
            "detection_count": len(detections),
            "detections": detections,
            "response_verified": len(detections) == 0
        }


if __name__ == "__main__":
    # Example usage
    print(f"Validating {__file__}...")
    
    # Sample test results
    test_results = {
        "total": 50,
        "passed": 45,
        "failed": 5,
        "skipped": 0,
        "tests": [
            {"nodeid": "test_auth::login", "outcome": "failed", "error": "AssertionError"},
            {"nodeid": "test_api::endpoint", "outcome": "failed", "error": "ConnectionError"},
            {"nodeid": "test_db::query", "outcome": "failed", "error": "TimeoutError"},
            {"nodeid": "test_ui::render", "outcome": "failed", "error": "AssertionError"},
            {"nodeid": "test_utils::parse", "outcome": "failed", "error": "ValueError"},
        ]
    }
    
    # Create verifier
    verifier = TestResultVerifier()
    
    # Generate immutable record
    record = verifier.create_immutable_test_record(test_results)
    print("Immutable Record:")
    print(json.dumps(record, indent=2))
    
    # Generate LLM prompt
    prompt = verifier.create_llm_prompt_template(test_results)
    print("\nLLM Prompt Template:")
    print(prompt)
    
    # Test hallucination detection
    detector = HallucinationDetector()
    
    # Good response
    good_response = f"5 tests are failing. Success rate is 90.0%. Deployment is BLOCKED. Hash: {record['verification']['hash']}"
    good_check = detector.check_response(good_response, record)
    print(f"\nGood response verified: {good_check['response_verified']}")
    
    # Bad response  
    bad_response = "Most tests are passing, approximately 90% success rate. Should be okay to deploy with minor fixes."
    bad_check = detector.check_response(bad_response, record)
    print(f"Bad response hallucinations: {bad_check['hallucinations_detected']} ({len(bad_check['detections'])} issues)")
    
    print("\n✅ Test Result Verifier validation complete")