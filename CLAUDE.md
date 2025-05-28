# CLAUDE.md - Claude Test Reporter Coding Standards

This project follows the Claude companion project coding standards.

## Key Principles

1. **Zero Dependencies** - This package uses ONLY Python standard library
2. **Function-First Design** - Simple functions over complex classes
3. **Real Data Testing** - All tests use actual test results, no mocking
4. **Clear Documentation** - Every module includes purpose and examples

## Project Structure

```
claude-test-reporter/
├── src/
│   └── claude_test_reporter/
│       ├── __init__.py
│       ├── adapters/       # Report adapters for different tools
│       ├── generators/     # HTML report generators
│       ├── runners/        # Test runners and orchestrators
│       └── report_config.py
├── tests/                  # Mirrors src structure
├── examples/               # Working examples
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## Testing

All modules must include validation in their `__main__` block:

```python
if __name__ == "__main__":
    # Test with real data
    data = [{"test": "example", "status": "PASS"}]
    report = generate_report(data)
    assert Path(report).exists()
    print("✅ Validation passed")
```

## Contributing

1. Maintain zero dependencies
2. Add tests for new features
3. Update examples for new functionality
4. Follow Python type hints
