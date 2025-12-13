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
"""Large and binary file detection."""

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class FileSizeRule(BaseRule):
    """Detect large files and binary files exceeding thresholds."""
    
    rule_id = "file-size-limit"
    default_severity = RuleSeverity.WARNING
    rule_tags = ["hygiene", "performance"]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate file size constraints."""
        issues = []
        evidence = {
            "large_files_count": len(self.facts.large_files),
            "binary_files_count": len(self.facts.binary_files),
        }
        
        # Check large files
        if self.facts.large_files:
            max_display = 10
            displayed_large = self.facts.large_files[:max_display]
            truncated_large = len(self.facts.large_files) > max_display
            
            large_list = "\n".join(
                f"  - {f['path']} ({f['size_mb']:.2f} MB)"
                for f in displayed_large
            )
            if truncated_large:
                large_list += f"\n  ... and {len(self.facts.large_files) - max_display} more files"
            
            issues.append(
                f"Large files (>10MB):\n{large_list}"
            )
            evidence["large_files"] = self.facts.large_files
        
        # Check binary files (informational, not necessarily a problem)
        if self.facts.binary_files:
            max_display_binary = 10
            displayed_binary = self.facts.binary_files[:max_display_binary]
            truncated_binary = len(self.facts.binary_files) > max_display_binary
            
            binary_list = "\n".join(f"  - {f}" for f in displayed_binary)
            if truncated_binary:
                binary_list += f"\n  ... and {len(self.facts.binary_files) - max_display_binary} more files"
            
            # Binary files are informational, not necessarily bad
            evidence["binary_files"] = [str(f) for f in self.facts.binary_files]
        
        if issues:
            return self._create_fail_result(
                message=f"Found {len(self.facts.large_files)} large file(s) and {len(self.facts.binary_files)} binary file(s)",
                evidence=evidence,
                remediation=(
                    "\n\n".join(issues) + "\n\n"
                    "Consider:\n"
                    "  - Using Git LFS for large binary files\n"
                    "  - Storing large assets externally (CDN, cloud storage)\n"
                    "  - Adding large files to .gitignore if they're build artifacts\n"
                    "  - Splitting large files or compressing them\n\n"
                    "Binary files are tracked for awareness; they're not always a problem "
                    "but can slow down repository operations."
                ),
            )
        
        return self._create_pass_result(
            message="No large files found",
            evidence=evidence,
        )
