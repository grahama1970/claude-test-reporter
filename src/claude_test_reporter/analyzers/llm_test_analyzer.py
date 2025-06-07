

Module: llm_test_analyzer.py
Description: Test suite for llm_analyzer functionality
"""

External Dependencies:
- llm_call: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
LLM Test Result Analyzer

Purpose: Send test reports to external LLM (Gemini 2.5 Pro) for analysis
Features: Hallucination prevention, test validation, intelligent insights
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from llm_call import call_llm
except ImportError:
    call_llm = None
    print("Warning: llm_call module not available. LLM analysis features disabled.")


class LLMTestAnalyzer:
    """Analyze test results using external LLM to prevent hallucinations."""

    def __init__(self, model: str = "gemini-2.5-pro", temperature: float = 0.1):
        """
        Initialize LLM analyzer.

        Args:
            model: LLM model to use
            temperature: Low temperature for factual accuracy
        """
        self.model = model
        self.temperature = temperature
        self.analysis_cache = {}

    def analyze_test_results(self, test_results: Dict[str, Any],
                           project_name: str) -> Dict[str, Any]:
        """
        Send test results to LLM for analysis.

        Returns analysis with:
        - Actual test status verification
        - Failure pattern recognition
        - Risk assessment
        - Recommended actions
        """
        if not call_llm:
            return {"error": "LLM module not available"}

        # Prepare structured prompt
        prompt = self._create_analysis_prompt(test_results, project_name)

        # Call LLM with structured format
        try:
            response = call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                response_format="json"
            )

            analysis = json.loads(response)
            self.analysis_cache[project_name] = analysis
            return analysis

        except Exception as e:
            return {"error": f"LLM analysis failed: {str(e)}"}

    def _create_analysis_prompt(self, test_results: Dict[str, Any],
                               project_name: str) -> str:
        """Create structured prompt for LLM analysis."""

        # Extract key metrics
        total_tests = test_results.get("total", 0)
        passed_tests = test_results.get("passed", 0)
        failed_tests = test_results.get("failed", 0)
        skipped_tests = test_results.get("skipped", 0)

        # Get failed test details
        failed_test_details = []
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                failed_test_details.append({
                    "name": test.get("nodeid", "unknown"),
                    "error": test.get("error", "No error message")[:200]
                })

        prompt = f"""
You are a test result analyzer. Your job is to provide FACTUAL analysis of test results.
Never claim tests are passing if they are not. Always base your analysis on the actual data.

Project: {project_name}
Test Results Summary:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Skipped: {skipped_tests}
- Success Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%

Failed Tests:
{json.dumps(failed_test_details, indent=2)}

Analyze these results and provide a JSON response with the following structure:
{{
    "summary": {{
        "overall_status": "passing|failing|unstable",
        "confidence_level": "high|medium|low",
        "actual_pass_rate": <number>,
        "requires_immediate_action": <boolean>
    }},
    "failed_test_analysis": [
        {{
            "test_name": "<test name>",
            "failure_category": "assertion|import|timeout|other",
            "likely_cause": "<brief explanation>",
            "suggested_fix": "<actionable suggestion>"
        }}
    ],
    "risk_assessment": {{
        "deployment_ready": <boolean>,
        "critical_failures": <number>,
        "blocking_issues": ["<issue1>", "<issue2>"]
    }},
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "action": "<specific action to take>",
            "reason": "<why this is important>"
        }}
    ],
    "hallucination_check": {{
        "stated_facts": ["<fact1>", "<fact2>"],
        "data_verification": {{
            "all_facts_verified": <boolean>,
            "unverified_claims": []
        }}
    }}
}}

IMPORTANT: Base ALL conclusions strictly on the provided data. Do not make assumptions.
"""
        return prompt

    def verify_agent_claims(self, agent_output: str,
                          actual_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an agent's claims about test results against actual data.

        This is the key anti-hallucination feature.
        """
        if not call_llm:
            return {"error": "LLM module not available"}

        verification_prompt = f"""
You are a fact-checker for test result claims. Your job is to verify claims against actual data.

AGENT'S CLAIMS:
{agent_output}

ACTUAL TEST DATA:
- Total Tests: {actual_results.get('total', 0)}
- Passed: {actual_results.get('passed', 0)}
- Failed: {actual_results.get('failed', 0)}
- Success Rate: {actual_results.get('success_rate', 0):.1f}%

Failed Tests: {[t['nodeid'] for t in actual_results.get('tests', []) if t.get('outcome') == 'failed']}

Analyze the agent's claims and provide a JSON response:
{{
    "verification_result": {{
        "claims_accurate": <boolean>,
        "hallucinations_detected": <boolean>,
        "incorrect_claims": [
            {{
                "claim": "<what agent claimed>",
                "reality": "<what actually happened>",
                "severity": "critical|major|minor"
            }}
        ],
        "verification_confidence": <0-100>
    }},
    "corrected_summary": "<accurate summary of actual test results>"
}}
"""

        try:
            response = call_llm(
                prompt=verification_prompt,
                model=self.model,
                temperature=0.0,  # Zero temperature for maximum accuracy
                response_format="json"
            )

            return json.loads(response)

        except Exception as e:
            return {"error": f"Verification failed: {str(e)}"}

    def generate_anti_hallucination_report(self,
                                         test_results: Dict[str, Any],
                                         project_name: str,
                                         output_file: str = "llm_analysis_report.json") -> str:
        """
        Generate a comprehensive report with LLM analysis and verification.
        """
        analysis = self.analyze_test_results(test_results, project_name)

        report = {
            "project": project_name,
            "timestamp": datetime.now().isoformat(),
            "actual_results": {
                "total": test_results.get("total", 0),
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "success_rate": test_results.get("success_rate", 0)
            },
            "llm_analysis": analysis,
            "verification_metadata": {
                "model_used": self.model,
                "temperature": self.temperature,
                "analysis_version": "1.0"
            }
        }

        output_path = Path(output_file)
        output_path.write_text(json.dumps(report, indent=2))

        return str(output_path.resolve())


class TestReportVerifier:
    """Verify test reports before sending to agents to prevent hallucinations."""

    def __init__(self):
        self.verification_history = []

    def create_verified_summary(self, test_results: Dict[str, Any]) -> str:
        """
        Create a fact-based summary that agents cannot misinterpret.
        """
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)

        summary = f"""
VERIFIED TEST RESULTS - DO NOT MODIFY OR INTERPRET DIFFERENTLY:
==============================================================
Total Tests: {total}
Passed: {passed}
Failed: {failed}
Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%

CRITICAL FACTS:
- {failed} tests are FAILING and must be fixed
- The project is {'NOT' if failed > 0 else ''} ready for deployment
- Success rate is EXACTLY {(passed/total*100) if total > 0 else 0:.1f}%, not higher

Failed Tests List:
"""

        # Add each failed test explicitly
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                summary += f"- {test.get('nodeid', 'unknown')}: FAILED\n"

        summary += """
==============================================================
Any claim that contradicts these facts is a hallucination.
"""
        return summary

    def create_structured_report_for_llm(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a structured report format that minimizes hallucination risk.
        """
        return {
            "version": "1.0",
            "strict_mode": True,
            "facts_only": {
                "test_counts": {
                    "total": test_results.get("total", 0),
                    "passed": test_results.get("passed", 0),
                    "failed": test_results.get("failed", 0),
                    "skipped": test_results.get("skipped", 0)
                },
                "calculated_metrics": {
                    "success_rate_percent": round((test_results.get("passed", 0) / test_results.get("total", 1)) * 100, 2),
                    "failure_rate_percent": round((test_results.get("failed", 0) / test_results.get("total", 1)) * 100, 2)
                },
                "failed_test_names": [
                    t.get("nodeid", "unknown")
                    for t in test_results.get("tests", [])
                    if t.get("outcome") == "failed"
                ],
                "deployment_status": "BLOCKED" if test_results.get("failed", 0) > 0 else "READY"
            },
            "instructions_for_llm": [
                "Report ONLY the facts provided above",
                "Do NOT claim tests are passing if failed > 0",
                "Do NOT round success rates up",
                "Do NOT ignore failed tests",
                "If failed tests exist, deployment is BLOCKED"
            ]
        }


if __name__ == "__main__":
    # Example usage
    print(f"Validating {__file__}...")

    # Create sample test data
    test_results = {
        "total": 100,
        "passed": 85,
        "failed": 15,
        "skipped": 0,
        "success_rate": 85.0,
        "tests": [
            {"nodeid": "test_auth::test_login", "outcome": "failed", "error": "AssertionError"},
            {"nodeid": "test_api::test_endpoint", "outcome": "failed", "error": "ConnectionError"},
            # ... more tests
        ]
    }

    # Test verifier
    verifier = TestReportVerifier()
    verified_summary = verifier.create_verified_summary(test_results)
    print("Verified Summary:")
    print(verified_summary)

    # Test structured report
    structured = verifier.create_structured_report_for_llm(test_results)
    print("\nStructured Report:")
    print(json.dumps(structured, indent=2))

    print("\n✅ LLM Test Analyzer validation complete")