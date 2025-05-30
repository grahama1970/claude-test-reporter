#!/usr/bin/env python3
"""
Demo: LLM Verification and Anti-Hallucination Features

Shows how to:
1. Generate verified test reports
2. Send to LLM (Gemini 2.5 Pro) for analysis
3. Detect and prevent hallucinations
4. Create deployment decisions based on facts
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.claude_test_reporter.core.test_result_verifier import TestResultVerifier, HallucinationDetector
from src.claude_test_reporter.analyzers.llm_test_analyzer import LLMTestAnalyzer, TestReportVerifier


def demo_verified_reporting():
    """Demonstrate verified test reporting that prevents hallucinations."""
    print("🔒 Demo: Verified Test Reporting\n")
    
    # Create test results with some failures
    test_results = {
        "total": 100,
        "passed": 92,
        "failed": 8,
        "skipped": 0,
        "tests": [
            {"nodeid": "test_auth::test_login", "outcome": "failed", "error": "AssertionError: Login failed"},
            {"nodeid": "test_auth::test_logout", "outcome": "failed", "error": "AssertionError: Logout failed"},
            {"nodeid": "test_api::test_create", "outcome": "failed", "error": "ConnectionError: API down"},
            {"nodeid": "test_api::test_update", "outcome": "failed", "error": "TimeoutError: Request timeout"},
            {"nodeid": "test_db::test_insert", "outcome": "failed", "error": "AssertionError: Insert failed"},
            {"nodeid": "test_db::test_delete", "outcome": "failed", "error": "AssertionError: Delete failed"},
            {"nodeid": "test_ui::test_render", "outcome": "failed", "error": "AssertionError: Render failed"},
            {"nodeid": "test_utils::test_parse", "outcome": "failed", "error": "ValueError: Parse error"},
            # ... 92 passing tests
        ] + [{"nodeid": f"test_suite_{i}::test_{i}", "outcome": "passed"} for i in range(92)]
    }
    
    # Create verifier
    verifier = TestResultVerifier()
    
    # Generate immutable record
    print("1️⃣ Creating immutable test record...")
    record = verifier.create_immutable_test_record(test_results)
    
    print(f"   • Failed tests: {record['immutable_facts']['failed_count']}")
    print(f"   • Success rate: {record['immutable_facts']['exact_success_rate']}%")
    print(f"   • Deployment: {'ALLOWED' if record['deployment_decision']['can_deploy'] else 'BLOCKED'}")
    print(f"   • Verification hash: {record['verification']['hash'][:16]}...")
    
    # Save verified record
    verified_file = "demo_verified_results.json"
    verifier.generate_verification_report(test_results, verified_file)
    print(f"\n   ✅ Verified record saved: {verified_file}")
    
    return record, test_results


def demo_llm_analysis(test_results: dict):
    """Demonstrate LLM analysis with anti-hallucination features."""
    print("\n🤖 Demo: LLM Analysis with Gemini 2.5 Pro\n")
    
    # Create LLM analyzer
    analyzer = LLMTestAnalyzer(model="gemini-2.5-pro", temperature=0.1)
    
    print("2️⃣ Sending to LLM for analysis...")
    
    # Note: This would actually call the LLM if llm_call module is available
    # For demo purposes, we'll simulate the response
    if analyzer:
        print("   (Simulating LLM call - in production this calls Gemini 2.5 Pro)")
        
        # Simulated LLM analysis
        simulated_analysis = {
            "summary": {
                "overall_status": "failing",
                "confidence_level": "high",
                "actual_pass_rate": 92.0,
                "requires_immediate_action": True
            },
            "failed_test_analysis": [
                {
                    "test_name": "test_auth::test_login",
                    "failure_category": "assertion",
                    "likely_cause": "Authentication logic error",
                    "suggested_fix": "Check login credentials validation"
                },
                {
                    "test_name": "test_api::test_create",
                    "failure_category": "connection",
                    "likely_cause": "API service not running",
                    "suggested_fix": "Ensure API service is started"
                }
            ],
            "risk_assessment": {
                "deployment_ready": False,
                "critical_failures": 8,
                "blocking_issues": ["Authentication broken", "API connectivity issues"]
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Fix authentication tests before any deployment",
                    "reason": "Login/logout failures block all user access"
                },
                {
                    "priority": "high", 
                    "action": "Investigate API connection issues",
                    "reason": "API failures prevent core functionality"
                }
            ]
        }
        
        print("   ✅ LLM analysis complete")
        return simulated_analysis
    else:
        print("   ⚠️  LLM module not available - skipping actual analysis")
        return None


def demo_hallucination_detection(record: dict):
    """Demonstrate hallucination detection."""
    print("\n🔍 Demo: Hallucination Detection\n")
    
    detector = HallucinationDetector()
    
    # Test various LLM responses
    test_responses = [
        # Good response - accurate
        {
            "name": "Accurate Response",
            "text": f"8 tests are failing. Success rate is 92.0%. Deployment is BLOCKED. Hash: {record['verification']['hash']}"
        },
        # Bad response - minimizes failures
        {
            "name": "Minimizing Failures",
            "text": "Most tests are passing with approximately 92% success rate. Only a few minor test failures."
        },
        # Bad response - suggests deployment
        {
            "name": "False Deployment Approval", 
            "text": "With a 92% pass rate, the system is mostly working. Should be safe to deploy with monitoring."
        },
        # Bad response - rounds up
        {
            "name": "Rounding Up Success",
            "text": "Nearly 95% of tests are passing. The system is in good shape overall."
        }
    ]
    
    print("3️⃣ Checking various LLM responses for hallucinations:\n")
    
    for response in test_responses:
        check = detector.check_response(response["text"], record)
        
        status = "✅ VERIFIED" if check["response_verified"] else f"❌ HALLUCINATION ({check['detection_count']} issues)"
        print(f"   {response['name']}: {status}")
        
        if check["detections"]:
            for detection in check["detections"]:
                print(f"      - {detection['type']}: {detection['details']}")
        print()


def demo_deployment_decision():
    """Demonstrate fact-based deployment decisions."""
    print("🚀 Demo: Deployment Decision Process\n")
    
    # Create report verifier
    verifier = TestReportVerifier()
    
    scenarios = [
        {"name": "All Passing", "total": 100, "passed": 100, "failed": 0},
        {"name": "One Failure", "total": 100, "passed": 99, "failed": 1},
        {"name": "95% Passing", "total": 100, "passed": 95, "failed": 5},
        {"name": "90% Passing", "total": 100, "passed": 90, "failed": 10},
    ]
    
    print("4️⃣ Deployment decisions based on test results:\n")
    
    for scenario in scenarios:
        summary = verifier.create_verified_summary(scenario)
        
        # Extract deployment decision
        if "NOT ready for deployment" in summary:
            decision = "🚫 BLOCKED"
            reason = f"{scenario['failed']} failing tests"
        else:
            decision = "✅ ALLOWED" 
            reason = "All tests passing"
            
        print(f"   {scenario['name']}: {decision} - {reason}")
    
    print("\n   📋 Rule: ANY test failure blocks deployment")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("Claude Test Reporter - LLM Verification Demo")
    print("=" * 60)
    print()
    
    # Run demos
    record, test_results = demo_verified_reporting()
    analysis = demo_llm_analysis(test_results)
    demo_hallucination_detection(record)
    demo_deployment_decision()
    
    print("=" * 60)
    print("🎯 Key Takeaways:")
    print("- Immutable records prevent misinterpretation")
    print("- Verification hashes ensure data integrity")
    print("- Hallucination detection catches false claims")
    print("- Clear deployment rules prevent risky deployments")
    print("- LLM analysis provides insights while maintaining accuracy")
    print("=" * 60)


if __name__ == "__main__":
    main()