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
"""Configuration schema for repo-policy using Pydantic."""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Rule severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Preset(str, Enum):
    """Configuration presets."""

    BASELINE = "baseline"
    STANDARD = "standard"
    STRICT = "strict"


class GlobPatterns(BaseModel):
    """Glob patterns for file classification."""

    source: List[str] = Field(
        default_factory=lambda: [
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.java",
            "**/*.go",
            "**/*.rs",
            "**/*.c",
            "**/*.cpp",
            "**/*.h",
            "**/*.hpp",
        ],
        description="Glob patterns for source files",
    )
    test: List[str] = Field(
        default_factory=lambda: [
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/**",
            "**/*.test.js",
            "**/*.test.ts",
            "**/*.spec.js",
            "**/*.spec.ts",
        ],
        description="Glob patterns for test files",
    )


class RuleConfig(BaseModel):
    """Rule configuration."""

    include: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Rules to include (glob patterns)",
    )
    exclude: List[str] = Field(
        default_factory=list,
        description="Rules to exclude (glob patterns)",
    )
    severity_overrides: Dict[str, Severity] = Field(
        default_factory=dict,
        description="Override severity for specific rules",
    )
    
    # Additional rule configuration options
    readme_required_sections: Optional[List[str]] = Field(
        default=None,
        description="Required sections in README (None = use defaults)",
    )
    tests_required_if_sources_present: bool = Field(
        default=True,
        description="Require tests if source files are present",
    )
    large_file_threshold_mb: int = Field(
        default=10,
        description="Threshold in MB for large file warnings",
    )
    forbidden_patterns: Optional[List[str]] = Field(
        default=None,
        description="Forbidden file patterns (None = use defaults)",
    )

    @field_validator("severity_overrides", mode="before")
    @classmethod
    def validate_severity_overrides(cls, v):
        """Validate severity override values."""
        if not isinstance(v, dict):
            return v

        result = {}
        for rule, severity in v.items():
            if isinstance(severity, str):
                try:
                    result[rule] = Severity(severity.lower())
                except ValueError:
                    valid_values = [s.value for s in Severity]
                    raise ValueError(
                        f"Invalid severity '{severity}' for rule '{rule}'. "
                        f"Valid values: {', '.join(valid_values)}"
                    )
            else:
                raise TypeError(f"Severity must be a string, not {type(severity).__name__}")
        return result
    
    def get(self, key: str, default=None):
        """Get a configuration value by key (for backward compatibility)."""
        return getattr(self, key, default)


class LicenseConfig(BaseModel):
    """License and header configuration."""

    spdx_id: Optional[str] = Field(
        default=None,
        description="SPDX license identifier (e.g., 'Apache-2.0')",
    )
    header_template_path: Optional[str] = Field(
        default=None,
        description="Path to license header template file",
    )
    require_header: bool = Field(
        default=False,
        description="Require license headers in source files",
    )
    include_globs: List[str] = Field(
        default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.java"],
        description="File patterns to include in header checks",
    )
    exclude_globs: List[str] = Field(
        default_factory=lambda: ["**/test_*.py", "**/*_test.py"],
        description="File patterns to exclude from header checks",
    )


class IntegrationConfig(BaseModel):
    """Integration tool configuration."""

    repo_analyzer_binary: Optional[str] = Field(
        default=None,
        description="Path to repo-analyzer binary (auto-detect if None)",
    )
    repo_analyzer_workspace_mode: str = Field(
        default="direct_output",
        description="Analyzer workspace mode: 'temp_workspace' or 'direct_output'",
    )
    license_header_binary: Optional[str] = Field(
        default=None,
        description="Path to license-header binary (auto-detect if None)",
    )
    enable_repo_analyzer: bool = Field(
        default=True,
        description="Enable repo analyzer integration",
    )
    enable_license_headers: bool = Field(
        default=True,
        description="Enable license header checking",
    )

    @field_validator("repo_analyzer_workspace_mode")
    @classmethod
    def validate_workspace_mode(cls, v):
        """Validate workspace mode value."""
        valid_modes = ["temp_workspace", "direct_output"]
        if v not in valid_modes:
            raise ValueError(
                f"Invalid workspace mode '{v}'. Valid values: {', '.join(valid_modes)}"
            )
        return v


class Config(BaseModel):
    """Main configuration schema for repo-policy."""

    target_path: str = Field(
        default=".",
        description="Path to the repository to analyze",
    )
    outdir: str = Field(
        default=".repo-policy-output",
        description="Output directory for reports and artifacts",
    )
    config_file: Optional[str] = Field(
        default=None,
        description="Path to the config file (for tracking purposes)",
    )

    # File classification
    globs: GlobPatterns = Field(
        default_factory=GlobPatterns,
        description="Glob patterns for file classification",
    )

    # Rule configuration
    rules: RuleConfig = Field(
        default_factory=RuleConfig,
        description="Rule configuration",
    )

    # License configuration
    license: LicenseConfig = Field(
        default_factory=LicenseConfig,
        description="License and header configuration",
    )

    # Integration configuration
    integration: IntegrationConfig = Field(
        default_factory=IntegrationConfig,
        description="External tool integration configuration",
    )

    # Repository metadata
    repo_tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Repository tags/metadata (e.g., repo_type: 'library')",
    )

    # Preset configuration
    preset: Optional[Preset] = Field(
        default=None,
        description="Configuration preset to apply",
    )

    # CLI-specific options
    keep_artifacts: bool = Field(
        default=False,
        description="Keep intermediate artifacts after run",
    )
    clean: bool = Field(
        default=False,
        description="Clean output directory before run",
    )
    advice: bool = Field(
        default=False,
        description="Show advice and recommendations (stub)",
    )

    @field_validator("preset", mode="before")
    @classmethod
    def validate_preset(cls, v):
        """Validate preset value."""
        if v is None or isinstance(v, Preset):
            return v
        if isinstance(v, str):
            try:
                return Preset(v.lower())
            except ValueError:
                valid_values = [p.value for p in Preset]
                raise ValueError(f"Invalid preset '{v}'. Valid values: {', '.join(valid_values)}")
        raise TypeError(f"Preset must be a string, not {type(v).__name__}")

    def model_post_init(self, __context):
        """Post-initialization validation."""
        # Warn about missing required fields
        if self.license.require_header and not self.license.spdx_id:
            # This will be handled by the loader with proper logging
            pass
