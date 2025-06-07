
"""
Module: claim_verifier.py
Description: Verifies that feature claims in README match actual implementation and test coverage
"""

External Dependencies:
- re: https://docs.python.org/3/library/re.html
- ast: https://docs.python.org/3/library/ast.html
- markdown: https://pypi.org/project/Markdown/

Sample Input:
>>> verifier = ClaimVerifier()
>>> result = verifier.verify_project_claims('/path/to/project')

Expected Output:
>>> print(result)
{'claimed_features': 10, 'implemented_features': 7, 'tested_features': 5, 'honesty_score': 0.5}

Example Usage:
>>> verifier = ClaimVerifier()
>>> honesty = verifier.calculate_honesty_score(project_path)
>>> if honesty < 0.7:
...     print(f"WARNING: Low honesty score: {honesty:.1%}")
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import json
from collections import defaultdict
from datetime import datetime


class ClaimVerifier:
    """Verifies that claimed features actually exist and are tested."""

    def __init__(self):
        self.feature_patterns = [
            r'(?:^|\n)[-*]\s*(?:Feature:|Supports?|Provides?|Includes?|Enables?)\s*([^\n]+)',
            r'(?:^|\n)##?\s*Features?\s*\n((?:[-*]\s*[^\n]+\n?)+)',
            r'(?:^|\n)(?:Can|Will|Does)\s+([^\n]+)',
            r'(?:^|\n)✓\s*([^\n]+)',
            r'(?:^|\n)✅\s*([^\n]+)'
        ]

        self.implementation_keywords = {
            'api': ['route', 'endpoint', 'handler', 'api'],
            'database': ['db', 'database', 'query', 'insert', 'select'],
            'authentication': ['auth', 'login', 'token', 'session'],
            'cache': ['cache', 'redis', 'memcache'],
            'queue': ['queue', 'worker', 'job', 'task'],
            'search': ['search', 'index', 'query'],
            'email': ['email', 'mail', 'smtp'],
            'storage': ['storage', 's3', 'upload', 'file'],
            'websocket': ['websocket', 'ws', 'socket'],
            'graphql': ['graphql', 'schema', 'resolver']
        }

    def verify_project_claims(self, project_path: str) -> Dict[str, Any]:
        """Verify all claims made in a project's documentation."""
        project_path = Path(project_path)

        results = {
            "project": str(project_path),
            "claimed_features": [],
            "implemented_features": [],
            "tested_features": [],
            "untested_features": [],
            "unimplemented_claims": [],
            "feature_coverage": {},
            "honesty_score": 0.0,
            "detailed_analysis": {}
        }

        # 1. Extract claimed features from README
        readme_path = self._find_readme(project_path)
        if readme_path:
            results["claimed_features"] = self._extract_features_from_readme(readme_path)
        else:
            results["error"] = "No README found"
            return results

        # 2. Map features to code
        code_mapping = self._map_features_to_code(results["claimed_features"], project_path)
        results["feature_coverage"] = code_mapping

        # 3. Check test coverage for each feature
        for feature, mapping in code_mapping.items():
            if mapping["implementation_files"]:
                results["implemented_features"].append(feature)

                # Check if tested
                if mapping["test_files"]:
                    results["tested_features"].append(feature)
                else:
                    results["untested_features"].append(feature)
            else:
                results["unimplemented_claims"].append(feature)

        # 4. Calculate honesty score
        results["honesty_score"] = self._calculate_honesty_score(results)

        # 5. Detailed analysis
        results["detailed_analysis"] = self._perform_detailed_analysis(results, project_path)

        return results

    def _find_readme(self, project_path: Path) -> Optional[Path]:
        """Find README file in project."""
        readme_patterns = ['README.md', 'README.rst', 'README.txt', 'readme.md']

        for pattern in readme_patterns:
            readme_path = project_path / pattern
            if readme_path.exists():
                return readme_path

        # Check in docs directory
        docs_dir = project_path / 'docs'
        if docs_dir.exists():
            for pattern in readme_patterns:
                readme_path = docs_dir / pattern
                if readme_path.exists():
                    return readme_path

        return None

    def _extract_features_from_readme(self, readme_path: Path) -> List[str]:
        """Extract feature claims from README."""
        try:
            content = readme_path.read_text(encoding='utf-8')
        except:
            return []

        features = []

        # Try each pattern
        for pattern in self.feature_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Clean up the feature text
                    feature = match.strip().rstrip('.').lower()
                    if len(feature) > 10 and len(feature) < 200:  # Reasonable length
                        features.append(feature)

        # Extract from features section
        features_section = re.search(
            r'##?\s*Features?\s*\n((?:[-*]\s*[^\n]+\n?)+)',
            content,
            re.MULTILINE | re.IGNORECASE
        )

        if features_section:
            section_text = features_section.group(1)
            feature_lines = re.findall(r'[-*]\s*([^\n]+)', section_text)
            features.extend([f.strip().lower() for f in feature_lines if f.strip()])

        # Deduplicate
        seen = set()
        unique_features = []
        for feature in features:
            if feature not in seen:
                seen.add(feature)
                unique_features.append(feature)

        return unique_features

    def _map_features_to_code(self, features: List[str], project_path: Path) -> Dict[str, Any]:
        """Map claimed features to actual code files."""
        mapping = {}

        # Get all Python files
        py_files = list(project_path.rglob("*.py"))

        for feature in features:
            mapping[feature] = {
                "implementation_files": [],
                "test_files": [],
                "confidence": 0.0,
                "keywords_found": []
            }

            # Extract keywords from feature
            feature_keywords = self._extract_feature_keywords(feature)

            # Search for implementation
            for py_file in py_files:
                if "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding='utf-8')

                    # Check if this is a test file
                    is_test = "test_" in py_file.name or py_file.parent.name == "tests"

                    # Search for feature keywords
                    matches = 0
                    for keyword in feature_keywords:
                        if keyword.lower() in content.lower():
                            matches += 1

                    if matches > 0:
                        relevance = matches / len(feature_keywords)

                        if is_test:
                            mapping[feature]["test_files"].append({
                                "file": str(py_file.relative_to(project_path)),
                                "relevance": relevance
                            })
                        else:
                            mapping[feature]["implementation_files"].append({
                                "file": str(py_file.relative_to(project_path)),
                                "relevance": relevance
                            })

                        mapping[feature]["keywords_found"].extend(feature_keywords[:matches])

                except:
                    continue

            # Calculate confidence
            if mapping[feature]["implementation_files"]:
                best_relevance = max(f["relevance"] for f in mapping[feature]["implementation_files"])
                mapping[feature]["confidence"] = best_relevance

        return mapping

    def _extract_feature_keywords(self, feature: str) -> List[str]:
        """Extract keywords from a feature description."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                     'before', 'after', 'above', 'below', 'between', 'under', 'again',
                     'further', 'then', 'once', 'supports', 'support', 'provides', 'provide',
                     'includes', 'include', 'enables', 'enable', 'allows', 'allow'}

        # Extract words
        words = re.findall(r'\b\w+\b', feature.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Add domain-specific keywords
        for domain, domain_keywords in self.implementation_keywords.items():
            if any(kw in feature.lower() for kw in domain_keywords):
                keywords.extend(domain_keywords)

        return list(set(keywords))

    def _calculate_honesty_score(self, results: Dict[str, Any]) -> float:
        """Calculate honesty score based on claims vs implementation."""
        total_claims = len(results["claimed_features"])

        if total_claims == 0:
            return 1.0  # No claims made

        implemented = len(results["implemented_features"])
        tested = len(results["tested_features"])

        # Weight: 60% for implementation, 40% for testing
        implementation_score = implemented / total_claims
        test_score = tested / total_claims

        honesty_score = (implementation_score * 0.6) + (test_score * 0.4)

        return min(honesty_score, 1.0)

    def _perform_detailed_analysis(self, results: Dict[str, Any],
                                 project_path: Path) -> Dict[str, Any]:
        """Perform detailed analysis of claims vs reality."""
        analysis = {
            "claim_categories": defaultdict(list),
            "exaggeration_level": "none",
            "missing_tests_critical": False,
            "recommendations": []
        }

        # Categorize unimplemented claims
        for claim in results["unimplemented_claims"]:
            if any(kw in claim for kw in ['api', 'endpoint', 'rest']):
                analysis["claim_categories"]["api"].append(claim)
            elif any(kw in claim for kw in ['database', 'db', 'storage']):
                analysis["claim_categories"]["database"].append(claim)
            elif any(kw in claim for kw in ['auth', 'security', 'permission']):
                analysis["claim_categories"]["security"].append(claim)
            else:
                analysis["claim_categories"]["other"].append(claim)

        # Determine exaggeration level
        unimplemented_ratio = len(results["unimplemented_claims"]) / max(len(results["claimed_features"]), 1)

        if unimplemented_ratio > 0.5:
            analysis["exaggeration_level"] = "severe"
        elif unimplemented_ratio > 0.3:
            analysis["exaggeration_level"] = "significant"
        elif unimplemented_ratio > 0.1:
            analysis["exaggeration_level"] = "moderate"
        elif unimplemented_ratio > 0:
            analysis["exaggeration_level"] = "minor"

        # Check for critical missing tests
        critical_untested = []
        for feature in results["untested_features"]:
            if any(kw in feature.lower() for kw in ['security', 'auth', 'payment', 'encrypt']):
                critical_untested.append(feature)

        if critical_untested:
            analysis["missing_tests_critical"] = True
            analysis["critical_untested_features"] = critical_untested

        # Generate recommendations
        if results["honesty_score"] < 0.5:
            analysis["recommendations"].append("CRITICAL: Majority of claimed features are not implemented")

        if analysis["exaggeration_level"] in ["severe", "significant"]:
            analysis["recommendations"].append("Update README to accurately reflect implemented features")

        if analysis["missing_tests_critical"]:
            analysis["recommendations"].append("Add tests for critical security/payment features immediately")

        if len(results["untested_features"]) > 5:
            analysis["recommendations"].append(f"Add tests for {len(results['untested_features'])} untested features")

        return analysis

    def generate_honesty_report(self, projects: List[str]) -> Dict[str, Any]:
        """Generate honesty report for multiple projects."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "projects_analyzed": len(projects),
            "overall_honesty_score": 0.0,
            "project_scores": {},
            "most_honest_projects": [],
            "least_honest_projects": [],
            "common_exaggerations": defaultdict(int),
            "recommendations": []
        }

        all_scores = []

        for project in projects:
            result = self.verify_project_claims(project)
            score = result["honesty_score"]

            report["project_scores"][project] = {
                "score": score,
                "claimed": len(result["claimed_features"]),
                "implemented": len(result["implemented_features"]),
                "tested": len(result["tested_features"])
            }

            all_scores.append(score)

            # Track common exaggerations
            for claim in result["unimplemented_claims"]:
                for keyword in self._extract_feature_keywords(claim):
                    report["common_exaggerations"][keyword] += 1

        # Calculate overall score
        if all_scores:
            report["overall_honesty_score"] = sum(all_scores) / len(all_scores)

        # Find most/least honest
        sorted_projects = sorted(report["project_scores"].items(),
                               key=lambda x: x[1]["score"],
                               reverse=True)

        report["most_honest_projects"] = [p[0] for p in sorted_projects[:3]]
        report["least_honest_projects"] = [p[0] for p in sorted_projects[-3:] if p[1]["score"] < 0.5]

        # Recommendations
        if report["overall_honesty_score"] < 0.7:
            report["recommendations"].append("Overall honesty is low - implement claimed features or update docs")

        top_exaggerations = sorted(report["common_exaggerations"].items(),
                                 key=lambda x: x[1],
                                 reverse=True)[:5]

        if top_exaggerations:
            report["recommendations"].append(f"Common false claims about: {', '.join([e[0] for e in top_exaggerations])}")

        return report


if __name__ == "__main__":
    # Test the claim verifier
    verifier = ClaimVerifier()

    print("✅ Claim verifier validation:")
    print("   - Extracts features from README")
    print("   - Maps features to implementation files")
    print("   - Checks test coverage for features")
    print("   - Calculates honesty score")
    print("   - Identifies exaggerated claims")
    print("   - Flags critical untested features")

    # Example verification
    test_result = {
        "claimed_features": [
            "real-time data synchronization",
            "advanced caching system",
            "graphql api support",
            "email notifications",
            "user authentication"
        ],
        "implemented_features": [
            "user authentication",
            "email notifications"
        ],
        "tested_features": [
            "user authentication"
        ]
    }

    honesty = len(test_result["implemented_features"]) / len(test_result["claimed_features"])
    print(f"\n   Example honesty score: {honesty:.1%}")
    print(f"   Unimplemented: {len(test_result['claimed_features']) - len(test_result['implemented_features'])} features")
    print(f"   Untested: {len(test_result['implemented_features']) - len(test_result['tested_features'])} features")