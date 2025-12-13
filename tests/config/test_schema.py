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
"""Tests for configuration schema."""

import pytest
from pydantic import ValidationError

from config.schema import Config, Severity, Preset, RuleConfig, LicenseConfig


def test_config_defaults():
    """Test that Config initializes with proper defaults."""
    config = Config()
    
    assert config.target_path == "."
    assert config.outdir == ".repo-policy-output"
    assert config.keep_artifacts is False
    assert config.clean is False
    assert config.advice is False
    assert config.preset is None


def test_config_with_values():
    """Test Config with explicit values."""
    config = Config(
        target_path="/path/to/repo",
        outdir="/tmp/output",
        keep_artifacts=True,
        clean=True,
    )
    
    assert config.target_path == "/path/to/repo"
    assert config.outdir == "/tmp/output"
    assert config.keep_artifacts is True
    assert config.clean is True


def test_severity_enum():
    """Test Severity enum values."""
    assert Severity.ERROR.value == "error"
    assert Severity.WARNING.value == "warning"
    assert Severity.INFO.value == "info"


def test_preset_enum():
    """Test Preset enum values."""
    assert Preset.BASELINE.value == "baseline"
    assert Preset.STANDARD.value == "standard"
    assert Preset.STRICT.value == "strict"


def test_rule_config_defaults():
    """Test RuleConfig defaults."""
    rules = RuleConfig()
    
    assert rules.include == ["*"]
    assert rules.exclude == []
    assert rules.severity_overrides == {}


def test_rule_config_severity_overrides_valid():
    """Test valid severity overrides."""
    rules = RuleConfig(
        severity_overrides={
            "license-header-missing": "error",
            "code-quality": "warning",
        }
    )
    
    assert rules.severity_overrides["license-header-missing"] == Severity.ERROR
    assert rules.severity_overrides["code-quality"] == Severity.WARNING


def test_rule_config_severity_overrides_invalid():
    """Test invalid severity override raises error."""
    with pytest.raises(ValidationError) as exc_info:
        RuleConfig(
            severity_overrides={
                "my-rule": "invalid-severity",
            }
        )
    
    error_msg = str(exc_info.value)
    assert "Invalid severity 'invalid-severity'" in error_msg


def test_rule_config_severity_overrides_non_string():
    """Test non-string severity override raises error."""
    with pytest.raises((ValidationError, TypeError)) as exc_info:
        RuleConfig(
            severity_overrides={
                "my-rule": 123,
            }
        )
    
    error_msg = str(exc_info.value)
    assert "must be a string" in error_msg


def test_license_config_defaults():
    """Test LicenseConfig defaults."""
    license_cfg = LicenseConfig()
    
    assert license_cfg.spdx_id is None
    assert license_cfg.header_template_path is None
    assert license_cfg.require_header is False


def test_license_config_with_values():
    """Test LicenseConfig with values."""
    license_cfg = LicenseConfig(
        spdx_id="Apache-2.0",
        header_template_path="LICENSE_HEADER.md",
        require_header=True,
    )
    
    assert license_cfg.spdx_id == "Apache-2.0"
    assert license_cfg.header_template_path == "LICENSE_HEADER.md"
    assert license_cfg.require_header is True


def test_glob_patterns_defaults():
    """Test GlobPatterns has reasonable defaults."""
    config = Config()
    
    assert "**/*.py" in config.globs.source
    assert "**/*.js" in config.globs.source
    assert "**/test_*.py" in config.globs.test
    assert "**/*.test.js" in config.globs.test


def test_config_preset_validation():
    """Test preset validation."""
    # Valid presets
    config1 = Config(preset="baseline")
    assert config1.preset == Preset.BASELINE
    
    config2 = Config(preset="standard")
    assert config2.preset == Preset.STANDARD
    
    config3 = Config(preset="strict")
    assert config3.preset == Preset.STRICT
    
    # Invalid preset
    with pytest.raises(ValidationError) as exc_info:
        Config(preset="invalid-preset")
    
    error_msg = str(exc_info.value)
    assert "Invalid preset 'invalid-preset'" in error_msg


def test_config_preset_validation_non_string():
    """Test non-string preset raises error."""
    with pytest.raises((ValidationError, TypeError)) as exc_info:
        Config(preset=123)
    
    error_msg = str(exc_info.value)
    assert "must be a string" in error_msg or "Preset must be" in error_msg


def test_config_repo_tags():
    """Test repository tags."""
    config = Config(
        repo_tags={
            "repo_type": "library",
            "language": "python",
            "team": "platform",
        }
    )
    
    assert config.repo_tags["repo_type"] == "library"
    assert config.repo_tags["language"] == "python"
    assert config.repo_tags["team"] == "platform"


def test_config_complete_example():
    """Test a complete configuration example."""
    config = Config(
        target_path="/path/to/repo",
        outdir="/tmp/output",
        globs={
            "source": ["**/*.py", "**/*.js"],
            "test": ["**/test_*.py"],
        },
        rules={
            "include": ["license-*", "code-*"],
            "exclude": ["code-style"],
            "severity_overrides": {
                "license-header-missing": "error",
                "code-quality": "warning",
            },
        },
        license={
            "spdx_id": "Apache-2.0",
            "header_template_path": "LICENSE_HEADER.md",
            "require_header": True,
        },
        repo_tags={
            "repo_type": "library",
        },
        preset="standard",
        keep_artifacts=True,
    )
    
    assert config.target_path == "/path/to/repo"
    assert config.rules.include == ["license-*", "code-*"]
    assert config.rules.exclude == ["code-style"]
    assert config.rules.severity_overrides["license-header-missing"] == Severity.ERROR
    assert config.license.spdx_id == "Apache-2.0"
    assert config.preset == Preset.STANDARD
    assert config.keep_artifacts is True
