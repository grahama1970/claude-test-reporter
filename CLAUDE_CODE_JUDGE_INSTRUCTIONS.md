# 🧑‍⚖️ CLAUDE CODE: Judge Model Instructions

## FOR CLAUDE CODE: When to Call the Judge Model

### The Golden Rule
**When ALL tests pass → ALWAYS call the judge model**

### Quick Reference

```python
# After running tests, ALWAYS do this check:
from claude_test_reporter import should_call_judge

needs_judge, reason = should_call_judge("test_results.json")
if needs_judge:
    # Run: claude-test-reporter judge test_results.json
```

### Decision Flow for Claude Code

```
1. Run tests: pytest --json-report --json-report-file=test_results.json
2. Load results
3. Check status:
   - Any failures? → Fix them first (don't call judge yet)
   - ALL PASS? → MUST CALL JUDGE! ← This is critical
   - Judge approves? → Safe to deploy
   - Judge rejects? → Fix test quality issues
```

### The Judge Command

When all tests pass, ALWAYS run:

```bash
claude-test-reporter judge test_results.json
```

This command:
- Uses an external LLM (Gemini 2.5 Pro) as a "judge"
- Validates test quality
- Detects lazy, incomplete, or fake tests
- Returns exit code 0 if quality is good, 1 if issues found

### Why This Matters

Perfect test results (100% pass) often hide:
- **Lazy tests**: `assert True` 
- **Incomplete tests**: Missing critical assertions
- **Hallucinated tests**: Test name doesn't match what it tests
- **Flaky tests**: Time-dependent or external dependencies

### Integration Pattern for Claude Code

```python
import subprocess
import json
from pathlib import Path

def validate_test_results():
    """Pattern Claude Code should follow."""
    
    # Load test results
    with open("test_results.json") as f:
        results = json.load(f)
    
    summary = results['summary']
    
    # Key decision point
    if summary['failed'] == 0 and summary['total'] > 0:
        print("✅ All tests passed!")
        print("🧑‍⚖️ Calling judge for quality validation...")
        
        # THIS IS THE CRITICAL STEP
        result = subprocess.run(
            ["claude-test-reporter", "judge", "test_results.json"],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ Judge approved - safe to deploy!")
            return True
        else:
            print("❌ Judge found quality issues - fix them first!")
            return False
    
    elif summary['failed'] > 0:
        print(f"❌ {summary['failed']} tests failing - fix them first")
        return False
```

### Common Scenarios

#### Scenario 1: All Tests Pass
```
Test Results: 50/50 passed
Claude Code Action: MUST run `claude-test-reporter judge test_results.json`
```

#### Scenario 2: Some Tests Fail
```
Test Results: 48/50 passed, 2 failed
Claude Code Action: Fix failures first, no judge needed yet
```

#### Scenario 3: Judge Finds Issues
```
Judge Output: Found 3 lazy tests, 1 incomplete test
Claude Code Action: Fix test quality, do NOT deploy
```

#### Scenario 4: Judge Approves
```
Judge Output: All tests have good quality
Claude Code Action: Safe to deploy ✅
```

### Error Messages Claude Code Might See

1. **When judge validation needed:**
   ```
   ✅ All tests passed!
   🧑‍⚖️ Perfect results - judge validation is critical!
   ```

2. **When judge finds issues:**
   ```
   ❌ Judge validation FAILED - Quality issues detected
     • lazy: 2 tests
     • incomplete: 1 tests
   ⚠️ Fix test quality before deployment!
   ```

3. **When judge approves:**
   ```
   ✅ Judge validation PASSED - Good test quality!
   ```

### Remember

1. **Perfect results are suspicious** - Always validate
2. **The judge is not optional** - It's required when all tests pass
3. **Judge failures block deployment** - This is by design
4. **Test quality = Code quality** - Both matter equally

### TL;DR

```bash
# When Claude Code sees all tests pass:
claude-test-reporter judge test_results.json

# Only deploy if exit code is 0
```