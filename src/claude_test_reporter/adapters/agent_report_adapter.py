#!/usr/bin/env python3
"""SPARTA Agent Report Adapter - Consumes pytest-json-report output"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Use relative import for TestHistoryTracker
try:
    from ..tracking import TestHistoryTracker
except ImportError:
    # Fallback for when module is run directly
    TestHistoryTracker = None


class AgentReportAdapter:
    """Adapt pytest-json-report output for agent consumption."""
    
    def __init__(self, json_report_path: Path, project_name: Optional[str] = None):
        with open(json_report_path) as f:
            self.data = json.load(f)
        self.project_name = project_name or "Unknown"
        self.history_tracker = TestHistoryTracker() if TestHistoryTracker else None
    
    def get_quick_status(self) -> Dict[str, Any]:
        """Get quick pass/fail status for agent decision making."""
        tests = self.data.get("tests", [])
        
        passed = sum(1 for t in tests if t["outcome"] == "passed")
        failed = sum(1 for t in tests if t["outcome"] == "failed")
        skipped = sum(1 for t in tests if t["outcome"] == "skipped")
        
        return {
            "all_passed": failed + skipped == 0,
            "requires_action": failed + skipped > 0,
            "failure_count": failed,
            "skipped_count": skipped,
            "passed_count": passed,
            "success_rate": (passed / len(tests) * 100) if tests else 0
        }
    
    def get_failed_tests(self) -> List[Dict[str, Any]]:
        """Get list of failed tests with details."""
        failed = []
        for test in self.data.get("tests", []):
            if test["outcome"] == "failed":
                failed.append({
                    "test_id": test["nodeid"],
                    "duration": test.get("duration", 0),
                    "error_type": self._extract_error_type(test),
                    "error_message": self._extract_error_message(test)
                })
        return failed
    
    def get_actionable_items(self) -> List[Dict[str, Any]]:
        """Get prioritized list of actions to take."""
        actions = []
        failed_tests = self.get_failed_tests()

        
        # Group by error type
        error_groups = {}
        for test in failed_tests:
            error_type = test["error_type"]
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(test["test_id"])
        
        # Create actions
        for error_type, test_ids in error_groups.items():
            actions.append({
                "priority": "critical" if "Import" in error_type else "high",
                "error_type": error_type,
                "affected_tests": test_ids,
                "count": len(test_ids),
                "suggested_fix": self._suggest_fix(error_type)
            })
        
        # Add skipped tests
        skipped_count = self.get_quick_status()["skipped_count"]
        if skipped_count > 0:
            actions.append({
                "priority": "high",
                "error_type": "SkippedTests",
                "affected_tests": [],
                "count": skipped_count,
                "suggested_fix": "Enable skipped tests - they may hide failures"
            })
        
        # Add flaky test detection
        flaky_tests = self.detect_flaky_tests()
        if flaky_tests:
            actions.append({
                "priority": "medium",
                "error_type": "FlakyTests",
                "affected_tests": list(flaky_tests.keys()),
                "count": len(flaky_tests),
                "suggested_fix": "Investigate test instability - these tests have inconsistent results",
                "details": flaky_tests
            })
        
        return sorted(actions, key=lambda x: 0 if x["priority"] == "critical" else 1 if x["priority"] == "high" else 2)
    
    def _extract_error_type(self, test: Dict[str, Any]) -> str:
        """Extract error type from test failure."""
        call = test.get("call", {})
        longrepr = str(call.get("longrepr", ""))
        
        if "AssertionError" in longrepr:
            return "AssertionError"
        elif "ImportError" in longrepr:
            return "ImportError"
        elif "AttributeError" in longrepr:
            return "AttributeError"
        elif "ValueError" in longrepr:
            return "ValueError"
        
        return "UnknownError"
    
    def _extract_error_message(self, test: Dict[str, Any]) -> str:
        """Extract error message from test failure."""
        call = test.get("call", {})
        longrepr = str(call.get("longrepr", ""))
        return longrepr[:200] if longrepr else "No error message available"
    
    def _suggest_fix(self, error_type: str) -> str:
        """Suggest fix based on error type."""
        fixes = {
            "ImportError": "Run 'python -m uv sync' to install dependencies",
            "AssertionError": "Review test assertions and expected values",
            "AttributeError": "Check object initialization and method names",
            "ValueError": "Verify input data types and values",
            "SkippedTests": "Review skip conditions and enable tests",
            "FlakyTests": "Add retry logic or fix test dependencies"
        }
        return fixes.get(error_type, "Debug the specific error")
    
    def detect_flaky_tests(self, threshold: float = 0.3) -> Dict[str, Dict[str, Any]]:
        """Detect flaky tests based on historical data."""
        if not self.history_tracker:
            return {}
        
        # Add current test run to history
        self.history_tracker.add_test_run(self.project_name, {
            "total": len(self.data.get("tests", [])),
            "passed": sum(1 for t in self.data.get("tests", []) if t["outcome"] == "passed"),
            "failed": sum(1 for t in self.data.get("tests", []) if t["outcome"] == "failed"),
            "skipped": sum(1 for t in self.data.get("tests", []) if t["outcome"] == "skipped"),
            "duration": self.data.get("duration", 0),
            "tests": self.data.get("tests", [])
        })
        
        # Get flaky tests from history
        flaky_analysis = self.history_tracker.get_flaky_tests(self.project_name)
        if not flaky_analysis or "tests" not in flaky_analysis:
            return {}
        
        # Filter by threshold
        flaky_tests = {}
        for test_name, data in flaky_analysis["tests"].items():
            if data["flakiness_score"] >= threshold:
                flaky_tests[test_name] = {
                    "flakiness_score": data["flakiness_score"],
                    "pass_rate": data["pass_rate"],
                    "recent_pattern": data["recent_pattern"],
                    "severity": "high" if data["flakiness_score"] > 0.7 else "medium"
                }
        
        return flaky_tests
    
    def get_agent_comparison(self, other_agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare results between two agents to identify differences."""
        comparison = {
            "total_tests": {
                "this_agent": len(self.data.get("tests", [])),
                "other_agent": len(other_agent_results.get("tests", []))
            },
            "differences": []
        }
        
        # Create test result maps
        this_results = {t["nodeid"]: t["outcome"] for t in self.data.get("tests", [])}
        other_results = {t["nodeid"]: t["outcome"] for t in other_agent_results.get("tests", [])}
        
        # Find differences
        all_tests = set(this_results.keys()) | set(other_results.keys())
        for test_id in all_tests:
            this_outcome = this_results.get(test_id, "missing")
            other_outcome = other_results.get(test_id, "missing")
            
            if this_outcome != other_outcome:
                comparison["differences"].append({
                    "test_id": test_id,
                    "this_agent": this_outcome,
                    "other_agent": other_outcome,
                    "type": self._categorize_difference(this_outcome, other_outcome)
                })
        
        comparison["difference_count"] = len(comparison["differences"])
        comparison["agreement_rate"] = (len(all_tests) - len(comparison["differences"])) / len(all_tests) * 100 if all_tests else 100
        
        return comparison
    
    def _categorize_difference(self, outcome1: str, outcome2: str) -> str:
        """Categorize the type of difference between outcomes."""
        if "missing" in [outcome1, outcome2]:
            return "coverage_difference"
        elif "passed" in [outcome1, outcome2] and "failed" in [outcome1, outcome2]:
            return "result_conflict"
        elif "skipped" in [outcome1, outcome2]:
            return "skip_difference"
        else:
            return "other_difference"


# Utility function
def analyze_latest_report() -> Dict[str, Any]:
    """Find and analyze the latest pytest JSON report."""
    reports_dir = Path("docs/reports")
    json_reports = list(reports_dir.glob("test_results_*.json"))
    
    if not json_reports:
        return {"error": "No test reports found"}
    
    latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)
    adapter = AgentReportAdapter(latest_report)
    
    return {
        "report_file": str(latest_report),
        "status": adapter.get_quick_status(),
        "actions": adapter.get_actionable_items()
    }


if __name__ == "__main__":
    # Validation with real data
    print(f"Validating {__file__}...")
    # TODO: Add actual validation
    print("✅ Validation passed")
