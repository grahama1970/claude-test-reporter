"""Validation command for test results using LLM."""
import json
import sys
from pathlib import Path
from typing import Optional
Module: validate.py
Description: Functions for validate operations

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.argument("test_results", type=click.Path(exists=True))
@click.option("--model", default="gemini-2.5-pro", help="Judge model to use (LLM for validation)")
@click.option("--output", "-o", default="validation_results.json", help="Output file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--fail-on-category", multiple=True, default=["lazy", "hallucinated"], 
              help="Categories that cause validation to fail")
@click.option("--min-confidence", default=0.8, type=float, 
              help="Minimum confidence threshold")
def validate(test_results: str, model: str, output: str, verbose: bool, 
            fail_on_category: tuple, min_confidence: float) -> int:
    """
    🧑‍⚖️ Validate test quality using JUDGE MODEL (external LLM).
    
    IMPORTANT: Run this when ALL TESTS PASS to detect:
    - Lazy tests (e.g., assert True)
    - Hallucinated tests (don't test what they claim)
    - Incomplete tests (missing assertions)
    - Flaky tests (timing dependent)
    
    The judge model provides a second opinion on test quality.
    """
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
    
    # Check if all tests passed
    all_passed = all(t.get('outcome') == 'passed' for t in tests if 'outcome' in t)
    if all_passed and len(tests) > 0:
        console.print("[green]✅ All tests passed![/green]")
        console.print("[yellow]🧑‍⚖️ Perfect results - judge validation is critical![/yellow]\n")
    
    console.print(f"[blue]🧑‍⚖️ Validating {len(tests)} tests with {model} judge model...[/blue]")
    
    # Run validation
    validator = TestValidator(model=f"gemini/{model}" if "gemini" in model else model)
    validation_results = validator.validate_all_tests({"tests": tests})
    
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
    
    # Check fail conditions based on summary
    summary = validation_results.get('summary', {})
    categories = summary.get('categories', {})
    problematic_tests = summary.get('problematic_tests', [])
    
    # Check if any fail categories are present
    failed_categories = [cat for cat in fail_on_category if categories.get(cat, 0) > 0]
    
    if failed_categories:
        console.print(f"\n[red]❌ Judge validation FAILED - Quality issues detected[/red]")
        for cat in failed_categories:
            count = categories.get(cat, 0)
            console.print(f"[red]  • {cat}: {count} tests[/red]")
        console.print(f"\n[red]Total problematic tests: {len(problematic_tests)}[/red]")
        console.print("[yellow]⚠️  Fix test quality before deployment![/yellow]")
        return 1
    
    console.print("\n[green]✅ Judge validation PASSED - Good test quality![/green]")
    return 0


def _display_summary(results: dict) -> None:
    """Display validation summary."""
    console.print("\n[bold]📋 Judge Model Summary[/bold]")
    console.print(f"Judge Model: {results.get('model', 'Unknown')}")
    console.print(f"Total tests validated: {results.get('total_tests', 0)}")
    
    summary = results.get('summary', {})
    categories = summary.get('categories', {})
    
    if categories:
        console.print("\n[bold]Test Quality Breakdown:[/bold]")
        for category, count in categories.items():
            if count > 0:
                icon = "✅" if category == "good" else "⚠️"
                console.print(f"  {icon} {category}: {count}")
    
    problematic = summary.get('problematic_tests', [])
    if problematic:
        console.print(f"\n[yellow]⚠️  Found {len(problematic)} problematic tests[/yellow]")
    else:
        console.print("\n[green]✅ All tests have good quality[/green]")


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