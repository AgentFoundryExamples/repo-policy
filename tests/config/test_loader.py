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
"""Tests for configuration loader."""

import pytest
import tempfile
from pathlib import Path

import yaml
from pydantic import ValidationError

from config.loader import (
    load_config,
    load_yaml_config,
    apply_cli_overrides,
    find_config_file,
)
from config.schema import Config, Severity


def test_load_yaml_config_valid(tmp_path):
    """Test loading valid YAML config."""
    config_file = tmp_path / "config.yml"
    config_data = {
        "target_path": "/test/path",
        "outdir": "/test/output",
        "license": {
            "spdx_id": "MIT",
        },
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    loaded = load_yaml_config(config_file)

    assert loaded["target_path"] == "/test/path"
    assert loaded["outdir"] == "/test/output"
    assert loaded["license"]["spdx_id"] == "MIT"


def test_load_yaml_config_empty(tmp_path):
    """Test loading empty YAML config."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("")

    loaded = load_yaml_config(config_file)

    assert loaded == {}


def test_load_yaml_config_missing():
    """Test loading non-existent config raises error."""
    with pytest.raises(FileNotFoundError):
        load_yaml_config(Path("/nonexistent/config.yml"))


def test_load_yaml_config_invalid(tmp_path):
    """Test loading invalid YAML raises error."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("[not a mapping")

    with pytest.raises(yaml.YAMLError):
        load_yaml_config(config_file)


def test_apply_cli_overrides_empty():
    """Test CLI overrides with empty dicts."""
    config_dict = {"target_path": "/config/path"}
    cli_args = {}

    result = apply_cli_overrides(config_dict, cli_args)

    assert result["target_path"] == "/config/path"


def test_apply_cli_overrides_precedence():
    """Test that CLI args take precedence over config file."""
    config_dict = {
        "target_path": "/config/path",
        "outdir": "/config/output",
    }
    cli_args = {
        "target_path": "/cli/path",
        "keep_artifacts": True,
    }

    result = apply_cli_overrides(config_dict, cli_args)

    assert result["target_path"] == "/cli/path"
    assert result["outdir"] == "/config/output"
    assert result["keep_artifacts"] is True


def test_apply_cli_overrides_none_values():
    """Test that None CLI values don't override config."""
    config_dict = {
        "target_path": "/config/path",
        "outdir": "/config/output",
    }
    cli_args = {
        "target_path": None,
        "outdir": "/cli/output",
    }

    result = apply_cli_overrides(config_dict, cli_args)

    assert result["target_path"] == "/config/path"
    assert result["outdir"] == "/cli/output"


def test_find_config_file_current_directory(tmp_path):
    """Test finding config in current directory."""
    config_file = tmp_path / "repo-policy.yml"
    config_file.write_text("target_path: .")

    found = find_config_file(str(tmp_path))

    assert found == config_file


def test_find_config_file_parent_directory(tmp_path):
    """Test finding config in parent directory."""
    config_file = tmp_path / "repo-policy.yml"
    config_file.write_text("target_path: .")

    subdir = tmp_path / "subdir"
    subdir.mkdir()

    found = find_config_file(str(subdir))

    assert found == config_file


def test_find_config_file_with_git_root(tmp_path):
    """Test finding config stops at git root."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    config_file = tmp_path / "repo-policy.yml"
    config_file.write_text("target_path: .")

    subdir = tmp_path / "deep" / "subdir"
    subdir.mkdir(parents=True)

    found = find_config_file(str(subdir))

    assert found == config_file


def test_find_config_file_not_found(tmp_path):
    """Test when config file is not found."""
    found = find_config_file(str(tmp_path))

    assert found is None


def test_find_config_file_alternative_names(tmp_path):
    """Test finding config with alternative file names."""
    # Test .repo-policy.yml
    config_file = tmp_path / ".repo-policy.yml"
    config_file.write_text("target_path: .")

    found = find_config_file(str(tmp_path))

    assert found == config_file


def test_find_config_file_max_depth(tmp_path):
    """Test that config search respects max_depth parameter."""
    # Create a deep directory structure
    deep_path = tmp_path
    for i in range(10):
        deep_path = deep_path / f"level{i}"
    deep_path.mkdir(parents=True)

    # Put config at the root
    config_file = tmp_path / "repo-policy.yml"
    config_file.write_text("target_path: .")

    # Should find with sufficient depth
    found = find_config_file(str(deep_path), max_depth=20)
    assert found == config_file

    # Should not find with insufficient depth
    found = find_config_file(str(deep_path), max_depth=5)
    assert found is None


def test_load_config_with_file(tmp_path):
    """Test loading config from explicit file path."""
    config_file = tmp_path / "custom-config.yml"
    config_data = {
        "target_path": "/test/path",
        "license": {
            "spdx_id": "Apache-2.0",
        },
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_path=str(config_file))

    assert config.target_path == "/test/path"
    assert config.license.spdx_id == "Apache-2.0"


def test_load_config_missing_allowed(tmp_path):
    """Test loading config with missing file allowed."""
    # Change to temp directory where no config exists
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        config = load_config(allow_missing=True)

        # Should use defaults
        assert config.target_path == "."
        assert config.outdir == ".repo-policy-output"
    finally:
        os.chdir(original_cwd)


def test_load_config_missing_not_allowed(tmp_path):
    """Test loading config with missing file raises error."""
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_config(allow_missing=False)
    finally:
        os.chdir(original_cwd)


def test_load_config_with_cli_overrides(tmp_path):
    """Test loading config with CLI overrides."""
    config_file = tmp_path / "repo-policy.yml"
    config_data = {
        "target_path": "/config/path",
        "outdir": "/config/output",
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    cli_args = {
        "target_path": "/cli/path",
        "keep_artifacts": True,
    }

    config = load_config(config_path=str(config_file), cli_args=cli_args)

    assert config.target_path == "/cli/path"
    assert config.outdir == "/config/output"
    assert config.keep_artifacts is True


def test_load_config_validation_error(tmp_path):
    """Test loading config with validation errors."""
    config_file = tmp_path / "repo-policy.yml"
    config_data = {
        "preset": "invalid-preset",
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValidationError):
        load_config(config_path=str(config_file))


def test_load_config_severity_override_validation(tmp_path):
    """Test config with invalid severity override."""
    config_file = tmp_path / "repo-policy.yml"
    config_data = {
        "rules": {
            "severity_overrides": {
                "my-rule": "invalid-severity",
            },
        },
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValidationError) as exc_info:
        load_config(config_path=str(config_file))

    error_msg = str(exc_info.value)
    assert "Invalid severity" in error_msg


def test_load_config_complete_example(tmp_path):
    """Test loading a complete config example."""
    config_file = tmp_path / "repo-policy.yml"
    config_data = {
        "target_path": "/test/repo",
        "outdir": "/test/output",
        "globs": {
            "source": ["**/*.py"],
            "test": ["**/test_*.py"],
        },
        "rules": {
            "include": ["license-*"],
            "exclude": ["code-style"],
            "severity_overrides": {
                "license-header-missing": "error",
            },
        },
        "license": {
            "spdx_id": "MIT",
            "require_header": True,
        },
        "repo_tags": {
            "repo_type": "library",
        },
        "preset": "standard",
        "keep_artifacts": True,
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_path=str(config_file))

    assert config.target_path == "/test/repo"
    assert config.outdir == "/test/output"
    assert config.globs.source == ["**/*.py"]
    assert config.rules.include == ["license-*"]
    assert config.rules.severity_overrides["license-header-missing"] == Severity.ERROR
    assert config.license.spdx_id == "MIT"
    assert config.license.require_header is True
    assert config.repo_tags["repo_type"] == "library"
    assert config.keep_artifacts is True
