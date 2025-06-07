"""
Module: code_review.py

Code review command for the CLI.
"""
import sys
from pathlib import Path
from typing import Optional
Description: Functions for code review operations

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--repo", "-r", default=".", help="Repository path to review")
@click.option("--model", "-m", default="gemini-2.5-pro", help="LLM model to use")
@click.option("--custom-prompt", "-p", help="Custom prompt for the review")
@click.option("--temperature", "-t", default=0.3, type=float, help="LLM temperature")
@click.option("--output", "-o", help="Output file path")
@click.option("--compare", is_flag=True, help="Compare reviews from multiple models")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def code_review(repo: str, model: str, custom_prompt: Optional[str],
                temperature: float, output: Optional[str], compare: bool,
                verbose: bool) -> None:
    """Perform AI-powered code review on a repository."""
    try:
        from claude_test_reporter.core.code_reviewer import CodeReviewer
    except ImportError:
        console.print("[red]Error: code_reviewer module not available[/red]")
        sys.exit(1)

    reviewer = CodeReviewer(model=model)
    repo_path = Path(repo).resolve()

    if not repo_path.exists():
        console.print(f"[red]Repository not found: {repo_path}[/red]")
        sys.exit(1)

    console.print(f"[blue]Reviewing repository: {repo_path}[/blue]")
    console.print(f"[blue]Using model: {model}[/blue]")

    if compare:
        # Compare multiple models
        models = ["gemini-2.5-pro", "claude-3-5-sonnet-20241022"]
        result = reviewer.compare_reviews(
            repo_path=str(repo_path),
            models=models,
            custom_prompt=custom_prompt,
            temperature=temperature
        )

        if result["success"]:
            console.print("\n[green]✅ Comparison complete![/green]")
            console.print(f"[blue]📊 Comparison saved to: {result['comparison_path']}[/blue]")

            # Show summary
            if verbose:
                console.print("\n[bold]Review Summary:[/bold]")
                for model_name, review_result in result["reviews"].items():
                    status = "✅" if review_result["success"] else "❌"
                    console.print(f"  {status} {model_name}")
        else:
            console.print(f"[red]❌ {result['message']}[/red]")
            sys.exit(1)
    else:
        # Single model review
        result = reviewer.review_repository(
            repo_path=str(repo_path),
            custom_prompt=custom_prompt,
            temperature=temperature,
            output_path=output
        )

        if result["success"]:
            if output:
                console.print(f"\n[green]✅ Review complete![/green]")
                console.print(f"[blue]📊 Review saved to: {output}[/blue]")
            else:
                # Print to stdout if no output file specified
                console.print("\n" + "="*60 + "\n")
                console.print(result["report"]["review"])
                console.print("\n" + "="*60)
        else:
            console.print(f"[red]❌ {result['message']}[/red]")
            sys.exit(1)


if __name__ == "__main__":
    code_review()