🧪 Testing LLM integration...")
    
    reviewer = CodeReviewer(model="gemini/gemini-2.5-pro-preview-05-06")
    
    # Test with a simple prompt
    test_prompt = "Please respond with: 'Integration test successful'"
    
    try:
        response = reviewer._get_llm_review(test_prompt, temperature=0.1)
        if "successful" in response.lower():
            print("✅ LLM communication working")
            print(f"   Response: {response[:100]}...")
            return True
        else:
            print(f"❌ Unexpected response: {response[:100]}...")
            return False
    except Exception as e:
        print(f"❌ Failed to communicate with LLM: {e}")
        return False


def test_full_review():
    """Test a minimal code review."""
    print("\n🧪 Testing full code review flow...")
    
    # Create a test file
    test_file = Path("test_change.txt")
    test_file.write_text("# Test change for code review\\n")
    
    try:
        reviewer = CodeReviewer(model="gemini/gemini-2.5-pro-preview-05-06")
        
        # Just test that the flow works, not the actual review
        collector = GitChangeCollector()
        changes = collector.collect_changes()
        stats = collector.get_review_stats(changes)
        
        print(f"✅ Review flow working")
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Has changes: {stats.get('has_changes', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed review flow: {e}")
        return False
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


def main():
    """Run all integration tests."""
    print("🚀 Git Review Integration Test")
    print("=" * 50)
    
    tests = [
        test_git_collection,
        test_llm_integration,
        test_full_review
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
