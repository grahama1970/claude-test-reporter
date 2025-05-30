# Git Code Review with Claude Test Reporter

## Overview

Claude Test Reporter now includes comprehensive git code review functionality that leverages `claude_max_proxy` for LLM communication. This follows proper separation of concerns:

- **claude-test-reporter**: Handles git operations, change collection, and report generation
- **claude_max_proxy**: Provides LLM communication services

## Architecture

```
┌─────────────────────────────┐
│   Git Repository            │
│   (Your Code)               │
└──────────┬──────────────────┘
           │
           │ git diff, git status
           ▼
┌─────────────────────────────┐
│   claude-test-reporter      │
│                             │
│  ┌─────────────────────┐    │
│  │ GitChangeCollector  │    │
│  │ - Collect changes   │    │
│  │ - Read files        │    │
│  │ - Format for review │    │
│  └──────────┬──────────┘    │
│             │               │
│  ┌──────────▼──────────┐    │
│  │ CodeReviewer        │    │     ┌──────────────────┐
│  │ - Orchestrate review├────┼────►│ claude_max_proxy │
│  │ - Handle models     │    │     │                  │
│  │ - Generate reports  │    │     │  LLM Services:   │
│  └──────────┬──────────┘    │     │  - Gemini        │
│             │               │     │  - Claude        │
│  ┌──────────▼──────────┐    │     │  - GPT-4         │
│  │ CodeReviewReport    │    │     └──────────────────┘
│  │ - Format output     │    │
│  │ - Save reports      │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

## Installation

Both projects should be installed:

```bash
# Install claude-test-reporter
cd /home/graham/workspace/experiments/claude-test-reporter
pip install -e .

# Install claude_max_proxy
cd /home/graham/workspace/experiments/claude_max_proxy
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Basic review
claude-test-reporter code-review

# Specify model
claude-test-reporter code-review -m claude-3-opus-20240229

# Compare multiple models
claude-test-reporter code-review --compare

# Custom output
claude-test-reporter code-review -o my-review.md

# Custom prompt
claude-test-reporter code-review -p security-review-prompt.txt

# Review specific repository
claude-test-reporter code-review --repo /path/to/repo
```

### Shell Script

A convenient shell script is provided:

```bash
# Use the git-review script
./scripts/git-review

# With options
./scripts/git-review -m gemini/gemini-2.5-pro-preview-05-06 -o review.md
```

### Python API

```python
from claude_test_reporter.core.code_reviewer import CodeReviewer

# Initialize reviewer
reviewer = CodeReviewer(model="gemini/gemini-2.5-pro-preview-05-06")

# Review current repository
result = reviewer.review_repository(
    temperature=0.3,
    output_path="review.md"
)

# Compare multiple models
comparison = reviewer.compare_reviews(
    models=["gemini/gemini-2.5-pro-preview-05-06", "claude-3-opus-20240229"],
    output_dir="./code-reviews"
)
```

## Features

### Complete Git State Capture

The tool captures:
- **Staged Changes**: Files added with `git add`
- **Unstaged Changes**: Modified files not yet staged
- **Untracked Files**: New files with full content (text files only)
- **Deleted Files**: Files removed from the repository

### Smart File Handling

- Binary files are automatically detected and skipped
- Large files are truncated with a note
- File content is safely read with encoding detection

### Review Statistics

Each review includes:
- Total files changed
- Lines added/deleted
- File counts by category (staged, unstaged, untracked)

### Multiple Output Formats

- **Markdown**: Human-readable reports with formatting
- **JSON**: Structured data for programmatic use

### Model Comparison

Compare reviews from different models side-by-side:

```bash
claude-test-reporter code-review --compare --models gemini/gemini-2.5-pro-preview-05-06 claude-3-opus-20240229 gpt-4
```

## Custom Review Prompts

Create focused review prompts for different needs:

### Security-Focused Review
```text
=== SECURITY-FOCUSED CODE REVIEW ===

Please perform a comprehensive security audit focusing on:
1. Authentication & Authorization vulnerabilities
2. Input validation and sanitization issues
3. Sensitive data handling
4. SQL injection, XSS, CSRF risks
5. Dependency vulnerabilities

Rate findings by severity (Critical/High/Medium/Low).
```

### Performance Review
```text
=== PERFORMANCE-FOCUSED CODE REVIEW ===

Analyze code for performance issues:
1. Algorithm complexity (Big O)
2. Database query optimization
3. Memory leaks or excessive allocation
4. Caching opportunities
5. Async/concurrent operations
```

## Git Integration

### Git Alias

Add to `~/.gitconfig`:

```ini
[alias]
    review = "!claude-test-reporter code-review"
    review-compare = "!claude-test-reporter code-review --compare"
    review-security = "!claude-test-reporter code-review -p ~/.git-review-prompts/security.txt"
```

Usage:
```bash
git review                    # Quick review
git review-compare            # Compare models
git review-security           # Security-focused review
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Code review before commit

echo "🔍 Running code review..."

# Only review if we have substantial changes
CHANGES=$(git diff --cached --numstat | wc -l)
if [ "$CHANGES" -gt 5 ]; then
    claude-test-reporter code-review -m gemini/gemini-2.5-pro-preview-05-06 -o .last-review.md
    
    # Check for critical issues
    if grep -i "critical\|security" .last-review.md > /dev/null; then
        echo "⚠️  Critical issues found! Review saved to .last-review.md"
        echo "Continue anyway? (y/n)"
        read response
        if [ "$response" != "y" ]; then
            exit 1
        fi
    fi
fi
```

## CI/CD Integration

### GitHub Actions

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install git+https://github.com/yourusername/claude-test-reporter.git
          pip install git+https://github.com/yourusername/claude_max_proxy.git
          
      - name: Run Code Review
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          claude-test-reporter code-review \
            -m gemini/gemini-2.5-pro-preview-05-06 \
            -o review.md
            
      - name: Post Review Comment
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🤖 AI Code Review\n\n${review}`
            });
```

## Environment Variables

```bash
# Default model for reviews
export GIT_REVIEW_MODEL="gemini/gemini-2.5-pro-preview-05-06"

# Output directory
export GIT_REVIEW_OUTPUT_DIR="./code-reviews"

# API keys (used by claude_max_proxy)
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

## Comparison with Direct LLM Tools

Your original command:
```bash
(git diff --cached && git diff && ...) | llm -m gemini-2.5-pro > review.md
```

Our solution provides:
- ✅ Proper separation of concerns
- ✅ Structured change collection
- ✅ Smart file handling (binary detection, size limits)
- ✅ Multiple model support
- ✅ Comparison mode
- ✅ Statistics and reporting
- ✅ Error handling and retries
- ✅ Integration with test reporting

## Troubleshooting

### Issue: claude_max_proxy not found
```bash
# Ensure claude_max_proxy is in Python path
export PYTHONPATH="/home/graham/workspace/experiments/claude_max_proxy/src:$PYTHONPATH"
```

### Issue: No changes detected
```bash
# Make sure you have uncommitted changes
git status

# Or review a different repository
claude-test-reporter code-review --repo /path/to/repo
```

### Issue: API key errors
```bash
# Set appropriate API keys
export GEMINI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

## Future Enhancements

- [ ] Incremental reviews (only changed lines)
- [ ] Review templates library
- [ ] Integration with test validation
- [ ] Historical review tracking
- [ ] Team review aggregation
- [ ] Auto-fix suggestions

This architecture provides a clean separation where `claude-test-reporter` handles all git and reporting logic while `claude_max_proxy` focuses solely on LLM communication.
