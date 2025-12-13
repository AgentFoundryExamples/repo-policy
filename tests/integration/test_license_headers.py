"""Tests for license header integration."""

import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from integration.license_headers import LicenseHeaderChecker, LicenseHeaderResult


class TestLicenseHeaderChecker:
    """Test LicenseHeaderChecker functionality."""

    def test_init_default(self):
        """Test initialization with defaults."""
        checker = LicenseHeaderChecker()
        # Binary path depends on system, just check it's set or None
        assert checker.binary_path is None or isinstance(checker.binary_path, str)

    def test_init_custom_binary(self):
        """Test initialization with custom binary path."""
        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")
        assert checker.binary_path == "/usr/bin/license-header"

    @patch("integration.license_headers.shutil.which")
    def test_find_binary_found(self, mock_which):
        """Test finding license-header in PATH."""
        mock_which.return_value = "/usr/bin/license-header"
        checker = LicenseHeaderChecker()
        assert checker.binary_path == "/usr/bin/license-header"

    @patch("integration.license_headers.shutil.which")
    def test_find_binary_not_found(self, mock_which):
        """Test when license-header is not in PATH."""
        mock_which.return_value = None
        checker = LicenseHeaderChecker()
        assert checker.binary_path is None

    @patch("integration.license_headers.subprocess.run")
    def test_get_version_success(self, mock_run):
        """Test getting version."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="license-header 2.0.0\n",
        )
        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")
        version = checker._get_version()
        assert version == "license-header 2.0.0"

    @patch("integration.license_headers.subprocess.run")
    def test_get_version_failure(self, mock_run):
        """Test getting version when command fails."""
        mock_run.side_effect = FileNotFoundError()
        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")
        version = checker._get_version()
        assert version is None

    def test_check_without_binary(self, tmp_path):
        """Test check when binary is not available."""
        checker = LicenseHeaderChecker(binary_path=None)
        result = checker.check(
            target_path=tmp_path,
            outdir=tmp_path / "output",
            spdx_id="Apache-2.0",
            header_template_path="LICENSE_HEADER",
            keep_artifacts=False,
        )

        assert not result.success
        assert result.exit_code == -1
        assert "not found" in result.error_message

    def test_check_template_not_found(self, tmp_path):
        """Test check when header template doesn't exist."""
        target = tmp_path / "repo"
        target.mkdir()

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="NONEXISTENT",
                keep_artifacts=False,
            )

        assert not result.success
        assert result.exit_code == -1
        assert "not found" in result.error_message

    def test_check_template_default_locations(self, tmp_path):
        """Test check with default template locations."""
        target = tmp_path / "repo"
        target.mkdir()

        # Create LICENSE_HEADER in target
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            with patch("integration.license_headers.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="All files compliant",
                    stderr="",
                )

                result = checker.check(
                    target_path=target,
                    outdir=tmp_path / "output",
                    spdx_id="Apache-2.0",
                    header_template_path=None,  # Use default
                    keep_artifacts=False,
                )

        assert result.success
        # Should have used LICENSE_HEADER
        assert "--header" in result.command

    @patch("integration.license_headers.subprocess.run")
    def test_check_success_all_compliant(self, mock_run, tmp_path):
        """Test successful check with all files compliant."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All files compliant",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=False,
            )

        assert result.success
        assert result.exit_code == 0
        assert result.version == "2.0.0"
        assert "check" in result.command

    @patch("integration.license_headers.subprocess.run")
    def test_check_non_compliant_files(self, mock_run, tmp_path):
        """Test check with non-compliant files."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.return_value = MagicMock(
            returncode=1,  # Exit code 1 for non-compliant
            stdout="Some files missing headers",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=False,
            )

        # Exit code 1 is expected for non-compliant files, not an error
        assert not result.success
        assert result.exit_code == 1
        assert result.error_message is None  # Not a tool error

    @patch("integration.license_headers.subprocess.run")
    def test_check_with_include_globs(self, mock_run, tmp_path):
        """Test check with include glob patterns."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Check complete",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                include_globs=["**/*.py", "**/*.js"],
                keep_artifacts=False,
            )

        assert result.success
        # Should have include-extension flags
        assert "--include-extension" in result.command
        assert ".py" in result.command
        assert ".js" in result.command

    @patch("integration.license_headers.subprocess.run")
    def test_check_with_exclude_globs(self, mock_run, tmp_path):
        """Test check with exclude glob patterns."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Check complete",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                exclude_globs=["**/test_*.py", "dist/**"],
                keep_artifacts=False,
            )

        assert result.success
        # Should have exclude-path flags
        assert "--exclude-path" in result.command
        assert "**/test_*.py" in result.command
        assert "dist/**" in result.command

    @patch("integration.license_headers.subprocess.run")
    def test_check_with_keep_artifacts(self, mock_run, tmp_path):
        """Test check with keep_artifacts=True."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")
        outdir = tmp_path / "output"

        # Create mock report
        report_dir = outdir / "license-headers"
        report_dir.mkdir(parents=True)
        report_file = report_dir / "license-header-check-report.json"
        report_data = {
            "files": {
                "compliant": ["src/main.py", "src/utils.py"],
                "non_compliant": ["src/new.py"],
                "skipped": ["dist/bundle.js"],
                "failed": [],
            },
            "summary": {
                "scanned": 4,
                "eligible": 3,
                "compliant": 2,
                "non_compliant": 1,
                "skipped": 1,
                "failed": 0,
            },
        }
        report_file.write_text(json.dumps(report_data))

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Check complete",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=outdir,
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=True,
            )

        # Should have parsed the report
        assert len(result.compliant_files) == 2
        assert len(result.non_compliant_files) == 1
        assert len(result.skipped_files) == 1
        assert result.summary["compliant"] == 2
        assert "--output" in result.command

    @patch("integration.license_headers.subprocess.run")
    def test_check_timeout(self, mock_run, tmp_path):
        """Test check with timeout."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=False,
            )

        assert not result.success
        assert result.exit_code == -1
        assert "timed out" in result.error_message

    @patch("integration.license_headers.subprocess.run")
    def test_check_tool_error(self, mock_run, tmp_path):
        """Test check when tool returns error exit code."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")

        mock_run.return_value = MagicMock(
            returncode=2,  # Not 0 or 1, indicates tool error
            stdout="",
            stderr="Error: invalid arguments",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=tmp_path / "output",
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=False,
            )

        assert not result.success
        assert result.exit_code == 2
        assert result.error_message == "Error: invalid arguments"

    @patch("integration.license_headers.subprocess.run")
    def test_check_report_parse_error(self, mock_run, tmp_path):
        """Test check with invalid report JSON."""
        target = tmp_path / "repo"
        target.mkdir()
        (target / "LICENSE_HEADER").write_text("Copyright 2025")
        outdir = tmp_path / "output"

        # Create invalid report
        report_dir = outdir / "license-headers"
        report_dir.mkdir(parents=True)
        report_file = report_dir / "license-header-check-report.json"
        report_file.write_text("invalid json{")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Check complete",
            stderr="",
        )

        checker = LicenseHeaderChecker(binary_path="/usr/bin/license-header")

        with patch.object(checker, "_get_version", return_value="2.0.0"):
            result = checker.check(
                target_path=target,
                outdir=outdir,
                spdx_id="Apache-2.0",
                header_template_path="LICENSE_HEADER",
                keep_artifacts=True,
            )

        # Should still succeed, just without parsed data
        assert result.success
        assert result.compliant_files == []
        assert result.non_compliant_files == []


class TestLicenseHeaderResult:
    """Test LicenseHeaderResult dataclass."""

    def test_license_header_result_creation(self):
        """Test creating a LicenseHeaderResult."""
        result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="2.0.0",
            command=["license-header", "check"],
            compliant_files=["file1.py", "file2.py"],
            non_compliant_files=[],
        )

        assert result.success
        assert result.exit_code == 0
        assert result.version == "2.0.0"
        assert len(result.compliant_files) == 2
        assert not result.skipped

    def test_license_header_result_defaults(self):
        """Test default values for LicenseHeaderResult."""
        result = LicenseHeaderResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="error",
        )

        assert result.version is None
        assert result.command == []
        assert result.compliant_files == []
        assert result.non_compliant_files == []
        assert result.skipped_files == []
        assert result.failed_files == []
        assert result.summary == {}
        assert result.error_message is None
        assert not result.skipped

    def test_license_header_result_skipped(self):
        """Test skipped result."""
        result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )

        assert result.success
        assert result.skipped
