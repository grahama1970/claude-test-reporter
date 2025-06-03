"""Claude Test Reporter - Universal test reporting engine for Claude companion projects."""

# Import core functionality
from claude_test_reporter.core.test_reporter import TestReporter
from claude_test_reporter.core.report_config import get_report_config

# Import generators
try:
    from claude_test_reporter.core.generators import (
        UniversalReportGenerator,
        MultiProjectDashboard,
        # HistoryReportGenerator might not exist yet
    )
except ImportError:
    # Handle missing imports gracefully during migration
    pass

# Import adapters
try:
    from claude_test_reporter.core.adapters import (
        # These might have different names
        AgentReportAdapter,
    )
except ImportError:
    pass

# Import agent integration
try:
    from claude_test_reporter.agent_integration import (
        AgentTestValidator,
        should_call_judge
    )
except ImportError:
    pass

__version__ = "0.1.0"
__all__ = [
    "TestReporter",
    "get_report_config",
    "UniversalReportGenerator",
    "MultiProjectDashboard",
    "AgentReportAdapter",
    "AgentTestValidator",
    "should_call_judge",
]

# Export pytest plugin hooks for plugin discovery
from claude_test_reporter.pytest_plugin import (
    pytest_addoption,
    pytest_configure,
    pytest_unconfigure
)
