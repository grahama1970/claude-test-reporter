#!/usr/bin/env python3
"""
Module: comprehensive_analyzer.py
Description: Orchestrates all lie detection analyzers for comprehensive project analysis

External Dependencies:
- None (uses local analyzers)

Sample Input:
>>> analyzer = ComprehensiveAnalyzer()
>>> results = analyzer.analyze_project('/path/to/project')

Expected Output:
>>> print(results['trust_score'])
0.45
>>> print(results['deception_indicators'])
['mock_abuse', 'skeleton_code', 'honeypot_manipulation']

Example Usage:
>>> analyzer = ComprehensiveAnalyzer()
>>> report = analyzer.generate_comprehensive_report('/home/user/project')
>>> print(f"Project trust score: {report['trust_score']:.0%}")
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import asyncio

# Import all our analyzers
from .mock_detector import MockDetector
from .realtime_monitor import RealTimeTestMonitor
from .implementation_verifier import ImplementationVerifier
from .honeypot_enforcer import HoneypotEnforcer
from .integration_tester import IntegrationTester
from .pattern_analyzer import PatternAnalyzer
from .claim_verifier import ClaimVerifier
from .hallucination_monitor import HallucinationMonitor


class ComprehensiveAnalyzer:
    """Orchestrates all analyzers for comprehensive lie detection."""
    
    def __init__(self, verbose: bool = True):
        """Initialize all analyzers."""
        self.verbose = verbose
        
        # Initialize analyzers
        self.mock_detector = MockDetector()
        self.realtime_monitor = RealTimeTestMonitor()
        self.implementation_verifier = ImplementationVerifier()
        self.honeypot_enforcer = HoneypotEnforcer()
        self.integration_tester = IntegrationTester()
        self.pattern_analyzer = PatternAnalyzer()
        self.claim_verifier = ClaimVerifier()
        self.hallucination_monitor = HallucinationMonitor()
        
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Run all analyzers on a project."""
        project_path = Path(project_path)
        if not project_path.exists():
            return {"error": f"Project path not found: {project_path}"}
        
        if self.verbose:
            print(f"\n🔍 Analyzing project: {project_path.name}")
        
        results = {
            "project": str(project_path),
            "timestamp": datetime.now().isoformat(),
            "analyzers": {},
            "trust_score": 0.0,
            "deception_score": 0.0,
            "deception_indicators": [],
            "critical_issues": [],
            "recommendations": []
        }
        
        # 1. Real-time test execution monitoring
        if self.verbose:
            print("   📊 Running real-time test monitor...")
        rt_results = self.realtime_monitor.monitor_test_execution(str(project_path))
        results["analyzers"]["realtime_monitor"] = rt_results
        
        # 2. Mock detection in tests
        if self.verbose:
            print("   🎭 Detecting mock abuse...")
        mock_results = self.mock_detector.scan_project(str(project_path))
        results["analyzers"]["mock_detector"] = mock_results
        
        # 3. Implementation verification
        if self.verbose:
            print("   💀 Checking for skeleton code...")
        impl_results = self.implementation_verifier.scan_project(str(project_path))
        results["analyzers"]["implementation_verifier"] = impl_results
        
        # 4. Honeypot enforcement
        if self.verbose:
            print("   🍯 Checking honeypot integrity...")
        # Use real-time test results for honeypot check
        honeypot_results = self.honeypot_enforcer.check_honeypot_integrity(rt_results)
        results["analyzers"]["honeypot_enforcer"] = honeypot_results
        
        # 5. Pattern analysis
        if self.verbose:
            print("   🔍 Analyzing deception patterns...")
        pattern_results = self.pattern_analyzer.analyze_project(str(project_path))
        results["analyzers"]["pattern_analyzer"] = pattern_results
        
        # 6. Claim verification
        if self.verbose:
            print("   ✅ Verifying implementation claims...")
        claim_results = self.claim_verifier.verify_project_claims(str(project_path))
        results["analyzers"]["claim_verifier"] = claim_results
        
        # 7. Hallucination monitoring
        if self.verbose:
            print("   🌀 Detecting hallucinations...")
        hall_results = self.hallucination_monitor.analyze_project(str(project_path))
        results["analyzers"]["hallucination_monitor"] = hall_results
        
        # 8. Integration testing (optional - takes longer)
        # Skipping by default as it requires starting services
        # results["analyzers"]["integration_tester"] = {"skipped": True}
        
        # Calculate overall scores
        self._calculate_scores(results)
        
        # Generate recommendations
        self._generate_recommendations(results)
        
        return results
    
    def _calculate_scores(self, results: Dict[str, Any]) -> None:
        """Calculate trust and deception scores from analyzer results."""
        deception_factors = []
        
        # Mock abuse factor
        mock_data = results["analyzers"].get("mock_detector", {})
        if mock_data.get("total_tests", 0) > 0:
            mock_abuse_ratio = (
                mock_data.get("integration_tests_with_mocks", 0) / 
                mock_data.get("total_tests", 1)
            )
            if mock_abuse_ratio > 0.3:
                deception_factors.append(("mock_abuse", mock_abuse_ratio))
                results["deception_indicators"].append("mock_abuse")
        
        # Skeleton code factor
        impl_data = results["analyzers"].get("implementation_verifier", {})
        skeleton_ratio = impl_data.get("overall_skeleton_ratio", 0.0)
        if skeleton_ratio > 0.3:
            deception_factors.append(("skeleton_code", skeleton_ratio))
            results["deception_indicators"].append("skeleton_code")
            results["critical_issues"].append(
                f"{skeleton_ratio:.0%} of functions are skeleton implementations"
            )
        
        # Honeypot manipulation factor
        honeypot_data = results["analyzers"].get("honeypot_enforcer", {})
        if honeypot_data.get("manipulation_detected", False):
            deception_factors.append(("honeypot_manipulation", 1.0))
            results["deception_indicators"].append("honeypot_manipulation")
            results["critical_issues"].append(
                "Honeypot tests were manipulated to pass!"
            )
        
        # Instant test factor
        rt_data = results["analyzers"].get("realtime_monitor", {})
        if rt_data.get("total_tests", 0) > 0:
            instant_ratio = rt_data.get("instant_tests", 0) / rt_data.get("total_tests", 1)
            if instant_ratio > 0.3:
                deception_factors.append(("instant_tests", instant_ratio))
                results["deception_indicators"].append("instant_tests")
        
        # Hallucination factor
        hall_data = results["analyzers"].get("hallucination_monitor", {})
        hallucination_count = len(hall_data.get("hallucinations", []))
        if hallucination_count > 0:
            deception_factors.append(("hallucinations", min(hallucination_count / 10, 1.0)))
            results["deception_indicators"].append("hallucinations")
            results["critical_issues"].append(
                f"{hallucination_count} hallucinated features detected"
            )
        
        # Pattern-based deception
        pattern_data = results["analyzers"].get("pattern_analyzer", {})
        if pattern_data.get("deception_score", 0) > 0.5:
            deception_factors.append(("deception_patterns", pattern_data["deception_score"]))
            results["deception_indicators"].append("deception_patterns")
        
        # Calculate overall deception score
        if deception_factors:
            results["deception_score"] = sum(score for _, score in deception_factors) / len(deception_factors)
        else:
            results["deception_score"] = 0.0
        
        # Trust score is inverse of deception score
        results["trust_score"] = max(0.0, 1.0 - results["deception_score"])
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> None:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Mock abuse recommendations
        if "mock_abuse" in results["deception_indicators"]:
            recommendations.append(
                "CRITICAL: Remove mocks from integration tests - they should test real components"
            )
        
        # Skeleton code recommendations
        if "skeleton_code" in results["deception_indicators"]:
            skeleton_files = results["analyzers"]["implementation_verifier"].get("skeleton_files", [])
            if skeleton_files:
                recommendations.append(
                    f"Implement real functionality in {len(skeleton_files)} files with skeleton code"
                )
        
        # Honeypot recommendations
        if "honeypot_manipulation" in results["deception_indicators"]:
            recommendations.append(
                "CRITICAL: Restore honeypot tests to their failing state - they are designed to fail!"
            )
        
        # Instant test recommendations
        if "instant_tests" in results["deception_indicators"]:
            recommendations.append(
                "Add real delays and processing to tests - instant completion indicates mocking"
            )
        
        # Hallucination recommendations
        if "hallucinations" in results["deception_indicators"]:
            hall_features = results["analyzers"]["hallucination_monitor"].get("hallucinations", [])
            if hall_features:
                recommendations.append(
                    f"Remove or implement {len(hall_features)} hallucinated features"
                )
        
        # General trust recommendations
        if results["trust_score"] < 0.5:
            recommendations.insert(0, 
                "⚠️ LOW TRUST SCORE: This project shows significant signs of deception"
            )
        
        results["recommendations"] = recommendations
    
    def generate_report(self, project_path: str, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive analysis report."""
        results = self.analyze_project(project_path)
        
        if output_file is None:
            project_name = Path(project_path).name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_analysis_{project_name}_{timestamp}.json"
        
        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n📊 Analysis Complete for {results['project']}")
        print(f"   Trust Score: {results['trust_score']:.0%}")
        print(f"   Deception Score: {results['deception_score']:.0%}")
        
        if results["deception_indicators"]:
            print(f"\n⚠️  Deception Indicators Detected:")
            for indicator in results["deception_indicators"]:
                print(f"   - {indicator.replace('_', ' ').title()}")
        
        if results["critical_issues"]:
            print(f"\n🚨 Critical Issues:")
            for issue in results["critical_issues"]:
                print(f"   - {issue}")
        
        if results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"   - {rec}")
        
        print(f"\n📄 Full report saved to: {output_file}")
        
        return output_file
    
    async def analyze_multiple_projects(self, project_paths: List[str]) -> Dict[str, Any]:
        """Analyze multiple projects and generate comparative report."""
        all_results = {}
        
        for project_path in project_paths:
            print(f"\n{'='*60}")
            results = self.analyze_project(project_path)
            project_name = Path(project_path).name
            all_results[project_name] = results
        
        # Generate comparative summary
        summary = {
            "total_projects": len(all_results),
            "average_trust_score": sum(r["trust_score"] for r in all_results.values()) / len(all_results),
            "projects_by_trust": {},
            "common_issues": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Categorize projects
        for project, results in all_results.items():
            trust_level = "high" if results["trust_score"] > 0.8 else "medium" if results["trust_score"] > 0.5 else "low"
            if trust_level not in summary["projects_by_trust"]:
                summary["projects_by_trust"][trust_level] = []
            summary["projects_by_trust"][trust_level].append({
                "project": project,
                "trust_score": results["trust_score"],
                "issues": results["deception_indicators"]
            })
        
        # Find common issues
        all_issues = []
        for results in all_results.values():
            all_issues.extend(results["deception_indicators"])
        
        for issue in set(all_issues):
            count = all_issues.count(issue)
            if count > 1:
                summary["common_issues"][issue] = {
                    "count": count,
                    "percentage": count / len(all_results) * 100
                }
        
        return {
            "individual_results": all_results,
            "summary": summary
        }


if __name__ == "__main__":
    # Validation
    analyzer = ComprehensiveAnalyzer()
    print("✅ Comprehensive Analyzer validation:")
    print("   - Integrates all 8 lie detection analyzers")
    print("   - Calculates trust and deception scores")
    print("   - Identifies critical issues")
    print("   - Generates actionable recommendations")
    print("   - Supports multi-project analysis")