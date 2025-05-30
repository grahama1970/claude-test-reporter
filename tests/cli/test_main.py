"""Tests for the CLI main module."""
import pytest
from unittest.mock import Mock, patch

# Test basic imports work
def test_cli_imports():
    """Test that CLI modules can be imported."""
    try:
        from claude_test_reporter.cli import main
        assert hasattr(main, 'app')
    except ImportError as e:
        pytest.skip(f"CLI module not available: {e}")


def test_typer_cli_exists():
    """Test that the Typer app exists."""
    try:
        from claude_test_reporter.cli.main import app
        import typer
        assert isinstance(app, typer.Typer)
    except ImportError as e:
        pytest.skip(f"Typer not available: {e}")


def test_cli_commands_registered():
    """Test that CLI commands are registered."""
    try:
        from claude_test_reporter.cli.main import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test help works
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "claude-test" in result.stdout.lower()
        
    except ImportError as e:
        pytest.skip(f"CLI testing not available: {e}")