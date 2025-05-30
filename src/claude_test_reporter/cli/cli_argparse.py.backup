#!/usr/bin/env python3
"""
CLI for Claude Test Reporter
"""

import sys
import json
from pathlib import Path
from typing import Optional
import argparse

from claude_test_reporter.generators import UniversalReportGenerator
from claude_test_reporter.generators.multi_project_dashboard import MultiProjectDashboard
from claude_test_reporter.tracking import TestHistoryTracker
from claude_test_reporter.adapters import AgentReportAdapter
from claude_test_reporter import get_report_config


def main():
    parser = argparse.ArgumentParser(description="Claude Test Reporter CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # From pytest command
    pytest_parser = subparsers.add_parser("from-pytest", help="Generate from pytest JSON")
    pytest_parser.add_argument("json_file", help="Pytest JSON report file")
    pytest_parser.add_argument("-o", "--output", default="report.html", help="Output file")
    pytest_parser.add_argument("-p", "--project", help="Project name for config")
    
    # From data command  
    data_parser = subparsers.add_parser("from-data", help="Generate from JSON data")
    data_parser.add_argument("data_file", help="JSON data file")
    data_parser.add_argument("-o", "--output", default="report.html", help="Output file")
    data_parser.add_argument("-t", "--title", default="Test Report", help="Report title")
    data_parser.add_argument("-c", "--color", default="#667eea", help="Theme color")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze pytest results")
    analyze_parser.add_argument("json_file", help="Pytest JSON report file")
    analyze_parser.add_argument("-p", "--project", help="Project name")
    
    # Multi-project dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Generate multi-project dashboard")
    dashboard_parser.add_argument("-o", "--output", default="dashboard.html", help="Output file")
    dashboard_parser.add_argument("-a", "--add", nargs=2, metavar=("PROJECT", "JSON_FILE"), 
                                 action="append", help="Add project results (can be used multiple times)")
    
    # History command
    history_parser = subparsers.add_parser("history", help="View test history")
    history_parser.add_argument("project", help="Project name")
    history_parser.add_argument("-o", "--output", default="history_report.html", help="Output file")
    history_parser.add_argument("-d", "--days", type=int, default=30, help="Days of history to show")
    
    # Compare agents command
    compare_parser = subparsers.add_parser("compare", help="Compare results between agents")
    compare_parser.add_argument("json_file1", help="First agent's JSON report")
    compare_parser.add_argument("json_file2", help="Second agent's JSON report")
    compare_parser.add_argument("-o", "--output", default="comparison.json", help="Output file")
    
    args = parser.parse_args()
    
    if args.command == "from-pytest":
        generate_from_pytest(args.json_file, args.output, args.project)
    elif args.command == "from-data":
        generate_from_data(args.data_file, args.output, args.title, args.color)
    elif args.command == "analyze":
        analyze_pytest_results(args.json_file, args.project)
    elif args.command == "dashboard":
        generate_dashboard(args.add, args.output)
    elif args.command == "history":
        generate_history_report(args.project, args.output, args.days)
    elif args.command == "compare":
        compare_agent_results(args.json_file1, args.json_file2, args.output)
    else:
        parser.print_help()


def generate_from_pytest(json_file: str, output: str, project: Optional[str] = None):
    """Generate HTML report from pytest JSON."""
    with open(json_file) as f:
        pytest_data = json.load(f)
    
    # Convert pytest data to report format
    data = []
    for test in pytest_data.get("tests", []):
        data.append({
            "Test": test["nodeid"],
            "Status": test["outcome"].upper(),
            "Duration": f"{test.get('duration', 0):.2f}s",
            "File": test["nodeid"].split("::")[0]
        })
    
    # Get config
    if project:
        config = get_report_config(project)
        generator = UniversalReportGenerator(**config)
    else:
        generator = UniversalReportGenerator(title="Pytest Results")
    
    # Generate report
    report_path = generator.generate(data, output)
    print(f"✅ Report generated: {report_path}")


def generate_from_data(data_file: str, output: str, title: str, color: str):
    """Generate HTML report from JSON data."""
    with open(data_file) as f:
        data = json.load(f)
    
    generator = UniversalReportGenerator(title=title, theme_color=color)
    report_path = generator.generate(data, output)
    print(f"✅ Report generated: {report_path}")


def analyze_pytest_results(json_file: str, project_name: Optional[str] = None):
    """Analyze pytest results for CI/CD."""
    adapter = AgentReportAdapter(Path(json_file), project_name)
    
    status = adapter.get_quick_status()
    print(f"\n📊 Test Results Summary:")
    print(f"  • Passed: {status['passed_count']}")
    print(f"  • Failed: {status['failure_count']}")
    print(f"  • Skipped: {status['skipped_count']}")
    print(f"  • Success Rate: {status['success_rate']:.1f}%")
    
    if not status['all_passed']:
        print(f"\n❌ Action Required:")
        for action in adapter.get_actionable_items():
            print(f"  • [{action['priority'].upper()}] {action['error_type']}: {action['count']} tests")
            print(f"    Fix: {action['suggested_fix']}")
            if action.get('details'):
                print(f"    Details: {action['details']}")


def generate_dashboard(project_files: list, output: str):
    """Generate multi-project dashboard."""
    if not project_files:
        print("❌ No projects specified. Use -a PROJECT JSON_FILE to add projects.")
        return
    
    dashboard = MultiProjectDashboard()
    
    for project_name, json_file in project_files:
        try:
            dashboard.load_project_from_json(project_name, Path(json_file))
            print(f"✅ Added {project_name} from {json_file}")
        except Exception as e:
            print(f"❌ Failed to load {project_name}: {e}")
    
    try:
        report_path = dashboard.generate(output)
        print(f"\n📊 Dashboard generated: {report_path}")
    except Exception as e:
        print(f"❌ Failed to generate dashboard: {e}")


def generate_history_report(project: str, output: str, days: int):
    """Generate test history report."""
    tracker = TestHistoryTracker()
    
    try:
        report_path = tracker.generate_history_report(project, output)
        print(f"📈 History report generated: {report_path}")
    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Failed to generate history report: {e}")


def compare_agent_results(json_file1: str, json_file2: str, output: str):
    """Compare test results between two agents."""
    try:
        # Load both reports
        with open(json_file1) as f:
            data1 = json.load(f)
        with open(json_file2) as f:
            data2 = json.load(f)
        
        # Create adapter and compare
        adapter1 = AgentReportAdapter(Path(json_file1))
        comparison = adapter1.get_agent_comparison(data2)
        
        # Save comparison
        with open(output, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Print summary
        print(f"\n🔍 Agent Comparison Summary:")
        print(f"  • Total tests (Agent 1): {comparison['total_tests']['this_agent']}")
        print(f"  • Total tests (Agent 2): {comparison['total_tests']['other_agent']}")
        print(f"  • Differences found: {comparison['difference_count']}")
        print(f"  • Agreement rate: {comparison['agreement_rate']:.1f}%")
        
        if comparison['differences']:
            print(f"\n📋 Top differences:")
            for diff in comparison['differences'][:5]:
                print(f"  • {diff['test_id']}: {diff['this_agent']} vs {diff['other_agent']} ({diff['type']})")
        
        print(f"\n💾 Full comparison saved to: {output}")
        
    except Exception as e:
        print(f"❌ Failed to compare results: {e}")


if __name__ == "__main__":
    main()
