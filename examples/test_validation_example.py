Response: 200"
                }
            },
            {
                "nodeid": "test_validation.py::test_email_validation",
                "outcome": "passed",
                "duration": 0.002,
                "call": {
                    "stdout": "Checked: test@example.com is valid"
                }
            },
            {
                "nodeid": "test_async.py::test_concurrent_operations",
                "outcome": "failed",
                "duration": 5.1,
                "call": {
                    "longrepr": "TimeoutError: Operation timed out after 5 seconds",
                    "stdout": "Starting 10 concurrent operations..."
                }
            }
        ],
        "summary": {
            "total": 5,
            "passed": 4,
            "failed": 1
        }
    }
    
    # Initialize components
    print("\n📊 Test Results Summary:")
    print(f"   Total: {test_results['summary']['total']}")
    print(f"   Passed: {test_results['summary']['passed']}")
    print(f"   Failed: {test_results['summary']['failed']}")
    
    # Create validator with Gemini
    print(f"\n🤖 Getting second opinion from Gemini...")
    validator = TestValidator(model="gemini/gemini-2.5-pro-preview-05-06")
    
    # Validate each test
    validation_results = validator.validate_all_tests(test_results)
    
    # Print validation summary
    print(f"\n📋 Validation Summary:")
    print(f"   Model: {validation_results['model']}")
    
    summary = validation_results['summary']
    print(f"\n   Categories:")
    for category, count in summary['categories'].items():
        print(f"     - {category}: {count}")
    
    print(f"\n   Severities:")
    for severity, count in summary['severities'].items():
        print(f"     - {severity}: {count}")
    
    print(f"\n   Total Issues Found: {summary['total_issues']}")
    
    if summary['problematic_tests']:
        print(f"\n   ⚠️  Problematic Tests:")
        for test in summary['problematic_tests']:
            print(f"     - {test}")
    
    # Show detailed issues for problematic tests
    print(f"\n🔍 Detailed Analysis:")
    for test_name, validation in validation_results['validations'].items():
        if not validation.get('is_valid', True):
            print(f"\n   Test: {test_name}")
            print(f"   Category: {validation['category']}")
            print(f"   Severity: {validation['severity']}")
            print(f"   Issues:")
            for issue in validation.get('issues', []):
                print(f"     - {issue}")
            print(f"   Suggestions:")
            for suggestion in validation.get('suggestions', []):
                print(f"     - {suggestion}")
    
    # Save full results
    output_file = "validated_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "test_results": test_results,
            "validation": validation_results
        }, f, indent=2)
    
    print(f"\n💾 Full results saved to: {output_file}")
    
    # Generate HTML report with validation
    print(f"\n📄 Generating HTML report with validation...")
    reporter = TestReporter()
    validation_reporter = TestValidationReporter(reporter, validator)
    
    # Note: This would generate an enhanced HTML report
    # For now, we just demonstrate the validation feature
    
    print("\n✅ Validation complete!")
    
    # Return non-zero if problematic tests found
    return len(summary['problematic_tests']) > 0


if __name__ == "__main__":
    sys.exit(main())
