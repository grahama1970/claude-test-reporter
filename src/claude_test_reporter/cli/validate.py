"""Validation command for test results using LLM."""
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.argument("test_results", type=click.Path(exists=True))
@click.option("--model", default="gemini-2.5-pro", help="LLM model to use")
@click.option("--output", "-o", default="validation_results.json", help="Output file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--fail-on-category", multiple=True, default=["suspicious", "invalid"], 
              help="Categories that cause validation to fail")
@click.option("--min-confidence", default=0.8, type=float, 
              help="Minimum confidence threshold")
def validate(test_results: str, model: str, output: str, verbose: bool, 
            fail_on_category: tuple, min_confidence: float) -> int:
    """Validate test results using LLM analysis."""
    try:
        from claude_test_reporter.core.test_validator import TestValidator
    except ImportError:
        console.print("[red]Error: test_validator module not available[/red]")
        return 1
    
    # Load test results
    with open(test_results, 'r') as f:
        data = json.load(f)
    
    # Extract test data
    if isinstance(data, dict) and 'tests' in data:
        tests = data['tests']
    elif isinstance(data, list):
        tests = data
    else:
        console.print("[red]Invalid test results format[/red]")
        return 1
    
    console.print(f"[blue]Validating {len(tests)} test results...[/blue]")
    
    # Run validation
    validator = TestValidator(model=model)
    validation_results = validator.validate_results(tests)
    
    # Display results
    if verbose:
        _display_verbose_results(validation_results)
    else:
        _display_summary(validation_results)
    
    # Save results
    output_path = Path(output)
    with open(output_path, 'w') as f:
        json.dump({
            "test_results": tests,
            "validation": validation_results
        }, f, indent=2)
    
    console.print(f"\n[green]✅ Validation results saved to: {output_path}[/green]")
    
    # Check fail conditions
    if validation_results.get('issues'):
        for issue in validation_results['issues']:
            if issue.get('category') in fail_on_category:
                console.print(f"\n[red]❌ Validation failed: {issue['message']}[/red]")
                return 1
    
    return 0


def _display_summary(results: dict) -> None:
    """Display validation summary."""
    console.print("\n[bold]📋 Validation Summary[/bold]")
    console.print(f"Model: {results.get('model', 'Unknown')}")
    console.print(f"Total tests validated: {results.get('total_tests', 0)}")
    
    if results.get('issues'):
        console.print(f"\n[yellow]⚠️  Found {len(results['issues'])} issues[/yellow]")
    else:
        console.print("\n[green]✅ No issues found[/green]")


def _display_verbose_results(results: dict) -> None:
    """Display detailed validation results."""
    console.print("\n[bold]📋 Validation Results[/bold]")
    
    table = Table(title="Test Validation Details")
    table.add_column("Test Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Issues", style="yellow")
    
    for test_name, validation in results.get('validations', {}).items():
        status = "✅ Valid" if not validation.get('issues') else "⚠️  Issues"
        issues = "\n".join(validation.get('issues', []))
        table.add_row(test_name, status, issues)
    
    console.print(table)


if __name__ == "__main__":
    sys.exit(validate())