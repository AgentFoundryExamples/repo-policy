"""CI workflow detection and test heuristics."""

import re
from pathlib import Path
from typing import List, Optional

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class CiRule(BaseRule):
    """Verify CI workflow presence and test execution."""
    
    rule_id = "ci-required"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["hygiene", "ci", "testing"]
    
    # Test command patterns to search for in CI workflows
    TEST_PATTERNS = [
        r'\bpytest\b',
        r'\btest\b',
        r'\bmake\s+test\b',
        r'\bnpm\s+test\b',
        r'\bnpm\s+run\s+test\b',
        r'\byarn\s+test\b',
        r'\bgo\s+test\b',
        r'\bcargo\s+test\b',
        r'\bmvn\s+test\b',
        r'\bgradle\s+test\b',
        r'\btox\b',
        r'\bcoverage\b',
        r'\bjest\b',
        r'\bmocha\b',
        r'\bjunit\b',
    ]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate CI requirements."""
        # Check if CI workflows exist
        if not self.facts.has_ci or not self.facts.ci_workflow_files:
            return self._create_fail_result(
                message="No CI workflow files found",
                evidence={
                    "has_ci": False,
                    "workflow_dir": ".github/workflows",
                    "checked_extensions": [".yml", ".yaml"],
                },
                remediation=(
                    "Add a CI workflow to .github/workflows/ directory.\n"
                    "Example: .github/workflows/ci.yml\n\n"
                    "Basic GitHub Actions workflow:\n"
                    "name: CI\n"
                    "on: [push, pull_request]\n"
                    "jobs:\n"
                    "  test:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - uses: actions/checkout@v3\n"
                    "      - name: Run tests\n"
                    "        run: pytest  # or your test command"
                ),
            )
        
        # Scan workflows for test execution patterns
        test_info = self._scan_workflows_for_tests()
        
        # Check if tests are detected
        if not test_info["has_test_commands"]:
            # This is a warning when tests aren't detected (heuristic check)
            # Default to WARNING severity, but can be overridden via rules.severity_overrides
            from rules.result import RuleStatus
            
            return RuleResult(
                rule_id=self.rule_id,
                severity=RuleSeverity.WARNING,  # Always WARNING for heuristic failures
                status=RuleStatus.WARN,
                message=f"CI workflows found but no test commands detected (heuristic check)",
                evidence={
                    "has_ci": True,
                    "workflow_files": [str(f) for f in self.facts.ci_workflow_files],
                    "has_test_commands": False,
                    "scanned_patterns": self.TEST_PATTERNS,
                },
                remediation=(
                    "Ensure your CI workflows run tests. Common test commands:\n"
                    "  Python: pytest, python -m unittest, tox\n"
                    "  JavaScript: npm test, yarn test, jest\n"
                    "  Go: go test\n"
                    "  Rust: cargo test\n"
                    "  Java: mvn test, gradle test\n\n"
                    "If tests are running but not detected, this is a heuristic warning "
                    "that can be safely ignored or the rule can be excluded."
                ),
                rule_tags=self.rule_tags,
            )
        
        return self._create_pass_result(
            message=f"CI workflows found with test execution: {len(self.facts.ci_workflow_files)} workflow(s)",
            evidence={
                "has_ci": True,
                "workflow_files": [str(f) for f in self.facts.ci_workflow_files],
                "has_test_commands": True,
                "detected_test_patterns": test_info["detected_patterns"],
                "workflows_with_tests": test_info["workflows_with_tests"],
            },
        )
    
    
    def _scan_workflows_for_tests(self) -> dict:
        """
        Scan CI workflow files for test command patterns.
        
        Returns:
            dict with has_test_commands, detected_patterns, workflows_with_tests
        """
        detected_patterns = []
        workflows_with_tests = []
        
        for workflow_path in self.facts.ci_workflow_files:
            full_path = self.target_path / workflow_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                
                # Check for test patterns
                found_patterns = []
                for pattern in self.TEST_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        pattern_name = pattern.replace(r'\b', '').replace(r'\s+', ' ')
                        if pattern_name not in found_patterns:
                            found_patterns.append(pattern_name)
                
                if found_patterns:
                    workflows_with_tests.append(str(workflow_path))
                    detected_patterns.extend(found_patterns)
            
            except Exception as e:
                from logging import getLogger
                getLogger(__name__).warning(f"Failed to read workflow {workflow_path}: {e}")
                continue
        
        # Remove duplicates from detected patterns
        detected_patterns = list(set(detected_patterns))
        
        return {
            "has_test_commands": len(detected_patterns) > 0,
            "detected_patterns": detected_patterns,
            "workflows_with_tests": workflows_with_tests,
        }
