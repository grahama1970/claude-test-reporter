# Example: How All Projects Should Declare Dependencies

## claude-test-reporter Example

```toml
[project]
name = "claude-test-reporter"
dependencies = [
    # Git dependencies for internal projects
    "llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master",
    
    # PyPI dependencies for public packages
    "typer>=0.12.0",
    "rich>=13.0.0",
    "click>=8.1.0",
]
```

## If claude-module-communicator Used Git URLs

Instead of everyone needing the exact same local paths, it could use:

```toml
[project]
name = "claude-module-communicator"
dependencies = [
    # Internal projects via git
    "llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master",
    "arangodb_tools @ git+https://github.com/grahama1970/arangodb.git@main",
    "marker @ git+https://github.com/grahama1970/marker.git@main",
    "sparta @ git+https://github.com/grahama1970/sparta.git@main",
    
    # External packages from PyPI
    "mcp>=1.2.0",
    "uvicorn>=0.30.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]
```

## Example: Creating a New Project That Uses These Tools

```toml
[project]
name = "my-space-cybersecurity-analyzer"
dependencies = [
    # Graham's tools via git
    "claude-test-reporter @ git+https://github.com/grahama1970/claude-test-reporter.git@master",
    "llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master",
    "marker @ git+https://github.com/grahama1970/marker.git@main",
    
    # Public packages
    "pandas>=2.0.0",
    "requests>=2.31.0",
]
```

## Benefits of This Approach

### 1. **Portable**
Anyone can install without needing Graham's exact directory structure:
```bash
pip install git+https://github.com/grahama1970/my-project.git
```

### 2. **Version Control**
Can pin to specific versions:
```toml
# Stable version
"marker @ git+https://github.com/grahama1970/marker.git@v2.1.0"

# Latest development
"marker @ git+https://github.com/grahama1970/marker.git@develop"

# Specific commit for reproducibility
"marker @ git+https://github.com/grahama1970/marker.git@abc123def"
```

### 3. **CI/CD Ready**
Works in GitHub Actions, GitLab CI, etc:
```yaml
- name: Install dependencies
  run: pip install -e .
```

### 4. **Collaboration Friendly**
Team members can:
```bash
# Clone and install
git clone https://github.com/grahama1970/claude-test-reporter.git
cd claude-test-reporter
pip install -e .  # Gets all dependencies automatically
```

## Development Setup for Multiple Projects

```bash
# Clone all repositories
mkdir ~/graham-tools && cd ~/graham-tools
git clone https://github.com/grahama1970/claude_max_proxy.git
git clone https://github.com/grahama1970/claude-test-reporter.git
git clone https://github.com/grahama1970/marker.git
git clone https://github.com/grahama1970/arangodb.git

# Install in development mode (order matters for dependencies)
cd claude_max_proxy && pip install -e . && cd ..
cd arangodb && pip install -e . && cd ..
cd marker && pip install -e . && cd ..
cd claude-test-reporter && pip install -e . && cd ..

# Now all projects use local editable versions for development
# But can still be installed from git by others
```

## Publishing Progression

```toml
# Stage 1: Local development
"llm_call @ file:///home/graham/workspace/experiments/claude_max_proxy"

# Stage 2: Git URL (current)
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master"

# Stage 3: PyPI (future)
"llm_call>=1.0.0"
```

This makes all projects easily installable by anyone, anywhere!
