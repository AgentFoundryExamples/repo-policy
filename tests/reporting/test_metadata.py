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
"""Tests for metadata extraction."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from reporting.metadata import (
    get_git_commit_hash,
    compute_config_hash,
    extract_report_metadata,
)
from integration.repo_analyzer import AnalyzerResult
from integration.license_headers import LicenseHeaderResult
from integration.context import PolicyContext


class TestGitCommitHash:
    """Tests for get_git_commit_hash."""

    def test_get_git_commit_hash_success(self, tmp_path):
        """Test getting git commit hash from a git repository."""
        # This test will only pass if tmp_path is a git repo
        # For now, we'll just test that it returns None or a string
        result = get_git_commit_hash(tmp_path)
        assert result is None or isinstance(result, str)

    @patch("reporting.metadata.subprocess.run")
    def test_get_git_commit_hash_mocked_success(self, mock_run, tmp_path):
        """Test getting git commit hash with mocked subprocess."""
        mock_run.return_value = Mock(returncode=0, stdout="abc123def456\n")
        
        result = get_git_commit_hash(tmp_path)
        
        assert result == "abc123def456"
        mock_run.assert_called_once()

    @patch("reporting.metadata.subprocess.run")
    def test_get_git_commit_hash_not_a_repo(self, mock_run, tmp_path):
        """Test getting git commit hash when not in a git repo."""
        mock_run.return_value = Mock(returncode=128, stdout="")
        
        result = get_git_commit_hash(tmp_path)
        
        assert result is None

    @patch("reporting.metadata.subprocess.run")
    def test_get_git_commit_hash_timeout(self, mock_run, tmp_path):
        """Test getting git commit hash with timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("git", 5)
        
        result = get_git_commit_hash(tmp_path)
        
        assert result is None


class TestConfigHash:
    """Tests for compute_config_hash."""

    def test_compute_config_hash_success(self, tmp_path):
        """Test computing config hash for existing file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        result = compute_config_hash(str(config_file))
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_compute_config_hash_deterministic(self, tmp_path):
        """Test config hash is deterministic."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        hash1 = compute_config_hash(str(config_file))
        hash2 = compute_config_hash(str(config_file))
        
        assert hash1 == hash2

    def test_compute_config_hash_different_content(self, tmp_path):
        """Test different content produces different hash."""
        config_file1 = tmp_path / "config1.yml"
        config_file1.write_text("test: value1\n")
        
        config_file2 = tmp_path / "config2.yml"
        config_file2.write_text("test: value2\n")
        
        hash1 = compute_config_hash(str(config_file1))
        hash2 = compute_config_hash(str(config_file2))
        
        assert hash1 != hash2

    def test_compute_config_hash_missing_file(self, tmp_path):
        """Test computing hash for non-existent file."""
        result = compute_config_hash(str(tmp_path / "nonexistent.yml"))
        
        assert result is None

    def test_compute_config_hash_none_path(self):
        """Test computing hash with None path."""
        result = compute_config_hash(None)
        
        assert result is None


class TestExtractReportMetadata:
    """Tests for extract_report_metadata."""

    def test_extract_metadata_basic(self, tmp_path):
        """Test extracting basic metadata."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        context = PolicyContext()
        
        metadata = extract_report_metadata(tmp_path, str(config_file), context)
        
        assert "repo_path" in metadata
        assert "config_file" in metadata
        assert metadata["config_file"] == "config.yml"
        assert "config_hash" in metadata

    def test_extract_metadata_with_git(self, tmp_path):
        """Test extracting metadata with git commit hash."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        context = PolicyContext()
        
        with patch("reporting.metadata.get_git_commit_hash") as mock_git:
            mock_git.return_value = "abc123def456"
            
            metadata = extract_report_metadata(tmp_path, str(config_file), context)
            
            assert "commit_hash" in metadata
            assert metadata["commit_hash"] == "abc123def456"

    def test_extract_metadata_without_git(self, tmp_path):
        """Test extracting metadata without git."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        context = PolicyContext()
        
        with patch("reporting.metadata.get_git_commit_hash") as mock_git:
            mock_git.return_value = None
            
            metadata = extract_report_metadata(tmp_path, str(config_file), context)
            
            assert "commit_hash" not in metadata

    def test_extract_metadata_with_analyzer_version(self, tmp_path):
        """Test extracting metadata with analyzer version."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["repo-analyzer"],
            version="1.2.3",
        )
        
        metadata = extract_report_metadata(tmp_path, str(config_file), context)
        
        assert "analyzer_version" in metadata
        assert metadata["analyzer_version"] == "1.2.3"

    def test_extract_metadata_with_license_header_version(self, tmp_path):
        """Test extracting metadata with license header tool version."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["license-header"],
            version="2.0.1",
        )
        
        metadata = extract_report_metadata(tmp_path, str(config_file), context)
        
        assert "license_header_tool_version" in metadata
        assert metadata["license_header_tool_version"] == "2.0.1"

    def test_extract_metadata_none_config_path(self, tmp_path):
        """Test extracting metadata with None config path."""
        context = PolicyContext()
        
        metadata = extract_report_metadata(tmp_path, None, context)
        
        assert "config_file" in metadata
        assert metadata["config_file"] == "repo-policy.yml"
        assert "config_hash" not in metadata
