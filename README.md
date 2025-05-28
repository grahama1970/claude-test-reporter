# Claude Test Reporter

A universal test reporting engine for Claude companion projects. Zero dependencies, beautiful reports, multi-project monitoring.

## Features

- 🚀 **Zero Dependencies** - Uses only Python standard library
- 📊 **Beautiful HTML Reports** - Sortable, searchable, exportable
- 🔍 **Pytest Integration** - Works seamlessly with pytest-json-report
- 🎨 **Customizable Themes** - Per-project branding support
- 🤖 **CI/CD Ready** - Agent-friendly report adapters
- 📈 **Multi-Project Dashboard** - Monitor all projects in one view
- 🕐 **Test History Tracking** - Trends and performance over time
- 🎲 **Flaky Test Detection** - Automatic identification of unreliable tests
- 🔄 **Agent Comparison** - Compare results between different agents

## Installation

Since this package is not yet published to PyPI, install directly from Git:

```bash
# Install from GitHub
pip install git+https://github.com/yourusername/claude-test-reporter.git

# Or install from local path in your pyproject.toml
[tool.poetry.dependencies]
claude-test-reporter = {path = "../claude-test-reporter", develop = true}

# Or with pip from local path
pip install -e ../claude-test-reporter
```

**Note:** Development dependencies are only needed for the claude-test-reporter project itself, not for companion projects using it.

## Quick Start

### 1. Generate a Basic Report

```python
from claude_test_reporter.generators import UniversalReportGenerator

# Create test data
data = [
    {"test": "test_login", "status": "PASS", "duration": 1.23},
    {"test": "test_signup", "status": "FAIL", "duration": 0.45},
]

# Generate report
generator = UniversalReportGenerator(
    title="My Test Results",
    theme_color="#667eea",
    logo="🧪"
)
report_path = generator.generate(data, "test_report.html")
print(f"Report generated: {report_path}")
```

### 2. With Pytest Integration

```bash
# Run tests with JSON report
pytest --json-report --json-report-file=results.json

# Generate HTML from JSON
claude-test-report from-pytest results.json -o report.html
```

### 3. Custom Project Configurations

```python
from claude_test_reporter import get_report_config
from claude_test_reporter.generators import UniversalReportGenerator

# Get project-specific config
config = get_report_config("sparta")  # or "marker", "arangodb"
generator = UniversalReportGenerator(**config)
```

## Advanced Features

### Multi-Project Dashboard

Monitor all your projects in a single view:

```bash
# Generate dashboard from multiple project results
claude-test-report dashboard \
  -a SPARTA sparta_results.json \
  -a Marker marker_results.json \
  -a ArangoDB arango_results.json \
  -o dashboard.html
```

### Test History Tracking

Track test performance and reliability over time:

```bash
# View test history for a project
claude-test-report history MyProject -d 30 -o history.html
```

### Agent Comparison

Compare test results between different agents:

```bash
# Compare two agent runs
claude-test-report compare agent1_results.json agent2_results.json -o comparison.json
```

### Flaky Test Detection

Automatically identifies unreliable tests:

```bash
# Analyze with flaky test detection
claude-test-report analyze results.json -p MyProject
```

## Components

### Generators
- `UniversalReportGenerator` - Main report generator with full features
- `SimpleHTMLReporter` - Lightweight alternative for quick reports
- `MultiProjectDashboard` - Cross-project monitoring dashboard

### Adapters
- `AgentReportAdapter` - Extracts actionable items for CI/CD agents with flaky test detection
- `TestReporter` - Basic test result adapter

### Tracking
- `TestHistoryTracker` - Historical test data storage and analysis

### Runners
- `PytestReportRunner` - Orchestrates pytest with multiple report formats

## Storage and Requirements

### Test History Storage
- Test history is stored in `.test_history/` directory (gitignored by default)
- JSON files store up to 100 test runs per project
- Flaky test analysis is stored separately in `flaky_tests.json`
- Storage location can be customized when initializing `TestHistoryTracker`

### Limitations
- **Zero Dependencies**: All features use only Python standard library
- **Browser Compatibility**: Reports work in all modern browsers (Chrome, Firefox, Safari, Edge)
- **Data Size**: HTML reports may become large with thousands of tests
- **History Retention**: Default 100 runs per project (configurable)

### Performance Considerations
- Multi-project dashboard scales well up to ~20 projects
- Test history tracking is efficient for up to 10,000 tests per project
- SVG charts render smoothly with up to 30 data points

## Examples

See the `examples/` directory for:
- Basic HTML report generation
- Multi-project configuration
- Multi-project monitoring demo
- Pytest integration
- CI/CD agent usage

## Integration with Companion Projects

Add to your project's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
claude-test-reporter = {git = "https://github.com/yourusername/claude-test-reporter.git", rev = "main"}

# Or for local development
claude-test-reporter = {path = "../claude-test-reporter", develop = true}
```

Then in your CI/CD pipeline:

```yaml
- name: Run tests and generate report
  run: |
    pytest --json-report --json-report-file=results.json
    claude-test-report from-pytest results.json -p MyProject -o report.html
    claude-test-report analyze results.json -p MyProject
```

## Development

```bash
# Clone and install
git clone https://github.com/yourusername/claude-test-reporter
cd claude-test-reporter
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/
```

## License

MIT
