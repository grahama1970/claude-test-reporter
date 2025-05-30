# Claude Test Reporter - Test Suite

This directory contains the test suite for the Claude Test Reporter project.

## Test Structure

The test directory structure mirrors the source code structure exactly:

```
tests/
├── analyzers/          # Tests for LLM test analyzers
├── cli/               # Tests for CLI commands
├── core/              # Tests for core functionality
│   ├── adapters/      # Tests for report adapters
│   ├── generators/    # Tests for report generators
│   ├── runners/       # Tests for test runners
│   └── tracking/      # Tests for test history tracking
├── mcp/               # Tests for MCP server
└── monitoring/        # Tests for hallucination monitoring
```

## Running Tests

### Prerequisites

1. Ensure you're in the project root directory
2. Activate the virtual environment if necessary:
   ```bash
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. Set PYTHONPATH (if not already set in .env):
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

### Run All Tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run all tests with coverage report
python -m pytest tests/ --cov=claude_test_reporter --cov-report=html

# Run tests and generate an HTML report
python -m pytest tests/ --html=test_report.html --self-contained-html
```

### Run Specific Test Categories

```bash
# Run only analyzer tests
python -m pytest tests/analyzers/ -v

# Run only CLI tests
python -m pytest tests/cli/ -v

# Run only core tests
python -m pytest tests/core/ -v

# Run only monitoring tests
python -m pytest tests/monitoring/ -v
```

### Run Individual Test Files

```bash
# Run a specific test file
python -m pytest tests/analyzers/test_llm_test_analyzer.py -v

# Run a specific test function
python -m pytest tests/analyzers/test_llm_test_analyzer.py::test_analyze_test_results -v
```

### Test Options

```bash
# Run tests in parallel (requires pytest-xdist)
python -m pytest tests/ -n auto

# Run only failed tests from last run
python -m pytest tests/ --lf

# Run tests matching a pattern
python -m pytest tests/ -k "analyzer or verifier" -v

# Show print statements during tests
python -m pytest tests/ -s

# Stop on first failure
python -m pytest tests/ -x
```

### Environment Variables for Testing

For LLM-related tests, you may need to set:
```bash
export GEMINI_API_KEY="your-api-key"
export CLAUDE_API_KEY="your-api-key"  # If using Claude
```

Or use a .env file in the project root:
```
GEMINI_API_KEY=your-api-key
CLAUDE_API_KEY=your-api-key
```

### Writing New Tests

1. Create test files with names starting with `test_`
2. Place tests in the directory that mirrors the source module
3. Follow the existing test patterns:

```python
import pytest
from claude_test_reporter.core.some_module import SomeClass

class TestSomeClass:
    def test_basic_functionality(self):
        # Arrange
        instance = SomeClass()
        
        # Act
        result = instance.some_method()
        
        # Assert
        assert result == expected_value
    
    def test_error_handling(self):
        with pytest.raises(ValueError):
            SomeClass().method_that_should_fail()
```

### Test Data

- Use fixtures for reusable test data
- Keep test data minimal but realistic
- Store larger test data files in `tests/fixtures/`

### Continuous Integration

Tests are automatically run on:
- Every push to main branch
- Every pull request
- Can be manually triggered in GitHub Actions

The CI pipeline includes:
- Running all tests
- Coverage reporting
- LLM hallucination verification
- Code quality checks

## Troubleshooting

### Import Errors
If you encounter import errors:
1. Ensure PYTHONPATH includes the src directory
2. Check that you're running from the project root
3. Verify the virtual environment is activated

### Missing Dependencies
```bash
# Install test dependencies
pip install -e .
```

### Slow Tests
Some LLM-related tests may be slow. To skip them:
```bash
python -m pytest tests/ -m "not slow"
```

## Test Coverage Goals

- Maintain >80% code coverage
- 100% coverage for critical paths (verification, hallucination detection)
- All new features must include tests
- All bug fixes must include regression tests