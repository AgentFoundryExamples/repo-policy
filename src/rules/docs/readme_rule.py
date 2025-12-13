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
"""README file and section requirements."""

import re
from typing import List

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class ReadmeRule(BaseRule):
    """Verify README file presence and required sections."""
    
    rule_id = "readme-required"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["docs", "documentation"]
    
    # Default required sections (can be overridden in config)
    DEFAULT_REQUIRED_SECTIONS = [
        "Installation",
        "Usage",
        "License",
    ]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate README requirements."""
        # Check if README exists
        if not self.facts.has_readme:
            return self._create_fail_result(
                message="README file is missing",
                evidence={
                    "has_readme": False,
                    "checked_names": ["README.md", "README.rst", "README.txt", "README"],
                },
                remediation=(
                    "Create a README.md file in the repository root with:\n"
                    "- Project description\n"
                    "- Installation instructions\n"
                    "- Usage examples\n"
                    "- License information"
                ),
            )
        
        # Check for required sections
        required_sections = self._get_required_sections()
        if not required_sections:
            # No sections required, just check presence
            return self._create_pass_result(
                message=f"README file found: {self.facts.readme_path}",
                evidence={
                    "has_readme": True,
                    "readme_path": str(self.facts.readme_path),
                },
            )
        
        # Find sections in README
        missing_sections = self._find_missing_sections(required_sections)
        
        if missing_sections:
            return self._create_fail_result(
                message=f"README is missing required sections: {', '.join(missing_sections)}",
                evidence={
                    "has_readme": True,
                    "readme_path": str(self.facts.readme_path),
                    "required_sections": required_sections,
                    "missing_sections": missing_sections,
                },
                remediation=(
                    f"Add the following sections to {self.facts.readme_path}:\n" +
                    "\n".join(f"- {section}" for section in missing_sections)
                ),
            )
        
        return self._create_pass_result(
            message=f"README file found with all required sections: {self.facts.readme_path}",
            evidence={
                "has_readme": True,
                "readme_path": str(self.facts.readme_path),
                "required_sections": required_sections,
            },
        )
    
    def _get_required_sections(self) -> List[str]:
        """Get required sections from config or use defaults."""
        # Check if config has readme section requirements
        readme_config = getattr(self.config.rules, "readme_required_sections", None)
        if readme_config is not None:
            return readme_config if isinstance(readme_config, list) else []
        return self.DEFAULT_REQUIRED_SECTIONS
    
    def _find_missing_sections(self, required_sections: List[str]) -> List[str]:
        """
        Find which required sections are missing from README.
        
        Args:
            required_sections: List of required section names
            
        Returns:
            List of missing section names
        """
        content = self.facts.readme_content.lower()
        missing = []
        
        for section in required_sections:
            # Try to find section as a markdown heading (e.g., # Section, ## Section)
            pattern = rf'^#+\s+{re.escape(section.lower())}'
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(section)
        
        return missing
