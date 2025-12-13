"""LICENSE file presence rule."""

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class LicenseFileRule(BaseRule):
    """Verify LICENSE file presence."""
    
    rule_id = "license-file-required"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["license", "legal"]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate LICENSE file requirement."""
        if not self.facts.has_license:
            return self._create_fail_result(
                message="LICENSE file is missing",
                evidence={
                    "has_license": False,
                    "checked_names": ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"],
                },
                remediation=(
                    "Add a LICENSE file to the repository root. "
                    "Choose an appropriate license from https://choosealicense.com/ "
                    "or https://spdx.org/licenses/"
                ),
            )
        
        return self._create_pass_result(
            message=f"LICENSE file found: {self.facts.license_path}",
            evidence={
                "has_license": True,
                "license_path": str(self.facts.license_path),
            },
        )
