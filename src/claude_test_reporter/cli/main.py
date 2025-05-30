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
def version():
    """Show version information."""
    console.print("[cyan]Claude Test Reporter[/cyan]")
    console.print("Version: 1.0.0")
    console.print("Generate test reports optimized for AI analysis")


@app.command()
def health():
    """Check system health and dependencies."""
    console.print("[cyan]System Health Check[/cyan]")
    console.print()
    
    # Check dependencies
    deps = {
        "jinja2": "Template engine",
        "pytest": "Test framework",
        "rich": "Terminal formatting"
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


# Add slash command and MCP generation capabilities
add_slash_mcp_commands(app, command_prefix="generate")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
