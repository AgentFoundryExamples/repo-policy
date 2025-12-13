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
"""Tests for CLI main entry point."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.main import main, create_parser


def test_create_parser():
    """Test parser creation."""
    parser = create_parser()
    
    assert parser.prog == "repo-policy"
    
    # Test that it doesn't fail
    args = parser.parse_args(["check"])
    assert args.command == "check"


def test_parser_check_command():
    """Test parsing check command."""
    parser = create_parser()
    args = parser.parse_args(["check"])
    
    assert args.command == "check"


def test_parser_init_command():
    """Test parsing init command."""
    parser = create_parser()
    args = parser.parse_args(["init"])
    
    assert args.command == "init"


def test_parser_init_with_preset():
    """Test parsing init command with preset."""
    parser = create_parser()
    args = parser.parse_args(["init", "--preset", "baseline"])
    
    assert args.command == "init"
    assert args.preset == "baseline"


def test_parser_init_with_force():
    """Test parsing init command with force."""
    parser = create_parser()
    args = parser.parse_args(["init", "--force"])
    
    assert args.command == "init"
    assert args.force is True


def test_parser_global_options():
    """Test parsing global options."""
    parser = create_parser()
    args = parser.parse_args([
        "--config", "/path/to/config.yml",
        "--path", "/path/to/repo",
        "--outdir", "/path/to/output",
        "--keep-artifacts",
        "--clean",
        "--advice",
        "-v",
        "check",
    ])
    
    assert args.config == "/path/to/config.yml"
    assert args.target_path == "/path/to/repo"
    assert args.outdir == "/path/to/output"
    assert args.keep_artifacts is True
    assert args.clean is True
    assert args.advice is True
    assert args.verbose is True
    assert args.command == "check"


def test_parser_default_command():
    """Test that check is the default command."""
    parser = create_parser()
    args = parser.parse_args([])
    
    # No command specified - will be handled in main()
    assert not hasattr(args, 'command') or args.command is None


@patch("cli.commands.check.check_command")
def test_main_check_command(mock_check):
    """Test main with check command."""
    mock_check.return_value = 0
    
    exit_code = main(["check"])
    
    assert exit_code == 0
    mock_check.assert_called_once()


@patch("cli.commands.init.init_command")
def test_main_init_command(mock_init):
    """Test main with init command."""
    mock_init.return_value = 0
    
    exit_code = main(["init"])
    
    assert exit_code == 0
    mock_init.assert_called_once()


@patch("cli.commands.check.check_command")
def test_main_default_to_check(mock_check):
    """Test main defaults to check command when none specified."""
    mock_check.return_value = 0
    
    exit_code = main([])
    
    assert exit_code == 0
    mock_check.assert_called_once()


@patch("cli.commands.check.check_command")
def test_main_error_handling(mock_check):
    """Test main error handling."""
    mock_check.side_effect = Exception("Test error")
    
    exit_code = main(["check"])
    
    assert exit_code == 1


@patch("cli.commands.check.check_command")
def test_main_keyboard_interrupt(mock_check):
    """Test main keyboard interrupt handling."""
    mock_check.side_effect = KeyboardInterrupt()
    
    exit_code = main(["check"])
    
    assert exit_code == 130


@patch("cli.commands.check.check_command")
def test_main_verbose_flag(mock_check):
    """Test main with verbose flag."""
    mock_check.return_value = 0
    
    exit_code = main(["-v", "check"])
    
    assert exit_code == 0
    mock_check.assert_called_once()
    args = mock_check.call_args[0][0]
    assert args.verbose is True


@patch("cli.commands.check.check_command")
def test_main_with_all_options(mock_check):
    """Test main with all options."""
    mock_check.return_value = 0
    
    exit_code = main([
        "--config", "/path/to/config.yml",
        "--path", "/path/to/repo",
        "--outdir", "/path/to/output",
        "--keep-artifacts",
        "--clean",
        "--advice",
        "-v",
        "check",
    ])
    
    assert exit_code == 0
    mock_check.assert_called_once()
    
    args = mock_check.call_args[0][0]
    assert args.config == "/path/to/config.yml"
    assert args.target_path == "/path/to/repo"
    assert args.outdir == "/path/to/output"
    assert args.keep_artifacts is True
    assert args.clean is True
    assert args.advice is True
    assert args.verbose is True
