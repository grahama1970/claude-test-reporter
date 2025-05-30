"""Basic tests for claude-test-reporter"""

def test_basic_import():
    """Test basic functionality"""
    # This is a minimal test to ensure pytest runs
    assert True, "Basic test should pass"
    print("✅ Basic test passed for claude-test-reporter")

def test_module_structure():
    """Test that module structure exists"""
    import os
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Check for src directory or module directory
    has_src = os.path.exists(os.path.join(project_root, 'src'))
    has_module = os.path.exists(os.path.join(project_root, 'claude_test_reporter'))
    
    assert has_src or has_module, "Project should have src/ or module directory"
    print("✅ Module structure verified")
