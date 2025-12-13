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
"""
Policy context for storing integration results.

This module provides a context object that stores the results from
integration tools (repo analyzer, license headers) for use by
downstream rules and reporting.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from integration.repo_analyzer import AnalyzerResult
from integration.license_headers import LicenseHeaderResult


@dataclass
class PolicyContext:
    """
    Context object for policy evaluation.

    Stores results from integration tools and provides them to rules
    for evaluation.
    """

    # Repo analyzer results
    analyzer_result: Optional[AnalyzerResult] = None

    # License header results
    license_header_result: Optional[LicenseHeaderResult] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_analyzer_data(self) -> bool:
        """Check if analyzer data is available."""
        return self.analyzer_result is not None and self.analyzer_result.success

    def has_license_header_data(self) -> bool:
        """Check if license header data is available."""
        return self.license_header_result is not None and not self.license_header_result.skipped

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """Get analyzer metadata for reporting."""
        if not self.analyzer_result:
            return {"status": "not_run"}

        return {
            "status": "success" if self.analyzer_result.success else "failed",
            "exit_code": self.analyzer_result.exit_code,
            "version": self.analyzer_result.version,
            "command": " ".join(self.analyzer_result.command),
            "output_files": self.analyzer_result.output_files,
            "error_message": self.analyzer_result.error_message,
        }

    def get_license_header_metadata(self) -> Dict[str, Any]:
        """Get license header metadata for reporting."""
        if not self.license_header_result:
            return {"status": "not_run"}

        if self.license_header_result.skipped:
            return {"status": "skipped"}

        return {
            "status": "success" if self.license_header_result.success else "failed",
            "exit_code": self.license_header_result.exit_code,
            "version": self.license_header_result.version,
            "command": " ".join(self.license_header_result.command),
            "summary": self.license_header_result.summary,
            "compliant_count": len(self.license_header_result.compliant_files),
            "non_compliant_count": len(self.license_header_result.non_compliant_files),
            "error_message": self.license_header_result.error_message,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "analyzer": self.get_analyzer_metadata(),
            "license_headers": self.get_license_header_metadata(),
            "metadata": self.metadata,
        }
