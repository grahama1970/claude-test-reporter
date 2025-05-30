# Test Result Verification Guide

## Overview

Claude Test Reporter includes advanced verification features to prevent hallucinations about test results when using LLMs (especially Gemini 2.5 Pro). This guide explains how to use these features effectively.

## Why Verification Matters

LLMs can sometimes:
- Round up success rates (e.g., "approximately 95%" when it's actually 92%)
- Minimize failures (e.g., "only a few tests failed" when 10+ failed)
- Suggest deployment when tests are failing
- Ignore or misrepresent critical failures

Our verification system prevents these hallucinations through cryptographic verification and strict fact enforcement.

## Quick Start

### 1. Install and Configure

```bash
# Install claude-test-reporter
pip install git+https://github.com/grahama1970/claude_test_reporter.git

# Run interactive setup
claude-test-reporter setup

# Or manually create .env file
GEMINI_API_KEY=your-api-key-here
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
```

### 2. Verify Test Results

```bash
# Run tests and generate JSON report
pytest --json-report --json-report-file=results.json

# Create cryptographically verified results
claude-test-reporter verify-test-results results.json \
  --output verified.json \
  --format json
```

### 3. Analyze with LLM

```bash
# Send to Gemini 2.5 Pro for analysis
claude-test-reporter llm-analyze results.json MyProject \
  --model gemini-2.5-pro \
  --temperature 0.1 \
  --output analysis.json
```

### 4. Check for Hallucinations

```bash
# Check any LLM/agent response for hallucinations
claude-test-reporter check-hallucination \
  verified.json \
  agent_response.txt \
  --output hallucination_report.json
```

## Verification Process

### 1. Immutable Test Records

Every test result is converted into an immutable record with:

```json
{
  "verification": {
    "version": "1.0",
    "timestamp": "2024-01-15T10:30:00",
    "hash": "a3f5b8c9d2e1..."  // SHA256 hash
  },
  "immutable_facts": {
    "total_test_count": 100,
    "passed_count": 92,
    "failed_count": 8,
    "exact_success_rate": 92.0,
    "deployment_allowed": false
  },
  "failed_test_details": [
    {
      "name": "test_auth::test_login",
      "error_type": "assertion_failure",
      "must_fix": true
    }
  ],
  "anti_hallucination_statements": [
    "EXACTLY 8 tests are failing",
    "Success rate is EXACTLY 92.0%",
    "Deployment is BLOCKED"
  ]
}
```

### 2. LLM Prompt Templates

The system generates prompts that enforce accurate reporting:

```bash
# Generate a strict prompt for LLM
claude-test-reporter create-llm-prompt results.json \
  --output prompt.txt \
  --style strict
```

The prompt includes:
- Exact numbers that MUST be stated
- Verification hash that MUST be included
- Rules preventing common hallucinations
- Clear deployment decision logic

### 3. Hallucination Detection

The system checks for common patterns:

| Pattern | Example | Detection |
|---------|---------|-----------|
| Rounding up | "approximately 95%" | Missing exact rate |
| Minimizing | "only a few failures" | Not stating exact count |
| False approval | "ready to deploy" | When failures > 0 |
| Missing hash | No verification hash | Critical verification failure |

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Verify and analyze tests
  run: |
    # Create verified results
    claude-test-reporter verify-test-results test-results.json
    
    # Analyze with LLM
    claude-test-reporter llm-analyze test-results.json ${{ github.repository }}
    
    # Create safe prompt for PR comment
    claude-test-reporter create-llm-prompt test-results.json \
      --output pr-comment-prompt.txt
```

### Monitoring Setup

Enable continuous monitoring:

```python
from claude_test_reporter.monitoring import HallucinationMonitor

# Initialize monitor
monitor = HallucinationMonitor(
    log_dir="./logs",
    enable_alerts=True
)

# Add alert callback
def slack_alert(alert):
    # Send to Slack when hallucinations detected
    pass

monitor.add_alert_callback(slack_alert)

# Start monitoring
monitor.start_background_monitoring()
```

## Best Practices

### 1. Always Verify First

```bash
# ❌ Bad: Direct LLM analysis
claude-test-reporter llm-analyze raw-results.json

# ✅ Good: Verify then analyze
claude-test-reporter verify-test-results raw-results.json
claude-test-reporter llm-analyze raw-results.json
```

### 2. Use Low Temperature

```bash
# For factual accuracy, use temperature 0.0-0.1
claude-test-reporter llm-analyze results.json \
  --temperature 0.1
```

### 3. Include Verification in Prompts

When creating custom prompts, always include:
- The verification hash
- Exact numbers
- Explicit deployment decision

### 4. Monitor Continuously

Set up monitoring to catch hallucinations:

```bash
# View hallucination dashboard
claude-test-reporter monitor-dashboard \
  --output dashboard.html
```

## Troubleshooting

### "No API key found"

```bash
# Check configuration
claude-test-reporter health

# Re-run setup
claude-test-reporter setup
```

### "Hallucinations detected"

1. Check the hallucination report for details
2. Review the original response
3. Use stricter prompts or lower temperature
4. Consider switching LLM models

### Performance Issues

- Verification adds minimal overhead (<100ms)
- LLM calls may take 2-5 seconds
- Use caching for repeated analyses

## Advanced Usage

### Custom Verification Rules

```python
from claude_test_reporter.core.test_result_verifier import TestResultVerifier

verifier = TestResultVerifier()

# Add custom rules
verifier.add_rule("no_flaky_tests", lambda r: r["flaky_count"] == 0)
verifier.add_rule("performance_threshold", lambda r: r["avg_duration"] < 1.0)
```

### Batch Processing

```bash
# Process multiple projects
for project in project1 project2 project3; do
  claude-test-reporter verify-test-results $project/results.json \
    --output $project/verified.json
done
```

### Integration with Other LLMs

While optimized for Gemini 2.5 Pro, the system works with any LLM:

```bash
# Use with Claude
export ANTHROPIC_API_KEY=your-key
claude-test-reporter llm-analyze results.json \
  --model claude-3-opus

# Use with GPT-4
export OPENAI_API_KEY=your-key  
claude-test-reporter llm-analyze results.json \
  --model gpt-4
```

## Security Considerations

1. **API Keys**: Never commit `.env` files
2. **Verification Hashes**: Cannot be forged without the original data
3. **Logs**: Hallucination logs may contain sensitive test names
4. **Network**: LLM calls require internet access

## Support

- **Issues**: https://github.com/grahama1970/claude-test-reporter/issues
- **Documentation**: https://github.com/grahama1970/claude-test-reporter/docs
- **Examples**: See `/examples/demo_llm_verification.py`

---

Remember: The goal is to ensure LLMs report test results accurately, preventing false confidence in failing code. When in doubt, verify!