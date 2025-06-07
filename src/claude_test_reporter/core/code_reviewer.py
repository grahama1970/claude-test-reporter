"""
Module: code_reviewer.py
Code Reviewer - Orchestrates git reviews using claude_max_proxy for LLM calls
Description: Implementation of code reviewer functionality

This module acts as the integration layer between git change collection
and LLM-based code reviews.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .git_reviewer import GitChangeCollector, GitChanges, CodeReviewReport

# Try to import llm_call directly (if installed via pyproject.toml)
try:
    from llm_call.core.llm_client import LLMClient
    HAS_LLM_CALL = True
except ImportError:
    HAS_LLM_CALL = False


class CodeReviewer:
    """Orchestrates code reviews using git changes and LLM analysis."""

    def __init__(self, model: str = "gemini/gemini-2.5-pro-preview-05-06"):
        self.model = model
        self.collector = GitChangeCollector()
        self.report_generator = CodeReviewReport()

        # Check if we can use direct import
        if HAS_LLM_CALL:
            print("✅ Using direct llm_call import")
            self.llm_client = LLMClient()
        else:
            print("⚠️  llm_call not found, will use CLI fallback")
            self.llm_client = None

    def review_repository(
        self,
        repo_path: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        temperature: float = 0.3,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform a complete code review of a repository."""

        print("📋 Collecting git changes...")

        # Collect changes
        if repo_path:
            self.collector.repo_path = Path(repo_path)
        changes = self.collector.collect_changes()

        # Get statistics
        stats = self.collector.get_review_stats(changes)

        if not stats["has_changes"]:
            print("No changes to review.")
            return {
                "success": False,
                "message": "No changes found in repository"
            }

        print(f"🔍 Repository: {changes.repo_name} ({changes.branch})")
        print(f"📊 Changes: {stats['total_files']} files, {stats['total_changes']} lines")

        # Format for review
        review_request = self.collector.format_for_review(changes, custom_prompt)

        # Get review from LLM
        print(f"🤖 Requesting review from {self.model}...")
        review_content = self._get_llm_review(review_request, temperature)

        # Create report
        report = self.report_generator.create_report(
            changes=changes,
            review_content=review_content,
            model=self.model,
            stats=stats
        )

        # Save if requested
        if output_path:
            self._save_report(report, output_path)

        return {
            "success": True,
            "report": report,
            "output_path": output_path
        }

    def compare_reviews(
        self,
        models: List[str],
        repo_path: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        temperature: float = 0.3,
        output_dir: str = "./code-reviews"
    ) -> Dict[str, Any]:
        """Get reviews from multiple models for comparison."""

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Collect changes once
        print("📋 Collecting git changes...")
        if repo_path:
            self.collector.repo_path = Path(repo_path)
        changes = self.collector.collect_changes()
        stats = self.collector.get_review_stats(changes)

        if not stats["has_changes"]:
            return {
                "success": False,
                "message": "No changes found in repository"
            }

        # Format for review
        review_request = self.collector.format_for_review(changes, custom_prompt)

        # Get reviews from each model
        reviews = {}
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        for model in models:
            print(f"\n🤖 Getting review from {model}...")

            try:
                review_content = self._get_llm_review(
                    review_request,
                    temperature,
                    model=model
                )

                # Create report
                report = self.report_generator.create_report(
                    changes=changes,
                    review_content=review_content,
                    model=model,
                    stats=stats
                )

                reviews[model] = {
                    "success": True,
                    "report": report,
                    "error": None
                }

                # Save individual report
                model_safe = model.replace("/", "-").replace(":", "-")
                output_path = f"{output_dir}/review-{model_safe}-{timestamp}.md"
                self._save_report(report, output_path)

                print(f"✅ Review saved to: {output_path}")

            except Exception as e:
                print(f"❌ Error with {model}: {e}")
                reviews[model] = {
                    "success": False,
                    "report": None,
                    "error": str(e)
                }

        # Create comparison summary
        comparison_path = f"{output_dir}/review-comparison-{timestamp}.md"
        self._create_comparison_summary(reviews, changes, comparison_path)

        return {
            "success": True,
            "reviews": reviews,
            "comparison_path": comparison_path,
            "timestamp": timestamp
        }

    def _get_llm_review(self, prompt: str, temperature: float, model: Optional[str] = None) -> str:
        """Get review from LLM via llm_call."""

        model = model or self.model

        if self.llm_client:
            # Use direct import
            try:
                response = self.llm_client.call(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature
                )
                return response["content"]
            except Exception as e:
                print(f"Direct call failed: {e}, falling back to CLI")

        # CLI fallback
        return self._get_llm_review_cli(prompt, temperature, model)

    def _get_llm_review_cli(self, prompt: str, temperature: float, model: str) -> str:
        """Get review via CLI (fallback method)."""

        cmd = [
            "python", "-m", "llm_call.cli.main",
            "ask",
            "--model", model,
            "--temperature", str(temperature)
        ]

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                raise Exception(f"LLM call failed: {result.stderr}")

            return result.stdout

        except FileNotFoundError:
            raise Exception(
                "llm_call CLI not found. Please ensure claude_max_proxy is installed: "
                "pip install -e /home/graham/workspace/experiments/claude_max_proxy"
            )

    def _save_report(self, report: Dict[str, Any], output_path: str):
        """Save report to file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix == ".json":
            self.report_generator.save_json(report, path)
        else:
            self.report_generator.save_markdown(report, path)

        print(f"💾 Report saved to: {output_path}")

    def _create_comparison_summary(self, reviews: Dict[str, Dict], changes: GitChanges, output_path: str):
        """Create a comparison summary of multiple reviews."""

        with open(output_path, 'w') as f:
            f.write("# Code Review Comparison\n\n")
            f.write(f"**Repository**: {changes.repo_name} ({changes.branch})  \n")
            f.write(f"**Generated**: {datetime.now()}\n\n")

            # Summary table
            f.write("## Summary\n\n")
            f.write("| Model | Status | Summary |\n")
            f.write("|-------|--------|----------|\n")

            for model, result in reviews.items():
                status = "✅ Success" if result["success"] else "❌ Failed"

                if result["success"]:
                    # Extract first paragraph as summary
                    review_text = result["report"]["review"]
                    lines = review_text.split('\n')[:3]
                    summary = " ".join(lines).replace("|", "\\|")[:100] + "..."
                else:
                    summary = result["error"]

                f.write(f"| {model} | {status} | {summary} |\n")

            f.write("\n---\n\n")

            # Full reviews
            for model, result in reviews.items():
                f.write(f"## Review by {model}\n\n")

                if result["success"]:
                    f.write(result["report"]["review"])
                else:
                    f.write(f"**Error**: {result['error']}\n")

                f.write("\n\n---\n\n")

        print(f"📊 Comparison saved to: {output_path}")
