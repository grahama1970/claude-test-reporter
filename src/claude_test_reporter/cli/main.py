
"""
Module: main.py
Description: Functions for main operations
"""

External Dependencies:
- typer: [Documentation URL]
- rich: [Documentation URL]
- claude_test_reporter: [Documentation URL]
- : [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Claude Test Reporter CLI - Typer Version

Command-line interface for generating test reports optimized for Claude analysis.

Features:
- Generate HTML reports from pytest JSON
- Create multi-project dashboards
- Track test history and trends
- Format reports for AI analysis
- Support multiple test frameworks

Dependencies:
- typer: CLI framework
- rich: Terminal formatting
- All claude_test_reporter dependencies
"""

import sys
import json
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import print

from claude_test_reporter.core.generators import UniversalReportGenerator
from claude_test_reporter.core.generators.multi_project_dashboard import MultiProjectDashboard
from claude_test_reporter.core.tracking import TestHistoryTracker
from claude_test_reporter.core.adapters import AgentReportAdapter
from claude_test_reporter import get_report_config
from claude_test_reporter.analyzers import LLMTestAnalyzer, TestReportVerifier
from claude_test_reporter.core.test_result_verifier import TestResultVerifier, HallucinationDetector
from claude_test_reporter.config import Config, setup_environment
from .slash_mcp_mixin import add_slash_mcp_commands
from .validate import validate
from .code_review import code_review

# Create console for pretty output
console = Console()

# Create Typer app
app = typer.Typer(
    name="claude-test-cli",
    help="Generate test reports optimized for Claude analysis",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command(name="from-pytest")
def from_pytest(
    json_file: Path = typer.Argument(..., help="Pytest JSON report file"),
    output: Path = typer.Option("report.html", "--output", "-o", help="Output file"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name for config")
):
    """Generate report from pytest JSON."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            data = json.load(f)

        # Get config if project specified
        config = get_report_config(project) if project else {}

        # Generate report
        generator = UniversalReportGenerator(config)
        html = generator.generate_pytest_report(data)

        # Write output
        output.write_text(html)
        console.print(f"[green]✓[/green] Report generated: {output}")

        # Show summary
        summary = data.get('summary', {})
        if summary:
            console.print(f"  Total: {summary.get('total', 0)} tests")
            console.print(f"  Passed: {summary.get('passed', 0)}")
            console.print(f"  Failed: {summary.get('failed', 0)}")

    except Exception as e:
        console.print(f"[red]Error generating report:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="from-data")
def from_data(
    data_file: Path = typer.Argument(..., help="JSON data file"),
    output: Path = typer.Option("report.html", "--output", "-o", help="Output file"),
    title: str = typer.Option("Test Report", "--title", "-t", help="Report title"),
    color: str = typer.Option("#667eea", "--color", "-c", help="Theme color")
):
    """Generate report from JSON data."""
    if not data_file.exists():
        console.print(f"[red]Error:[/red] File not found: {data_file}")
        raise typer.Exit(1)

    try:
        with open(data_file) as f:
            data = json.load(f)

        # Create config
        config = {
            'title': title,
            'theme_color': color
        }

        # Generate report
        generator = UniversalReportGenerator(config)
        html = generator.generate_from_data(data)

        # Write output
        output.write_text(html)
        console.print(f"[green]✓[/green] Report generated: {output}")

    except Exception as e:
        console.print(f"[red]Error generating report:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def analyze(
    json_file: Path = typer.Argument(..., help="Pytest JSON report file"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name")
):
    """Analyze pytest results and show insights."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            data = json.load(f)

        # Create adapter for analysis
        adapter = AgentReportAdapter()
        analysis = adapter.analyze_results(data)

        # Display analysis
        console.print("[cyan]Test Analysis[/cyan]")
        console.print()

        # Summary table
        table = Table(title="Test Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        summary = data.get('summary', {})
        table.add_row("Total Tests", str(summary.get('total', 0)))
        table.add_row("Passed", str(summary.get('passed', 0)))
        table.add_row("Failed", str(summary.get('failed', 0)))
        table.add_row("Skipped", str(summary.get('skipped', 0)))
        table.add_row("Duration", f"{data.get('duration', 0):.2f}s")

        console.print(table)

        # Failed tests
        if analysis.get('failed_tests'):
            console.print("\n[red]Failed Tests:[/red]")
            for test in analysis['failed_tests']:
                console.print(f"  • {test['name']}")
                if test.get('error'):
                    console.print(f"    {test['error'][:100]}...")

        # Recommendations
        if analysis.get('recommendations'):
            console.print("\n[yellow]Recommendations:[/yellow]")
            for rec in analysis['recommendations']:
                console.print(f"  • {rec}")

    except Exception as e:
        console.print(f"[red]Error analyzing results:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def dashboard(
    project_dirs: List[Path] = typer.Argument(..., help="Project directories to include"),
    output: Path = typer.Option("dashboard.html", "--output", "-o", help="Output file"),
    title: str = typer.Option("Test Dashboard", "--title", "-t", help="Dashboard title")
):
    """Create multi-project test dashboard."""
    try:
        # Validate directories
        for dir_path in project_dirs:
            if not dir_path.exists():
                console.print(f"[red]Error:[/red] Directory not found: {dir_path}")
                raise typer.Exit(1)

        # Create dashboard
        dashboard = MultiProjectDashboard()

        # Add projects
        for dir_path in project_dirs:
            # Look for test results
            json_files = list(dir_path.glob("**/test-results*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file) as f:
                    data = json.load(f)
                dashboard.add_project(dir_path.name, data)
                console.print(f"[green]✓[/green] Added project: {dir_path.name}")
            else:
                console.print(f"[yellow]⚠[/yellow]  No test results found in: {dir_path}")

        # Generate dashboard
        html = dashboard.generate(title=title)

        # Write output
        output.write_text(html)
        console.print(f"\n[green]✓[/green] Dashboard generated: {output}")

    except Exception as e:
        console.print(f"[red]Error creating dashboard:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def history(
    project: str = typer.Argument(..., help="Project name"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to show"),
    metric: str = typer.Option("pass_rate", "--metric", "-m", help="Metric to display")
):
    """Show test history and trends."""
    try:
        tracker = TestHistoryTracker()
        history_data = tracker.get_history(project, days=days)

        if not history_data:
            console.print(f"No history found for project: {project}")
            return

        # Create history table
        table = Table(title=f"{project} Test History ({days} days)")
        table.add_column("Date", style="cyan")
        table.add_column("Tests", style="yellow")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Pass Rate", style="magenta")

        for entry in history_data:
            table.add_row(
                entry['date'],
                str(entry['total']),
                str(entry['passed']),
                str(entry['failed']),
                f"{entry['pass_rate']:.1f}%"
            )

        console.print(table)

        # Show trend
        if len(history_data) > 1:
            first_rate = history_data[0]['pass_rate']
            last_rate = history_data[-1]['pass_rate']
            trend = last_rate - first_rate

            if trend > 0:
                console.print(f"\n[green]↑ Pass rate improved by {trend:.1f}%[/green]")
            elif trend < 0:
                console.print(f"\n[red]↓ Pass rate decreased by {abs(trend):.1f}%[/red]")
            else:
                console.print("\n[yellow]→ Pass rate unchanged[/yellow]")

    except Exception as e:
        console.print(f"[red]Error showing history:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def format(
    json_file: Path = typer.Argument(..., help="Test results JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    style: str = typer.Option("claude", "--style", "-s", help="Format style (claude, github, markdown)")
):
    """Format test results for AI analysis."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            data = json.load(f)

        # Create adapter
        adapter = AgentReportAdapter()

        # Format based on style
        if style == "claude":
            formatted = adapter.format_for_claude(data)
        elif style == "github":
            formatted = adapter.format_for_github(data)
        elif style == "markdown":
            formatted = adapter.format_as_markdown(data)
        else:
            console.print(f"[red]Error:[/red] Unknown style: {style}")
            raise typer.Exit(1)

        # Output
        if output:
            output.write_text(formatted)
            console.print(f"[green]✓[/green] Formatted output written to: {output}")
        else:
            console.print(formatted)

    except Exception as e:
        console.print(f"[red]Error formatting results:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def setup():
    """Interactive setup for environment configuration."""
    setup_environment()


@app.command()
def version():
    """Show version information."""
    console.print("[cyan]Claude Test Reporter[/cyan]")
    console.print("Version: 0.2.1")
    console.print("Generate test reports optimized for AI analysis with hallucination prevention")


@app.command()
def health():
    """Check system health and dependencies."""
    console.print("[cyan]System Health Check[/cyan]")
    console.print()

    # Check dependencies
    deps = {
        "jinja2": "Template engine",
        "pytest": "Test framework",
        "rich": "Terminal formatting",
        "llm_call": "LLM integration",
        "typer": "CLI framework"
    }

    all_good = True
    for package, description in deps.items():
        try:
            __import__(package)
            console.print(f"[green]✓[/green] {package} ({description})")
        except ImportError:
            console.print(f"[red]✗[/red] {package} ({description}) - Not installed")
            all_good = False

    if all_good:
        console.print("\n[green]✓ All dependencies are installed![/green]")
    else:
        console.print("\n[yellow]⚠ Some dependencies are missing[/yellow]")


@app.command(name="verify-test-results")
def verify_test_results(
    json_file: Path = typer.Argument(..., help="Test results JSON file"),
    output: Path = typer.Option("verified_results.json", "--output", "-o", help="Output file"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json/text)")
):
    """Create cryptographically verified test results to prevent hallucinations."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            test_results = json.load(f)

        # Create verifier
        verifier = TestResultVerifier()

        if format == "json":
            # Create immutable record
            record = verifier.create_immutable_test_record(test_results)
            output.write_text(json.dumps(record, indent=2))

            console.print(f"[green]✓[/green] Verified record created: {output}")
            console.print(f"  Hash: {record['verification']['hash'][:16]}...")
            console.print(f"  Failed tests: {record['immutable_facts']['failed_count']}")
            console.print(f"  Deployment: {'BLOCKED' if record['immutable_facts']['failed_count'] > 0 else 'ALLOWED'}")
        else:
            # Create text summary
            summary = TestReportVerifier().create_verified_summary(test_results)
            output.write_text(summary)
            console.print(f"[green]✓[/green] Verified summary created: {output}")

    except Exception as e:
        console.print(f"[red]Error verifying results:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="llm-analyze")
def llm_analyze(
    json_file: Path = typer.Argument(..., help="Test results JSON file"),
    project: str = typer.Argument(..., help="Project name"),
    model: str = typer.Option("gemini-2.5-pro", "--model", "-m", help="LLM model to use"),
    output: Path = typer.Option("llm_analysis.json", "--output", "-o", help="Output file"),
    temperature: float = typer.Option(0.1, "--temperature", "-t", help="LLM temperature (0.0-1.0)")
):
    """Analyze test results with LLM (Gemini 2.5 Pro) for insights."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            test_results = json.load(f)

        console.print(f"[cyan]Analyzing with {model}...[/cyan]")

        # Create analyzer
        analyzer = LLMTestAnalyzer(model=model, temperature=temperature)

        # Generate analysis
        report_path = analyzer.generate_anti_hallucination_report(
            test_results, project, str(output)
        )

        console.print(f"[green]✓[/green] Analysis complete: {report_path}")

        # Load and show key findings
        with open(report_path) as f:
            report = json.load(f)

        analysis = report.get("llm_analysis", {})
        if "error" not in analysis:
            # Show summary
            summary = analysis.get("summary", {})
            console.print(f"\n[bold]Analysis Summary:[/bold]")
            console.print(f"  Status: {summary.get('overall_status', 'unknown')}")
            console.print(f"  Confidence: {summary.get('confidence_level', 'unknown')}")
            console.print(f"  Deployment Ready: {'Yes' if summary.get('requires_immediate_action') == False else 'No'}")

            # Show top recommendations
            recs = analysis.get("recommendations", [])
            if recs:
                console.print(f"\n[bold]Top Recommendations:[/bold]")
                for i, rec in enumerate(recs[:3], 1):
                    console.print(f"  {i}. [{rec['priority']}] {rec['action']}")
        else:
            console.print(f"[yellow]Analysis failed: {analysis['error']}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during LLM analysis:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="check-hallucination")
def check_hallucination(
    results_file: Path = typer.Argument(..., help="Verified test results JSON"),
    response_file: Path = typer.Argument(..., help="LLM or agent response text file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for detailed report")
):
    """Check an LLM/agent response for hallucinations about test results."""
    if not results_file.exists() or not response_file.exists():
        console.print("[red]Error:[/red] One or more files not found")
        raise typer.Exit(1)

    try:
        # Load verified results
        with open(results_file) as f:
            verified_record = json.load(f)

        # Load response text
        response_text = response_file.read_text()

        # Create detector
        detector = HallucinationDetector()

        # Check for hallucinations
        result = detector.check_response(response_text, verified_record)

        # Display results
        if result["hallucinations_detected"]:
            console.print(f"[red]❌ Hallucinations detected: {result['detection_count']} issues[/red]\n")

            for detection in result["detections"]:
                severity_color = "red" if detection["severity"] == "critical" else "yellow"
                console.print(f"[{severity_color}]• {detection['type']}:[/{severity_color}]")
                console.print(f"  {detection['details']}")
                console.print(f"  Expected: {detection['expected']}\n")
        else:
            console.print("[green]✓ No hallucinations detected![/green]")
            console.print("The response accurately reflects the test results.")

        # Save detailed report if requested
        if output:
            report = {
                "timestamp": typer.get_app_dir("claude-test-reporter"),
                "verified_results": verified_record,
                "response_analyzed": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "hallucination_check": result
            }
            output.write_text(json.dumps(report, indent=2))
            console.print(f"\n[green]✓[/green] Detailed report saved: {output}")

    except Exception as e:
        console.print(f"[red]Error checking hallucinations:[/red] {e}")
        raise typer.Exit(1)


@app.command(name="create-llm-prompt")
def create_llm_prompt(
    json_file: Path = typer.Argument(..., help="Test results JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    style: str = typer.Option("strict", "--style", "-s", help="Prompt style (strict/friendly)")
):
    """Create an LLM prompt that enforces accurate test reporting."""
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        with open(json_file) as f:
            test_results = json.load(f)

        # Create verifier
        verifier = TestResultVerifier()

        # Generate prompt
        prompt = verifier.create_llm_prompt_template(test_results)

        # Output
        if output:
            output.write_text(prompt)
            console.print(f"[green]✓[/green] LLM prompt saved: {output}")
        else:
            console.print("[bold]LLM Prompt:[/bold]")
            console.print(prompt)

    except Exception as e:
        console.print(f"[red]Error creating prompt:[/red] {e}")
        raise typer.Exit(1)


# Add the validate command with clear judge model description
app.add_typer(
    validate,
    name="validate",
    help="🧑‍⚖️ Use JUDGE MODEL (LLM) to validate test quality - IMPORTANT: Run this when ALL tests pass!"
)

# Add the code review command
app.add_typer(
    code_review,
    name="code-review",
    help="Review code changes using LLM for quality and security issues"
)

# Add slash command and MCP generation capabilities
add_slash_mcp_commands(app, command_prefix="generate")


@app.command(name="judge")
def judge_command(
    json_file: Path = typer.Argument(..., help="Test results JSON file"),
    output: Path = typer.Option("judge_validation.json", "--output", "-o", help="Output file"),
    model: str = typer.Option("gemini-2.5-pro", "--model", "-m", help="Judge model to use (default: Gemini 2.5 Pro)"),
    strict: bool = typer.Option(True, "--strict", help="Fail on any quality issues found")
):
    """
    🧑‍⚖️ REQUEST SECOND OPINION from JUDGE MODEL when all tests pass.

    The JUDGE MODEL is an external LLM (Gemini 2.5 Pro) that validates test quality.

    WHEN TO USE THIS:
    • ✅ When ALL tests pass (100% success) - most important!
    • ✅ Before deployment decisions
    • ✅ After fixing all test failures
    • ✅ When test results seem too good to be true

    The judge detects:
    • Lazy tests (e.g., assert True)
    • Incomplete tests (missing assertions)
    • Hallucinated tests (don't test what they claim)
    • Flaky tests (timing dependencies)

    Example:
        claude-test-reporter judge test_results.json
        claude-test-reporter judge test_results.json --strict --model gemini-2.5-pro
    """
    if not json_file.exists():
        console.print(f"[red]Error:[/red] File not found: {json_file}")
        raise typer.Exit(1)

    try:
        # Load test results
        with open(json_file) as f:
            test_results = json.load(f)

        # Check if validation is needed
        summary = test_results.get('summary', {})
        total = summary.get('total', 0)
        failed = summary.get('failed', 0)

        if failed == 0 and total > 0:
            console.print("[green]✅ All tests passed![/green]")
            console.print("[yellow]🔍 This is exactly when judge validation is most important![/yellow]\n")

        # Create validator
        from claude_test_reporter.core.test_validator import TestValidator
        validator = TestValidator(model=f"gemini/{model}" if "gemini" in model else model)

        console.print(f"[cyan]🧑‍⚖️ Requesting second opinion from {model} judge model...[/cyan]\n")

        # Validate all tests
        validation_results = validator.validate_all_tests(test_results)

        # Save results
        with open(output, 'w') as f:
            json.dump(validation_results, f, indent=2)

        # Display summary
        summary = validation_results.get('summary', {})
        problematic = summary.get('problematic_tests', [])
        categories = summary.get('categories', {})

        console.print(f"[bold]📋 Judge Model Validation Complete[/bold]")
        console.print(f"Model: {validation_results.get('model')}")
        console.print(f"Tests validated: {validation_results.get('total_tests')}")
        console.print()

        # Show categories
        if categories:
            console.print("[bold]Test Quality Categories:[/bold]")
            for category, count in categories.items():
                icon = "✅" if category == "good" else "⚠️"
                console.print(f"  {icon} {category}: {count}")

        # Check for issues
        quality_issues = ['lazy', 'hallucinated', 'incomplete', 'flaky']
        issues_found = any(cat in categories for cat in quality_issues)

        if issues_found and strict:
            console.print(f"\n[red]❌ VALIDATION FAILED - Quality issues detected[/red]")
            console.print(f"[red]Found {len(problematic)} problematic tests[/red]")
            console.print("\n[yellow]Action required: Fix test quality issues before deployment[/yellow]")
            raise typer.Exit(1)
        elif issues_found:
            console.print(f"\n[yellow]⚠️  Quality issues found in {len(problematic)} tests[/yellow]")
            console.print("Consider fixing these before deployment")
        else:
            console.print("\n[green]✅ All tests validated - good quality![/green]")
            console.print("[green]Safe to deploy[/green]")

        console.print(f"\n[dim]Full validation report saved: {output}[/dim]")

    except ImportError:
        console.print("[red]Error: Test validator not available. Install llm_call dependency.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during validation:[/red] {e}")
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
