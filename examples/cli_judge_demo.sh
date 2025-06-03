#!/bin/bash

# CLI Judge Model Demo Script
# Shows how agents should use the judge model

echo "🧑‍⚖️ JUDGE MODEL DEMO - Test Quality Validation"
echo "=============================================="
echo

# Create test results where all pass
cat > all_pass_results.json << 'EOF'
{
  "summary": {
    "total": 5,
    "passed": 5,
    "failed": 0,
    "skipped": 0
  },
  "tests": [
    {
      "nodeid": "test_auth.py::test_login",
      "outcome": "passed",
      "duration": 0.5
    },
    {
      "nodeid": "test_auth.py::test_logout",
      "outcome": "passed",
      "duration": 0.3
    },
    {
      "nodeid": "test_validation.py::test_email",
      "outcome": "passed",
      "duration": 0.1
    },
    {
      "nodeid": "test_api.py::test_get_users",
      "outcome": "passed",
      "duration": 0.8
    },
    {
      "nodeid": "test_database.py::test_connection",
      "outcome": "passed",
      "duration": 1.2
    }
  ]
}
EOF

echo "📊 Test Results:"
echo "   Total: 5"
echo "   Passed: 5 ✅"
echo "   Failed: 0"
echo "   Success Rate: 100%"
echo

echo "🤖 Agent Decision Point:"
echo "   All tests passed! What should the agent do?"
echo

echo "❌ WRONG APPROACH:"
echo '   echo "All tests passed! Ready to deploy!"'
echo

echo "✅ CORRECT APPROACH:"
echo "   Request judge model validation first!"
echo

echo "─────────────────────────────────────────────"
echo "COMMAND 1: Using 'judge' command (RECOMMENDED)"
echo "─────────────────────────────────────────────"
echo
echo "$ claude-test-reporter judge all_pass_results.json"
echo
echo "Expected output:"
echo "  ✅ All tests passed!"
echo "  🔍 This is exactly when judge validation is most important!"
echo "  "
echo "  🧑‍⚖️ Requesting second opinion from gemini-2.5-pro judge model..."
echo "  "
echo "  📋 Judge Model Validation Complete"
echo "  Model: gemini/gemini-2.5-pro"
echo "  Tests validated: 5"
echo "  "
echo "  Test Quality Categories:"
echo "    ✅ good: 3"
echo "    ⚠️ lazy: 1"
echo "    ⚠️ incomplete: 1"
echo "  "
echo "  ❌ VALIDATION FAILED - Quality issues detected"
echo "  Found 2 problematic tests"
echo "  "
echo "  Action required: Fix test quality issues before deployment"
echo

echo "─────────────────────────────────────────────"
echo "COMMAND 2: Using 'validate' command"
echo "─────────────────────────────────────────────"
echo
echo "$ claude-test-reporter validate all_pass_results.json \\"
echo "    --fail-on-category lazy \\"
echo "    --fail-on-category hallucinated"
echo
echo "Expected output:"
echo "  ✅ All tests passed!"
echo "  🧑‍⚖️ Perfect results - judge validation is critical!"
echo "  "
echo "  🧑‍⚖️ Validating 5 tests with gemini-2.5-pro judge model..."
echo "  "
echo "  ✅ Validation results saved to: validation_results.json"
echo "  "
echo "  ❌ Judge validation FAILED - Quality issues detected"
echo "    • lazy: 1 tests"
echo "  "
echo "  Total problematic tests: 1"
echo "  ⚠️  Fix test quality before deployment!"
echo

echo "─────────────────────────────────────────────"
echo "KEY TAKEAWAYS FOR AGENTS"
echo "─────────────────────────────────────────────"
echo
echo "1. When ALL tests pass → ALWAYS run judge validation"
echo "2. Use 'judge' command - it's clearest about purpose"
echo "3. Judge failures = deployment blocked"
echo "4. Test quality matters as much as passing"
echo "5. Perfect results are suspicious - validate them!"
echo

echo "─────────────────────────────────────────────"
echo "AGENT PSEUDOCODE"
echo "─────────────────────────────────────────────"
cat << 'EOF'

if all_tests_passed:
    print("✅ All tests passed!")
    print("🧑‍⚖️ Requesting judge model validation...")
    
    result = run("claude-test-reporter judge test_results.json")
    
    if result.exit_code == 0:
        print("✅ Safe to deploy")
    else:
        print("❌ Quality issues - do not deploy")
else:
    print("Fix test failures first")

EOF

# Cleanup
rm -f all_pass_results.json

echo
echo "✅ Demo complete! Remember: Perfect test results need judge validation!"