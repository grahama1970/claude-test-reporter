#!/usr/bin/env python3
"""
Agent Validation Workflow Example

Demonstrates how agents should request second opinions when all tests pass.
This is critical for detecting lazy, incomplete, or hallucinated tests.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from claude_test_reporter.core.adapters.agent_report_adapter import AgentReportAdapter
from claude_test_reporter.core.test_validator import TestValidator


def agent_test_workflow(test_results_path: str) -> Dict[str, Any]:
    """
    Complete agent workflow for running tests and requesting validation.
    
    This demonstrates the recommended pattern for agents:
    1. Run tests
    2. Check results
    3. Request judge model validation when all tests pass
    4. Make deployment decision based on validation
    """
    
    print("🤖 Agent Test Workflow Starting...\n")
    
    # Step 1: Analyze test results
    adapter = AgentReportAdapter(Path(test_results_path))
    status = adapter.get_quick_status()
    actions = adapter.get_actionable_items()
    
    print(f"📊 Test Results Summary:")
    print(f"   Total tests: {status['passed_count'] + status['failure_count'] + status['skipped_count']}")
    print(f"   Passed: {status['passed_count']}")
    print(f"   Failed: {status['failure_count']}")
    print(f"   Skipped: {status['skipped_count']}")
    print(f"   Success rate: {status['success_rate']:.1f}%")
    print()
    
    # Step 2: Check if validation is recommended
    if status.get('validation_recommended'):
        print("✅ All tests passed!")
        print(f"🔍 {status.get('validation_reason')}")
        print()
        
        # Step 3: Request judge model validation
        print("🧑‍⚖️ Requesting second opinion from judge model...")
        validator = TestValidator(model="gemini/gemini-2.5-pro-preview-05-06")
        
        # Load test data
        with open(test_results_path) as f:
            test_data = json.load(f)
        
        # Validate all tests
        validation_results = validator.validate_all_tests(test_data)
        
        # Check validation results
        problematic_tests = validation_results['summary'].get('problematic_tests', [])
        categories = validation_results['summary'].get('categories', {})
        
        print(f"\n📋 Validation Results:")
        print(f"   Model: {validation_results['model']}")
        print(f"   Total validated: {validation_results['total_tests']}")
        print(f"   Problematic tests: {len(problematic_tests)}")
        print(f"   Categories: {categories}")
        
        # Step 4: Make deployment decision
        if 'lazy' in categories or 'hallucinated' in categories or 'incomplete' in categories:
            print("\n❌ DEPLOYMENT BLOCKED")
            print("   Reason: Test quality issues detected")
            print(f"   - Lazy tests: {categories.get('lazy', 0)}")
            print(f"   - Hallucinated tests: {categories.get('hallucinated', 0)}")
            print(f"   - Incomplete tests: {categories.get('incomplete', 0)}")
            
            return {
                "decision": "BLOCK",
                "reason": "Test quality validation failed",
                "validation_performed": True,
                "issues_found": len(problematic_tests),
                "problematic_tests": problematic_tests
            }
        else:
            print("\n✅ DEPLOYMENT APPROVED")
            print("   All tests passed AND quality verified")
            
            return {
                "decision": "DEPLOY",
                "reason": "All tests passed with quality verification",
                "validation_performed": True,
                "issues_found": 0
            }
    
    elif status['failure_count'] > 0:
        print(f"❌ {status['failure_count']} tests failed")
        print("\n📋 Required Actions:")
        for action in actions:
            if action['error_type'] not in ['ValidationNeeded', 'FlakyTests']:
                print(f"   - Fix {action['error_type']}: {action['count']} tests affected")
                print(f"     Suggestion: {action['suggested_fix']}")
        
        return {
            "decision": "BLOCK",
            "reason": f"{status['failure_count']} tests failing",
            "validation_performed": False,
            "failed_tests": status['failure_count']
        }
    
    else:
        # Edge case: no failures but validation not recommended
        # (e.g., no tests run, or all tests skipped)
        return {
            "decision": "REVIEW",
            "reason": "Unusual test state - manual review required",
            "validation_performed": False
        }


def demonstrate_validation_command():
    """Show how to use the CLI validation command."""
    
    print("\n" + "="*60)
    print("CLI VALIDATION EXAMPLES")
    print("="*60 + "\n")
    
    print("1. Basic validation:")
    print("   claude-test-reporter validate results.json")
    print()
    
    print("2. Strict validation (fail on lazy/hallucinated tests):")
    print("   claude-test-reporter validate results.json \\")
    print("     --fail-on-category lazy \\")
    print("     --fail-on-category hallucinated \\")
    print("     --min-confidence 0.8")
    print()
    
    print("3. With specific model:")
    print("   claude-test-reporter validate results.json \\")
    print("     --model gemini-2.5-pro \\")
    print("     --output validation_report.json")
    print()
    
    print("4. In CI/CD pipeline:")
    print("   # Exit with code 1 if validation fails")
    print("   claude-test-reporter validate $TEST_RESULTS || exit 1")


if __name__ == "__main__":
    # Example 1: Create mock test results where all pass
    all_pass_results = {
        "tests": [
            {
                "nodeid": "test_auth.py::test_login",
                "outcome": "passed",
                "duration": 0.5,
                "call": {"stdout": "Login successful"}
            },
            {
                "nodeid": "test_auth.py::test_logout",
                "outcome": "passed",
                "duration": 0.3,
                "call": {"stdout": "Logout successful"}
            },
            {
                "nodeid": "test_validation.py::test_email",
                "outcome": "passed",
                "duration": 0.1,
                "call": {"stdout": "Email validation passed"}
            }
        ],
        "summary": {
            "total": 3,
            "passed": 3,
            "failed": 0,
            "skipped": 0
        }
    }
    
    # Save to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(all_pass_results, f)
        temp_path = f.name
    
    # Run the workflow
    print("EXAMPLE: All Tests Pass Scenario")
    print("================================\n")
    
    try:
        result = agent_test_workflow(temp_path)
        print(f"\n🎯 Final Decision: {result['decision']}")
        print(f"📝 Reason: {result['reason']}")
    finally:
        # Cleanup
        Path(temp_path).unlink()
    
    # Show CLI examples
    demonstrate_validation_command()
    
    print("\n✅ Agent validation workflow example completed!")