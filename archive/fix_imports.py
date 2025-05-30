#!/usr/bin/env python3
"""Fix imports after restructuring claude-test-reporter project."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports that need to add .core
    replacements = [
        # Update imports to use core submodule
        (r'from claude_test_reporter\.generators', r'from claude_test_reporter.core.generators'),
        (r'from claude_test_reporter\.tracking', r'from claude_test_reporter.core.tracking'),
        (r'from claude_test_reporter\.adapters', r'from claude_test_reporter.core.adapters'),
        (r'from claude_test_reporter\.runners', r'from claude_test_reporter.core.runners'),
        (r'from claude_test_reporter\.report_config', r'from claude_test_reporter.core.report_config'),
        (r'from claude_test_reporter\.test_reporter', r'from claude_test_reporter.core.test_reporter'),
        
        # Import statements
        (r'import claude_test_reporter\.generators', r'import claude_test_reporter.core.generators'),
        (r'import claude_test_reporter\.tracking', r'import claude_test_reporter.core.tracking'),
        (r'import claude_test_reporter\.adapters', r'import claude_test_reporter.core.adapters'),
        (r'import claude_test_reporter\.runners', r'import claude_test_reporter.core.runners'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all imports in the claude-test-reporter project."""
    fixed_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk('src/claude_test_reporter'):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_files.append(filepath)
                    print(f"Fixed: {filepath}")
    
    print(f"\nTotal files fixed: {len(fixed_files)}")

if __name__ == "__main__":
    main()
