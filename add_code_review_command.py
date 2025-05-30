#!/usr/bin/env python3
"""
Script to add the code-review command to the CLI
"""

import re

# Read the current main.py
with open("src/claude_test_reporter/cli/main.py", "r") as f:
    content = f.read()

# Add import if not already there
if "from .code_review import code_review" not in content:
    # Find the validate import line
    import_pattern = r"(from \.validate import validate)"
    content = re.sub(import_pattern, r"\1\nfrom .code_review import code_review", content)

# Add the command registration if not already there
if "app.command()(code_review)" not in content:
    # Find where validate command is added
    add_pattern = r"(app\.command\(\)\(validate\))"
    content = re.sub(add_pattern, r"\1\napp.command()(code_review)", content)

# Write back
with open("src/claude_test_reporter/cli/main.py", "w") as f:
    f.write(content)

print("✅ Added code-review command to CLI")
