"""
Git Change Reviewer - Collects git changes and formats them for review
Module: git_reviewer.py
Description: Implementation of git reviewer functionality

This module handles all git operations and change collection.
The actual LLM calls are delegated to claude_max_proxy.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class GitChanges:
    """Container for git repository changes."""
    repo_name: str
    repo_path: str
    branch: str
    last_commit: str
    staged_changes: str
    unstaged_changes: str
    untracked_files: List[str]
    untracked_contents: Dict[str, str]
    deleted_files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class GitChangeCollector:
    """Collects and formats git changes for review."""

    DEFAULT_REVIEW_PROMPT = """Please review the following code changes and provide:
1. **Security Analysis**: Identify any security vulnerabilities or concerns
2. **Performance Review**: Highlight performance issues and optimization opportunities
3. **Code Quality**: Assess adherence to best practices and clean code principles
4. **Bug Detection**: Identify potential bugs, edge cases, or logic errors
5. **Architecture Review**: Comment on design patterns and architectural decisions
6. **Testing**: Suggest missing tests or test improvements
7. **Documentation**: Note any missing or inadequate documentation
8. **Dependencies**: Review any new dependencies or version changes
9. **Breaking Changes**: Identify any breaking changes or compatibility issues
10. **Overall Assessment**: Provide a summary and actionable recommendations

Focus on the most important issues first. Be constructive and specific in your feedback."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def collect_changes(self) -> GitChanges:
        """Collect all git changes in the repository."""

        # Save current directory
        original_cwd = Path.cwd()

        try:
            # Change to repo directory
            import os
            os.chdir(self.repo_path)

            # Get repository info
            repo_root = self._run_git_command(["git", "rev-parse", "--show-toplevel"])
            repo_name = Path(repo_root.strip()).name

            branch = self._run_git_command(["git", "branch", "--show-current"]).strip()
            last_commit = self._run_git_command(["git", "log", "-1", "--oneline"]).strip()

            # Get staged changes
            staged_changes = self._run_git_command(["git", "diff", "--cached"])
            if not staged_changes:
                staged_changes = "No staged changes"

            # Get unstaged changes
            unstaged_changes = self._run_git_command(["git", "diff"])
            if not unstaged_changes:
                unstaged_changes = "No unstaged changes"

            # Get untracked files
            untracked_output = self._run_git_command(["git", "ls-files", "--others", "--exclude-standard"])
            untracked_files = [f for f in untracked_output.strip().split('\n') if f]

            # Get content of untracked files
            untracked_contents = {}
            for file in untracked_files:
                content = self._read_file_safely(file)
                if content:
                    untracked_contents[file] = content

            # Get deleted files
            deleted_output = self._run_git_command(["git", "diff", "--name-only", "--diff-filter=D"])
            deleted_files = [f for f in deleted_output.strip().split('\n') if f]

            return GitChanges(
                repo_name=repo_name,
                repo_path=str(self.repo_path),
                branch=branch,
                last_commit=last_commit,
                staged_changes=staged_changes,
                unstaged_changes=unstaged_changes,
                untracked_files=untracked_files,
                untracked_contents=untracked_contents,
                deleted_files=deleted_files
            )

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    def format_for_review(self, changes: GitChanges, custom_prompt: Optional[str] = None) -> str:
        """Format git changes into a review request."""

        sections = [
            f"=== GIT REPOSITORY STATUS ===",
            f"Repository: {changes.repo_name}",
            f"Branch: {changes.branch}",
            f"Last commit: {changes.last_commit}",
            "",
            "=== CODE REVIEW REQUEST ===",
            custom_prompt or self.DEFAULT_REVIEW_PROMPT,
            "",
            "=== STAGED CHANGES ===",
            changes.staged_changes,
            "",
            "=== UNSTAGED CHANGES ===",
            changes.unstaged_changes,
            ""
        ]

        if changes.untracked_files:
            sections.extend([
                "=== UNTRACKED FILES ===",
                "\n".join(changes.untracked_files),
                "",
                "=== CONTENT OF UNTRACKED FILES ==="
            ])

            for file, content in changes.untracked_contents.items():
                sections.extend([
                    f"--- File: {file} ---",
                    content,
                    ""
                ])
        else:
            sections.extend([
                "=== UNTRACKED FILES ===",
                "No untracked files",
                ""
            ])

        if changes.deleted_files:
            sections.extend([
                "=== DELETED FILES ===",
                "\n".join(changes.deleted_files)
            ])
        else:
            sections.extend([
                "=== DELETED FILES ===",
                "No deleted files"
            ])

        return "\n".join(sections)

    def get_review_stats(self, changes: GitChanges) -> Dict[str, Any]:
        """Get statistics about the changes."""

        # Count lines changed
        staged_lines = self._count_diff_lines(changes.staged_changes)
        unstaged_lines = self._count_diff_lines(changes.unstaged_changes)

        # Count files
        staged_files = self._count_diff_files(changes.staged_changes)
        unstaged_files = self._count_diff_files(changes.unstaged_changes)

        return {
            "has_changes": any([
                changes.staged_changes != "No staged changes",
                changes.unstaged_changes != "No unstaged changes",
                changes.untracked_files,
                changes.deleted_files
            ]),
            "staged": {
                "files": staged_files,
                "additions": staged_lines["additions"],
                "deletions": staged_lines["deletions"]
            },
            "unstaged": {
                "files": unstaged_files,
                "additions": unstaged_lines["additions"],
                "deletions": unstaged_lines["deletions"]
            },
            "untracked_files": len(changes.untracked_files),
            "deleted_files": len(changes.deleted_files),
            "total_files": staged_files + unstaged_files + len(changes.untracked_files),
            "total_changes": (staged_lines["additions"] + staged_lines["deletions"] +
                            unstaged_lines["additions"] + unstaged_lines["deletions"])
        }

    def _run_git_command(self, command: List[str]) -> str:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def _read_file_safely(self, filepath: str, max_lines: int = 1000) -> Optional[str]:
        """Safely read a file, skipping binary files."""
        try:
            path = Path(filepath)

            # Skip if file is too large
            if path.stat().st_size > 1_000_000:  # 1MB
                return f"[File too large: {path.stat().st_size:,} bytes]"

            # Check if file is text
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Binary file
                    return None

            # Read text file
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:max_lines]
                if len(lines) == max_lines:
                    lines.append(f"\n[... truncated at {max_lines} lines ...]")
                return ''.join(lines)

        except Exception as e:
            return f"[Error reading file: {e}]"

    def _count_diff_lines(self, diff_text: str) -> Dict[str, int]:
        """Count additions and deletions in a diff."""
        if diff_text in ["No staged changes", "No unstaged changes"]:
            return {"additions": 0, "deletions": 0}

        additions = sum(1 for line in diff_text.split('\n') if line.startswith('+' ) and not line.startswith('+++' ))
        deletions = sum(1 for line in diff_text.split('\n') if line.startswith('-' ) and not line.startswith('---' ))

        return {"additions": additions, "deletions": deletions}

    def _count_diff_files(self, diff_text: str) -> int:
        """Count number of files in a diff."""
        if diff_text in ["No staged changes", "No unstaged changes"]:
            return 0

        return len([line for line in diff_text.split('\n') if line.startswith('diff --git' )])


class CodeReviewReport:
    """Formats and saves code review reports."""

    def __init__(self):
        self.timestamp = datetime.now()

    def create_report(
        self,
        changes: GitChanges,
        review_content: str,
        model: str,
        stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a structured review report."""

        return {
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "model": model,
                "repository": changes.repo_name,
                "branch": changes.branch,
                "last_commit": changes.last_commit
            },
            "statistics": stats or {},
            "review": review_content,
            "changes_summary": {
                "staged": changes.staged_changes != "No staged changes",
                "unstaged": changes.unstaged_changes != "No unstaged changes",
                "untracked": len(changes.untracked_files),
                "deleted": len(changes.deleted_files)
            }
        }

    def save_markdown(self, report: Dict[str, Any], filepath: Path):
        """Save report as markdown."""

        with open(filepath, 'w') as f:
            f.write(f"# Code Review Report\n\n")

            # Metadata
            meta = report["metadata"]
            f.write(f"**Model**: {meta['model']}\n")
            f.write(f"**Repository**: {meta['repository']} ({meta['branch']})  \n")
            f.write(f"**Last Commit**: {meta['last_commit']}\n")
            f.write(f"**Generated**: {meta['timestamp']}\n\n")

            # Statistics
            if report.get("statistics"):
                stats = report["statistics"]
                f.write("## Change Statistics\n\n")
                f.write(f"- Total Files: {stats.get('total_files', 0)}\n")
                f.write(f"- Total Changes: {stats.get('total_changes', 0)}\n")
                f.write(f"- Staged: {stats['staged']['files']} files "
                       f"(+{stats['staged']['additions']} -{stats['staged']['deletions']})  \n")
                f.write(f"- Unstaged: {stats['unstaged']['files']} files\n")
                f.write(f"- Untracked: {stats.get('untracked_files', 0)} files\n")
                f.write(f"- Deleted: {stats.get('deleted_files', 0)} files\n\n")

            # Review content
            f.write("## Review\n\n")
            f.write(report["review"])

    def save_json(self, report: Dict[str, Any], filepath: Path):
        """Save report as JSON."""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
