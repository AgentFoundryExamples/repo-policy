"""SPDX ID requirement rule."""

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class SpdxIdRule(BaseRule):
    """Enforce SPDX ID requirement in configuration."""
    
    rule_id = "license-spdx-id-required"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["license", "legal"]
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate SPDX ID requirement."""
        spdx_id = self.config.license.spdx_id
        
        if not spdx_id:
            return self._create_fail_result(
                message="SPDX license identifier is not configured",
                evidence={
                    "has_spdx_id": False,
                    "config_path": str(self.config.config_file) if self.config.config_file else "repo-policy.yml",
                },
                remediation=(
                    "Add an SPDX license identifier to your configuration:\n"
                    "license:\n"
                    "  spdx_id: Apache-2.0  # or MIT, GPL-3.0, etc.\n\n"
                    "See https://spdx.org/licenses/ for valid identifiers"
                ),
            )
        
        # Validate SPDX ID format (basic check)
        if not spdx_id or len(spdx_id) < 3:
            return self._create_fail_result(
                message=f"Invalid SPDX license identifier: {spdx_id}",
                evidence={
                    "has_spdx_id": True,
                    "spdx_id": spdx_id,
                    "invalid": True,
                },
                remediation=(
                    f"The SPDX identifier '{spdx_id}' appears to be invalid. "
                    "Use a valid SPDX identifier like 'Apache-2.0', 'MIT', 'GPL-3.0', etc.\n"
                    "See https://spdx.org/licenses/ for valid identifiers"
                ),
            )
        
        return self._create_pass_result(
            message=f"SPDX license identifier configured: {spdx_id}",
            evidence={
                "has_spdx_id": True,
                "spdx_id": spdx_id,
            },
        )
