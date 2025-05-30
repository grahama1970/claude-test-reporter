#!/usr/bin/env python3
"""Update pyproject.toml to properly include claude_max_proxy as a dependency"""

import re

with open("pyproject.toml", "r") as f:
    content = f.read()

# Find the dependencies line and update it
content = re.sub(
    r^dependencies = [],
    dependencies = [