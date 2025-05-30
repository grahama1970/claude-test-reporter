# Dependency Architecture: claude-test-reporter + claude_max_proxy

## Overview

`claude-test-reporter` uses `claude_max_proxy` (packaged as `llm_call`) as a dependency for LLM communication. This follows proper Python packaging practices.

## Dependency Setup

### In pyproject.toml

```toml
[project]
dependencies = [
    # LLM Communication via claude_max_proxy
    "llm_call @ file:///home/graham/workspace/experiments/claude_max_proxy",
    # CLI and formatting
    "typer>=0.12.0",
    "rich>=13.0.0",
    "click>=8.1.0",
]
```

### Installation

```bash
# Install claude-test-reporter with all dependencies
cd /home/graham/workspace/experiments/claude-test-reporter
pip install -e .

# This will automatically install claude_max_proxy as llm_call
```

## Import Structure

### Proper Import (New Way)

```python
# In code_reviewer.py
try:
    from llm_call.core.llm_client import LLMClient
    HAS_LLM_CALL = True
except ImportError:
    HAS_LLM_CALL = False

# Use it
if HAS_LLM_CALL:
    client = LLMClient()
    response = client.call(model="gemini/gemini-2.5-pro-preview-05-06", ...)
```

### Old Way (Removed)

```python
# DON'T DO THIS - Hacky path manipulation
sys.path.insert(0, "/home/graham/workspace/experiments/claude_max_proxy/src")
from llm_call.core.llm_client import LLMClient
```

## Package Names

- **Repository**: `claude_max_proxy`
- **Package Name**: `llm_call`
- **Import**: `from llm_call.core.llm_client import LLMClient`

## Architecture Diagram

```
┌─────────────────────────────┐
│  claude-test-reporter       │
│                             │
│  pyproject.toml:            │
│  dependencies = [           │
│    "llm_call @ file://..."  │ ──── Installs ────►
│  ]                          │
│                             │
│  Code:                      │
│  from llm_call.core...      │ ──── Imports ────►
└─────────────────────────────┘

┌─────────────────────────────┐
│  claude_max_proxy           │
│                             │
│  pyproject.toml:            │
│  name = "llm_call"          │
│                             │
│  src/llm_call/              │
│    ├── core/                │
│    │   └── llm_client.py    │
│    └── cli/                 │
│        └── main.py          │
└─────────────────────────────┘
```

## Benefits

1. **Proper Dependency Management**: pip handles installation and updates
2. **No Path Hacks**: Clean imports without sys.path manipulation
3. **Version Control**: Can specify versions when needed
4. **Development Mode**: Both projects can be installed with `-e` for development
5. **Clear Dependencies**: pyproject.toml shows all dependencies

## CLI Fallback

If direct import fails, the code falls back to CLI:

```python
# CLI fallback in code_reviewer.py
cmd = ["python", "-m", "llm_call.cli.main", "ask", "--model", model]
result = subprocess.run(cmd, input=prompt, ...)
```

## Comparison with claude-module-communicator

`claude-module-communicator` uses a similar approach with many dependencies:

```toml
dependencies = [
    "mcp>=1.2.0",
    "playwright>=1.40.0", 
    "stix2>=3.0.0",
    # ... many more
]
```

Our approach is simpler because:
- Only one local dependency (llm_call)
- Minimal external dependencies (typer, rich, click)
- Clear separation of concerns

## Development Workflow

```bash
# 1. Make changes to claude_max_proxy
cd /home/graham/workspace/experiments/claude_max_proxy
# ... edit code ...

# 2. Changes immediately available in claude-test-reporter
# (because both are installed with -e flag)

# 3. Test the integration
cd /home/graham/workspace/experiments/claude-test-reporter
python test_git_review_integration.py
```

## Troubleshooting

### Import Error
```bash
# Reinstall both packages
pip install -e /home/graham/workspace/experiments/claude_max_proxy
pip install -e /home/graham/workspace/experiments/claude-test-reporter
```

### CLI Not Found
```bash
# Ensure claude_max_proxy CLI is available
python -m llm_call.cli.main --help
```

This architecture provides clean separation of concerns with proper Python packaging practices.
