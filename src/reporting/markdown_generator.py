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
"""Markdown report generator for policy check results."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from rules.engine import RuleEngineResult
from rules.result import RuleResult, RuleStatus, RuleSeverity
from integration.context import PolicyContext
from reporting.metadata import extract_report_metadata

logger = logging.getLogger(__name__)

# Maximum number of evidence items to display before summarizing
MAX_EVIDENCE_ITEMS = 20


def generate_markdown_report(
    rule_results: RuleEngineResult,
    context: PolicyContext,
    repo_path: Path,
    config_path: str,
    output_path: Path,
) -> None:
    """
    Generate Markdown policy report.
    
    Args:
        rule_results: Results from rule engine evaluation
        context: Policy context with integration results
        repo_path: Path to repository
        config_path: Path to config file
        output_path: Path to write Markdown report
    """
    logger.info(f"Generating Markdown report: {output_path}")
    
    # Extract metadata
    metadata = extract_report_metadata(repo_path, config_path, context)
    
    # Build report sections
    sections = []
    
    # Header
    sections.append("# Policy Check Report\n")
    sections.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    sections.append("---\n")
    
    # Overview
    sections.append(_format_overview(rule_results, metadata))
    
    # Failures (errors and warnings)
    failures = [r for r in rule_results.results if r.status == RuleStatus.FAIL]
    if failures:
        sections.append(_format_failures(failures))
    
    # Passed rules
    passed = [r for r in rule_results.results if r.status == RuleStatus.PASS]
    if passed:
        sections.append(_format_passed(passed))
    
    # Skipped rules
    skipped = [r for r in rule_results.results if r.status == RuleStatus.SKIP]
    if skipped:
        sections.append(_format_skipped(skipped))
    
    # Artifacts
    sections.append(_format_artifacts(context))
    
    # Command guidance
    sections.append(_format_command_guidance())
    
    # Write Markdown file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(sections))
    
    logger.info(f"Markdown report written to: {output_path}")


def _format_overview(
    rule_results: RuleEngineResult,
    metadata: Dict[str, Any],
) -> str:
    """Format overview section."""
    lines = ["## Overview\n"]
    
    # Summary statistics
    lines.append("### Summary\n")
    lines.append(f"- **Total Rules:** {rule_results.total_rules}")
    lines.append(f"- **Passed:** {rule_results.passed_rules}")
    lines.append(f"- **Failed:** {rule_results.failed_rules}")
    lines.append(f"  - Errors: {rule_results.error_count}")
    lines.append(f"  - Warnings: {rule_results.warning_count}")
    lines.append(f"- **Skipped:** {rule_results.skipped_rules}")
    
    # Exit status
    status_emoji = "✅" if rule_results.error_count == 0 else "❌"
    status_text = "PASS" if rule_results.error_count == 0 else "FAIL"
    lines.append(f"\n**Status:** {status_emoji} {status_text}\n")
    
    # Metadata
    lines.append("### Metadata\n")
    lines.append(f"- **Repository:** `{metadata.get('repo_path', 'N/A')}`")
    lines.append(f"- **Config File:** `{metadata.get('config_file', 'N/A')}`")
    
    if "commit_hash" in metadata:
        lines.append(f"- **Commit Hash:** `{metadata['commit_hash']}`")
    
    if "config_hash" in metadata:
        lines.append(f"- **Config Hash:** `{metadata['config_hash'][:12]}...`")
    
    if "analyzer_version" in metadata:
        lines.append(f"- **Analyzer Version:** {metadata['analyzer_version']}")
    
    if "license_header_tool_version" in metadata:
        lines.append(f"- **License Header Tool Version:** {metadata['license_header_tool_version']}")
    
    lines.append("")
    return "\n".join(lines)


def _format_failures(failures: List[RuleResult]) -> str:
    """Format failures section."""
    lines = ["## Failures\n"]
    
    # Sort failures by severity (errors first) then by rule_id
    failures_sorted = sorted(
        failures,
        key=lambda r: (0 if r.severity == RuleSeverity.ERROR else 1, r.rule_id)
    )
    
    for result in failures_sorted:
        severity_emoji = "🔴" if result.severity == RuleSeverity.ERROR else "⚠️"
        lines.append(f"### {severity_emoji} {result.rule_id}\n")
        lines.append(f"**Severity:** {result.severity.value.upper()}\n")
        lines.append(f"**Message:** {result.message}\n")
        
        # Evidence
        if result.evidence:
            lines.append("**Evidence:**\n")
            lines.append(_format_evidence(result.evidence))
        
        # Remediation
        if result.remediation:
            lines.append("**Remediation:**\n")
            lines.append(f"{result.remediation}\n")
        
        lines.append("---\n")
    
    return "\n".join(lines)


def _format_passed(passed: List[RuleResult]) -> str:
    """Format passed rules section."""
    lines = ["## Passed Rules\n"]
    
    # Sort by rule_id for deterministic output
    passed_sorted = sorted(passed, key=lambda r: r.rule_id)
    
    lines.append("The following rules passed successfully:\n")
    for result in passed_sorted:
        lines.append(f"- ✅ `{result.rule_id}`: {result.message}")
    
    lines.append("")
    return "\n".join(lines)


def _format_skipped(skipped: List[RuleResult]) -> str:
    """Format skipped rules section."""
    lines = ["## Skipped Rules\n"]
    
    # Sort by rule_id for deterministic output
    skipped_sorted = sorted(skipped, key=lambda r: r.rule_id)
    
    lines.append("The following rules were skipped:\n")
    for result in skipped_sorted:
        lines.append(f"- ⏭️ `{result.rule_id}`: {result.message}")
    
    lines.append("")
    return "\n".join(lines)


def _format_evidence(evidence: Dict[str, Any]) -> str:
    """Format evidence dictionary."""
    lines = []
    
    for key, value in sorted(evidence.items()):
        if isinstance(value, list):
            if len(value) == 0:
                lines.append(f"- **{key}:** (empty)")
            elif len(value) <= MAX_EVIDENCE_ITEMS:
                lines.append(f"- **{key}:** ({len(value)} items)")
                for item in value:
                    lines.append(f"  - `{item}`")
            else:
                lines.append(f"- **{key}:** ({len(value)} items, showing first {MAX_EVIDENCE_ITEMS})")
                for item in value[:MAX_EVIDENCE_ITEMS]:
                    lines.append(f"  - `{item}`")
                lines.append(f"  - _(... and {len(value) - MAX_EVIDENCE_ITEMS} more)_")
        elif isinstance(value, dict):
            lines.append(f"- **{key}:**")
            for sub_key, sub_value in sorted(value.items()):
                lines.append(f"  - {sub_key}: `{sub_value}`")
        else:
            lines.append(f"- **{key}:** `{value}`")
    
    lines.append("")
    return "\n".join(lines)


def _format_artifacts(context: PolicyContext) -> str:
    """Format artifacts section."""
    lines = ["## Artifacts\n"]
    
    has_artifacts = False
    
    # Analyzer artifacts
    if context.analyzer_result:
        has_artifacts = True
        status = "✅ Success" if context.analyzer_result.success else "❌ Failed"
        lines.append(f"### Repository Analyzer\n")
        lines.append(f"**Status:** {status}\n")
        
        if context.analyzer_result.version:
            lines.append(f"**Version:** {context.analyzer_result.version}\n")
        
        if context.analyzer_result.output_files:
            lines.append("**Output Files:**\n")
            for file_path in sorted(context.analyzer_result.output_files):
                lines.append(f"- `{file_path}`")
            lines.append("")
        
        if context.analyzer_result.error_message:
            lines.append(f"**Error:** {context.analyzer_result.error_message}\n")
    
    # License header artifacts
    if context.license_header_result:
        has_artifacts = True
        lines.append("### License Headers\n")
        
        if context.license_header_result.skipped:
            lines.append("**Status:** ⏭️ Skipped (not required)\n")
        else:
            status = "✅ Success" if context.license_header_result.success else "❌ Failed"
            lines.append(f"**Status:** {status}\n")
            
            if context.license_header_result.version:
                lines.append(f"**Version:** {context.license_header_result.version}\n")
            
            compliant_count = len(context.license_header_result.compliant_files or [])
            non_compliant_count = len(context.license_header_result.non_compliant_files or [])
            
            lines.append(f"**Compliant Files:** {compliant_count}")
            lines.append(f"**Non-Compliant Files:** {non_compliant_count}\n")
            
            if context.license_header_result.error_message:
                lines.append(f"**Error:** {context.license_header_result.error_message}\n")
    
    if not has_artifacts:
        lines.append("No integration artifacts were generated.\n")
    
    return "\n".join(lines)


def _format_command_guidance() -> str:
    """Format command guidance section."""
    lines = ["## Command Guidance\n"]
    lines.append("To re-run the policy check:\n")
    lines.append("```bash")
    lines.append("repo-policy check")
    lines.append("```\n")
    lines.append("For more options:\n")
    lines.append("```bash")
    lines.append("repo-policy --help")
    lines.append("```\n")
    
    return "\n".join(lines)
