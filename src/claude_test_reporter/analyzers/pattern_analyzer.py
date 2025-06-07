"""
Module: pattern_analyzer.py
Description: Analyzes deception patterns across multiple projects to identify systematic lying

External Dependencies:
- collections: https://docs.python.org/3/library/collections.html
- difflib: https://docs.python.org/3/library/difflib.html
- statistics: https://docs.python.org/3/library/statistics.html

Sample Input:
>>> analyzer = DeceptionPatternAnalyzer()
>>> results = analyzer.analyze_project_patterns([
...     {'project': 'sparta', 'instant_tests': 5, 'mock_score': 0.8},
...     {'project': 'marker', 'instant_tests': 3, 'mock_score': 0.6}
... ])

Expected Output:
>>> print(results)
{'deception_score': 0.7, 'patterns_found': ['excessive_mocking', 'instant_tests'], 'recommendations': [...]}

Example Usage:
>>> analyzer = DeceptionPatternAnalyzer()
>>> patterns = analyzer.find_repeated_patterns(test_results)
>>> if patterns['deception_score'] > 0.5:
...     print(f"WARNING: High deception score: {patterns['deception_score']:.1%}")
"""

from collections import defaultdict, Counter
from difflib import SequenceMatcher
import statistics
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
import json


class DeceptionPatternAnalyzer:
    """Analyzes patterns of deception across projects."""
    
    def __init__(self):
        self.deception_patterns = {
            'instant_tests': 0.3,  # Weight for instant test pattern
            'excessive_mocking': 0.3,  # Weight for mock abuse
            'no_failures': 0.2,  # Weight for suspiciously perfect tests
            'identical_errors': 0.1,  # Weight for copy-pasted errors
            'missing_integration': 0.1  # Weight for no integration tests
        }
        
        self.similarity_threshold = 0.85  # For detecting copy-pasted code
        
    def analyze_project_patterns(self, project_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze deception patterns across multiple projects."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_projects": len(project_results),
            "patterns_found": [],
            "deception_scores": {},
            "overall_deception_score": 0.0,
            "repeated_patterns": {},
            "recommendations": [],
            "high_risk_projects": []
        }
        
        # Analyze each pattern type
        patterns = {
            "instant_test_pattern": self._analyze_instant_test_pattern(project_results),
            "mock_pattern": self._analyze_mock_pattern(project_results),
            "error_pattern": self._analyze_error_patterns(project_results),
            "perfect_test_pattern": self._analyze_perfect_test_pattern(project_results),
            "integration_pattern": self._analyze_integration_pattern(project_results)
        }
        
        # Calculate deception scores per project
        for project in project_results:
            project_name = project.get('project', 'unknown')
            score = self._calculate_project_deception_score(project, patterns)
            analysis["deception_scores"][project_name] = score
            
            if score > 0.7:
                analysis["high_risk_projects"].append({
                    "project": project_name,
                    "score": score,
                    "main_issues": self._identify_main_issues(project, patterns)
                })
                
        # Find repeated patterns
        analysis["repeated_patterns"] = self._find_repeated_patterns(patterns)
        
        # Calculate overall deception score
        if analysis["deception_scores"]:
            analysis["overall_deception_score"] = statistics.mean(
                analysis["deception_scores"].values()
            )
            
        # Identify found patterns
        for pattern_name, pattern_data in patterns.items():
            if pattern_data.get("severity", 0) > 0.5:
                analysis["patterns_found"].append(pattern_name.replace("_pattern", ""))
                
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis, patterns)
        
        return analysis
        
    def _analyze_instant_test_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pattern of tests completing instantly."""
        instant_tests_by_project = {}
        total_instant = 0
        total_tests = 0
        
        for project in results:
            project_name = project.get('project', 'unknown')
            instant = project.get('instant_tests', 0)
            total = project.get('total_tests', 1)
            
            instant_tests_by_project[project_name] = {
                "count": instant,
                "ratio": instant / max(total, 1)
            }
            
            total_instant += instant
            total_tests += total
            
        pattern = {
            "type": "instant_tests",
            "projects_affected": len([p for p in instant_tests_by_project.values() 
                                    if p["count"] > 0]),
            "severity": total_instant / max(total_tests, 1),
            "details": instant_tests_by_project,
            "threshold_violations": [
                p for p, data in instant_tests_by_project.items() 
                if data["ratio"] > 0.3
            ]
        }
        
        return pattern
        
    def _analyze_mock_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pattern of excessive mocking."""
        mock_scores = {}
        integration_with_mocks = 0
        
        for project in results:
            project_name = project.get('project', 'unknown')
            mock_score = project.get('mock_score', 0)
            mock_scores[project_name] = mock_score
            
            # Check if integration tests use mocks
            if project.get('integration_tests_with_mocks', 0) > 0:
                integration_with_mocks += 1
                
        pattern = {
            "type": "excessive_mocking",
            "projects_affected": len([s for s in mock_scores.values() if s > 0.5]),
            "severity": statistics.mean(mock_scores.values()) if mock_scores else 0,
            "integration_tests_mocked": integration_with_mocks,
            "worst_offenders": sorted(
                [(p, s) for p, s in mock_scores.items() if s > 0.7],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
        
        return pattern
        
    def _analyze_error_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find identical error messages across projects."""
        error_messages = defaultdict(list)
        
        for project in results:
            project_name = project.get('project', 'unknown')
            errors = project.get('error_messages', [])
            
            for error in errors:
                # Normalize error message
                normalized = self._normalize_error_message(error)
                error_messages[normalized].append(project_name)
                
        # Find errors that appear in multiple projects
        repeated_errors = {
            error: projects 
            for error, projects in error_messages.items() 
            if len(projects) > 1
        }
        
        pattern = {
            "type": "identical_errors",
            "repeated_count": len(repeated_errors),
            "severity": len(repeated_errors) / max(len(error_messages), 1),
            "examples": list(repeated_errors.items())[:5],
            "most_common": Counter(
                [error for error, projects in repeated_errors.items()]
            ).most_common(3)
        }
        
        return pattern
        
    def _analyze_perfect_test_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze suspiciously perfect test results."""
        perfect_projects = []
        failure_rates = []
        
        for project in results:
            project_name = project.get('project', 'unknown')
            total = project.get('total_tests', 0)
            failed = project.get('failed_tests', 0)
            
            if total > 10:  # Only consider projects with substantial tests
                failure_rate = failed / total
                failure_rates.append(failure_rate)
                
                if failure_rate == 0:
                    perfect_projects.append({
                        "project": project_name,
                        "tests": total
                    })
                    
        # Calculate how unusual perfect tests are
        avg_failure_rate = statistics.mean(failure_rates) if failure_rates else 0.1
        
        pattern = {
            "type": "no_failures",
            "perfect_projects": len(perfect_projects),
            "severity": len(perfect_projects) / max(len(results), 1),
            "average_failure_rate": avg_failure_rate,
            "suspicious_projects": perfect_projects,
            "statistical_anomaly": avg_failure_rate > 0.05 and len(perfect_projects) > 2
        }
        
        return pattern
        
    def _analyze_integration_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze missing integration tests."""
        missing_integration = []
        poor_integration = []
        
        for project in results:
            project_name = project.get('project', 'unknown')
            integration_tests = project.get('integration_tests', 0)
            total_tests = project.get('total_tests', 1)
            
            integration_ratio = integration_tests / total_tests
            
            if integration_tests == 0:
                missing_integration.append(project_name)
            elif integration_ratio < 0.1:
                poor_integration.append({
                    "project": project_name,
                    "ratio": integration_ratio
                })
                
        pattern = {
            "type": "missing_integration",
            "projects_without": missing_integration,
            "projects_with_poor": poor_integration,
            "severity": len(missing_integration) / max(len(results), 1),
            "total_affected": len(missing_integration) + len(poor_integration)
        }
        
        return pattern
        
    def _calculate_project_deception_score(self, project: Dict[str, Any], 
                                         patterns: Dict[str, Any]) -> float:
        """Calculate deception score for a single project."""
        score = 0.0
        project_name = project.get('project', 'unknown')
        
        # Instant tests contribution
        instant_pattern = patterns.get("instant_test_pattern", {})
        if project_name in instant_pattern.get("details", {}):
            ratio = instant_pattern["details"][project_name]["ratio"]
            score += ratio * self.deception_patterns['instant_tests']
            
        # Mock score contribution
        mock_score = project.get('mock_score', 0)
        score += mock_score * self.deception_patterns['excessive_mocking']
        
        # Perfect tests contribution
        if project.get('failed_tests', 0) == 0 and project.get('total_tests', 0) > 10:
            score += self.deception_patterns['no_failures']
            
        # Missing integration contribution
        if project.get('integration_tests', 0) == 0:
            score += self.deception_patterns['missing_integration']
            
        return min(score, 1.0)  # Cap at 1.0
        
    def _identify_main_issues(self, project: Dict[str, Any], 
                            patterns: Dict[str, Any]) -> List[str]:
        """Identify main deception issues for a project."""
        issues = []
        project_name = project.get('project', 'unknown')
        
        # Check instant tests
        instant_pattern = patterns.get("instant_test_pattern", {})
        if project_name in instant_pattern.get("threshold_violations", []):
            issues.append("excessive_instant_tests")
            
        # Check mocking
        if project.get('mock_score', 0) > 0.7:
            issues.append("excessive_mocking")
            
        # Check failures
        if project.get('failed_tests', 0) == 0 and project.get('total_tests', 0) > 10:
            issues.append("suspiciously_perfect")
            
        # Check integration
        if project.get('integration_tests', 0) == 0:
            issues.append("no_integration_tests")
            
        return issues
        
    def _find_repeated_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Find patterns that repeat across multiple projects."""
        repeated = {}
        
        # Check instant test pattern repetition
        instant = patterns.get("instant_test_pattern", {})
        if instant.get("projects_affected", 0) > 3:
            repeated["instant_test_epidemic"] = {
                "affected_projects": instant["projects_affected"],
                "severity": "high",
                "description": "Multiple projects show instant test completion"
            }
            
        # Check mock pattern repetition
        mock = patterns.get("mock_pattern", {})
        if mock.get("projects_affected", 0) > 3:
            repeated["mock_abuse_pattern"] = {
                "affected_projects": mock["projects_affected"],
                "severity": "high",
                "description": "Widespread mock abuse in integration tests"
            }
            
        # Check error repetition
        errors = patterns.get("error_pattern", {})
        if errors.get("repeated_count", 0) > 5:
            repeated["copy_paste_errors"] = {
                "repeated_errors": errors["repeated_count"],
                "severity": "medium",
                "description": "Identical errors suggest copy-pasted test code"
            }
            
        return repeated
        
    def _normalize_error_message(self, error: str) -> str:
        """Normalize error message for comparison."""
        # Remove file paths
        error = re.sub(r'[/\\][\w/\\.-]+\.(py|js|ts)', '<FILE>', error)
        # Remove line numbers
        error = re.sub(r'line \d+', 'line <NUM>', error)
        # Remove memory addresses
        error = re.sub(r'0x[0-9a-fA-F]+', '<ADDR>', error)
        # Remove timestamps
        error = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '<TIME>', error)
        
        return error.strip().lower()
        
    def _generate_recommendations(self, analysis: Dict[str, Any], 
                                patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on patterns found."""
        recommendations = []
        
        # Overall deception score
        if analysis["overall_deception_score"] > 0.7:
            recommendations.append("CRITICAL: Systematic deception detected across multiple projects")
            recommendations.append("Implement mandatory real-time test monitoring")
            
        # Instant tests
        instant = patterns.get("instant_test_pattern", {})
        if instant.get("severity", 0) > 0.3:
            recommendations.append("Force minimum test durations for integration tests (>0.1s)")
            
        # Mocking
        mock = patterns.get("mock_pattern", {})
        if mock.get("integration_tests_mocked", 0) > 2:
            recommendations.append("Ban mocks in integration tests via pre-commit hooks")
            
        # Perfect tests
        perfect = patterns.get("perfect_test_pattern", {})
        if perfect.get("statistical_anomaly", False):
            recommendations.append("Add deliberate failing tests (honeypots) to detect manipulation")
            
        # High-risk projects
        if len(analysis["high_risk_projects"]) > 0:
            projects = [p["project"] for p in analysis["high_risk_projects"]]
            recommendations.append(f"Priority review needed for: {', '.join(projects)}")
            
        return recommendations
        
    def compare_code_similarity(self, file_pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Compare code files for suspicious similarity."""
        similarities = []
        
        for file1, file2 in file_pairs:
            try:
                with open(file1, 'r') as f1, open(file2, 'r') as f2:
                    content1 = f1.read()
                    content2 = f2.read()
                    
                # Calculate similarity
                similarity = SequenceMatcher(None, content1, content2).ratio()
                
                if similarity > self.similarity_threshold:
                    similarities.append({
                        "file1": file1,
                        "file2": file2,
                        "similarity": similarity,
                        "likely_copied": True
                    })
                    
            except Exception as e:
                continue
                
        return {
            "files_compared": len(file_pairs),
            "suspicious_similarities": len(similarities),
            "examples": similarities[:5]
        }


if __name__ == "__main__":
    # Test the pattern analyzer
    analyzer = DeceptionPatternAnalyzer()
    
    # Example project results with deception indicators
    test_results = [
        {
            "project": "sparta",
            "total_tests": 50,
            "failed_tests": 0,  # Suspicious!
            "instant_tests": 15,  # Too many!
            "mock_score": 0.8,  # High mocking
            "integration_tests": 0,  # No integration!
            "error_messages": ["Connection refused", "Timeout error"]
        },
        {
            "project": "marker", 
            "total_tests": 30,
            "failed_tests": 0,  # Also suspicious!
            "instant_tests": 10,
            "mock_score": 0.6,
            "integration_tests": 2,
            "error_messages": ["Connection refused", "Invalid input"]
        },
        {
            "project": "arangodb",
            "total_tests": 40,
            "failed_tests": 3,  # More realistic
            "instant_tests": 2,
            "mock_score": 0.2,
            "integration_tests": 8,
            "error_messages": ["Query failed", "Document not found"]
        }
    ]
    
    patterns = analyzer.analyze_project_patterns(test_results)
    
    print("✅ Pattern analyzer validation:")
    print(f"   Overall deception score: {patterns['overall_deception_score']:.1%}")
    print(f"   Patterns found: {patterns['patterns_found']}")
    print(f"   High-risk projects: {len(patterns['high_risk_projects'])}")
    print("\n   Deception scores by project:")
    for project, score in patterns['deception_scores'].items():
        print(f"      {project}: {score:.1%}")
        
    if patterns['recommendations']:
        print("\n   Recommendations:")
        for rec in patterns['recommendations']:
            print(f"      - {rec}")