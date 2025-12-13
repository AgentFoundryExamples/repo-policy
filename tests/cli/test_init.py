"""Tests for init command."""

import pytest
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

from cli.commands.init import init_command, get_config_template
from config.schema import Preset


def test_get_config_template_default():
    """Test default config template."""
    template = get_config_template(None)
    
    assert "repo-policy configuration file" in template
    assert "spdx_id:" in template
    assert "require_header:" in template


def test_get_config_template_baseline():
    """Test baseline preset template."""
    template = get_config_template(Preset.BASELINE.value)
    
    assert "preset: baseline" in template
    assert "Baseline preset" in template


def test_get_config_template_standard():
    """Test standard preset template."""
    template = get_config_template(Preset.STANDARD.value)
    
    assert "preset: standard" in template
    assert "Standard preset" in template


def test_get_config_template_strict():
    """Test strict preset template."""
    template = get_config_template(Preset.STRICT.value)
    
    assert "preset: strict" in template
    assert "Strict preset" in template


def test_init_command_creates_file(tmp_path):
    """Test init command creates config file."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        args = Namespace(
            force=False,
            preset=None,
        )
        
        exit_code = init_command(args)
        
        assert exit_code == 0
        
        config_file = tmp_path / "repo-policy.yml"
        assert config_file.exists()
        
        content = config_file.read_text()
        assert "repo-policy configuration file" in content
        assert "spdx_id:" in content
    finally:
        os.chdir(original_cwd)


def test_init_command_with_preset(tmp_path):
    """Test init command with preset."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        args = Namespace(
            force=False,
            preset="baseline",
        )
        
        exit_code = init_command(args)
        
        assert exit_code == 0
        
        config_file = tmp_path / "repo-policy.yml"
        assert config_file.exists()
        
        content = config_file.read_text()
        assert "preset: baseline" in content
    finally:
        os.chdir(original_cwd)


def test_init_command_existing_file_no_force(tmp_path):
    """Test init command with existing file and no force."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        # Create existing config
        config_file = tmp_path / "repo-policy.yml"
        config_file.write_text("existing content")
        
        args = Namespace(
            force=False,
            preset=None,
        )
        
        # Mock prompt_confirm to return False
        with patch("cli.commands.init.prompt_confirm", return_value=False):
            exit_code = init_command(args)
        
        assert exit_code == 0
        
        # File should not be changed
        content = config_file.read_text()
        assert content == "existing content"
    finally:
        os.chdir(original_cwd)


def test_init_command_existing_file_with_force(tmp_path):
    """Test init command with existing file and force flag."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        # Create existing config
        config_file = tmp_path / "repo-policy.yml"
        config_file.write_text("existing content")
        
        args = Namespace(
            force=True,
            preset=None,
        )
        
        exit_code = init_command(args)
        
        assert exit_code == 0
        
        # File should be overwritten
        content = config_file.read_text()
        assert "repo-policy configuration file" in content
        assert "existing content" not in content
    finally:
        os.chdir(original_cwd)


def test_init_command_existing_file_confirm_yes(tmp_path):
    """Test init command with existing file and user confirms."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        # Create existing config
        config_file = tmp_path / "repo-policy.yml"
        config_file.write_text("existing content")
        
        args = Namespace(
            force=False,
            preset=None,
        )
        
        # Mock prompt_confirm to return True
        with patch("cli.commands.init.prompt_confirm", return_value=True):
            exit_code = init_command(args)
        
        assert exit_code == 0
        
        # File should be overwritten
        content = config_file.read_text()
        assert "repo-policy configuration file" in content
    finally:
        os.chdir(original_cwd)


def test_init_command_write_error(tmp_path):
    """Test init command with write error."""
    import os
    original_cwd = os.getcwd()
    
    try:
        os.chdir(tmp_path)
        
        args = Namespace(
            force=False,
            preset=None,
        )
        
        # Mock open to raise an error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            exit_code = init_command(args)
        
        assert exit_code == 1
    finally:
        os.chdir(original_cwd)


def test_prompt_confirm_yes():
    """Test prompt_confirm with yes response."""
    from cli.commands.init import prompt_confirm
    
    # Test various yes responses
    for response in ["y", "yes", "Y", "YES"]:
        with patch("builtins.input", return_value=response):
            assert prompt_confirm("Test?") is True


def test_prompt_confirm_no():
    """Test prompt_confirm with no response."""
    from cli.commands.init import prompt_confirm
    
    # Test various no responses
    for response in ["n", "no", "N", "NO", ""]:
        with patch("builtins.input", return_value=response):
            assert prompt_confirm("Test?") is False


def test_prompt_confirm_keyboard_interrupt():
    """Test prompt_confirm with keyboard interrupt."""
    from cli.commands.init import prompt_confirm
    
    with patch("builtins.input", side_effect=KeyboardInterrupt()):
        assert prompt_confirm("Test?") is False


def test_prompt_confirm_eof():
    """Test prompt_confirm with EOF."""
    from cli.commands.init import prompt_confirm
    
    with patch("builtins.input", side_effect=EOFError()):
        assert prompt_confirm("Test?") is False
