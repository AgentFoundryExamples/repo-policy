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
                raise TypeError(
                    f"Severity for rule '{rule}' must be a string, not {type(severity).__name__}"
                )
        return result


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
                raise ValueError(
                    f"Invalid preset '{v}'. Valid values: {', '.join(valid_values)}"
                )
        raise TypeError(f"Preset must be a string, not {type(v).__name__}")

    def model_post_init(self, __context):
        """Post-initialization validation."""
        # Warn about missing required fields
        if self.license.require_header and not self.license.spdx_id:
            # This will be handled by the loader with proper logging
            pass
