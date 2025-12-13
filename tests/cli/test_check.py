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
"""Tests for check command."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

from cli.commands.check import check_command


@patch("cli.commands.check.LicenseHeaderChecker")
@patch("cli.commands.check.RepoAnalyzerRunner")
@patch("cli.commands.check.load_config")
def test_check_command_success(mock_load_config, mock_analyzer, mock_checker, tmp_path):
    """Test successful check command execution."""
    # Create target directory
    target_path = tmp_path / "repo"
    target_path.mkdir()

    # Mock config
    mock_config = MagicMock()
    mock_config.target_path = str(target_path)
    mock_config.outdir = str(tmp_path / "output")
    mock_config.clean = False
    mock_config.advice = False
    mock_config.keep_artifacts = False
    mock_config.rules.include = ["*"]
    mock_config.rules.exclude = []
    mock_config.rules.severity_overrides = {}
    mock_config.license.spdx_id = "Apache-2.0"
    mock_config.license.require_header = False
    mock_config.repo_tags = {}
    mock_config.integration.enable_repo_analyzer = True
    mock_config.integration.enable_license_headers = True

    mock_load_config.return_value = mock_config

    # Mock analyzer and checker
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.run.return_value = MagicMock(
        success=True, error_message=None, output_files={}
    )
    mock_analyzer.return_value = mock_analyzer_instance

    mock_checker_instance = MagicMock()
    mock_checker_instance.check.return_value = MagicMock(
        success=True, skipped=False, error_message=None
    )
    mock_checker.return_value = mock_checker_instance

    # Create args
    args = Namespace(
        config=None,
        target_path=str(target_path),
        outdir=None,
        keep_artifacts=False,
        clean=False,
        advice=False,
    )

    exit_code = check_command(args)

    assert exit_code == 0
    mock_load_config.assert_called_once()


@patch("cli.commands.check.load_config")
def test_check_command_missing_target(mock_load_config, tmp_path):
    """Test check command with missing target path."""
    # Mock config with non-existent path
    mock_config = MagicMock()
    mock_config.target_path = "/nonexistent/path"
    mock_config.outdir = str(tmp_path / "output")
    mock_config.clean = False
    mock_config.advice = False

    mock_load_config.return_value = mock_config

    args = Namespace(
        config=None,
        target_path=None,
        outdir=None,
        keep_artifacts=False,
        clean=False,
        advice=False,
    )

    exit_code = check_command(args)

    assert exit_code == 1


@patch("cli.commands.check.load_config")
def test_check_command_config_load_error(mock_load_config):
    """Test check command with config loading error."""
    mock_load_config.side_effect = Exception("Config error")

    args = Namespace(
        config=None,
        target_path=None,
        outdir=None,
        keep_artifacts=False,
        clean=False,
        advice=False,
    )

    exit_code = check_command(args)

    assert exit_code == 1


@patch("cli.commands.check.LicenseHeaderChecker")
@patch("cli.commands.check.RepoAnalyzerRunner")
@patch("cli.commands.check.load_config")
def test_check_command_with_clean(mock_load_config, mock_analyzer, mock_checker, tmp_path):
    """Test check command with clean option."""
    target_path = tmp_path / "repo"
    target_path.mkdir()

    outdir = tmp_path / "output"
    outdir.mkdir()

    mock_config = MagicMock()
    mock_config.target_path = str(target_path)
    mock_config.outdir = str(outdir)
    mock_config.clean = True
    mock_config.advice = False
    mock_config.keep_artifacts = False
    mock_config.rules.include = ["*"]
    mock_config.rules.exclude = []
    mock_config.rules.severity_overrides = {}
    mock_config.license.spdx_id = None
    mock_config.license.require_header = False
    mock_config.repo_tags = {}
    mock_config.integration.enable_repo_analyzer = True
    mock_config.integration.enable_license_headers = True

    mock_load_config.return_value = mock_config

    # Mock analyzer and checker
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.run.return_value = MagicMock(
        success=True, error_message=None, output_files={}
    )
    mock_analyzer.return_value = mock_analyzer_instance

    mock_checker_instance = MagicMock()
    mock_checker_instance.check.return_value = MagicMock(
        success=True, skipped=False, error_message=None
    )
    mock_checker.return_value = mock_checker_instance

    args = Namespace(
        config=None,
        target_path=str(target_path),
        outdir=str(outdir),
        keep_artifacts=False,
        clean=True,
        advice=False,
    )

    exit_code = check_command(args)

    assert exit_code == 0


@patch("cli.commands.check.LicenseHeaderChecker")
@patch("cli.commands.check.RepoAnalyzerRunner")
@patch("cli.commands.check.load_config")
def test_check_command_with_advice(mock_load_config, mock_analyzer, mock_checker, tmp_path):
    """Test check command with advice option."""
    target_path = tmp_path / "repo"
    target_path.mkdir()

    mock_config = MagicMock()
    mock_config.target_path = str(target_path)
    mock_config.outdir = str(tmp_path / "output")
    mock_config.clean = False
    mock_config.advice = True
    mock_config.keep_artifacts = False
    mock_config.rules.include = ["*"]
    mock_config.rules.exclude = []
    mock_config.rules.severity_overrides = {}
    mock_config.license.spdx_id = "MIT"
    mock_config.license.require_header = True
    mock_config.repo_tags = {"repo_type": "library"}
    mock_config.integration.enable_repo_analyzer = True
    mock_config.integration.enable_license_headers = True

    mock_load_config.return_value = mock_config

    # Mock analyzer and checker
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.run.return_value = MagicMock(
        success=True, error_message=None, output_files={}
    )
    mock_analyzer.return_value = mock_analyzer_instance

    mock_checker_instance = MagicMock()
    mock_checker_instance.check.return_value = MagicMock(
        success=True, skipped=False, error_message=None, summary={}
    )
    mock_checker.return_value = mock_checker_instance

    args = Namespace(
        config=None,
        target_path=str(target_path),
        outdir=None,
        keep_artifacts=False,
        clean=False,
        advice=True,
    )

    exit_code = check_command(args)

    assert exit_code == 0


@patch("cli.commands.check.LicenseHeaderChecker")
@patch("cli.commands.check.RepoAnalyzerRunner")
@patch("cli.commands.check.load_config")
def test_check_command_cli_args_passed(mock_load_config, mock_analyzer, mock_checker, tmp_path):
    """Test that CLI args are properly passed to config loader."""
    target_path = tmp_path / "repo"
    target_path.mkdir()

    mock_config = MagicMock()
    mock_config.target_path = str(target_path)
    mock_config.outdir = str(tmp_path / "output")
    mock_config.clean = False
    mock_config.advice = False
    mock_config.keep_artifacts = False
    mock_config.rules.include = ["*"]
    mock_config.rules.exclude = []
    mock_config.rules.severity_overrides = {}
    mock_config.license.spdx_id = None
    mock_config.license.require_header = False
    mock_config.repo_tags = {}
    mock_config.integration.enable_repo_analyzer = True
    mock_config.integration.enable_license_headers = True

    mock_load_config.return_value = mock_config

    # Mock analyzer and checker
    mock_analyzer_instance = MagicMock()
    mock_analyzer_instance.run.return_value = MagicMock(
        success=True, error_message=None, output_files={}
    )
    mock_analyzer.return_value = mock_analyzer_instance

    mock_checker_instance = MagicMock()
    mock_checker_instance.check.return_value = MagicMock(
        success=True, skipped=False, error_message=None
    )
    mock_checker.return_value = mock_checker_instance

    args = Namespace(
        config="/path/to/config.yml",
        target_path="/custom/path",
        outdir="/custom/output",
        keep_artifacts=True,
        clean=True,
        advice=True,
    )

    exit_code = check_command(args)

    # Verify config loader was called with correct CLI args
    call_args = mock_load_config.call_args
    assert call_args[1]["config_path"] == "/path/to/config.yml"

    cli_args = call_args[1]["cli_args"]
    assert cli_args["target_path"] == "/custom/path"
    assert cli_args["outdir"] == "/custom/output"
    assert cli_args["keep_artifacts"] is True
    assert cli_args["clean"] is True
    assert cli_args["advice"] is True
