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
"""Configuration loader with YAML support and CLI override precedence."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from pydantic import ValidationError

from .schema import Config

logger = logging.getLogger(__name__)


def find_config_file(search_path: Optional[str] = None, max_depth: int = 50) -> Optional[Path]:
    """
    Find the config file by searching up from the target path.
    
    Args:
        search_path: Starting path for search (defaults to current directory)
        max_depth: Maximum number of directories to traverse upward (default: 50)
        
    Returns:
        Path to config file if found, None otherwise
    """
    try:
        if search_path:
            current = Path(search_path).resolve()
        else:
            current = Path.cwd()
    except (OSError, RuntimeError) as e:
        logger.warning(f"Error resolving search path: {e}")
        return None
    
    # Search up to repository root with depth limit
    depth = 0
    while depth < max_depth:
        config_candidates = [
            current / "repo-policy.yml",
            current / "repo-policy.yaml",
            current / ".repo-policy.yml",
            current / ".repo-policy.yaml",
        ]
        
        for candidate in config_candidates:
            try:
                if candidate.exists():
                    return candidate
            except (OSError, PermissionError) as e:
                logger.debug(f"Cannot access {candidate}: {e}")
                continue
        
        # Check if we're at the repository root or filesystem root
        try:
            if (current / ".git").exists() or current == current.parent:
                break
        except (OSError, PermissionError):
            # Cannot check for .git directory, likely at or near root
            break
            
        current = current.parent
        depth += 1
    
    return None


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary of config values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    if config_data is None:
        return {}
    
    if not isinstance(config_data, dict):
        raise ValueError(f"Config file must contain a YAML mapping, got {type(config_data)}")
    
    return config_data


def apply_cli_overrides(config_dict: Dict[str, Any], cli_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply CLI arguments to config dictionary with proper precedence.
    
    CLI arguments take precedence over config file values.
    
    Args:
        config_dict: Configuration from file
        cli_args: CLI arguments
        
    Returns:
        Merged configuration dictionary
    """
    # Create a copy to avoid modifying the original
    merged = config_dict.copy()
    
    # Direct mappings
    cli_to_config = {
        "target_path": "target_path",
        "outdir": "outdir",
        "keep_artifacts": "keep_artifacts",
        "clean": "clean",
        "advice": "advice",
        "preset": "preset",
    }
    
    for cli_key, config_key in cli_to_config.items():
        if cli_key in cli_args and cli_args[cli_key] is not None:
            merged[config_key] = cli_args[cli_key]
    
    return merged


def load_config(
    config_path: Optional[str] = None,
    cli_args: Optional[Dict[str, Any]] = None,
    allow_missing: bool = True,
) -> Config:
    """
    Load configuration from file and apply CLI overrides.
    
    Args:
        config_path: Explicit path to config file (or None to auto-discover)
        cli_args: CLI arguments to override config file values
        allow_missing: If True, use defaults when config file is missing
        
    Returns:
        Validated Config object
        
    Raises:
        FileNotFoundError: If config file is specified but doesn't exist
        ValidationError: If config fails schema validation
        yaml.YAMLError: If config file is invalid YAML
    """
    cli_args = cli_args or {}
    config_dict: Dict[str, Any] = {}
    
    # Determine config file path
    if config_path:
        config_file_path = Path(config_path)
        if not config_file_path.exists():
            raise FileNotFoundError(f"Specified config file not found: {config_path}")
    else:
        # Auto-discover config file
        search_path = cli_args.get("target_path")
        config_file_path = find_config_file(search_path)
    
    # Load config file if found
    if config_file_path:
        try:
            config_dict = load_yaml_config(config_file_path)
            config_dict["config_file"] = str(config_file_path)
            logger.info(f"Loaded config from: {config_file_path}")
        except Exception as e:
            logger.error(f"Error loading config file {config_file_path}: {e}")
            raise
    else:
        if not allow_missing:
            raise FileNotFoundError("No config file found and allow_missing=False")
        logger.warning(
            "No config file found, using defaults. "
            "Run 'repo-policy init' to create a baseline configuration."
        )
    
    # Apply CLI overrides
    config_dict = apply_cli_overrides(config_dict, cli_args)
    
    # Validate and create Config object
    try:
        config = Config(**config_dict)
    except ValidationError as e:
        logger.error("Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            logger.error(f"  {field}: {error['msg']}")
        raise
    
    # Post-validation warnings
    if config.license.require_header:
        if not config.license.spdx_id:
            logger.warning(
                "license.require_header is True but license.spdx_id is not set. "
                "Header validation may be limited."
            )
        if not config.license.header_template_path:
            logger.warning(
                "license.require_header is True but license.header_template_path is not set. "
                "Using default header template."
            )
    
    return config
