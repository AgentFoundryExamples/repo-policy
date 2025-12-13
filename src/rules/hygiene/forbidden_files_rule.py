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
"""Forbidden file pattern detection."""

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class ForbiddenFilesRule(BaseRule):
    """Detect files matching forbidden patterns."""
    
    rule_id = "forbidden-files"
    default_severity = RuleSeverity.WARNING
    rule_tags = ["hygiene", "cleanup"]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate forbidden files."""
        if not self.facts.forbidden_files:
            return self._create_pass_result(
                message="No forbidden files found",
                evidence={
                    "forbidden_count": 0,
                },
            )
        
        # Limit displayed files to avoid overwhelming output
        max_display = 20
        forbidden_count = len(self.facts.forbidden_files)
        displayed_files = self.facts.forbidden_files[:max_display]
        truncated = forbidden_count > max_display
        
        file_list = "\n".join(f"  - {f}" for f in displayed_files)
        if truncated:
            file_list += f"\n  ... and {forbidden_count - max_display} more files"
        
        return self._create_fail_result(
            message=f"Found {forbidden_count} forbidden file(s)",
            evidence={
                "forbidden_count": forbidden_count,
                "forbidden_files": [str(f) for f in self.facts.forbidden_files],
                "patterns_checked": [
                    "**/.DS_Store",
                    "**/Thumbs.db",
                    "**/*.swp",
                    "**/*.bak",
                    "**/*~",
                ],
            },
            remediation=(
                f"Remove or add to .gitignore the following files:\n{file_list}\n\n"
                "These files are typically:\n"
                "  - OS-specific (e.g., .DS_Store, Thumbs.db)\n"
                "  - Editor temporaries (e.g., *.swp, *~)\n"
                "  - Backup files (e.g., *.bak)\n\n"
                "Add patterns to your .gitignore to prevent them from being committed."
            ),
        )
