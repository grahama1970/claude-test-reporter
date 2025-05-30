#!/usr/bin/env python3
"""Update pyproject.toml to use git URL instead of local path"""

content = open("pyproject.toml").read()

# Replace local file path with git URL
content = content.replace(
    llm_call @ file:///home/graham/workspace/experiments/claude_max_proxy,,
    llm_call @ git+https://github.com/grahama1970/claude_max_proxy.git@master,
)

with open("pyproject.toml", "w") as f:
    f.write(content)

print("✅ Updated to use git URL for claude_max_proxy dependency")
