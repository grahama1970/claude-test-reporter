#!/usr/bin/env python3
"""
Claude Code Integration Example

This example shows EXACTLY how Claude Code (or any AI agent) should
integrate with the test reporter and judge model.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def claude_code_test_workflow():
    """
    This is the EXACT workflow Claude Code should follow when handling tests.
    
    The key insight: When all tests pass, ALWAYS call the judge model.
    """
    
    print("🤖 Claude Code Test Validation Workflow")
    print("=" * 50)
    
    # Step 1: Check if test results exist
    test_results_path = Path("test_results.json")
    
    if not test_results_path.exists():
        print("\n❌ No test results found!")
        print("📝 Action: Run tests first")
        print("   Command: pytest --json-report --json-report-file=test_results.json")
        return {
            "action": "RUN_TESTS",
            "safe_to_deploy": False
        }
    
    # Step 2: Load and analyze test results
    with open(test_results_path) as f:
        test_data = json.load(f)
    
    summary = test_data.get('summary', {})
    total = summary.get('total', 0) 
    passed = summary.get('passed', 0)
    failed = summary.get('failed', 0)
    skipped = summary.get('skipped', 0)
    
    print(f"\n📊 Test Results:")
    print(f"   Total: {total}")
    print(f"   Passed: {passed} {'✅' if passed > 0 else ''}")
    print(f"   Failed: {failed} {'❌' if failed > 0 else ''}")
    print(f"   Skipped: {skipped} {'⚠️' if skipped > 0 else ''}")
    
    # Step 3: CRITICAL DECISION POINT
    if failed > 0:
        # Tests failing - no judge needed yet
        print(f"\n❌ {failed} tests are failing!")
        print("📝 Action: Fix failing tests before deployment")
        print("   Judge validation: Not needed until all tests pass")
        
        return {
            "action": "FIX_FAILURES",
            "safe_to_deploy": False,
            "reason": f"{failed} tests failing"
        }
    
    elif failed == 0 and total > 0:
        # ALL TESTS PASS - THIS IS THE KEY MOMENT!
        print("\n✅ All tests passed!")
        print("🚨 CRITICAL: This is when judge validation is REQUIRED!")
        print()
        print("WHY? Perfect test results often hide:")
        print("  • Lazy tests (assert True)")
        print("  • Incomplete tests (missing assertions)")
        print("  • Hallucinated tests (don't test what they claim)")
        print()
        print("🧑‍⚖️ Action: Request judge model validation")
        print("   Command: claude-test-reporter judge test_results.json")
        
        # Simulate running judge command
        print("\n" + "─" * 50)
        print("SIMULATING: claude-test-reporter judge test_results.json")
        print("─" * 50)
        
        # In real usage, Claude Code would run:
        # result = subprocess.run(
        #     ["claude-test-reporter", "judge", "test_results.json"],
        #     capture_output=True
        # )
        
        # Simulate judge finding issues (common case)
        judge_found_issues = True  # Change to False to see approval case
        
        if judge_found_issues:
            print("\n❌ Judge validation FAILED")
            print("Found quality issues:")
            print("  • 2 lazy tests")
            print("  • 1 incomplete test")
            print()
            print("📝 Action: Fix test quality issues")
            print("⛔ Deployment: BLOCKED until quality issues fixed")
            
            return {
                "action": "FIX_TEST_QUALITY",
                "safe_to_deploy": False,
                "reason": "Judge found test quality issues"
            }
        else:
            print("\n✅ Judge validation PASSED")
            print("All tests have good quality!")
            print()
            print("✅ Action: Safe to deploy")
            print("🚀 Deployment: APPROVED")
            
            return {
                "action": "DEPLOY",
                "safe_to_deploy": True,
                "reason": "Tests pass AND quality verified"
            }
    
    else:
        # Edge cases
        print("\n⚠️ Unusual test state")
        print("📝 Action: Review test configuration")
        
        return {
            "action": "REVIEW",
            "safe_to_deploy": False,
            "reason": "No tests or all skipped"
        }


def show_claude_code_integration():
    """
    Show how Claude Code can use the simple integration function.
    """
    print("\n\n" + "=" * 60)
    print("SIMPLE INTEGRATION FOR CLAUDE CODE")
    print("=" * 60)
    
    code_example = '''
# In Claude Code, use this simple check:

from claude_test_reporter import should_call_judge

# After running tests, check if judge is needed
needs_judge, reason = should_call_judge("test_results.json")

if needs_judge:
    print(f"🧑‍⚖️ {reason}")
    # Run: claude-test-reporter judge test_results.json
else:
    print(f"📝 {reason}")
    # Handle based on reason (fix failures, etc.)
'''
    
    print(code_example)
    
    print("\n" + "=" * 60)
    print("DECISION TREE FOR CLAUDE CODE")
    print("=" * 60)
    
    decision_tree = '''
    Tests Complete?
         |
         ├─ No → Run: pytest --json-report
         |
         └─ Yes → Check Results
                    |
                    ├─ Failures? → Fix them (no judge yet)
                    |
                    └─ All Pass? → MUST CALL JUDGE!
                                    |
                                    ├─ Judge Approves → Deploy ✅
                                    |
                                    └─ Judge Rejects → Fix Quality ❌
    '''
    
    print(decision_tree)


def show_common_mistakes():
    """Show what NOT to do."""
    
    print("\n" + "=" * 60)
    print("❌ COMMON MISTAKES TO AVOID")
    print("=" * 60)
    
    print("\n1. WRONG: Skipping judge when all pass")
    print("   if all_tests_pass:")
    print('       print("Ready to deploy!")  # NO!')
    
    print("\n2. WRONG: Only calling judge sometimes")
    print("   if random.choice([True, False]):")
    print('       call_judge()  # NO! Always call when all pass')
    
    print("\n3. WRONG: Ignoring judge results")
    print("   judge_result = call_judge()")
    print('   deploy_anyway()  # NO! Respect judge decision')
    
    print("\n" + "=" * 60)
    print("✅ CORRECT APPROACH")
    print("=" * 60)
    
    print("\nALWAYS follow this pattern:")
    print("1. All tests pass → Call judge")
    print("2. Judge approves → Deploy")
    print("3. Judge rejects → Fix quality issues")
    print("4. Never skip judge validation for 'simple' changes")


if __name__ == "__main__":
    # Run the example workflow
    result = claude_code_test_workflow()
    
    print("\n" + "=" * 60)
    print("FINAL DECISION")
    print("=" * 60)
    print(f"Action: {result['action']}")
    print(f"Safe to deploy: {'YES' if result['safe_to_deploy'] else 'NO'}")
    print(f"Reason: {result['reason']}")
    
    # Show integration examples
    show_claude_code_integration()
    
    # Show common mistakes
    show_common_mistakes()
    
    print("\n" + "=" * 60)
    print("💡 KEY TAKEAWAY FOR CLAUDE CODE")
    print("=" * 60)
    print()
    print("When you see: 'All tests passed!'")
    print("Always think: 'Time to call the judge!'")
    print()
    print("Command: claude-test-reporter judge test_results.json")
    print()
    print("This ensures you're not fooled by lazy or fake tests!")
    print("=" * 60)