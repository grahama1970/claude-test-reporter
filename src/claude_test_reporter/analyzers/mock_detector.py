
"""
Module: mock_detector.py
Description: Detects inappropriate mock usage in test files, especially in integration tests
"""

External Dependencies:
- ast: https://docs.python.org/3/library/ast.html
- re: https://docs.python.org/3/library/re.html

Sample Input:
>>> test_content = '''
... from unittest.mock import patch
... def test_integration():
...     with patch('module.function'):
...         pass
... '''

Expected Output:
>>> detector = MockDetector()
>>> result = detector.analyze_test_content(test_content, 'test_integration.py')
>>> print(result)
{'has_mocks': True, 'mock_score': 0.8, 'violations': ['Mock usage in integration test']}

Example Usage:
>>> detector = MockDetector()
>>> issues = detector.scan_test_file('/path/to/test_integration.py')
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class MockDetector:
    """Detects mock usage patterns in test files to identify fake tests."""

    def __init__(self):
        self.mock_patterns = [
            r'from\s+unittest\.mock\s+import',
            r'from\s+mock\s+import',
            r'@patch\s*\(',
            r'@mock\.',
            r'MagicMock\s*\(',
            r'Mock\s*\(',
            r'create_autospec\s*\(',
            r'patch\.object\s*\(',
        ]

        self.integration_indicators = [
            'integration',
            'e2e',
            'end_to_end',
            'system',
            'functional'
        ]

    def scan_test_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a test file for mock usage patterns."""
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.analyze_test_content(content, file_path.name)
        except Exception as e:
            return {"error": f"Failed to analyze {file_path}: {str(e)}"}

    def analyze_test_content(self, content: str, filename: str) -> Dict[str, Any]:
        """Analyze test content for mock usage."""
        result = {
            "filename": filename,
            "has_mocks": False,
            "mock_count": 0,
            "mock_types": [],
            "is_integration_test": self._is_integration_test(filename, content),
            "violations": [],
            "mock_score": 0.0,  # 0 = no mocks, 1 = heavy mocking
            "suspicious_patterns": []
        }

        # Check for mock imports and usage
        mock_matches = []
        for pattern in self.mock_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                mock_matches.extend(matches)
                result["has_mocks"] = True

        result["mock_count"] = len(mock_matches)

        # Analyze AST for more detailed mock usage
        try:
            tree = ast.parse(content)
            mock_visitor = MockVisitor()
            mock_visitor.visit(tree)

            result["mock_types"] = mock_visitor.mock_types
            result["patch_targets"] = mock_visitor.patch_targets
            result["mock_in_test_count"] = mock_visitor.mock_in_test_count

        except SyntaxError:
            result["ast_error"] = "Failed to parse Python AST"

        # Calculate mock score
        if result["has_mocks"]:
            lines = content.count('\n')
            mock_density = min(result["mock_count"] / max(lines / 10, 1), 1.0)
            result["mock_score"] = mock_density

        # Check for violations
        if result["is_integration_test"] and result["has_mocks"]:
            result["violations"].append("Mock usage detected in integration test")
            result["suspicious_patterns"].append("Integration tests should use real implementations")

        # Check for specific suspicious patterns
        if "@patch" in content and "return_value = True" in content:
            result["suspicious_patterns"].append("Patch with hardcoded return value")

        if "mock.ANY" in content or "ANY" in content:
            result["suspicious_patterns"].append("Using mock.ANY to bypass assertions")

        if re.search(r'assert.*[Cc]alled', content) and not re.search(r'assert.*[Cc]alled.*with', content):
            result["suspicious_patterns"].append("Asserting called without checking arguments")

        return result

    def _is_integration_test(self, filename: str, content: str) -> bool:
        """Determine if this is an integration test."""
        filename_lower = filename.lower()
        content_lower = content.lower()

        for indicator in self.integration_indicators:
            if indicator in filename_lower or indicator in content_lower:
                return True
        return False

    def scan_project(self, project_path: str) -> Dict[str, Any]:
        """Scan all test files in a project."""
        project_path = Path(project_path)
        test_dirs = [project_path / "tests", project_path / "test"]

        results = {
            "project": str(project_path),
            "total_test_files": 0,
            "files_with_mocks": 0,
            "integration_tests_with_mocks": 0,
            "total_mock_count": 0,
            "average_mock_score": 0.0,
            "violations": [],
            "file_results": {}
        }

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            for test_file in test_dir.rglob("test_*.py"):
                results["total_test_files"] += 1

                file_result = self.scan_test_file(str(test_file))
                results["file_results"][str(test_file)] = file_result

                if file_result.get("has_mocks"):
                    results["files_with_mocks"] += 1
                    results["total_mock_count"] += file_result.get("mock_count", 0)

                    if file_result.get("is_integration_test"):
                        results["integration_tests_with_mocks"] += 1

                results["violations"].extend(file_result.get("violations", []))

        # Calculate average mock score
        if results["total_test_files"] > 0:
            total_score = sum(
                r.get("mock_score", 0)
                for r in results["file_results"].values()
            )
            results["average_mock_score"] = total_score / results["total_test_files"]

        return results


class MockVisitor(ast.NodeVisitor):
    """AST visitor to find mock usage patterns."""

    def __init__(self):
        self.mock_types = []
        self.patch_targets = []
        self.mock_in_test_count = 0
        self.in_test_function = False

    def visit_FunctionDef(self, node):
        """Track when we're inside a test function."""
        was_in_test = self.in_test_function
        if node.name.startswith('test_'):
            self.in_test_function = True

        self.generic_visit(node)
        self.in_test_function = was_in_test

    def visit_Import(self, node):
        """Track mock imports."""
        for alias in node.names:
            if 'mock' in alias.name.lower() or 'patch' in alias.name.lower():
                self.mock_types.append(f"import {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track mock imports."""
        if node.module and 'mock' in node.module.lower():
            for alias in node.names:
                self.mock_types.append(f"from {node.module} import {alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node):
        """Track mock calls."""
        if self.in_test_function:
            call_name = self._get_call_name(node)
            if call_name and any(mock in call_name.lower() for mock in ['mock', 'patch']):
                self.mock_in_test_count += 1

        # Check for patch decorators
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'patch':
            if node.args:
                target = ast.unparse(node.args[0]) if hasattr(ast, 'unparse') else str(node.args[0])
                self.patch_targets.append(target)

        self.generic_visit(node)

    def _get_call_name(self, node):
        """Get the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


if __name__ == "__main__":
    # Test the mock detector
    detector = MockDetector()

    # Example test content with mocks
    test_content = """
import pytest
from unittest.mock import patch, MagicMock

class TestIntegration:
    @patch('requests.get')
    def test_api_integration(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        # This should be flagged as inappropriate
        result = my_api_function()
        assert result == True
        mock_get.assert_called()
"""

    result = detector.analyze_test_content(test_content, "test_integration.py")
    print(f"✅ Mock detector validation:")
    print(f"   Has mocks: {result['has_mocks']}")
    print(f"   Mock score: {result['mock_score']:.2f}")
    print(f"   Violations: {result['violations']}")
    print(f"   Suspicious patterns: {result['suspicious_patterns']}")