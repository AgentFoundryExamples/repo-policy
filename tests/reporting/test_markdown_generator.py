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
"""Tests for Markdown report generator."""

from pathlib import Path
from unittest.mock import patch

import pytest

from reporting.markdown_generator import (
    generate_markdown_report,
    _format_overview,
    _format_failures,
    _format_passed,
    _format_skipped,
    _format_evidence,
    _format_artifacts,
)
from rules.engine import RuleEngineResult
from rules.result import RuleResult, RuleStatus, RuleSeverity
from integration.context import PolicyContext
from integration.repo_analyzer import AnalyzerResult
from integration.license_headers import LicenseHeaderResult


class TestFormatOverview:
    """Tests for _format_overview."""

    def test_format_overview_all_passed(self):
        """Test overview with all rules passed."""
        engine_result = RuleEngineResult()
        engine_result.total_rules = 5
        engine_result.passed_rules = 5
        engine_result.failed_rules = 0
        engine_result.skipped_rules = 0
        engine_result.error_count = 0
        engine_result.warning_count = 0
        
        metadata = {
            "repo_path": "/test/repo",
            "config_file": "test.yml",
        }
        
        output = _format_overview(engine_result, metadata)
        
        assert "## Overview" in output
        assert "**Total Rules:** 5" in output
        assert "**Passed:** 5" in output
        assert "**Failed:** 0" in output
        assert "✅ PASS" in output

    def test_format_overview_with_errors(self):
        """Test overview with error failures."""
        engine_result = RuleEngineResult()
        engine_result.total_rules = 5
        engine_result.passed_rules = 3
        engine_result.failed_rules = 2
        engine_result.skipped_rules = 0
        engine_result.error_count = 2
        engine_result.warning_count = 0
        
        metadata = {"repo_path": "/test/repo", "config_file": "test.yml"}
        
        output = _format_overview(engine_result, metadata)
        
        assert "❌ FAIL" in output
        assert "Errors: 2" in output

    def test_format_overview_with_metadata(self):
        """Test overview includes all metadata fields."""
        engine_result = RuleEngineResult()
        
        metadata = {
            "repo_path": "/test/repo",
            "config_file": "test.yml",
            "commit_hash": "abc123def456",
            "config_hash": "7d2e6a18538da4d62b05942115df5b1b0ccfae2a193b5016893a479230ca54d7",
            "analyzer_version": "1.0.0",
            "license_header_tool_version": "2.0.0",
        }
        
        output = _format_overview(engine_result, metadata)
        
        assert "**Repository:** `/test/repo`" in output
        assert "**Config File:** `test.yml`" in output
        assert "**Commit Hash:** `abc123def456`" in output
        assert "**Config Hash:** `7d2e6a18538d...`" in output
        assert "**Analyzer Version:** 1.0.0" in output
        assert "**License Header Tool Version:** 2.0.0" in output


class TestFormatFailures:
    """Tests for _format_failures."""

    def test_format_failures_single_error(self):
        """Test formatting single error failure."""
        failures = [
            RuleResult(
                rule_id="test-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.FAIL,
                message="Test failed",
                evidence={"key": "value"},
                remediation="Fix the issue",
            )
        ]
        
        output = _format_failures(failures)
        
        assert "## Failures" in output
        assert "🔴 test-rule" in output
        assert "**Severity:** ERROR" in output
        assert "**Message:** Test failed" in output
        assert "**Evidence:**" in output
        assert "**Remediation:**" in output
        assert "Fix the issue" in output

    def test_format_failures_single_warning(self):
        """Test formatting single warning failure."""
        failures = [
            RuleResult(
                rule_id="warning-rule",
                severity=RuleSeverity.WARNING,
                status=RuleStatus.FAIL,
                message="Warning issued",
            )
        ]
        
        output = _format_failures(failures)
        
        assert "⚠️ warning-rule" in output
        assert "**Severity:** WARNING" in output

    def test_format_failures_sorted_by_severity(self):
        """Test failures are sorted by severity (errors first)."""
        failures = [
            RuleResult(
                rule_id="warning-rule",
                severity=RuleSeverity.WARNING,
                status=RuleStatus.FAIL,
                message="Warning",
            ),
            RuleResult(
                rule_id="error-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.FAIL,
                message="Error",
            ),
        ]
        
        output = _format_failures(failures)
        
        # Error should appear before warning
        error_pos = output.find("error-rule")
        warning_pos = output.find("warning-rule")
        assert error_pos < warning_pos


class TestFormatPassed:
    """Tests for _format_passed."""

    def test_format_passed_empty(self):
        """Test formatting with no passed rules."""
        passed = []
        
        output = _format_passed(passed)
        
        assert "## Passed Rules" in output

    def test_format_passed_multiple(self):
        """Test formatting multiple passed rules."""
        passed = [
            RuleResult(
                rule_id="zebra-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Z passed",
            ),
            RuleResult(
                rule_id="alpha-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="A passed",
            ),
        ]
        
        output = _format_passed(passed)
        
        assert "## Passed Rules" in output
        assert "✅ `alpha-rule`" in output
        assert "✅ `zebra-rule`" in output
        
        # Check sorting
        alpha_pos = output.find("alpha-rule")
        zebra_pos = output.find("zebra-rule")
        assert alpha_pos < zebra_pos


class TestFormatSkipped:
    """Tests for _format_skipped."""

    def test_format_skipped_empty(self):
        """Test formatting with no skipped rules."""
        skipped = []
        
        output = _format_skipped(skipped)
        
        assert "## Skipped Rules" in output

    def test_format_skipped_multiple(self):
        """Test formatting multiple skipped rules."""
        skipped = [
            RuleResult(
                rule_id="skip-b",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.SKIP,
                message="B skipped",
            ),
            RuleResult(
                rule_id="skip-a",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.SKIP,
                message="A skipped",
            ),
        ]
        
        output = _format_skipped(skipped)
        
        assert "⏭️ `skip-a`" in output
        assert "⏭️ `skip-b`" in output


class TestFormatEvidence:
    """Tests for _format_evidence."""

    def test_format_evidence_simple_values(self):
        """Test formatting evidence with simple values."""
        evidence = {
            "string_key": "value",
            "int_key": 42,
            "bool_key": True,
        }
        
        output = _format_evidence(evidence)
        
        assert "**bool_key:** `True`" in output
        assert "**int_key:** `42`" in output
        assert "**string_key:** `value`" in output

    def test_format_evidence_list_small(self):
        """Test formatting evidence with small list."""
        evidence = {
            "files": ["file1.py", "file2.py"],
        }
        
        output = _format_evidence(evidence)
        
        assert "**files:** (2 items)" in output
        assert "`file1.py`" in output
        assert "`file2.py`" in output

    def test_format_evidence_list_large(self):
        """Test formatting evidence with large list (should be truncated)."""
        # Create a list with more than MAX_EVIDENCE_ITEMS items
        evidence = {
            "files": [f"file{i}.py" for i in range(30)],
        }
        
        output = _format_evidence(evidence)
        
        assert "**files:** (30 items, showing first 20)" in output
        assert "... and 10 more" in output

    def test_format_evidence_dict(self):
        """Test formatting evidence with nested dict."""
        evidence = {
            "details": {
                "count": 5,
                "type": "test",
            }
        }
        
        output = _format_evidence(evidence)
        
        assert "**details:**" in output
        assert "count: `5`" in output
        assert "type: `test`" in output

    def test_format_evidence_sorted_keys(self):
        """Test evidence keys are sorted."""
        evidence = {
            "zebra": "z",
            "alpha": "a",
            "beta": "b",
        }
        
        output = _format_evidence(evidence)
        
        lines = output.split("\n")
        # Find positions of keys
        alpha_idx = next(i for i, line in enumerate(lines) if "alpha" in line)
        beta_idx = next(i for i, line in enumerate(lines) if "beta" in line)
        zebra_idx = next(i for i, line in enumerate(lines) if "zebra" in line)
        
        assert alpha_idx < beta_idx < zebra_idx


class TestFormatArtifacts:
    """Tests for _format_artifacts."""

    def test_format_artifacts_empty(self):
        """Test formatting with no artifacts."""
        context = PolicyContext()
        
        output = _format_artifacts(context)
        
        assert "## Artifacts" in output
        assert "No integration artifacts were generated" in output

    def test_format_artifacts_with_analyzer(self):
        """Test formatting with analyzer artifacts."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["repo-analyzer"],
            version="1.0.0",
            output_files=["report.json"],
        )
        
        output = _format_artifacts(context)
        
        assert "### Repository Analyzer" in output
        assert "**Status:** ✅ Success" in output
        assert "**Version:** 1.0.0" in output
        assert "`report.json`" in output

    def test_format_artifacts_with_license_headers_skipped(self):
        """Test formatting with skipped license headers."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )
        
        output = _format_artifacts(context)
        
        assert "### License Headers" in output
        assert "**Status:** ⏭️ Skipped (not required)" in output


class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report."""

    def test_generate_markdown_report_basic(self, tmp_path):
        """Test generating a basic Markdown report."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path = tmp_path / "report.md"
        
        engine_result = RuleEngineResult()
        engine_result.total_rules = 1
        engine_result.passed_rules = 1
        engine_result.results = [
            RuleResult(
                rule_id="test-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Test passed",
            )
        ]
        
        context = PolicyContext()
        
        generate_markdown_report(
            rule_results=engine_result,
            context=context,
            repo_path=tmp_path,
            config_path=str(config_file),
            output_path=output_path,
        )
        
        assert output_path.exists()
        
        content = output_path.read_text()
        
        assert "# Policy Check Report" in content
        assert "## Overview" in content
        assert "## Passed Rules" in content
        assert "## Artifacts" in content
        assert "## Command Guidance" in content

    def test_generate_markdown_report_with_failures(self, tmp_path):
        """Test generating Markdown report with failures."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path = tmp_path / "report.md"
        
        engine_result = RuleEngineResult()
        engine_result.total_rules = 2
        engine_result.passed_rules = 1
        engine_result.failed_rules = 1
        engine_result.error_count = 1
        engine_result.results = [
            RuleResult(
                rule_id="pass-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Passed",
            ),
            RuleResult(
                rule_id="fail-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.FAIL,
                message="Failed",
                evidence={"reason": "bad"},
                remediation="Fix it",
            ),
        ]
        
        context = PolicyContext()
        
        generate_markdown_report(
            rule_results=engine_result,
            context=context,
            repo_path=tmp_path,
            config_path=str(config_file),
            output_path=output_path,
        )
        
        content = output_path.read_text()
        
        assert "## Failures" in content
        assert "🔴 fail-rule" in content
        assert "**Remediation:**" in content

    def test_generate_markdown_report_deterministic(self, tmp_path):
        """Test Markdown report structure is deterministic."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path1 = tmp_path / "report1.md"
        output_path2 = tmp_path / "report2.md"
        
        engine_result = RuleEngineResult()
        engine_result.total_rules = 2
        engine_result.passed_rules = 2
        engine_result.results = [
            RuleResult(
                rule_id="zebra-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Z",
            ),
            RuleResult(
                rule_id="alpha-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="A",
            ),
        ]
        
        context = PolicyContext()
        
        from datetime import datetime, timezone
        from unittest.mock import Mock
        
        with patch("reporting.markdown_generator.datetime") as mock_dt:
            # Mock datetime.now(timezone.utc).strftime()
            mock_now = Mock()
            mock_now.strftime.return_value = "2025-01-01 00:00:00"
            mock_dt.now.return_value = mock_now
            mock_dt.timezone = timezone
            
            generate_markdown_report(
                rule_results=engine_result,
                context=context,
                repo_path=tmp_path,
                config_path=str(config_file),
                output_path=output_path1,
            )
            
            generate_markdown_report(
                rule_results=engine_result,
                context=context,
                repo_path=tmp_path,
                config_path=str(config_file),
                output_path=output_path2,
            )
        
        content1 = output_path1.read_text()
        content2 = output_path2.read_text()
        
        # Should be identical when timestamp is mocked
        assert content1 == content2
