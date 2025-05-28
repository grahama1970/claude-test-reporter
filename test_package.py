#!/usr/bin/env python3
"""
Test the Claude Test Reporter package functionality
"""

import sys
import json
from pathlib import Path

# Add the package to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_test_reporter import get_report_config
from claude_test_reporter.generators import UniversalReportGenerator, SimpleHTMLReporter
from claude_test_reporter.adapters import TestReporter
from claude_test_reporter.runners import run_pytest_reports


def test_universal_generator():
    """Test the UniversalReportGenerator."""
    print("🧪 Testing UniversalReportGenerator...")
    
    # Test data
    data = [
        {"Test": "test_login", "Status": "PASS ✅", "Duration": 1.23, "Module": "auth"},
        {"Test": "test_signup", "Status": "FAIL ❌", "Duration": 0.45, "Module": "auth"},
        {"Test": "test_profile", "Status": "PASS ✅", "Duration": 0.67, "Module": "user"},
        {"Test": "test_settings", "Status": "PASS ✅", "Duration": 0.89, "Module": "user"},
    ]
    
    # Create generator
    generator = UniversalReportGenerator(
        title="Test Package Validation",
        theme_color="#10b981",
        logo="🧪"
    )
    
    # Generate report
    report_path = generator.generate(
        data, 
        "test_universal_report.html",
        summary_stats={
            "Total Tests": 4,
            "Passed": 3,
            "Failed": 1,
            "Success Rate": "75%"
        },
        group_by="Module"
    )
    
    assert Path(report_path).exists()
    print(f"✅ UniversalReportGenerator works! Report: {report_path}")
    return report_path


def test_simple_reporter():
    """Test the SimpleHTMLReporter."""
    print("\n🧪 Testing SimpleHTMLReporter...")
    
    # Test data
    data = [
        {"Check Name": "Import Test", "Status": "PASS", "Priority": "HIGH"},
        {"Check Name": "Functionality Test", "Status": "FAIL", "Priority": "CRITICAL"},
        {"Check Name": "Integration Test", "Status": "PASS", "Priority": "MEDIUM"},
    ]
    
    # Create reporter
    reporter = SimpleHTMLReporter(
        title="Simple Report Test",
        theme_color="#ef4444"
    )
    
    # Generate report
    html_content = reporter.generate_report(
        data,
        description="Testing the simple HTML reporter",
        additional_info={
            "Project": "Claude Test Reporter",
            "Version": "0.1.0",
            "Date": "2024-12-19"
        }
    )
    
    # Save report
    report_path = Path("test_simple_report.html")
    report_path.write_text(html_content)
    
    assert report_path.exists()
    assert len(html_content) > 1000  # Should have substantial content
    print(f"✅ SimpleHTMLReporter works! Report: {report_path}")
    return report_path


def test_report_config():
    """Test report configuration system."""
    print("\n🧪 Testing report configuration...")
    
    # Test getting configs
    sparta_config = get_report_config("sparta")
    assert sparta_config["title"] == "SPARTA Download Report"
    assert sparta_config["theme_color"] == "#667eea"
    assert sparta_config["logo"] == "🚀"
    
    marker_config = get_report_config("marker")
    assert marker_config["title"] == "Marker Extraction Report"
    assert marker_config["theme_color"] == "#10b981"
    
    # Test with override
    custom_config = get_report_config("sparta", base_url_override="http://localhost:9000")
    assert custom_config["base_url"] == "http://localhost:9000"
    
    print("✅ Report configuration works!")


def test_test_reporter():
    """Test the TestReporter class."""
    print("\n🧪 Testing TestReporter...")
    
    # Create instance
    reporter = TestReporter()
    
    # Test methods exist
    assert hasattr(reporter, 'run_tests_and_report')
    assert hasattr(reporter, 'generate_markdown_report')
    assert hasattr(reporter, '_parse_test_line')
    
    print("✅ TestReporter structure is valid!")


def test_imports():
    """Test that all imports work correctly."""
    print("\n🧪 Testing package imports...")
    
    # Test main imports
    from claude_test_reporter import get_report_config, REPORT_CONFIGS
    assert callable(get_report_config)
    assert isinstance(REPORT_CONFIGS, dict)
    
    # Test submodule imports
    from claude_test_reporter.generators import UniversalReportGenerator, SimpleHTMLReporter
    from claude_test_reporter.adapters import TestReporter
    from claude_test_reporter.runners import run_pytest_reports, get_latest_json_report
    
    print("✅ All imports work correctly!")


def main():
    """Run all tests."""
    print("🚀 Testing Claude Test Reporter Package\n")
    
    try:
        # Run all tests
        test_imports()
        test_report_config()
        test_test_reporter()
        
        # Generate example reports
        universal_report = test_universal_generator()
        simple_report = test_simple_reporter()
        
        print("\n✨ All tests passed!")
        print("\nGenerated reports:")
        print(f"  • {universal_report}")
        print(f"  • {simple_report}")
        
        print("\n📦 The claude-test-reporter package is ready to use!")
        print("\nTo install in another project:")
        print('  pip install "claude-test-reporter @ git+https://github.com/yourusername/claude-test-reporter.git"')
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()