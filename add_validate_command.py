#!/usr/bin/env python3
"""
Script to add the validate command to the CLI
"""

import re

# Read the current main.py
with open("src/claude_test_reporter/cli/main.py", "r") as f:
    content = f.read()

# Add import if not already there
if "from .validate import validate" not in content:
    # Find the last import line
    import_pattern = r"(from \.slash_mcp_mixin import add_slash_mcp_commands)"
    content = re.sub(import_pattern, r"\1\nfrom .validate import validate", content)

# Add the command registration after the app is created
if "app.command()(validate)" not in content:
    # Find where slash commands are added
    add_pattern = r"(add_slash_mcp_commands\(app\))"
    content = re.sub(add_pattern, r"\1\n\n# Add validate command\napp.command()(validate)", content)

# Write back
with open("src/claude_test_reporter/cli/main.py", "w") as f:
    f.write(content)

print("✅ Added validate command to CLI")
