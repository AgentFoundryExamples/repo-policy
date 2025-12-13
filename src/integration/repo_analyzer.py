"""
Repo analyzer integration for extracting repository metadata.

This module provides a runner abstraction that can invoke the repo analyzer
tool in different modes (temp workspace or direct output) while keeping the
working tree clean by default.
"""

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerResult:
    """Result from running the repo analyzer."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    version: Optional[str] = None
    command: List[str] = field(default_factory=list)
    output_files: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None


class RepoAnalyzerRunner:
    """
    Runner for the repo analyzer tool.

    Supports different execution modes:
    - temp_workspace: Clone to temp directory, analyze there, copy outputs
    - direct_output: Write outputs directly to outdir (working tree stays clean)
    """

    def __init__(
        self,
        analyzer_binary: Optional[str] = None,
        workspace_mode: str = "direct_output",
    ):
        """
        Initialize the analyzer runner.

        Args:
            analyzer_binary: Path to analyzer binary (None = auto-detect)
            workspace_mode: 'temp_workspace' or 'direct_output'
        """
        self.analyzer_binary = analyzer_binary or self._find_analyzer()
        self.workspace_mode = workspace_mode

    def _find_analyzer(self) -> Optional[str]:
        """
        Find the repo analyzer binary in PATH.

        Returns:
            Path to analyzer binary or None if not found
        """
        analyzer = shutil.which("repo-analyzer")
        if not analyzer:
            logger.debug("repo-analyzer not found in PATH")
        return analyzer

    def _get_version(self) -> Optional[str]:
        """
        Get the version of the repo analyzer.

        Returns:
            Version string or None if unavailable
        """
        if not self.analyzer_binary:
            return None

        try:
            result = subprocess.run(
                [self.analyzer_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug(f"Could not get analyzer version: {e}")

        return None

    def run(
        self,
        target_path: Path,
        outdir: Path,
        keep_artifacts: bool = False,
    ) -> AnalyzerResult:
        """
        Run the repo analyzer on the target repository.

        Args:
            target_path: Path to the repository to analyze
            outdir: Output directory for analyzer artifacts
            keep_artifacts: Keep artifacts after run (if False, cleanup unless error)

        Returns:
            AnalyzerResult with execution metadata and outputs
        """
        if not self.analyzer_binary:
            return AnalyzerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=(
                    "repo-analyzer tool not found. "
                    "Please install it or provide the binary path in configuration."
                ),
            )

        # Get version for metadata
        version = self._get_version()

        if self.workspace_mode == "temp_workspace":
            return self._run_temp_workspace(target_path, outdir, keep_artifacts, version)
        else:
            return self._run_direct_output(target_path, outdir, keep_artifacts, version)

    def _run_direct_output(
        self,
        target_path: Path,
        outdir: Path,
        keep_artifacts: bool,
        version: Optional[str],
    ) -> AnalyzerResult:
        """
        Run analyzer with direct output to outdir.

        Args:
            target_path: Repository path
            outdir: Output directory
            keep_artifacts: Keep artifacts after run
            version: Analyzer version

        Returns:
            AnalyzerResult
        """
        outdir.mkdir(parents=True, exist_ok=True)
        analyzer_outdir = outdir / "analyzer"
        analyzer_outdir.mkdir(exist_ok=True)

        cmd = [
            self.analyzer_binary,
            "--path",
            str(target_path),
            "--output",
            str(analyzer_outdir),
        ]

        logger.info(f"Running repo-analyzer in direct output mode: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(target_path),
            )

            output_files = self._collect_output_files(analyzer_outdir)

            # Cleanup artifacts if requested and successful
            if not keep_artifacts and result.returncode == 0:
                logger.debug(f"Cleaning up analyzer artifacts: {analyzer_outdir}")
                shutil.rmtree(analyzer_outdir, ignore_errors=True)
                output_files = {}  # Clear since we cleaned up

            return AnalyzerResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                version=version,
                command=cmd,
                output_files=output_files,
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            error_msg = "repo-analyzer timed out after 5 minutes"
            logger.error(error_msg)
            return AnalyzerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                version=version,
                command=cmd,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Failed to run repo-analyzer: {e}"
            logger.error(error_msg)
            return AnalyzerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                version=version,
                command=cmd,
                error_message=error_msg,
            )

    def _run_temp_workspace(
        self,
        target_path: Path,
        outdir: Path,
        keep_artifacts: bool,
        version: Optional[str],
    ) -> AnalyzerResult:
        """
        Run analyzer in a temporary workspace.

        Args:
            target_path: Repository path
            outdir: Output directory for results
            keep_artifacts: Keep artifacts after run
            version: Analyzer version

        Returns:
            AnalyzerResult
        """
        temp_dir = None
        try:
            # Create temp directory for the analysis
            temp_dir = Path(tempfile.mkdtemp(prefix="repo-policy-analyzer-"))
            logger.debug(f"Created temp workspace: {temp_dir}")

            # Clone repository to temp directory
            logger.info(f"Cloning {target_path} to temp workspace...")
            clone_result = subprocess.run(
                ["git", "clone", "--quiet", str(target_path), str(temp_dir / "repo")],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if clone_result.returncode != 0:
                error_msg = f"Failed to clone repository: {clone_result.stderr}"
                logger.error(error_msg)
                return AnalyzerResult(
                    success=False,
                    exit_code=clone_result.returncode,
                    stdout=clone_result.stdout,
                    stderr=clone_result.stderr,
                    version=version,
                    error_message=error_msg,
                )

            # Run analyzer in temp workspace
            temp_repo = temp_dir / "repo"
            temp_output = temp_dir / "output"
            temp_output.mkdir()

            cmd = [
                self.analyzer_binary,
                "--path",
                str(temp_repo),
                "--output",
                str(temp_output),
            ]

            logger.info(f"Running repo-analyzer in temp workspace: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(temp_repo),
            )

            # Copy outputs to outdir if keeping artifacts
            output_files = {}
            if keep_artifacts and result.returncode == 0:
                outdir.mkdir(parents=True, exist_ok=True)
                analyzer_outdir = outdir / "analyzer"
                if temp_output.exists():
                    shutil.copytree(temp_output, analyzer_outdir, dirs_exist_ok=True)
                    output_files = self._collect_output_files(analyzer_outdir)
                    logger.info(f"Copied analyzer outputs to {analyzer_outdir}")

            return AnalyzerResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                version=version,
                command=cmd,
                output_files=output_files,
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            error_msg = "Operation timed out after 5 minutes"
            logger.error(error_msg)
            return AnalyzerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                version=version,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Failed to run analyzer in temp workspace: {e}"
            logger.error(error_msg)
            return AnalyzerResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                version=version,
                error_message=error_msg,
            )
        finally:
            # Always cleanup temp directory
            if temp_dir and temp_dir.exists():
                logger.debug(f"Cleaning up temp workspace: {temp_dir}")
                try:
                    shutil.rmtree(temp_dir)
                except OSError as e:
                    logger.warning(
                        f"Failed to clean up temp workspace {temp_dir}: {e}. "
                        f"Manual cleanup may be required."
                    )

    def _collect_output_files(self, outdir: Path) -> Dict[str, str]:
        """
        Collect paths to output files from the analyzer.

        Args:
            outdir: Analyzer output directory

        Returns:
            Dictionary mapping file type to path
        """
        output_files = {}

        if not outdir.exists():
            return output_files

        # Common analyzer output files
        common_files = {
            "tree": "tree.json",
            "dependencies": "dependencies.json",
            "metadata": "metadata.json",
            "summary": "summary.json",
        }

        for file_type, filename in common_files.items():
            file_path = outdir / filename
            if file_path.exists():
                output_files[file_type] = str(file_path)

        return output_files
