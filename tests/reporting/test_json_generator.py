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
"""Tests for JSON report generator."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from reporting.json_generator import generate_json_report, _format_rules, _format_artifacts
from rules.engine import RuleEngineResult
from rules.result import RuleResult, RuleStatus, RuleSeverity
from integration.context import PolicyContext
from integration.repo_analyzer import AnalyzerResult
from integration.license_headers import LicenseHeaderResult


class TestFormatRules:
    """Tests for _format_rules."""

    def test_format_rules_empty(self):
        """Test formatting empty rule results."""
        engine_result = RuleEngineResult()
        
        rules = _format_rules(engine_result)
        
        assert rules == []

    def test_format_rules_single(self):
        """Test formatting single rule result."""
        engine_result = RuleEngineResult()
        engine_result.results = [
            RuleResult(
                rule_id="test-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Test passed",
                evidence={"key": "value"},
                remediation="",
                rule_tags=["test"],
            )
        ]
        
        rules = _format_rules(engine_result)
        
        assert len(rules) == 1
        assert rules[0]["rule_id"] == "test-rule"
        assert rules[0]["severity"] == "error"
        assert rules[0]["status"] == "pass"
        assert rules[0]["message"] == "Test passed"
        assert rules[0]["evidence"] == {"key": "value"}
        assert rules[0]["tags"] == ["test"]

    def test_format_rules_sorted_by_id(self):
        """Test rules are sorted by rule_id for determinism."""
        engine_result = RuleEngineResult()
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
            RuleResult(
                rule_id="beta-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="B",
            ),
        ]
        
        rules = _format_rules(engine_result)
        
        assert len(rules) == 3
        assert rules[0]["rule_id"] == "alpha-rule"
        assert rules[1]["rule_id"] == "beta-rule"
        assert rules[2]["rule_id"] == "zebra-rule"

    def test_format_rules_tags_sorted(self):
        """Test rule tags are sorted."""
        engine_result = RuleEngineResult()
        engine_result.results = [
            RuleResult(
                rule_id="test-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.PASS,
                message="Test",
                rule_tags=["zebra", "alpha", "beta"],
            )
        ]
        
        rules = _format_rules(engine_result)
        
        assert rules[0]["tags"] == ["alpha", "beta", "zebra"]


class TestFormatArtifacts:
    """Tests for _format_artifacts."""

    def test_format_artifacts_empty_context(self):
        """Test formatting artifacts with empty context."""
        context = PolicyContext()
        
        artifacts = _format_artifacts(context)
        
        assert artifacts == {}

    def test_format_artifacts_with_analyzer_success(self):
        """Test formatting artifacts with successful analyzer."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["repo-analyzer"],
            version="1.0.0",
            output_files=["file2.json", "file1.json"],  # Intentionally unsorted
        )
        
        artifacts = _format_artifacts(context)
        
        assert "analyzer" in artifacts
        assert artifacts["analyzer"]["status"] == "success"
        assert artifacts["analyzer"]["version"] == "1.0.0"
        # Check that files are sorted
        assert artifacts["analyzer"]["output_files"] == ["file1.json", "file2.json"]

    def test_format_artifacts_with_analyzer_failure(self):
        """Test formatting artifacts with failed analyzer."""
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="",
            command=["repo-analyzer"],
            version="1.0.0",
            error_message="Tool not found",
        )
        
        artifacts = _format_artifacts(context)
        
        assert "analyzer" in artifacts
        assert artifacts["analyzer"]["status"] == "failed"
        assert artifacts["analyzer"]["error_message"] == "Tool not found"

    def test_format_artifacts_with_license_headers_success(self):
        """Test formatting artifacts with successful license headers."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["license-header"],
            version="2.0.0",
            compliant_files=["file2.py", "file1.py"],
            non_compliant_files=["bad2.py", "bad1.py"],
        )
        
        artifacts = _format_artifacts(context)
        
        assert "license_headers" in artifacts
        assert artifacts["license_headers"]["status"] == "success"
        assert artifacts["license_headers"]["version"] == "2.0.0"
        # Check that files are sorted
        assert artifacts["license_headers"]["compliant_files"] == ["file1.py", "file2.py"]
        assert artifacts["license_headers"]["non_compliant_files"] == ["bad1.py", "bad2.py"]

    def test_format_artifacts_with_license_headers_skipped(self):
        """Test formatting artifacts with skipped license headers."""
        context = PolicyContext()
        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )
        
        artifacts = _format_artifacts(context)
        
        assert "license_headers" in artifacts
        assert artifacts["license_headers"]["status"] == "skipped"


class TestGenerateJsonReport:
    """Tests for generate_json_report."""

    def test_generate_json_report_basic(self, tmp_path):
        """Test generating a basic JSON report."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path = tmp_path / "report.json"
        
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
        
        generate_json_report(
            rule_results=engine_result,
            context=context,
            repo_path=tmp_path,
            config_path=str(config_file),
            output_path=output_path,
        )
        
        assert output_path.exists()
        
        # Parse and validate JSON
        with output_path.open() as f:
            data = json.load(f)
        
        assert "version" in data
        assert "generated_at" in data
        assert "metadata" in data
        assert "summary" in data
        assert "rules" in data
        assert "artifacts" in data
        
        assert data["summary"]["total_rules"] == 1
        assert data["summary"]["passed_rules"] == 1
        assert len(data["rules"]) == 1

    def test_generate_json_report_deterministic(self, tmp_path):
        """Test JSON report is deterministic (same input produces same output)."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path1 = tmp_path / "report1.json"
        output_path2 = tmp_path / "report2.json"
        
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
        
        with patch("reporting.metadata.get_git_commit_hash") as mock_git:
            mock_git.return_value = "abc123"
            
            generate_json_report(
                rule_results=engine_result,
                context=context,
                repo_path=tmp_path,
                config_path=str(config_file),
                output_path=output_path1,
            )
            
            generate_json_report(
                rule_results=engine_result,
                context=context,
                repo_path=tmp_path,
                config_path=str(config_file),
                output_path=output_path2,
            )
        
        # Read both files and compare (excluding generated_at timestamp)
        with output_path1.open() as f:
            data1 = json.load(f)
        with output_path2.open() as f:
            data2 = json.load(f)
        
        # Remove timestamp for comparison
        del data1["generated_at"]
        del data2["generated_at"]
        
        assert data1 == data2

    def test_generate_json_report_with_all_data(self, tmp_path):
        """Test generating JSON report with all data populated."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("test: value\n")
        
        output_path = tmp_path / "report.json"
        
        engine_result = RuleEngineResult()
        engine_result.total_rules = 3
        engine_result.passed_rules = 1
        engine_result.failed_rules = 1
        engine_result.skipped_rules = 1
        engine_result.error_count = 1
        engine_result.warning_count = 0
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
            RuleResult(
                rule_id="skip-rule",
                severity=RuleSeverity.ERROR,
                status=RuleStatus.SKIP,
                message="Skipped",
            ),
        ]
        
        context = PolicyContext()
        context.analyzer_result = AnalyzerResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            command=["repo-analyzer"],
            version="1.0.0",
            output_files=["out.json"],
        )
        
        with patch("reporting.metadata.get_git_commit_hash") as mock_git:
            mock_git.return_value = "abc123def456"
            
            generate_json_report(
                rule_results=engine_result,
                context=context,
                repo_path=tmp_path,
                config_path=str(config_file),
                output_path=output_path,
            )
        
        with output_path.open() as f:
            data = json.load(f)
        
        assert data["metadata"]["commit_hash"] == "abc123def456"
        assert data["summary"]["error_count"] == 1
        assert len(data["rules"]) == 3
        assert data["artifacts"]["analyzer"]["version"] == "1.0.0"
