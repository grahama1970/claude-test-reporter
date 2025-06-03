# 🧑‍⚖️ AGENT INSTRUCTIONS: Judge Model for Test Validation

## CRITICAL: When to Request a Second Opinion

**THE JUDGE MODEL IS YOUR QUALITY ASSURANCE PARTNER**

When you run tests and see **ALL TESTS PASS (100% success rate)**, you MUST request validation from the judge model before recommending deployment.

## What is the Judge Model?

The **JUDGE MODEL** is an external LLM (typically Gemini 2.5 Pro) that provides a second opinion on test quality. It acts like a senior engineer reviewing your test results to catch issues that passing tests might hide.

## When to Use the Judge Model

### 🚨 MANDATORY SCENARIOS:
1. **All Tests Pass (100% Success Rate)** - THIS IS THE MOST IMPORTANT TRIGGER
   - Perfect results often hide lazy or incomplete tests
   - Always validate before saying "ready to deploy"

2. **Before Any Deployment Decision**
   - Never recommend deployment without judge validation
   - Even if tests pass, quality matters

3. **After Fixing All Test Failures**
   - When you've fixed failures and now all pass
   - Verify the fixes are real, not just bypassed

### 📊 RECOMMENDED SCENARIOS:
- Test results seem suspiciously good
- Major refactoring just completed
- Critical features (auth, payments, data)
- First time running tests on new code

## How to Use the Judge Model

### Command 1: `judge` (Recommended - Clearest for Agents)
```bash
# BEST COMMAND - explicitly mentions "judge model"
claude-test-reporter judge test_results.json

# With options
claude-test-reporter judge test_results.json --strict --model gemini-2.5-pro
```

### Command 2: `validate` (Alternative)
```bash
# Alternative command (same functionality)
claude-test-reporter validate test_results.json --fail-on-category lazy --fail-on-category hallucinated
```

## What the Judge Model Detects

### 🚫 Lazy Tests
```python
def test_user_authentication():
    assert True  # This passes but tests nothing!
```

### 🤔 Hallucinated Tests
```python
def test_database_connection():
    # Name suggests DB test, but only tests strings
    assert "hello" + "world" == "helloworld"
```

### ⚠️ Incomplete Tests
```python
def test_api_response():
    response = api.get("/users")
    assert response is not None  # Missing status code, data validation
```

### 🎲 Flaky Tests
```python
def test_async_operation():
    time.sleep(1)  # Timing dependent
    assert check_result()  # May randomly fail
```

## Agent Workflow Example

```python
# Step 1: Run tests
pytest --json-report --json-report-file=test_results.json

# Step 2: Check results
results = analyze_test_results("test_results.json")

if results["all_passed"]:
    print("✅ All tests passed!")
    print("🧑‍⚖️ Requesting judge model validation...")
    
    # Step 3: MANDATORY - Request judge validation
    validation = run_command("claude-test-reporter judge test_results.json --strict")
    
    if validation.exit_code == 0:
        print("✅ Tests pass AND quality verified by judge")
        print("✅ SAFE TO DEPLOY")
    else:
        print("❌ Judge found quality issues")
        print("❌ DO NOT DEPLOY - Fix test quality first")
else:
    print(f"❌ {results['failed_count']} tests failing")
    print("Fix failures before requesting judge validation")
```

## Understanding Judge Output

### Good Result:
```
🧑‍⚖️ Judge Model Validation Complete
Model: gemini/gemini-2.5-pro
Tests validated: 50

Test Quality Categories:
  ✅ good: 48
  ⚠️ incomplete: 2

✅ All tests validated - good quality!
✅ Safe to deploy
```

### Bad Result:
```
🧑‍⚖️ Judge Model Validation Complete
Model: gemini/gemini-2.5-pro
Tests validated: 50

Test Quality Categories:
  ✅ good: 35
  ⚠️ lazy: 10
  ⚠️ hallucinated: 3
  ⚠️ incomplete: 2

❌ VALIDATION FAILED - Quality issues detected
Found 15 problematic tests

Action required: Fix test quality issues before deployment
```

## Quick Decision Tree

```
Tests Run
    |
    ├── Some Failed → Fix failures first
    |
    └── All Passed → Run: claude-test-reporter judge test_results.json
                        |
                        ├── Judge Approves → Safe to deploy ✅
                        |
                        └── Judge Finds Issues → Fix test quality ❌
```

## Common Agent Mistakes to Avoid

### ❌ WRONG: Skipping judge validation when all pass
```bash
# Tests pass
echo "All tests passed! Ready to deploy!"  # NO! Need judge validation first
```

### ✅ CORRECT: Always validate perfect results
```bash
# Tests pass
echo "All tests passed! Requesting judge validation..."
claude-test-reporter judge test_results.json --strict
```

### ❌ WRONG: Ignoring judge warnings
```bash
# Judge finds issues but agent proceeds
echo "Some warnings but tests pass, deploying anyway"  # NO!
```

### ✅ CORRECT: Treating judge issues as blockers
```bash
# Judge finds issues
echo "Judge found quality issues - blocking deployment"
echo "Action required: Fix lazy/incomplete tests"
```

## Integration with AgentReportAdapter

The `AgentReportAdapter` now includes built-in validation recommendations:

```python
from claude_test_reporter.core.adapters.agent_report_adapter import AgentReportAdapter

adapter = AgentReportAdapter(Path("test_results.json"))
status = adapter.get_quick_status()

if status.get("validation_recommended"):
    print(f"📋 {status['validation_reason']}")
    # Run: claude-test-reporter judge test_results.json
```

## Remember

1. **Perfect test results are suspicious** - Always validate with judge
2. **The judge is your quality partner** - Not an obstacle
3. **Test quality matters as much as passing** - Both must be good
4. **When in doubt, ask the judge** - Better safe than sorry

## TL;DR for Agents

**WHEN ALL TESTS PASS → RUN `claude-test-reporter judge test_results.json`**

This ensures you're not being fooled by lazy or fake tests. Only recommend deployment when BOTH tests pass AND judge approves.