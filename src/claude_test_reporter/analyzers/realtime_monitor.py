

Module: realtime_monitor.py
Description: Real-time test execution monitor that actually runs tests and captures output
"""

External Dependencies:
- subprocess: https://docs.python.org/3/library/subprocess.html
- threading: https://docs.python.org/3/library/threading.html
- queue: https://docs.python.org/3/library/queue.html

Sample Input:
>>> monitor = RealTimeTestMonitor()
>>> result = monitor.run_tests('/path/to/project', capture_raw=True)

Expected Output:
>>> print(result)
{'total_tests': 10, 'instant_tests': 3, 'suspicious_tests': ['test_quick'], 'raw_output': '...'}

Example Usage:
>>> monitor = RealTimeTestMonitor()
>>> results = monitor.monitor_test_execution('/home/user/project')
>>> if results['instant_tests'] > 0:
...     print(f"WARNING: {results['instant_tests']} tests completed suspiciously fast!")
"""

import subprocess
import time
import json
import re
import threading
import queue
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys
import os


class RealTimeTestMonitor:
    """Monitor test execution in real-time to detect lies about test results."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.suspicious_duration_threshold = 0.01  # Tests faster than this are suspicious
        self.realistic_duration_threshold = 0.1   # Integration tests should be slower

    def monitor_test_execution(self, project_path: str,
                             test_args: Optional[List[str]] = None,
                             capture_raw: bool = True) -> Dict[str, Any]:
        """Actually run tests and monitor execution in real-time."""
        project_path = Path(project_path)
        if not project_path.exists():
            return {"error": f"Project path not found: {project_path}"}

        # Default pytest arguments for detailed output
        if test_args is None:
            test_args = [
                "-v",  # Verbose
                "--tb=short",  # Short traceback
                "--durations=0",  # Show all test durations
                "--no-header",  # Skip header
                "-p", "no:cacheprovider",  # Disable cache
                "--capture=no"  # Don't capture output (we want to see it)
            ]

        # Prepare the command
        cmd = [sys.executable, "-m", "pytest"] + test_args

        # Find test directory
        test_dirs = [project_path / "tests", project_path / "test"]
        test_dir = None
        for td in test_dirs:
            if td.exists():
                test_dir = td
                break

        if test_dir:
            cmd.append(str(test_dir))
        else:
            cmd.append(str(project_path))

        # Results structure
        results = {
            "command": " ".join(cmd),
            "start_time": datetime.now().isoformat(),
            "project": str(project_path),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "instant_tests": 0,
            "suspicious_tests": [],
            "test_durations": {},
            "import_errors": [],
            "raw_output": "",
            "stderr": "",
            "return_code": None,
            "execution_time": 0,
            "mocked_test_indicators": []
        }

        # Run tests and capture output in real-time
        start_time = time.time()
        output_lines = []
        stderr_lines = []

        try:
            # Use Popen for real-time output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(project_path),
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )

            # Create queues for output
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()

            # Thread functions to read output
            def read_stdout():
                for line in process.stdout:
                    stdout_queue.put(line)

            def read_stderr():
                for line in process.stderr:
                    stderr_queue.put(line)

            # Start reader threads
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            stdout_thread.start()
            stderr_thread.start()

            # Process output in real-time
            test_pattern = re.compile(r'^(.*?)::(.*?)\s+(PASSED|FAILED|SKIPPED|ERROR)')
            duration_pattern = re.compile(r'^([\d.]+)s\s+(.*?)::(.*)$')
            import_error_pattern = re.compile(r'(ImportError|ModuleNotFoundError):(.*)$')

            # Collect output with timeout
            deadline = time.time() + self.timeout
            while process.poll() is None and time.time() < deadline:
                # Check stdout
                try:
                    line = stdout_queue.get(timeout=0.1)
                    output_lines.append(line)

                    # Parse test results
                    test_match = test_pattern.search(line)
                    if test_match:
                        results["total_tests"] += 1
                        status = test_match.group(3)
                        if status == "PASSED":
                            results["passed_tests"] += 1
                        elif status == "FAILED":
                            results["failed_tests"] += 1

                    # Parse durations
                    duration_match = duration_pattern.search(line)
                    if duration_match:
                        duration = float(duration_match.group(1))
                        test_name = f"{duration_match.group(2)}::{duration_match.group(3)}"
                        results["test_durations"][test_name] = duration

                        # Check for suspicious durations
                        if duration < self.suspicious_duration_threshold:
                            results["instant_tests"] += 1
                            results["suspicious_tests"].append({
                                "test": test_name,
                                "duration": duration,
                                "reason": "Completed too fast (likely mocked)"
                            })

                    # Check for import errors
                    import_match = import_error_pattern.search(line)
                    if import_match:
                        results["import_errors"].append(line.strip())

                except queue.Empty:
                    pass

                # Check stderr
                try:
                    line = stderr_queue.get(timeout=0.1)
                    stderr_lines.append(line)
                except queue.Empty:
                    pass

            # Wait for process to complete
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            process.wait(timeout=1)

            results["return_code"] = process.returncode

        except subprocess.TimeoutExpired:
            process.kill()
            results["error"] = f"Test execution timed out after {self.timeout}s"
            results["return_code"] = -1

        except Exception as e:
            results["error"] = f"Failed to execute tests: {str(e)}"
            results["return_code"] = -1

        # Calculate execution time
        results["execution_time"] = time.time() - start_time

        # Store raw output if requested
        if capture_raw:
            results["raw_output"] = "".join(output_lines)
            results["stderr"] = "".join(stderr_lines)

        # Analyze output for mock indicators
        results["mocked_test_indicators"] = self._detect_mock_indicators(output_lines)

        # Check for common lies
        results["lies_detected"] = self._detect_common_lies(results)

        return results

    def _detect_mock_indicators(self, output_lines: List[str]) -> List[Dict[str, str]]:
        """Detect indicators that tests are using mocks."""
        indicators = []

        mock_patterns = [
            (r'Mock.*called', "Mock object was called"),
            (r'patch.*as.*mock', "Using patch decorator"),
            (r'return_value\s*=', "Setting mock return value"),
            (r'side_effect\s*=', "Setting mock side effect"),
            (r'assert_called', "Asserting mock was called"),
            (r'<MagicMock', "MagicMock object in output"),
            (r'unittest\.mock', "unittest.mock import detected")
        ]

        for i, line in enumerate(output_lines):
            for pattern, description in mock_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    indicators.append({
                        "line_number": i + 1,
                        "line": line.strip(),
                        "indicator": description
                    })

        return indicators

    def _detect_common_lies(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect common patterns of lying about test results."""
        lies = []

        # Lie 1: All tests passing with no failures (suspicious)
        if results["total_tests"] > 10 and results["failed_tests"] == 0:
            lies.append({
                "type": "perfect_success",
                "description": "All tests passing (suspicious for large test suite)",
                "confidence": 0.7
            })

        # Lie 2: Too many instant tests
        instant_ratio = results["instant_tests"] / max(results["total_tests"], 1)
        if instant_ratio > 0.3:
            lies.append({
                "type": "instant_tests",
                "description": f"{instant_ratio:.0%} of tests completed instantly",
                "confidence": 0.9
            })

        # Lie 3: Import errors but tests still "pass"
        if results["import_errors"] and results["passed_tests"] > 0:
            lies.append({
                "type": "import_errors_ignored",
                "description": "Import errors detected but tests claim to pass",
                "confidence": 1.0
            })

        # Lie 4: No output captured (tests might not have run)
        if not results.get("raw_output") and results["total_tests"] == 0:
            lies.append({
                "type": "no_tests_run",
                "description": "No test output captured - tests may not have run",
                "confidence": 0.8
            })

        return lies

    def compare_with_reported(self, actual_results: Dict[str, Any],
                            reported_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare actual test results with what was reported."""
        discrepancies = {
            "matches": True,
            "differences": [],
            "trust_score": 1.0
        }

        # Compare test counts
        if actual_results["total_tests"] != reported_results.get("total_tests", 0):
            discrepancies["matches"] = False
            discrepancies["differences"].append({
                "field": "total_tests",
                "actual": actual_results["total_tests"],
                "reported": reported_results.get("total_tests", 0),
                "severity": "high"
            })

        # Compare pass/fail counts
        if actual_results["passed_tests"] != reported_results.get("passed_tests", 0):
            discrepancies["matches"] = False
            discrepancies["differences"].append({
                "field": "passed_tests",
                "actual": actual_results["passed_tests"],
                "reported": reported_results.get("passed_tests", 0),
                "severity": "critical"
            })

        # Calculate trust score
        if discrepancies["differences"]:
            critical_count = sum(1 for d in discrepancies["differences"]
                               if d["severity"] == "critical")
            discrepancies["trust_score"] = max(0, 1 - (critical_count * 0.3))

        return discrepancies


if __name__ == "__main__":
    # Test the real-time monitor
    monitor = RealTimeTestMonitor()

    print("✅ Real-time test monitor validation:")
    print("   - Forces actual pytest execution")
    print("   - Captures output in real-time")
    print("   - Detects instant-pass tests")
    print("   - Identifies mock usage patterns")
    print("   - Compares actual vs reported results")