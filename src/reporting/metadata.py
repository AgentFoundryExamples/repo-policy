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
"""Metadata extraction for policy reports."""

import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuration constants
GIT_TIMEOUT_SECONDS = 10  # Increased timeout for large repositories


def get_git_commit_hash(repo_path: Path) -> Optional[str]:
    """
    Get the current git commit hash.
    
    Args:
        repo_path: Path to repository
        
    Returns:
        Commit hash or None if not available
    """
    if not shutil.which("git"):
        logger.debug("git command not found, skipping commit hash retrieval.")
        return None
    
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.debug(f"Git command timed out after {GIT_TIMEOUT_SECONDS} seconds")
        return None
    except subprocess.CalledProcessError as e:
        logger.debug(f"Git command failed with exit code {e.returncode}")
        return None
    except FileNotFoundError:
        logger.debug("git executable not found")
        return None
    except OSError as e:
        logger.debug(f"OS error while executing git: {e}")
        return None


def compute_config_hash(config_path: Optional[str]) -> Optional[str]:
    """
    Compute SHA-256 hash of config file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config file hash or None if not available
    """
    if not config_path:
        return None
    
    try:
        config_file = Path(config_path)
        if config_file.exists():
            content = config_file.read_bytes()
            return hashlib.sha256(content).hexdigest()
    except (OSError, IOError) as e:
        logger.debug(f"Failed to read config file for hashing: {e}")
        return None
    except ValueError as e:
        logger.debug(f"Invalid config path: {e}")
        return None


def extract_report_metadata(
    repo_path: Path,
    config_path: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Extract metadata for policy report.
    
    Args:
        repo_path: Path to repository
        config_path: Path to config file
        context: Policy context with integration results
        
    Returns:
        Dictionary with metadata fields
    """
    metadata = {
        "repo_path": str(repo_path.resolve()),
        "config_file": Path(config_path).name if config_path else "repo-policy.yml",
    }
    
    # Git commit hash
    commit_hash = get_git_commit_hash(repo_path)
    if commit_hash:
        metadata["commit_hash"] = commit_hash
    
    # Config hash
    config_hash = compute_config_hash(config_path)
    if config_hash:
        metadata["config_hash"] = config_hash
    
    # Analyzer version
    if context.analyzer_result and context.analyzer_result.version:
        metadata["analyzer_version"] = context.analyzer_result.version
    
    # License header tool version
    if context.license_header_result and context.license_header_result.version:
        metadata["license_header_tool_version"] = context.license_header_result.version
    
    return metadata
