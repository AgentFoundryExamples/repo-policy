"""License header enforcement rule."""

from typing import Optional

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class HeaderRule(BaseRule):
    """Verify license headers using header tool results."""
    
    rule_id = "license-header-required"
    default_severity = RuleSeverity.ERROR
    rule_tags = ["license", "legal"]
    
    def _check_preconditions(self) -> Optional[RuleResult]:
        """Check if license header checking is enabled."""
        if not self.config.license.require_header:
            return self._create_skip_result(
                message="License header enforcement is disabled (require_header: false)",
                evidence={
                    "require_header": False,
                },
            )
        
        # Check if header checking was actually run
        if not self.context.has_license_header_data():
            return self._create_skip_result(
                message="License header check was not run or integration is disabled",
                evidence={
                    "integration_enabled": self.config.integration.enable_license_headers,
                    "require_header": self.config.license.require_header,
                },
            )
        
        return None
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate license header requirement."""
        header_result = self.context.license_header_result
        
        # If the header check itself failed (tool error), report it
        if header_result.error_message:
            return self._create_fail_result(
                message=f"License header check failed: {header_result.error_message}",
                evidence={
                    "tool_error": True,
                    "error_message": header_result.error_message,
                    "exit_code": header_result.exit_code,
                },
                remediation="Fix the license header checking tool configuration or installation.",
            )
        
        # Check if all files are compliant
        non_compliant_count = len(header_result.non_compliant_files)
        compliant_count = len(header_result.compliant_files)
        
        if non_compliant_count > 0:
            # Limit displayed files to avoid overwhelming output
            max_display = 10
            displayed_files = header_result.non_compliant_files[:max_display]
            truncated = non_compliant_count > max_display
            
            file_list = "\n".join(f"  - {f}" for f in displayed_files)
            if truncated:
                file_list += f"\n  ... and {non_compliant_count - max_display} more files"
            
            return self._create_fail_result(
                message=f"{non_compliant_count} file(s) missing license headers",
                evidence={
                    "compliant_count": compliant_count,
                    "non_compliant_count": non_compliant_count,
                    "non_compliant_files": header_result.non_compliant_files,
                    "spdx_id": self.config.license.spdx_id,
                },
                remediation=(
                    f"Add license headers to the following files:\n{file_list}\n\n"
                    f"Use the configured SPDX ID: {self.config.license.spdx_id}\n"
                    f"Template path: {self.config.license.header_template_path or 'default'}"
                ),
            )
        
        return self._create_pass_result(
            message=f"All {compliant_count} checked file(s) have valid license headers",
            evidence={
                "compliant_count": compliant_count,
                "non_compliant_count": 0,
                "spdx_id": self.config.license.spdx_id,
            },
        )
