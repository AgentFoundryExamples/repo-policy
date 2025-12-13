"""Tests for policy context."""

import pytest
from integration.context import PolicyContext
from integration.repo_analyzer import AnalyzerResult
from integration.license_headers import LicenseHeaderResult


class TestPolicyContext:
    """Test PolicyContext functionality."""

    def test_init_empty(self):
        """Test initialization with no data."""
        context = PolicyContext()
        assert context.analyzer_result is None
        assert context.license_header_result is None
        assert context.metadata == {}

    def test_has_analyzer_data_none(self):
        """Test has_analyzer_data when result is None."""
        context = PolicyContext()
        assert not context.has_analyzer_data()

    def test_has_analyzer_data_failed(self):
        """Test has_analyzer_data when result failed."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="error",
        )
        assert not context.has_analyzer_data()

    def test_has_analyzer_data_success(self):
        """Test has_analyzer_data when result succeeded."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
        )
        assert context.has_analyzer_data()

    def test_has_license_header_data_none(self):
        """Test has_license_header_data when result is None."""
        context = PolicyContext()
        assert not context.has_license_header_data()

    def test_has_license_header_data_skipped(self):
        """Test has_license_header_data when check was skipped."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )
        assert not context.has_license_header_data()

    def test_has_license_header_data_success(self):
        """Test has_license_header_data when check succeeded."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            skipped=False,
        )
        assert context.has_license_header_data()

    def test_get_analyzer_metadata_not_run(self):
        """Test get_analyzer_metadata when not run."""
        context = PolicyContext()
        metadata = context.get_analyzer_metadata()
        assert metadata["status"] == "not_run"

    def test_get_analyzer_metadata_success(self):
        """Test get_analyzer_metadata for successful run."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="1.0.0",
            command=["repo-analyzer", "--path", "."],
            output_files={"tree": "/path/to/tree.json"},
        )
        
        metadata = context.get_analyzer_metadata()
        assert metadata["status"] == "success"
        assert metadata["exit_code"] == 0
        assert metadata["version"] == "1.0.0"
        assert metadata["command"] == "repo-analyzer --path ."
        assert metadata["output_files"] == {"tree": "/path/to/tree.json"}
        assert metadata["error_message"] is None

    def test_get_analyzer_metadata_failed(self):
        """Test get_analyzer_metadata for failed run."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="error output",
            version="1.0.0",
            command=["repo-analyzer"],
            error_message="Analysis failed",
        )
        
        metadata = context.get_analyzer_metadata()
        assert metadata["status"] == "failed"
        assert metadata["exit_code"] == 1
        assert metadata["error_message"] == "Analysis failed"

    def test_get_license_header_metadata_not_run(self):
        """Test get_license_header_metadata when not run."""
        context = PolicyContext()
        metadata = context.get_license_header_metadata()
        assert metadata["status"] == "not_run"

    def test_get_license_header_metadata_skipped(self):
        """Test get_license_header_metadata when skipped."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )
        
        metadata = context.get_license_header_metadata()
        assert metadata["status"] == "skipped"

    def test_get_license_header_metadata_success(self):
        """Test get_license_header_metadata for successful check."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="2.0.0",
            command=["license-header", "check"],
            compliant_files=["file1.py", "file2.py"],
            non_compliant_files=[],
            summary={"compliant": 2, "non_compliant": 0},
        )
        
        metadata = context.get_license_header_metadata()
        assert metadata["status"] == "success"
        assert metadata["exit_code"] == 0
        assert metadata["version"] == "2.0.0"
        assert metadata["command"] == "license-header check"
        assert metadata["summary"] == {"compliant": 2, "non_compliant": 0}
        assert metadata["compliant_count"] == 2
        assert metadata["non_compliant_count"] == 0
        assert metadata["error_message"] is None

    def test_get_license_header_metadata_failed(self):
        """Test get_license_header_metadata for failed check."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="error",
            version="2.0.0",
            command=["license-header", "check"],
            compliant_files=["file1.py"],
            non_compliant_files=["file2.py", "file3.py"],
            summary={"compliant": 1, "non_compliant": 2},
            error_message="Check failed",
        )
        
        metadata = context.get_license_header_metadata()
        assert metadata["status"] == "failed"
        assert metadata["exit_code"] == 1
        assert metadata["compliant_count"] == 1
        assert metadata["non_compliant_count"] == 2
        assert metadata["error_message"] == "Check failed"

    def test_to_dict_empty(self):
        """Test to_dict with empty context."""
        context = PolicyContext()
        result = context.to_dict()
        
        assert "analyzer" in result
        assert "license_headers" in result
        assert "metadata" in result
        assert result["analyzer"]["status"] == "not_run"
        assert result["license_headers"]["status"] == "not_run"
        assert result["metadata"] == {}

    def test_to_dict_with_data(self):
        """Test to_dict with populated context."""
        context = PolicyContext()
        
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="1.0.0",
            command=["repo-analyzer"],
        )
        
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="2.0.0",
            command=["license-header", "check"],
            compliant_files=["file1.py"],
            non_compliant_files=[],
        )
        
        context.metadata = {"key": "value"}
        
        result = context.to_dict()
        
        assert result["analyzer"]["status"] == "success"
        assert result["analyzer"]["version"] == "1.0.0"
        assert result["license_headers"]["status"] == "success"
        assert result["license_headers"]["version"] == "2.0.0"
        assert result["metadata"]["key"] == "value"

    def test_metadata_field(self):
        """Test storing custom metadata."""
        context = PolicyContext()
        context.metadata["custom_key"] = "custom_value"
        context.metadata["another_key"] = {"nested": "data"}
        
        assert context.metadata["custom_key"] == "custom_value"
        assert context.metadata["another_key"]["nested"] == "data"
