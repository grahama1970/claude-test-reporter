# Installation Guide: claude-test-reporter

## For Users (Simple Installation)

Since we now use git URLs instead of local paths, anyone can install this tool:

```bash
# Install directly from GitHub
pip install git+https://github.com/grahama1970/claude-test-reporter.git

# Or install a specific version/branch
pip install git+https://github.com/grahama1970/claude-test-reporter.git@v1.0.0
pip install git+https://github.com/grahama1970/claude-test-reporter.git@develop
```

This will automatically install all dependencies including:
- `llm_call` (from claude_max_proxy)
- `typer`, `rich`, `click` (from PyPI)

## For Developers

If you want to modify the code:

```bash
# 1. Clone the repository
git clone https://github.com/grahama1970/claude-test-reporter.git
cd claude-test-reporter

# 2. Install in editable mode
pip install -e .

# 3. (Optional) Clone and install claude_max_proxy locally for development
git clone https://github.com/grahama1970/claude_max_proxy.git
cd claude_max_proxy
pip install -e .
```

## Usage After Installation

Once installed, you can use it from anywhere:

```bash
# Test validation with Gemini
claude-test-reporter validate test_results.json

# Code review
claude-test-reporter code-review

# Compare models
claude-test-reporter code-review --compare
```

## Why This is Better

### Before (Local Paths) ❌
```toml
"llm_call @ file:///home/graham/workspace/experiments/claude_max_proxy"
```
- Only worked on Graham's machine
- Required exact directory structure
- Failed for other users

### Now (Git URLs) ✅
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master"
```
- Works for anyone
- Automatically fetches from GitHub
- Version controlled
- CI/CD compatible

## Troubleshooting

### If you get "repository not found"
Make sure the repositories are public or you have access:
```bash
# Test access
git ls-remote https://github.com/grahama1970/claude_max_proxy.git
```

### For private repositories
Use SSH URL instead:
```bash
pip install git+ssh://git@github.com/grahama1970/claude-test-reporter.git
```

### Force update to latest
```bash
pip install --upgrade --force-reinstall git+https://github.com/grahama1970/claude-test-reporter.git@master
```

## For CI/CD

Add to your GitHub Actions, GitLab CI, etc:

```yaml
- name: Install claude-test-reporter
  run: |
    pip install git+https://github.com/grahama1970/claude-test-reporter.git@master
    
- name: Run test validation
  run: |
    claude-test-reporter validate test_results.json --fail-on-category lazy
```

Now anyone can use your tools without needing your exact setup! 🚀
