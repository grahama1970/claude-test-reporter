
"""
Module: agent_integration.py
Description: Implementation of agent integration functionality

External Dependencies:
- claude_test_reporter: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Agent Integration Module - Clear instructions for Claude Code and other agents.

This module provides explicit guidance on when and how to use the judge model
for test validation. It's designed to be easily understood by AI agents.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


class AgentTestValidator:
    """
    High-level test validation orchestrator for AI agents.

    This class provides clear, unambiguous instructions about when to call
    the judge model and how to interpret results.
    """

    # Decision tree for agents
    DECISION_RULES = """
    TEST VALIDATION DECISION TREE FOR AGENTS:

    1. Run tests → Get results
    2. Check results:
       - Any failures? → FIX THEM FIRST (no judge needed yet)
       - All pass? → MUST CALL JUDGE (critical step!)
       - No tests? → WRITE TESTS FIRST
    3. Judge validation:
       - Judge approves? → SAFE TO DEPLOY ✅
       - Judge finds issues? → FIX QUALITY ISSUES ❌
    """

    def __init__(self, test_results_path: Path):
        """Initialize with test results."""
        self.results_path = test_results_path
        self.test_data = self._load_results()

    def _load_results(self) -> Dict[str, Any]:
        """Load test results from file."""
        if not self.results_path.exists():
            return {"error": "No test results found"}

        with open(self.results_path) as f:
            return json.load(f)

    def analyze_and_decide(self) -> Dict[str, Any]:
        """
        Main entry point for agents. Returns explicit instructions.

        Returns a dictionary with:
        - decision: What to do (RUN_JUDGE, FIX_TESTS, etc.)
        - commands: List of commands to execute
        - explanation: Human-readable explanation
        - deployment_safe: Boolean indicating if deployment is safe
        """

        # Check for errors
        if "error" in self.test_data:
            return {
                "decision": "RUN_TESTS",
                "commands": ["pytest --json-report --json-report-file=test_results.json"],
                "explanation": "No test results found. Run tests first.",
                "deployment_safe": False,
                "judge_needed": False
            }

        summary = self.test_data.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        skipped = summary.get('skipped', 0)

        # CASE 1: Tests are failing
        if failed > 0:
            return {
                "decision": "FIX_FAILURES",
                "commands": [],
                "explanation": f"❌ {failed} tests failing. Fix them before requesting judge validation.",
                "deployment_safe": False,
                "judge_needed": False,
                "details": {
                    "failed_count": failed,
                    "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
                }
            }

        # CASE 2: All tests pass - JUDGE VALIDATION REQUIRED!
        if failed == 0 and total > 0 and skipped == 0:
            return {
                "decision": "CALL_JUDGE",
                "commands": [
                    f"claude-test-reporter judge {self.results_path}",
                    "# Alternative: claude-test-reporter validate {self.results_path} --fail-on-category lazy --fail-on-category hallucinated"
                ],
                "explanation": "✅ All tests passed! 🧑‍⚖️ MUST request judge validation to check test quality.",
                "deployment_safe": False,  # Not safe until judge approves!
                "judge_needed": True,
                "warning": "⚠️ NEVER deploy when all tests pass without judge validation!",
                "details": {
                    "total_tests": total,
                    "all_passed": True,
                    "reason": "Perfect results often hide lazy or incomplete tests"
                }
            }

        # CASE 3: Tests with skipped
        if skipped > 0:
            return {
                "decision": "REVIEW_SKIPPED",
                "commands": [],
                "explanation": f"⚠️ {skipped} tests skipped. Review and enable them first.",
                "deployment_safe": False,
                "judge_needed": False
            }

        # CASE 4: No tests
        if total == 0:
            return {
                "decision": "WRITE_TESTS",
                "commands": [],
                "explanation": "❌ No tests found. Write tests first.",
                "deployment_safe": False,
                "judge_needed": False
            }

        # Shouldn't reach here
        return {
            "decision": "UNKNOWN",
            "commands": [],
            "explanation": "Unable to determine status. Manual review needed.",
            "deployment_safe": False,
            "judge_needed": False
        }

    def interpret_judge_results(self, judge_output_path: Path) -> Dict[str, Any]:
        """
        Interpret judge validation results for agents.

        Args:
            judge_output_path: Path to judge validation results

        Returns:
            Clear interpretation with deployment decision
        """
        if not judge_output_path.exists():
            return {
                "error": "Judge results not found",
                "deployment_safe": False
            }

        with open(judge_output_path) as f:
            judge_results = json.load(f)

        summary = judge_results.get('summary', {})
        categories = summary.get('categories', {})
        problematic_tests = summary.get('problematic_tests', [])

        # Check for quality issues
        quality_issues = {
            "lazy": categories.get('lazy', 0),
            "hallucinated": categories.get('hallucinated', 0),
            "incomplete": categories.get('incomplete', 0),
            "flaky": categories.get('flaky', 0)
        }

        total_issues = sum(quality_issues.values())

        if total_issues > 0:
            return {
                "decision": "BLOCK_DEPLOYMENT",
                "deployment_safe": False,
                "explanation": f"❌ Judge found {total_issues} quality issues in {len(problematic_tests)} tests",
                "quality_issues": quality_issues,
                "action_required": "Fix test quality issues before deployment",
                "problematic_tests": problematic_tests
            }
        else:
            return {
                "decision": "APPROVE_DEPLOYMENT",
                "deployment_safe": True,
                "explanation": "✅ All tests passed AND judge validated quality. Safe to deploy!",
                "quality_issues": quality_issues,
                "action_required": None
            }

    @staticmethod
    def get_agent_instructions() -> str:
        """
        Return clear instructions for agents on how to use this system.
        """
        return """
# AGENT INSTRUCTIONS: Test Validation with Judge Model

## Quick Reference for Claude Code and other agents:

### 1. After running tests, use this code:

```python
from claude_test_reporter.agent_integration import AgentTestValidator

# Analyze test results
validator = AgentTestValidator(Path("test_results.json"))
decision = validator.analyze_and_decide()

print(f"Decision: {decision['decision']}")
print(f"Explanation: {decision['explanation']}")

# Execute commands if provided
for cmd in decision.get('commands', []):
    print(f"Running: {cmd}")
    # subprocess.run(cmd, shell=True)
```

### 2. Key Decision Points:

- **decision == "CALL_JUDGE"** → You MUST run the judge command
- **decision == "FIX_FAILURES"** → Fix test failures first
- **decision == "APPROVE_DEPLOYMENT"** → Safe to deploy (after judge approval)
- **decision == "BLOCK_DEPLOYMENT"** → Do NOT deploy

### 3. Judge Model Command:

When you see "CALL_JUDGE", run:
```bash
claude-test-reporter judge test_results.json
```

### 4. Remember:

- ✅ All tests pass → Call judge (ALWAYS!)
- ❌ Any test fails → Fix failures first
- 🧑‍⚖️ Judge finds issues → Fix quality problems
- ✅ Judge approves → Safe to deploy

### 5. NEVER:

- Deploy when all tests pass without judge validation
- Ignore judge warnings about test quality
- Skip judge validation for "simple" changes
"""


def create_integration_example():
    """Create a complete example for agents."""

    example = """
# Complete Agent Workflow Example

```python
import subprocess
import json
from pathlib import Path
from claude_test_reporter.agent_integration import AgentTestValidator

def handle_test_validation():
    '''Complete test validation workflow for agents.'''

    # Step 1: Run tests
    print("🧪 Running tests...")
    result = subprocess.run(
        ["pytest", "--json-report", "--json-report-file=test_results.json"],
        capture_output=True
    )

    # Step 2: Analyze results
    print("📊 Analyzing test results...")
    validator = AgentTestValidator(Path("test_results.json"))
    decision = validator.analyze_and_decide()

    print(f"\\nDecision: {decision['decision']}")
    print(f"Explanation: {decision['explanation']}")

    # Step 3: Act based on decision
    if decision['decision'] == 'CALL_JUDGE':
        print("\\n🧑‍⚖️ Calling judge for validation...")

        # Run judge command
        judge_cmd = decision['commands'][0]
        judge_result = subprocess.run(
            judge_cmd.split(),
            capture_output=True
        )

        if judge_result.returncode == 0:
            # Interpret judge results
            judge_decision = validator.interpret_judge_results(
                Path("judge_validation.json")
            )

            if judge_decision['deployment_safe']:
                print("\\n✅ DEPLOYMENT APPROVED")
                print("All tests pass AND quality verified!")
                return True
            else:
                print("\\n❌ DEPLOYMENT BLOCKED")
                print(f"Reason: {judge_decision['explanation']}")
                return False

    elif decision['decision'] == 'FIX_FAILURES':
        print("\\n❌ Cannot proceed - fix test failures first")
        return False

    # Default: not safe to deploy
    return False

# Run the workflow
if __name__ == "__main__":
    safe_to_deploy = handle_test_validation()
    print(f"\\nFinal decision: {'DEPLOY' if safe_to_deploy else 'DO NOT DEPLOY'}")
```
"""
    return example


# Module-level helper function for agents
def should_call_judge(test_results_path: str) -> Tuple[bool, str]:
    """
    Simple function for agents to check if judge validation is needed.

    Args:
        test_results_path: Path to test results JSON

    Returns:
        (should_call_judge, reason)
    """
    validator = AgentTestValidator(Path(test_results_path))
    decision = validator.analyze_and_decide()

    if decision['decision'] == 'CALL_JUDGE':
        return True, decision['explanation']
    else:
        return False, decision['explanation']


if __name__ == "__main__":
    print("🤖 Agent Integration Module")
    print("==========================\n")
    print(AgentTestValidator.get_agent_instructions())
    print("\n" + "="*60 + "\n")
    print(create_integration_example())