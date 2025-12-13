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
