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
"""Init command implementation."""

import logging
import argparse
import sys
from pathlib import Path
from typing import Optional

from config.schema import Preset

logger = logging.getLogger(__name__)


DEFAULT_CONFIG_TEMPLATE = """# repo-policy configuration file
# See documentation: https://github.com/AgentFoundryExamples/repo-policy

# Target repository path (default: current directory)
target_path: .

# Output directory for reports and artifacts
outdir: .repo-policy-output

# License configuration
license:
  # SPDX license identifier (e.g., Apache-2.0, MIT, GPL-3.0)
  # See https://spdx.org/licenses/ for full list
  spdx_id: null  # TODO: Set your license SPDX ID
  
  # Path to license header template file
  # Template can use variables: {year}, {author}, etc.
  header_template_path: null  # TODO: Set path if using custom header
  
  # Require license headers in source files
  require_header: false

# File classification glob patterns
globs:
  # Source file patterns
  source:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.java"
    - "**/*.go"
    - "**/*.rs"
    - "**/*.c"
    - "**/*.cpp"
    - "**/*.h"
    - "**/*.hpp"
  
  # Test file patterns
  test:
    - "**/test_*.py"
    - "**/*_test.py"
    - "**/tests/**"
    - "**/*.test.js"
    - "**/*.test.ts"
    - "**/*.spec.js"
    - "**/*.spec.ts"

# Rule configuration
rules:
  # Rules to include (glob patterns, default: all)
  include:
    - "*"
  
  # Rules to exclude (glob patterns)
  exclude: []
  
  # Override severity for specific rules
  # Valid severities: error, warning, info
  severity_overrides: {}
    # Example:
    # license-header-missing: warning
    # code-quality-threshold: error

# Repository metadata and tags
repo_tags:
  # Examples:
  # repo_type: library
  # language: python
  # team: platform

# Configuration preset (optional)
# Valid presets: baseline, standard, strict
preset: null

# Runtime options (can be overridden via CLI)
keep_artifacts: false
clean: false
advice: false
"""


BASELINE_PRESET = """
# Baseline preset - minimal policy enforcement
preset: baseline

license:
  spdx_id: null  # TODO: Set your license
  require_header: false

rules:
  include: ["*"]
  exclude: []
  severity_overrides: {}
"""


STANDARD_PRESET = """
# Standard preset - recommended policy enforcement
preset: standard

license:
  spdx_id: Apache-2.0  # TODO: Update if different
  require_header: true
  header_template_path: LICENSE_HEADER.md

rules:
  include: ["*"]
  exclude: []
  severity_overrides:
    license-header-missing: error
    code-quality-threshold: warning
"""


STRICT_PRESET = """
# Strict preset - comprehensive policy enforcement
preset: strict

license:
  spdx_id: Apache-2.0  # TODO: Update if different
  require_header: true
  header_template_path: LICENSE_HEADER.md

rules:
  include: ["*"]
  exclude: []
  severity_overrides:
    license-header-missing: error
    code-quality-threshold: error
    security-vulnerability: error
"""


def get_config_template(preset: Optional[str] = None) -> str:
    """
    Get the appropriate config template based on preset.

    Args:
        preset: Configuration preset (baseline, standard, strict, or None)

    Returns:
        Config template string
    """
    if preset == Preset.BASELINE.value:
        return BASELINE_PRESET
    elif preset == Preset.STANDARD.value:
        return STANDARD_PRESET
    elif preset == Preset.STRICT.value:
        return STRICT_PRESET
    else:
        return DEFAULT_CONFIG_TEMPLATE


def prompt_confirm(message: str) -> bool:
    """
    Prompt user for yes/no confirmation.

    Args:
        message: Confirmation message

    Returns:
        True if user confirms, False otherwise
    """
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def init_command(args: argparse.Namespace) -> int:
    """
    Execute the init command to create a baseline configuration.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Initializing repo-policy configuration")

    # Determine config file path
    config_file = Path("repo-policy.yml")

    # Check if config already exists
    if config_file.exists():
        if not args.force:
            logger.warning(f"Config file already exists: {config_file}")
            if not prompt_confirm("Overwrite existing configuration?"):
                logger.info("Init cancelled by user")
                return 0
        logger.info(f"Overwriting existing config: {config_file}")

    # Get template based on preset
    preset = getattr(args, "preset", None)
    template = get_config_template(preset)

    # Write config file
    try:
        with open(config_file, "w") as f:
            f.write(template)
        logger.info(f"Created configuration file: {config_file}")

        if preset:
            logger.info(f"Applied preset: {preset}")
        else:
            logger.info("Created baseline configuration with comments")

        # Provide next steps
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Edit repo-policy.yml to set your license SPDX ID")
        logger.info("  2. Configure header template path if using license headers")
        logger.info("  3. Adjust rule includes/excludes as needed")
        logger.info("  4. Run 'repo-policy check' to validate your repository")

        return 0
    except Exception as e:
        logger.error(f"Failed to create config file: {e}")
        return 1
