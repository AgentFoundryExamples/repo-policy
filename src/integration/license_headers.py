"""
License header tool integration for checking header compliance.

This module provides integration with the license-header tool to check
whether source files have the required license headers. It runs the tool
in dry-run/check mode only to avoid modifying files.
"""

import logging
import shutil
import subprocess
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class LicenseHeaderResult:
    """Result from running the license header checker."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    version: Optional[str] = None
    command: List[str] = field(default_factory=list)
    compliant_files: List[str] = field(default_factory=list)
    non_compliant_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None
    skipped: bool = False  # True if check was skipped due to config


class LicenseHeaderChecker:
    """
    Checker for license headers in source files.

    Integrates with the license-header tool in dry-run/check mode to verify
    header compliance without modifying files.
    """

    def __init__(
        self,
        binary_path: Optional[str] = None,
    ):
        """
        Initialize the license header checker.

        Args:
            binary_path: Path to license-header binary (None = auto-detect)
        """
        self.binary_path = binary_path or self._find_binary()

    def _find_binary(self) -> Optional[str]:
        """
        Find the license-header binary in PATH.

        Returns:
            Path to binary or None if not found
        """
        binary = shutil.which("license-header")
        if not binary:
            logger.debug("license-header tool not found in PATH")
        return binary

    def _get_version(self) -> Optional[str]:
        """
        Get the version of the license-header tool.

        Returns:
            Version string or None if unavailable
        """
        if not self.binary_path:
            return None

        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug(f"Could not get license-header version: {e}")

        return None

    def check(
        self,
        target_path: Path,
        outdir: Path,
        spdx_id: Optional[str],
        header_template_path: Optional[str],
        include_globs: Optional[List[str]] = None,
        exclude_globs: Optional[List[str]] = None,
        keep_artifacts: bool = False,
    ) -> LicenseHeaderResult:
        """
        Check license headers in the target repository.

        Args:
            target_path: Path to repository to check
            outdir: Output directory for reports
            spdx_id: SPDX license identifier
            header_template_path: Path to header template file
            include_globs: File patterns to include
            exclude_globs: File patterns to exclude
            keep_artifacts: Keep report artifacts after check

        Returns:
            LicenseHeaderResult with compliance data
        """
        if not self.binary_path:
            return LicenseHeaderResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=(
                    "license-header tool not found. "
                    "Please install it or provide the binary path in configuration."
                ),
            )

        # Get version for metadata
        version = self._get_version()

        # Resolve header template path
        if header_template_path:
            header_path = Path(header_template_path)
            if not header_path.is_absolute():
                header_path = target_path / header_path

            if not header_path.exists():
                return LicenseHeaderResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    version=version,
                    error_message=f"Header template file not found: {header_path}",
                )
        else:
            # Try default location
            header_path = target_path / "LICENSE_HEADER"
            if not header_path.exists():
                header_path = target_path / "LICENSE_HEADER.md"

            if not header_path.exists():
                return LicenseHeaderResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    version=version,
                    error_message=(
                        "No header template file found. "
                        "Expected LICENSE_HEADER or LICENSE_HEADER.md in repository root, "
                        "or specify header_template_path in configuration."
                    ),
                )

        # Build command for check mode
        cmd = [
            self.binary_path,
            "check",
            "--path",
            str(target_path),
            "--header",
            str(header_path),
        ]

        # Add output directory for reports if keeping artifacts
        if keep_artifacts:
            outdir.mkdir(parents=True, exist_ok=True)
            report_dir = outdir / "license-headers"
            report_dir.mkdir(exist_ok=True)
            cmd.extend(["--output", str(report_dir)])

        # Add include extensions if specified
        if include_globs:
            for glob in include_globs:
                # Convert glob to extension format expected by license-header tool
                if glob.startswith("**/*"):
                    ext = glob[4:]  # Extract extension like .py from **/*.py
                    cmd.extend(["--include-extension", ext])

        # Add exclude paths if specified
        if exclude_globs:
            for glob in exclude_globs:
                cmd.extend(["--exclude-path", glob])

        logger.info(f"Running license-header check: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(target_path),
            )

            # Parse output files if they exist
            compliant_files = []
            non_compliant_files = []
            skipped_files = []
            failed_files = []
            summary = {}

            if keep_artifacts:
                report_file = report_dir / "license-header-check-report.json"
                if report_file.exists():
                    try:
                        with open(report_file, "r") as f:
                            report_data = json.load(f)
                            compliant_files = report_data.get("files", {}).get("compliant", [])
                            non_compliant_files = report_data.get("files", {}).get(
                                "non_compliant", []
                            )
                            skipped_files = report_data.get("files", {}).get("skipped", [])
                            failed_files = report_data.get("files", {}).get("failed", [])
                            summary = report_data.get("summary", {})
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Could not parse license-header report: {e}")

            # Exit code 0 means all files compliant, 1 means some non-compliant
            success = result.returncode == 0

            return LicenseHeaderResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                version=version,
                command=cmd,
                compliant_files=compliant_files,
                non_compliant_files=non_compliant_files,
                skipped_files=skipped_files,
                failed_files=failed_files,
                summary=summary,
                error_message=result.stderr if result.returncode not in (0, 1) else None,
            )

        except subprocess.TimeoutExpired:
            error_msg = "license-header check timed out after 5 minutes"
            logger.error(error_msg)
            return LicenseHeaderResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                version=version,
                command=cmd,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Failed to run license-header check: {e}"
            logger.error(error_msg)
            return LicenseHeaderResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                version=version,
                command=cmd,
                error_message=error_msg,
            )
