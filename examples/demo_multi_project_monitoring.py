#!/usr/bin/env python3
"""
Demo: Multi-Project Test Monitoring

Shows how to use the new multi-project monitoring features:
- Multi-project dashboard
- Test history tracking
- Flaky test detection
- Agent comparison
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.claude_test_reporter.generators import MultiProjectDashboard
from src.claude_test_reporter.tracking import TestHistoryTracker
from src.claude_test_reporter.adapters import AgentReportAdapter


def create_sample_test_data(project_name: str, run_number: int):
    """Create sample test data for demonstration."""
    # Simulate some test variability
    flaky_test_pass = (run_number % 3) != 0  # Fails every 3rd run
    slow_test_duration = 1.0 + (run_number * 0.1)  # Gets slower over time
    
    return {
        "created": (datetime.now() - timedelta(hours=run_number)).timestamp(),
        "duration": 45.2 + run_number,
        "tests": [
            {
                "nodeid": f"{project_name}::test_core_functionality",
                "outcome": "passed",
                "duration": 1.2
            },
            {
                "nodeid": f"{project_name}::test_flaky_feature",
                "outcome": "passed" if flaky_test_pass else "failed",
                "duration": 0.8
            },
            {
                "nodeid": f"{project_name}::test_slow_operation",
                "outcome": "passed",
                "duration": slow_test_duration
            },
            {
                "nodeid": f"{project_name}::test_edge_case",
                "outcome": "failed" if run_number < 2 else "passed",
                "duration": 0.5
            }
        ]
    }


def demo_multi_project_dashboard():
    """Demonstrate the multi-project dashboard."""
    print("🚀 Demo: Multi-Project Dashboard\n")
    
    dashboard = MultiProjectDashboard()
    
    # Add sample projects
    projects = ["SPARTA", "Marker", "ArangoDB"]
    for i, project in enumerate(projects):
        # Create sample data
        total = 100 + i * 20
        failed = 5 + i * 3
        passed = total - failed - 2
        
        dashboard.add_project(project, {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": 2,
            "duration": 45.2 + i * 10,
            "success_rate": (passed / total) * 100,
            "health": "healthy" if passed/total > 0.9 else "warning" if passed/total > 0.8 else "critical",
            "failed_tests": [
                {"name": f"test_feature_{j}", "duration": 0.5 + j * 0.1, "file": f"tests/test_{project.lower()}.py"}
                for j in range(min(failed, 3))
            ]
        }, f"{project.lower()}_report.html")
    
    # Generate dashboard
    output_file = dashboard.generate("example_multi_project_dashboard.html")
    print(f"✅ Dashboard generated: {output_file}\n")
    
    return output_file


def demo_test_history():
    """Demonstrate test history tracking and flaky test detection."""
    print("🔍 Demo: Test History & Flaky Test Detection\n")
    
    tracker = TestHistoryTracker(".example_test_history")
    project = "ExampleProject"
    
    # Simulate multiple test runs
    print(f"Adding test runs for {project}...")
    for i in range(10):
        test_data = create_sample_test_data(project, i)
        tracker.add_test_run(project, {
            "total": len(test_data["tests"]),
            "passed": sum(1 for t in test_data["tests"] if t["outcome"] == "passed"),
            "failed": sum(1 for t in test_data["tests"] if t["outcome"] == "failed"),
            "skipped": 0,
            "duration": test_data["duration"],
            "tests": test_data["tests"]
        }, f"run_{i}")
        print(f"  • Run {i}: {sum(1 for t in test_data['tests'] if t['outcome'] == 'passed')}/4 passed")
    
    # Get test trends
    print("\n📈 Test Trends:")
    for test_name in [f"{project}::test_flaky_feature", f"{project}::test_slow_operation"]:
        trends = tracker.get_test_trends(project, test_name, days=30)
        print(f"\n  {test_name}:")
        print(f"    • Success rate: {trends['success_rate']:.1f}%")
        print(f"    • Avg duration: {trends['duration_stats']['mean']:.2f}s")
        if trends.get('performance_regression'):
            print(f"    • ⚠️  Performance regression detected! {trends['regression_factor']:.1f}x slower")
    
    # Get flaky tests
    flaky_tests = tracker.get_flaky_tests(project)
    if flaky_tests and "tests" in flaky_tests:
        print("\n🎲 Flaky Tests Detected:")
        for test_name, data in flaky_tests["tests"].items():
            print(f"  • {test_name}")
            print(f"    - Flakiness score: {data['flakiness_score']}")
            print(f"    - Pass rate: {data['pass_rate']}%")
            print(f"    - Recent pattern: {data['recent_pattern']}")
    
    # Generate history report
    report_file = tracker.generate_history_report(project, "example_test_history_report.html")
    print(f"\n✅ History report generated: {report_file}\n")
    
    return report_file


def demo_agent_comparison():
    """Demonstrate agent comparison functionality."""
    print("🤖 Demo: Agent Comparison\n")
    
    # Create two different agent results
    agent1_data = {
        "tests": [
            {"nodeid": "test_shared_1", "outcome": "passed"},
            {"nodeid": "test_shared_2", "outcome": "failed"},
            {"nodeid": "test_agent1_only", "outcome": "passed"},
            {"nodeid": "test_flaky", "outcome": "passed"},
        ]
    }
    
    agent2_data = {
        "tests": [
            {"nodeid": "test_shared_1", "outcome": "passed"},
            {"nodeid": "test_shared_2", "outcome": "passed"},  # Different result!
            {"nodeid": "test_agent2_only", "outcome": "failed"},
            {"nodeid": "test_flaky", "outcome": "failed"},  # Different result!
        ]
    }
    
    # Save to temp files
    Path("temp_agent1.json").write_text(json.dumps(agent1_data))
    Path("temp_agent2.json").write_text(json.dumps(agent2_data))
    
    # Create adapter and compare
    adapter = AgentReportAdapter(Path("temp_agent1.json"), "Agent1")
    comparison = adapter.get_agent_comparison(agent2_data)
    
    print("📊 Comparison Results:")
    print(f"  • Agent 1 tests: {comparison['total_tests']['this_agent']}")
    print(f"  • Agent 2 tests: {comparison['total_tests']['other_agent']}")
    print(f"  • Agreement rate: {comparison['agreement_rate']:.1f}%")
    print(f"  • Differences: {comparison['difference_count']}")
    
    if comparison['differences']:
        print("\n📋 Differences found:")
        for diff in comparison['differences']:
            print(f"  • {diff['test_id']}: {diff['this_agent']} vs {diff['other_agent']} ({diff['type']})")
    
    # Clean up temp files
    Path("temp_agent1.json").unlink()
    Path("temp_agent2.json").unlink()
    
    print("\n✅ Agent comparison complete\n")


def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("Claude Test Reporter - Multi-Project Monitoring Demo")
    print("=" * 60)
    print()
    
    # Run demos
    dashboard_file = demo_multi_project_dashboard()
    history_file = demo_test_history()
    demo_agent_comparison()
    
    print("=" * 60)
    print("🎉 All demos complete!")
    print("\nGenerated reports:")
    print(f"  • Multi-project dashboard: {dashboard_file}")
    print(f"  • Test history report: {history_file}")
    print("\nNew CLI commands:")
    print("  • claude-test-report dashboard -a SPARTA sparta.json -a Marker marker.json")
    print("  • claude-test-report history ExampleProject")
    print("  • claude-test-report compare agent1.json agent2.json")
    print("  • claude-test-report analyze results.json -p MyProject")
    print("=" * 60)


if __name__ == "__main__":
    main()