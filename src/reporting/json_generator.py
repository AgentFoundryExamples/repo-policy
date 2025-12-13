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
"""JSON report generator for policy check results."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from rules.engine import RuleEngineResult
from integration.context import PolicyContext
from reporting.metadata import extract_report_metadata

logger = logging.getLogger(__name__)


def generate_json_report(
    rule_results: RuleEngineResult,
    context: PolicyContext,
    repo_path: Path,
    config_path: str,
    output_path: Path,
) -> None:
    """
    Generate JSON policy report.
    
    Args:
        rule_results: Results from rule engine evaluation
        context: Policy context with integration results
        repo_path: Path to repository
        config_path: Path to config file
        output_path: Path to write JSON report
    """
    logger.info(f"Generating JSON report: {output_path}")
    
    # Extract metadata
    metadata = extract_report_metadata(repo_path, config_path, context)
    
    # Build report structure
    report = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata,
        "summary": {
            "total_rules": rule_results.total_rules,
            "passed_rules": rule_results.passed_rules,
            "failed_rules": rule_results.failed_rules,
            "skipped_rules": rule_results.skipped_rules,
            "error_count": rule_results.error_count,
            "warning_count": rule_results.warning_count,
        },
        "rules": _format_rules(rule_results),
        "artifacts": _format_artifacts(context),
    }
    
    # Write JSON file with deterministic ordering
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, ensure_ascii=False)
    
    logger.info(f"JSON report written to: {output_path}")


def _format_rules(rule_results: RuleEngineResult) -> List[Dict[str, Any]]:
    """
    Format rule results for JSON report.
    
    Args:
        rule_results: Results from rule engine
        
    Returns:
        List of rule dictionaries, sorted by rule_id
    """
    rules = []
    for result in rule_results.results:
        rule_dict = {
            "rule_id": result.rule_id,
            "severity": result.severity.value,
            "status": result.status.value,
            "message": result.message,
            "evidence": result.evidence,
            "remediation": result.remediation,
            "tags": sorted(result.rule_tags),  # Sort tags for determinism
        }
        rules.append(rule_dict)
    
    # Sort rules by rule_id for deterministic output
    rules.sort(key=lambda r: r["rule_id"])
    return rules


def _format_artifacts(context: PolicyContext) -> Dict[str, Any]:
    """
    Format artifact information for JSON report.
    
    Args:
        context: Policy context
        
    Returns:
        Dictionary with artifact information
    """
    artifacts = {}
    
    # Analyzer artifacts
    if context.analyzer_result:
        artifacts["analyzer"] = {
            "status": "success" if context.analyzer_result.success else "failed",
            "output_files": sorted(context.analyzer_result.output_files or []),
            "version": context.analyzer_result.version,
        }
        if context.analyzer_result.error_message:
            artifacts["analyzer"]["error_message"] = context.analyzer_result.error_message
    
    # License header artifacts
    if context.license_header_result:
        if context.license_header_result.skipped:
            artifacts["license_headers"] = {
                "status": "skipped",
            }
        else:
            artifacts["license_headers"] = {
                "status": "success" if context.license_header_result.success else "failed",
                "compliant_files": sorted(context.license_header_result.compliant_files or []),
                "non_compliant_files": sorted(context.license_header_result.non_compliant_files or []),
                "version": context.license_header_result.version,
            }
            if context.license_header_result.error_message:
                artifacts["license_headers"]["error_message"] = context.license_header_result.error_message
    
    return artifacts
