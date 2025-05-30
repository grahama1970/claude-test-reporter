# Git Dependencies Best Practices

## Why Git URLs are Better Than Local Paths

### ❌ Local File Path (Old Way)
```toml
dependencies = [
    "llm_call @ file:///home/graham/workspace/experiments/claude_max_proxy",
]
```

**Problems:**
- Only works on Graham's machine
- Hardcoded absolute path
- Breaks for other developers
- Can't use in CI/CD
- No version control

### ✅ Git URL (Better Way)
```toml
dependencies = [
    "llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master",
]
```

**Benefits:**
- Works on any machine
- Version controlled
- Can specify branches/tags
- Works in CI/CD pipelines
- Shareable with team

## Git URL Options

### 1. Latest from Main Branch
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@main"
```

### 2. Specific Branch
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@feature/new-models"
```

### 3. Specific Tag/Release
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@v1.2.3"
```

### 4. Specific Commit
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@abc123def"
```

### 5. With Subdirectory (if needed)
```toml
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master#subdirectory=src"
```

## Installation

### For Users
```bash
# Just install normally
pip install git+https://github.com/grahama1970/claude-test-reporter.git

# Or if cloned locally
cd claude-test-reporter
pip install .
```

### For Developers
```bash
# Clone both repos
git clone https://github.com/grahama1970/claude-test-reporter.git
git clone https://github.com/grahama1970/claude_max_proxy.git

# Install claude_max_proxy in editable mode
cd claude_max_proxy
pip install -e .

# Install claude-test-reporter (will use local editable claude_max_proxy)
cd ../claude-test-reporter
pip install -e .
```

## Private Repositories

If the repository is private, you have several options:

### 1. SSH URL (Recommended for Development)
```toml
"llm_call @ git+ssh://git@github.com/grahama1970/claude_max_proxy.git@master"
```

### 2. Personal Access Token
```toml
"llm_call @ git+https://{token}@github.com/grahama1970/claude_max_proxy.git@master"
```

### 3. Environment Variable
```bash
export GIT_TOKEN=your_token_here
```
```toml
"llm_call @ git+https://${GIT_TOKEN}@github.com/grahama1970/claude_max_proxy.git@master"
```

## CI/CD Configuration

### GitHub Actions
```yaml
- name: Install dependencies
  run: |
    # Public repos work directly
    pip install git+https://github.com/grahama1970/claude-test-reporter.git
    
    # For private repos, use token
    pip install git+https://${{ secrets.GITHUB_TOKEN }}@github.com/org/private-repo.git
```

### GitLab CI
```yaml
install:
  script:
    - pip install git+https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/org/repo.git
```

## Development Workflow

### Working on Both Projects
```bash
# 1. Make changes to claude_max_proxy
cd claude_max_proxy
# ... edit code ...
git commit -am "Add new feature"
git push

# 2. Update dependency in claude-test-reporter
cd ../claude-test-reporter
pip install --upgrade git+https://github.com/grahama1970/claude_max_proxy.git@master

# 3. Or for rapid development, use local editable installs
pip install -e ../claude_max_proxy
```

### Pinning Versions
```toml
# Good practice: pin to specific version
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@v1.0.0"

# Or to commit SHA for reproducibility
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@7d4a8b9c"
```

## Advantages Over PyPI

While publishing to PyPI is best for public packages, git dependencies are great for:
- Private packages
- Rapid development
- Pre-release versions
- Organization-specific tools
- Avoiding PyPI publication overhead

## Migration Path

```toml
# Development phase
"llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master"

# After stabilization, publish to PyPI
"llm_call>=1.0.0"
```

## Troubleshooting

### Authentication Issues
```bash
# Configure git credentials
git config --global credential.helper store

# Or use SSH
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### Caching Issues
```bash
# Force reinstall
pip install --force-reinstall git+https://github.com/grahama1970/claude_max_proxy.git@master

# Clear pip cache
pip cache purge
```

### Finding the Right Commit/Tag
```bash
# List tags
git ls-remote --tags https://github.com/grahama1970/claude_max_proxy.git

# List branches
git ls-remote --heads https://github.com/grahama1970/claude_max_proxy.git
```

This approach makes the package truly portable and shareable while maintaining flexibility for development!
