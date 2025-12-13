# Copyright 2025 John Brosnihan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests vs sources linkage rule."""

from typing import Optional

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class TestsVsSourcesRule(BaseRule):
    """Verify tests exist when sources are present."""
    
    rule_id = "tests-required-with-sources"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["tests", "quality"]
    
    def _check_preconditions(self) -> Optional[RuleResult]:
        """Check if tests are required based on configuration and repo type."""
        # Check if tests are explicitly disabled
        tests_config = getattr(self.config.rules, "tests_required_if_sources_present", True)
        if not isinstance(tests_config, bool):
            tests_config = True
        
        if not tests_config:
            return self._create_skip_result(
                message="Tests requirement disabled (tests_required_if_sources_present: false)",
                evidence={
                    "tests_required": False,
                },
            )
        
        # Check repo_type tag
        repo_type = self.facts.repo_tags.get("repo_type", "").lower()
        if repo_type in ["docs", "documentation", "config"]:
            return self._create_skip_result(
                message=f"Tests not required for repo_type: {repo_type}",
                evidence={
                    "repo_type": repo_type,
                    "tests_required": False,
                },
            )
        
        # Skip if no source files found
        if not self.facts.source_files:
            return self._create_skip_result(
                message="No source files found (nothing to test)",
                evidence={
                    "source_count": 0,
                    "source_patterns": self.config.globs.source,
                },
            )
        
        # Skip if no languages detected (no code repository)
        if not self.facts.detected_languages:
            return self._create_skip_result(
                message="No programming languages detected (no language markers)",
                evidence={
                    "detected_languages": [],
                },
            )
        
        return None
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate tests vs sources requirement."""
        source_count = len(self.facts.source_files)
        test_count = len(self.facts.test_files)
        
        if test_count == 0:
            languages_str = ", ".join(sorted(self.facts.detected_languages))
            
            return self._create_fail_result(
                message=f"No test files found despite {source_count} source file(s)",
                evidence={
                    "source_count": source_count,
                    "test_count": 0,
                    "source_patterns": self.config.globs.source,
                    "test_patterns": self.config.globs.test,
                    "detected_languages": list(self.facts.detected_languages),
                    "searched_patterns": {
                        "sources": self.config.globs.source,
                        "tests": self.config.globs.test,
                    },
                },
                remediation=(
                    f"Add tests for your source code.\n\n"
                    f"Detected languages: {languages_str}\n"
                    f"Source files: {source_count}\n"
                    f"Test files: 0\n\n"
                    f"Test file patterns searched:\n" +
                    "\n".join(f"  - {pattern}" for pattern in self.config.globs.test) +
                    "\n\n"
                    "To disable this rule, set in config:\n"
                    "rules:\n"
                    "  tests_required_if_sources_present: false\n\n"
                    "Or set repo_type to 'docs' or 'config' if tests aren't applicable."
                ),
            )
        
        # Tests found - check ratio (informational)
        test_ratio = test_count / source_count if source_count > 0 else 0
        
        return self._create_pass_result(
            message=f"Tests found: {test_count} test file(s) for {source_count} source file(s) (ratio: {test_ratio:.2f})",
            evidence={
                "source_count": source_count,
                "test_count": test_count,
                "test_ratio": round(test_ratio, 2),
                "detected_languages": list(self.facts.detected_languages),
            },
        )
