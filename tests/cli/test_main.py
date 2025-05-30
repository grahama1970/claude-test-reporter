"""Tests for the CLI main module."""
import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from claude_test_reporter.cli.main import app

runner = CliRunner()


class TestCLICommands:
    def test_run_command_help(self):
        """Test the run command help output."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "Run tests and generate reports" in result.stdout
    
    def test_verify_command_help(self):
        """Test the verify-test-results command help output."""
        result = runner.invoke(app, ["verify-test-results", "--help"])
        assert result.exit_code == 0
        assert "Verify test results" in result.stdout
    
    def test_llm_analyze_command_help(self):
        """Test the llm-analyze command help output."""
        result = runner.invoke(app, ["llm-analyze", "--help"])
        assert result.exit_code == 0
        assert "Analyze test results using LLM" in result.stdout
    
    @patch('claude_test_reporter.cli.main.TestResultVerifier')
    def test_verify_test_results_command(self, mock_verifier):
        """Test the verify-test-results command execution."""
        # Create a mock verifier instance
        verifier_instance = Mock()
        verifier_instance.create_immutable_test_record.return_value = {
            "total_tests": 10,
            "passed_tests": 8,
            "failed_tests": 2,
            "hash": "abc123"
        }
        mock_verifier.return_value = verifier_instance
        
        # Create a temporary test results file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"name": "test_1", "status": "PASS"},
                {"name": "test_2", "status": "FAIL"}
            ], f)
            temp_file = f.name
        
        try:
            result = runner.invoke(app, ["verify-test-results", temp_file])
            assert result.exit_code == 0
            assert "Creating immutable test record" in result.stdout
        finally:
            import os
            os.unlink(temp_file)