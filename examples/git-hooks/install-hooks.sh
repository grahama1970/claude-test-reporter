#!/bin/bash
# Install git hooks for automated code review

HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing git hooks for automated code review..."

# Pre-commit hook
cp "$SCRIPT_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ Installed pre-commit hook"

# Pre-push hook
cp "$SCRIPT_DIR/pre-push" "$HOOKS_DIR/pre-push"
chmod +x "$HOOKS_DIR/pre-push"
echo "✅ Installed pre-push hook"

echo ""
echo "Git hooks installed! They will:"
echo "  - Run quick review on every commit (pre-commit)"
echo "  - Run comprehensive review before push (pre-push)"
echo ""
echo "To skip hooks, use: git commit --no-verify"
