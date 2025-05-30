"""
Test Validator - Uses LLMs to provide second opinions on test results

Purpose: Detect hallucinated, incomplete, or lazy tests by getting 
critique from external LLMs via claude-max-proxy
"""

import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Try to import llm_call (installed via pyproject.toml)
try:
    from llm_call.core.llm_client import LLMClient
    HAS_LLM_CALL = True
except ImportError:
    HAS_LLM_CALL = False


class TestValidator:
    """Validates test results using external LLM critique."""
    
    def __init__(self, model: str = "gemini/gemini-2.5-pro-preview-05-06"):
        self.model = model
        self.validation_results = {}
        
    def validate_test_result(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM critique for a single test result."""
        
        # Build prompt for analysis
        prompt = self._build_validation_prompt(test_data)
        
        # Call claude-max-proxy via CLI or direct import
        critique = self._get_llm_critique(prompt)
        
        # Parse the critique
        return self._parse_critique(critique, test_data)
    
    def validate_all_tests(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all test results in a report."""
        
        validations = {}
        tests = test_results.get("tests", [])
        
        print(f"🔍 Validating {len(tests)} tests with {self.model}...")
        
        for test in tests:
            test_name = test.get("nodeid", "unknown")
            validation = self.validate_test_result(test)
            validations[test_name] = validation
            
            # Print progress
            status_icon = "✅" if validation["is_valid"] else "⚠️"
            print(f"  {status_icon} {test_name}: {validation['summary']}")
        
        return {
            "model": self.model,
            "total_tests": len(tests),
            "validations": validations,
            "summary": self._summarize_validations(validations)
        }
    
    def _build_validation_prompt(self, test_data: Dict[str, Any]) -> str:
        """Build prompt for LLM to analyze test result."""
        
        return f"""Analyze this test result for quality issues. Be critical and identify:
1. Hallucinated tests (tests that don't match their description)
2. Incomplete tests (missing important assertions)
3. Lazy tests (superficial validation only)
4. Flaky patterns (timing dependencies, external dependencies)

Test Data:
- Name: {test_data.get('nodeid', 'unknown')}
- Outcome: {test_data.get('outcome', 'unknown')}
- Duration: {test_data.get('duration', 0):.3f}s
- Setup: {test_data.get('setup', {})}
- Call: {test_data.get('call', {})}

{self._extract_test_details(test_data)}

Provide a JSON response with:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "severity": "low/medium/high",
    "category": "good/incomplete/lazy/hallucinated/flaky",
    "suggestions": ["improvement1", "improvement2"],
    "summary": "one-line summary"
}}"""

    def _extract_test_details(self, test_data: Dict[str, Any]) -> str:
        """Extract relevant test details for analysis."""
        
        details = []
        
        # Get stdout/stderr if available
        if "call" in test_data and "stdout" in test_data["call"]:
            details.append(f"Stdout: {test_data['call']['stdout'][:500]}")
        
        # Get error info if test failed
        if test_data.get("outcome") == "failed":
            if "call" in test_data and "longrepr" in test_data["call"]:
                details.append(f"Error: {test_data['call']['longrepr'][:500]}")
        
        # Get test docstring if available
        if "metadata" in test_data:
            details.append(f"Metadata: {json.dumps(test_data['metadata'])}")
            
        return "\n".join(details) if details else "No additional details available"
    
    def _get_llm_critique(self, prompt: str) -> str:
        """Get critique from LLM via claude-max-proxy."""
        
        try:
            # Try direct import first
            if not HAS_LLM_CALL:
                raise ImportError("llm_call not available")
            
            client = LLMClient()
            response = client.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}
            )
            return response["content"]
            
        except ImportError:
            # Fall back to CLI
            cmd = [
                "python", "-m", "llm_call.cli.main",
                "ask",
                "--model", self.model,
                "--prompt", prompt,
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Warning: LLM call failed: {result.stderr}")
                return json.dumps({
                    "is_valid": True,
                    "confidence": 0.5,
                    "issues": ["Could not validate with LLM"],
                    "severity": "low",
                    "category": "unknown",
                    "suggestions": [],
                    "summary": "LLM validation unavailable"
                })
            
            return result.stdout
    
    def _parse_critique(self, critique: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM critique response."""
        
        try:
            result = json.loads(critique)
            
            # Add test info
            result["test_name"] = test_data.get("nodeid", "unknown")
            result["test_outcome"] = test_data.get("outcome", "unknown")
            result["test_duration"] = test_data.get("duration", 0)
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if LLM response isn't valid JSON
            return {
                "is_valid": True,
                "confidence": 0.5,
                "issues": ["Could not parse LLM response"],
                "severity": "low", 
                "category": "unknown",
                "suggestions": [],
                "summary": "Parse error in LLM response",
                "test_name": test_data.get("nodeid", "unknown"),
                "test_outcome": test_data.get("outcome", "unknown"),
                "test_duration": test_data.get("duration", 0)
            }
    
    def _summarize_validations(self, validations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize all validation results."""
        
        categories = {}
        severities = {}
        total_issues = 0
        
        for test_name, validation in validations.items():
            # Count categories
            category = validation.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            # Count severities
            severity = validation.get("severity", "low")
            severities[severity] = severities.get(severity, 0) + 1
            
            # Count issues
            total_issues += len(validation.get("issues", []))
        
        return {
            "categories": categories,
            "severities": severities,
            "total_issues": total_issues,
            "problematic_tests": [
                name for name, val in validations.items() 
                if not val.get("is_valid", True)
            ]
        }


class TestValidationReporter:
    """Generates reports with LLM validation included."""
    
    def __init__(self, base_reporter, validator: Optional[TestValidator] = None):
        self.base_reporter = base_reporter
        self.validator = validator or TestValidator()
    
    def generate_validated_report(
        self,
        test_results: Dict[str, Any],
        output_path: str = "validated_test_report.html"
    ) -> str:
        """Generate report with validation results included."""
        
        # Get validation results
        validation_results = self.validator.validate_all_tests(test_results)
        
        # Add validation to test results
        test_results["validation"] = validation_results
        
        # Generate enhanced report
        return self.base_reporter.generate_report(test_results, format="html")
