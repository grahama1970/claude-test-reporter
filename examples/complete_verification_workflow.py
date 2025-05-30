#!/usr/bin/env python3
"""
Complete Test Verification Workflow Example

This example demonstrates the full workflow of:
1. Running tests
2. Creating verified results
3. Analyzing with LLM (Gemini 2.5 Pro)
4. Detecting hallucinations
5. Monitoring and alerting
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.claude_test_reporter.config import Config
from src.claude_test_reporter.core.test_result_verifier import TestResultVerifier, HallucinationDetector
from src.claude_test_reporter.analyzers.llm_test_analyzer import LLMTestAnalyzer
from src.claude_test_reporter.monitoring import HallucinationMonitor, HallucinationDashboard


def run_tests_with_verification():
    """Complete workflow for running and verifying tests."""
    
    print("=" * 60)
    print("Claude Test Reporter - Complete Verification Workflow")
    print("=" * 60)
    print()
    
    # Step 1: Check configuration
    print("1️⃣ Checking configuration...")
    config = Config()
    valid, message = config.validate_llm_config()
    
    if not valid:
        print(f"❌ Configuration error: {message}")
        print("Run 'claude-test-reporter setup' to configure")
        return
    
    print("✅ Configuration valid")
    print()
    
    # Step 2: Run tests (simulated for demo)
    print("2️⃣ Running tests...")
    
    # In real usage, you would run: pytest --json-report --json-report-file=results.json
    # For demo, we'll create sample results
    test_results = {
        "created": datetime.now().timestamp(),
        "duration": 45.23,
        "total": 150,
        "passed": 142,
        "failed": 8,
        "skipped": 0,
        "tests": [
            {"nodeid": "test_auth::test_login", "outcome": "failed", "error": "AssertionError: Login failed"},
            {"nodeid": "test_auth::test_logout", "outcome": "failed", "error": "AssertionError: Logout failed"},
            {"nodeid": "test_api::test_create_user", "outcome": "failed", "error": "ConnectionError"},
            {"nodeid": "test_api::test_delete_user", "outcome": "failed", "error": "PermissionError"},
            {"nodeid": "test_db::test_migration", "outcome": "failed", "error": "DatabaseError"},
            {"nodeid": "test_ui::test_dashboard", "outcome": "failed", "error": "TimeoutError"},
            {"nodeid": "test_utils::test_parser", "outcome": "failed", "error": "ValueError"},
            {"nodeid": "test_integration::test_workflow", "outcome": "failed", "error": "AssertionError"},
        ] + [{"nodeid": f"test_suite_{i}", "outcome": "passed"} for i in range(142)]
    }
    
    # Save test results
    with open("test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"✅ Tests complete: {test_results['passed']}/{test_results['total']} passed")
    print(f"❌ {test_results['failed']} tests failed")
    print()
    
    # Step 3: Create verified results
    print("3️⃣ Creating cryptographically verified results...")
    
    verifier = TestResultVerifier()
    verified_record = verifier.create_immutable_test_record(test_results)
    
    # Save verified results
    with open("verified_results.json", "w") as f:
        json.dump(verified_record, f, indent=2)
    
    print(f"✅ Verified record created")
    print(f"   Hash: {verified_record['verification']['hash'][:32]}...")
    print(f"   Deployment: {'BLOCKED' if verified_record['immutable_facts']['failed_count'] > 0 else 'ALLOWED'}")
    print()
    
    # Step 4: LLM Analysis
    print("4️⃣ Analyzing with LLM (Gemini 2.5 Pro)...")
    
    llm_config = config.get_llm_config()
    if llm_config.api_key:
        analyzer = LLMTestAnalyzer(
            model=llm_config.model,
            temperature=llm_config.temperature
        )
        
        # Note: This would actually call Gemini in production
        print("   (Simulating LLM call for demo)")
        
        # Simulated analysis result
        analysis = {
            "summary": {
                "overall_status": "failing",
                "confidence_level": "high",
                "actual_pass_rate": 94.67,
                "requires_immediate_action": True
            },
            "failed_test_analysis": [
                {
                    "test_name": "test_auth::test_login",
                    "failure_category": "assertion",
                    "likely_cause": "Authentication logic changed",
                    "suggested_fix": "Review recent auth changes"
                }
            ],
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Fix authentication tests immediately",
                    "reason": "Core functionality is broken"
                }
            ]
        }
        
        # Save analysis
        with open("llm_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        print("✅ LLM analysis complete")
    else:
        print("⚠️  No API key configured, skipping LLM analysis")
    print()
    
    # Step 5: Hallucination Detection Demo
    print("5️⃣ Demonstrating hallucination detection...")
    
    detector = HallucinationDetector()
    
    # Test various responses
    test_responses = [
        ("Good Agent", f"8 tests are failing. Success rate is 94.67%. Deployment is BLOCKED. Hash: {verified_record['verification']['hash']}"),
        ("Bad Agent 1", "Most tests are passing, around 95% success rate. Should be fine to deploy."),
        ("Bad Agent 2", "Only a handful of tests failed. The system is mostly working correctly."),
        ("Bad Agent 3", "With nearly 95% of tests passing, the system is ready for production.")
    ]
    
    for agent_name, response in test_responses:
        result = detector.check_response(response, verified_record)
        
        if result["hallucinations_detected"]:
            print(f"❌ {agent_name}: Hallucinations detected ({result['detection_count']} issues)")
            for detection in result["detections"]:
                print(f"   - {detection['type']}: {detection['details']}")
        else:
            print(f"✅ {agent_name}: Response verified - no hallucinations")
    print()
    
    # Step 6: Monitoring Setup
    print("6️⃣ Setting up hallucination monitoring...")
    
    monitor = HallucinationMonitor(log_dir="./demo_logs")
    
    # Log the detections
    for agent_name, response in test_responses:
        result = detector.check_response(response, verified_record)
        monitor.log_hallucination(
            "demo_project",
            result,
            {"agent": agent_name, "timestamp": datetime.now().isoformat()}
        )
    
    # Generate dashboard
    dashboard = HallucinationDashboard(monitor)
    dashboard_file = dashboard.generate_dashboard_html("hallucination_dashboard.html")
    
    print(f"✅ Monitoring configured")
    print(f"   Dashboard: {dashboard_file}")
    print(f"   Logs: ./demo_logs/")
    print()
    
    # Step 7: Generate safe prompt
    print("7️⃣ Generating safe LLM prompt...")
    
    safe_prompt = verifier.create_llm_prompt_template(test_results)
    
    with open("safe_prompt.txt", "w") as f:
        f.write(safe_prompt)
    
    print("✅ Safe prompt created: safe_prompt.txt")
    print()
    
    # Summary
    print("=" * 60)
    print("Workflow Complete!")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  - test_results.json       : Raw test results")
    print("  - verified_results.json   : Cryptographically verified results")
    print("  - llm_analysis.json      : LLM analysis (if API key set)")
    print("  - safe_prompt.txt        : Hallucination-proof prompt template")
    print("  - hallucination_dashboard.html : Monitoring dashboard")
    print()
    print("Key findings:")
    print(f"  - {test_results['failed']} tests are failing")
    print(f"  - Success rate: {verified_record['immutable_facts']['exact_success_rate']}%")
    print(f"  - Deployment: {'BLOCKED' if test_results['failed'] > 0 else 'ALLOWED'}")
    print(f"  - Verification hash: {verified_record['verification']['hash'][:16]}...")
    print()
    print("Next steps:")
    print("  1. Fix the failing tests")
    print("  2. Use verified results for all reporting")
    print("  3. Monitor for hallucinations in CI/CD")
    print("  4. Never trust unverified test claims")


def cleanup_demo_files():
    """Clean up demo files."""
    files = [
        "test_results.json",
        "verified_results.json",
        "llm_analysis.json",
        "safe_prompt.txt",
        "hallucination_dashboard.html"
    ]
    
    for file in files:
        if Path(file).exists():
            Path(file).unlink()
    
    # Clean up logs
    import shutil
    if Path("./demo_logs").exists():
        shutil.rmtree("./demo_logs")


if __name__ == "__main__":
    try:
        run_tests_with_verification()
    finally:
        # Optional: cleanup demo files
        # cleanup_demo_files()
        pass