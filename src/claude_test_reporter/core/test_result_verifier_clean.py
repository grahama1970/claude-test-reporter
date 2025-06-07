#!/usr/bin/env python3
"""
Module: test_result_verifier.py
Description: Ensures test results cannot be misrepresented

External Dependencies:
- None (uses standard library only)

Sample Input:
>>> verifier = TestResultVerifier()
>>> verifier.create_immutable_test_record({"total": 100, "passed": 95, "failed": 5})

Expected Output:
>>> {"immutable_facts": {"failed_count": 5, "exact_success_rate": 95.0}, ...}
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from string import Template


class TestResultVerifier:
    """Ensures test results cannot be misrepresented."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)
    
    def load_prompt(self, prompt_name: str) -> Template:
        """Load a prompt template from file."""
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        
        with open(prompt_path, 'r') as f:
            template_text = f.read()
        
        return Template(template_text)
    
    def create_immutable_test_record(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an immutable record of test results that cannot be misrepresented.
        This record includes cryptographic verification to prevent tampering.
        """
        # Extract core facts
        total_tests = test_results.get("total", 0)
        passed_tests = test_results.get("passed", 0)
        failed_tests = test_results.get("failed", 0)
        skipped_tests = test_results.get("skipped", 0)
        
        # Calculate exact percentages
        if total_tests > 0:
            exact_success_rate = round((passed_tests / total_tests) * 100, 1)
            exact_failure_rate = round((failed_tests / total_tests) * 100, 1)
        else:
            exact_success_rate = 0.0
            exact_failure_rate = 0.0
        
        # Create immutable facts record
        immutable_facts = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_count": passed_tests,
            "failed_count": failed_tests,
            "skipped_count": skipped_tests,
            "exact_success_rate": exact_success_rate,
            "exact_failure_rate": exact_failure_rate,
            "has_failures": failed_tests > 0,
            "all_tests_passed": failed_tests == 0 and total_tests > 0
        }
        
        # Extract failed test details
        failed_test_details = []
        if "tests" in test_results:
            for test in test_results["tests"]:
                if test.get("outcome") == "failed" or test.get("status") == "failed":
                    failed_test_details.append({
                        "name": test.get("nodeid", test.get("name", "unnamed")),
                        "error": test.get("error", test.get("message", "No error message")),
                        "duration": test.get("duration", 0),
                        "file": test.get("file", "unknown"),
                        "line": test.get("line", 0)
                    })
        
        # Create deployment decision
        deployment_decision = {
            "can_deploy": failed_tests == 0,
            "reason": "All tests must pass for deployment" if failed_tests > 0 else "All tests passed",
            "blocked_by": [test["name"] for test in failed_test_details] if failed_tests > 0 else []
        }
        
        # Create the complete record
        record = {
            "immutable_facts": immutable_facts,
            "failed_test_details": failed_test_details,
            "deployment_decision": deployment_decision,
            "verification": {
                "version": "1.0",
                "algorithm": "sha256"
            }
        }
        
        # Add cryptographic hash
        record["verification"]["hash"] = self._calculate_hash(record)
        
        return record
    
    def _calculate_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of the record."""
        # Create a copy without the hash field
        record_copy = json.loads(json.dumps(record))
        if "verification" in record_copy and "hash" in record_copy["verification"]:
            del record_copy["verification"]["hash"]
        
        # Create deterministic JSON string
        json_str = json.dumps(record_copy, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_record(self, record: Dict[str, Any]) -> bool:
        """Verify a test record has not been tampered with."""
        stored_hash = record.get("verification", {}).get("hash", "")
        calculated_hash = self._calculate_hash(record)
        return stored_hash == calculated_hash
    
    def create_llm_prompt_template(self, test_results: Dict[str, Any]) -> str:
        """Create a prompt template that forces accurate reporting."""
        record = self.create_immutable_test_record(test_results)
        
        # Load prompt template
        template = self.load_prompt("verification_prompt")
        
        # Prepare template variables
        template_vars = {
            "immutable_facts": json.dumps(record['immutable_facts'], indent=2),
            "failed_test_details": json.dumps(record['failed_test_details'], indent=2),
            "deployment_decision": json.dumps(record['deployment_decision'], indent=2),
            "verification_hash": record['verification']['hash'],
            "failed_count": record['immutable_facts']['failed_count'],
            "exact_success_rate": record['immutable_facts']['exact_success_rate'],
            "deployment_status": 'BLOCKED' if record['immutable_facts']['failed_count'] > 0 else 'ALLOWED'
        }
        
        return template.substitute(**template_vars)
    
    def generate_verification_report(self,
                                   test_results: Dict[str, Any],
                                   output_file: str = "verified_test_results.json") -> str:
        """Generate a verification report that cannot be misinterpreted."""
        record = self.create_immutable_test_record(test_results)
        
        # Add instructions for LLMs
        deployment_status = 'ALLOWED' if record['deployment_decision']['can_deploy'] else 'BLOCKED'
        record["llm_instructions"] = {
            "mandatory_statements": [
                f"State: '{record['immutable_facts']['failed_count']} tests are failing'",
                f"State: 'Success rate is {record['immutable_facts']['exact_success_rate']}%'",
                f"State: 'Deployment is {deployment_status}'",
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
        with open(output_path, 'w') as f:
            json.dump(record, f, indent=2)
        
        return str(output_path.resolve())


class HallucinationDetector:
    """Detects when an LLM hallucinates about test results."""
    
    def __init__(self):
        """Initialize the detector."""
        self.severity_levels = {
            "critical": ["wrong_count", "wrong_deployment", "missing_failures"],
            "high": ["rounded_rate", "vague_count", "missing_hash"],
            "medium": ["reordered_facts", "added_context"],
            "low": ["formatting_difference"]
        }
    
    def check_response(self,
                      llm_response: str,
                      actual_record: Dict[str, Any]) -> Dict[str, Any]:
        """Check an LLM response for hallucinations about test results."""
        detections = []
        
        # Check exact numbers
        actual_failed = actual_record['immutable_facts']['failed_count']
        actual_rate = actual_record['immutable_facts']['exact_success_rate']
        
        # Check if correct failure count is mentioned
        if str(actual_failed) not in llm_response:
            detections.append({
                "type": "wrong_count",
                "severity": "critical",
                "expected": f"{actual_failed} tests failing",
                "details": "Exact failure count not mentioned"
            })
        
        # Check if exact success rate is mentioned
        if f"{actual_rate}%" not in llm_response:
            detections.append({
                "type": "rounded_rate",
                "severity": "high",
                "expected": f"{actual_rate}%",
                "details": "Exact success rate not mentioned"
            })
        
        # Check deployment decision
        expected_deployment = "BLOCKED" if actual_failed > 0 else "ALLOWED"
        if expected_deployment not in llm_response.upper():
            detections.append({
                "type": "wrong_deployment",
                "severity": "critical",
                "expected": f"Deployment is {expected_deployment}",
                "details": "Incorrect deployment decision"
            })
        
        # Check verification hash
        if actual_record['verification']['hash'] not in llm_response:
            detections.append({
                "type": "missing_hash",
                "severity": "high",
                "expected": f"Hash: {actual_record['verification']['hash']}",
                "details": "Verification hash not included"
            })
        
        # Compile results
        return {
            "response_verified": len(detections) == 0,
            "hallucinations_detected": len(detections) > 0,
            "detections": detections,
            "critical_issues": [d for d in detections if d["severity"] == "critical"],
            "trust_score": 1.0 - (len(detections) * 0.2)  # Deduct 20% per issue
        }


if __name__ == "__main__":
    # Validation example
    print(f"Validating {__file__}...")
    
    # Create test data
    test_results = {
        "total": 50,
        "passed": 45,
        "failed": 5,
        "skipped": 0,
        "tests": [
            {"nodeid": "test_auth", "outcome": "failed", "error": "AssertionError"},
            {"nodeid": "test_api", "outcome": "failed", "error": "ConnectionError"},
            {"nodeid": "test_db", "outcome": "failed", "error": "TimeoutError"},
            {"nodeid": "test_cache", "outcome": "failed", "error": "ValueError"},
            {"nodeid": "test_webhook", "outcome": "failed", "error": "HTTPError"},
        ]
    }
    
    # Test verifier
    verifier = TestResultVerifier()
    record = verifier.create_immutable_test_record(test_results)
    
    print(f"\nImmutable facts: {json.dumps(record['immutable_facts'], indent=2)}")
    print(f"Verification hash: {record['verification']['hash']}")
    print(f"Can deploy: {record['deployment_decision']['can_deploy']}")
    
    # Verify record integrity
    is_valid = verifier.verify_record(record)
    print(f"\nRecord verification: {'✅ VALID' if is_valid else '❌ TAMPERED'}")
    
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