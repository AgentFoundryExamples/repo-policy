"""Tests for repo analyzer integration."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from integration.repo_analyzer import RepoAnalyzerRunner, AnalyzerResult


class TestRepoAnalyzerRunner:
    """Test RepoAnalyzerRunner functionality."""

    def test_init_default(self):
        """Test initialization with defaults."""
        runner = RepoAnalyzerRunner()
        assert runner.workspace_mode == "direct_output"

    def test_init_custom_mode(self):
        """Test initialization with custom workspace mode."""
        runner = RepoAnalyzerRunner(workspace_mode="temp_workspace")
        assert runner.workspace_mode == "temp_workspace"

    @patch("integration.repo_analyzer.shutil.which")
    def test_find_analyzer_found(self, mock_which):
        """Test finding analyzer in PATH."""
        mock_which.return_value = "/usr/bin/repo-analyzer"
        runner = RepoAnalyzerRunner()
        assert runner.analyzer_binary == "/usr/bin/repo-analyzer"

    @patch("integration.repo_analyzer.shutil.which")
    def test_find_analyzer_not_found(self, mock_which):
        """Test when analyzer is not in PATH."""
        mock_which.return_value = None
        runner = RepoAnalyzerRunner()
        assert runner.analyzer_binary is None

    @patch("integration.repo_analyzer.subprocess.run")
    def test_get_version_success(self, mock_run):
        """Test getting analyzer version."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="repo-analyzer 1.2.3\n",
        )
        runner = RepoAnalyzerRunner(analyzer_binary="/usr/bin/repo-analyzer")
        version = runner._get_version()
        assert version == "repo-analyzer 1.2.3"

    @patch("integration.repo_analyzer.subprocess.run")
    def test_get_version_failure(self, mock_run):
        """Test getting version when command fails."""
        mock_run.side_effect = FileNotFoundError()
        runner = RepoAnalyzerRunner(analyzer_binary="/usr/bin/repo-analyzer")
        version = runner._get_version()
        assert version is None

    def test_run_without_binary(self, tmp_path):
        """Test run when analyzer binary is not available."""
        runner = RepoAnalyzerRunner(analyzer_binary=None)
        result = runner.run(
            target_path=tmp_path,
            outdir=tmp_path / "output",
            keep_artifacts=False,
        )

        assert not result.success
        assert result.exit_code == -1
        assert "not found" in result.error_message

    @patch("integration.repo_analyzer.subprocess.run")
    def test_run_direct_output_success(self, mock_run, tmp_path):
        """Test successful run in direct output mode."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Analysis complete",
            stderr="",
        )

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="direct_output",
        )

        # Mock version check
        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=False,
            )

        assert result.success
        assert result.exit_code == 0
        assert result.version == "1.0.0"
        assert "--path" in result.command
        assert "--output" in result.command

    @patch("integration.repo_analyzer.subprocess.run")
    def test_run_direct_output_failure(self, mock_run, tmp_path):
        """Test failed run in direct output mode."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: invalid path",
        )

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="direct_output",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=False,
            )

        assert not result.success
        assert result.exit_code == 1
        assert result.error_message == "Error: invalid path"

    @patch("integration.repo_analyzer.subprocess.run")
    def test_run_direct_output_timeout(self, mock_run, tmp_path):
        """Test timeout in direct output mode."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="direct_output",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=False,
            )

        assert not result.success
        assert result.exit_code == -1
        assert "timed out" in result.error_message

    @patch("integration.repo_analyzer.subprocess.run")
    def test_run_with_keep_artifacts(self, mock_run, tmp_path):
        """Test run with keep_artifacts=True."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        # Create mock output files
        analyzer_outdir = outdir / "analyzer"
        analyzer_outdir.mkdir(parents=True)
        (analyzer_outdir / "tree.json").write_text('{"files": []}')
        (analyzer_outdir / "metadata.json").write_text('{"version": 1}')

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Analysis complete",
            stderr="",
        )

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="direct_output",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=True,
            )

        assert result.success
        assert "tree" in result.output_files
        assert "metadata" in result.output_files
        # Artifacts should still exist
        assert (analyzer_outdir / "tree.json").exists()

    @patch("integration.repo_analyzer.subprocess.run")
    @patch("integration.repo_analyzer.shutil.rmtree")
    def test_run_cleanup_on_success(self, mock_rmtree, mock_run, tmp_path):
        """Test artifact cleanup when keep_artifacts=False and successful."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Analysis complete",
            stderr="",
        )

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="direct_output",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=False,
            )

        assert result.success
        # Should cleanup artifacts
        mock_rmtree.assert_called_once()

    @patch("integration.repo_analyzer.subprocess.run")
    @patch("integration.repo_analyzer.shutil.copytree")
    @patch("integration.repo_analyzer.shutil.rmtree")
    @patch("integration.repo_analyzer.tempfile.mkdtemp")
    def test_run_temp_workspace_success(
        self, mock_mkdtemp, mock_rmtree, mock_copytree, mock_run, tmp_path
    ):
        """Test successful run in temp workspace mode."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)

        # Mock git clone and analyzer run
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # git clone
            MagicMock(returncode=0, stdout="Analysis done", stderr=""),  # analyzer
        ]

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="temp_workspace",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=True,
            )

        assert result.success
        # Should cleanup temp directory
        mock_rmtree.assert_called()

    @patch("integration.repo_analyzer.subprocess.run")
    @patch("integration.repo_analyzer.shutil.rmtree")
    @patch("integration.repo_analyzer.tempfile.mkdtemp")
    def test_run_temp_workspace_clone_failure(self, mock_mkdtemp, mock_rmtree, mock_run, tmp_path):
        """Test temp workspace mode when git clone fails."""
        target = tmp_path / "repo"
        target.mkdir()
        outdir = tmp_path / "output"

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)

        # Mock git clone failure
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: repository not found",
        )

        runner = RepoAnalyzerRunner(
            analyzer_binary="/usr/bin/repo-analyzer",
            workspace_mode="temp_workspace",
        )

        with patch.object(runner, "_get_version", return_value="1.0.0"):
            result = runner.run(
                target_path=target,
                outdir=outdir,
                keep_artifacts=False,
            )

        assert not result.success
        assert "Failed to clone" in result.error_message
        # Should still cleanup temp directory
        mock_rmtree.assert_called()

    def test_collect_output_files(self, tmp_path):
        """Test collecting output files."""
        outdir = tmp_path / "analyzer"
        outdir.mkdir()

        # Create some output files
        (outdir / "tree.json").write_text('{"files": []}')
        (outdir / "dependencies.json").write_text('{"deps": []}')
        (outdir / "metadata.json").write_text('{"meta": {}}')

        runner = RepoAnalyzerRunner()
        output_files = runner._collect_output_files(outdir)

        assert "tree" in output_files
        assert "dependencies" in output_files
        assert "metadata" in output_files
        assert output_files["tree"] == str(outdir / "tree.json")

    def test_collect_output_files_empty(self, tmp_path):
        """Test collecting output files from empty directory."""
        outdir = tmp_path / "analyzer"
        outdir.mkdir()

        runner = RepoAnalyzerRunner()
        output_files = runner._collect_output_files(outdir)

        assert output_files == {}

    def test_collect_output_files_nonexistent(self, tmp_path):
        """Test collecting output files when directory doesn't exist."""
        outdir = tmp_path / "nonexistent"

        runner = RepoAnalyzerRunner()
        output_files = runner._collect_output_files(outdir)

        assert output_files == {}


class TestAnalyzerResult:
    """Test AnalyzerResult dataclass."""

    def test_analyzer_result_creation(self):
        """Test creating an AnalyzerResult."""
        result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            version="1.0.0",
            command=["repo-analyzer", "--path", "."],
        )

        assert result.success
        assert result.exit_code == 0
        assert result.version == "1.0.0"
        assert len(result.command) == 3

    def test_analyzer_result_defaults(self):
        """Test default values for AnalyzerResult."""
        result = AnalyzerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="error",
        )

        assert result.version is None
        assert result.command == []
        assert result.output_files == {}
        assert result.error_message is None
