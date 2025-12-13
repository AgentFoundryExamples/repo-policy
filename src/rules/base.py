"""Base rule class for policy evaluation."""

import fnmatch
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from config.schema import Config
from facts.extractor import RepoFacts
from integration.context import PolicyContext
from rules.result import RuleResult, RuleSeverity, RuleStatus

logger = logging.getLogger(__name__)


class BaseRule(ABC):
    """Base class for all policy rules."""
    
    # Rule metadata (override in subclasses)
    rule_id: str = "base-rule"
    default_severity: RuleSeverity = RuleSeverity.ERROR
    rule_tags: List[str] = []
    
    def __init__(
        self,
        config: Config,
        facts: RepoFacts,
        context: PolicyContext,
        target_path: Path,
    ):
        """
        Initialize rule.
        
        Args:
            config: Policy configuration
            facts: Extracted repository facts
            context: Policy context with integration results
            target_path: Path to repository
        """
        self.config = config
        self.facts = facts
        self.context = context
        self.target_path = target_path
        
        # Get severity from config overrides or use default
        self.severity = self._get_severity()
    
    def _get_severity(self) -> RuleSeverity:
        """Get severity from config overrides or use default."""
        overrides = self.config.rules.severity_overrides
        if self.rule_id in overrides:
            override_severity = overrides[self.rule_id]
            # Convert from config.schema.Severity to rules.result.RuleSeverity
            if override_severity.value == "error":
                return RuleSeverity.ERROR
            elif override_severity.value == "warning":
                return RuleSeverity.WARNING
            elif override_severity.value == "info":
                return RuleSeverity.INFO
        return self.default_severity
    
    def should_run(self) -> bool:
        """
        Check if this rule should run based on include/exclude patterns.
        
        Returns:
            True if rule should run, False otherwise
        """
        # Check include patterns
        included = False
        for pattern in self.config.rules.include:
            if fnmatch.fnmatch(self.rule_id, pattern):
                included = True
                break
        
        if not included:
            return False
        
        # Check exclude patterns
        for pattern in self.config.rules.exclude:
            if fnmatch.fnmatch(self.rule_id, pattern):
                return False
        
        return True
    
    def evaluate(self) -> RuleResult:
        """
        Evaluate the rule.
        
        Returns:
            RuleResult with evaluation outcome
        """
        # Check if rule should run
        if not self.should_run():
            return self._create_skip_result("Rule excluded by configuration")
        
        # Check rule-specific preconditions
        precondition_result = self._check_preconditions()
        if precondition_result:
            return precondition_result
        
        # Run the actual rule evaluation
        try:
            return self._evaluate_impl()
        except Exception as e:
            logger.exception(f"Error evaluating rule {self.rule_id}: {e}")
            return self._create_fail_result(
                message=f"Rule evaluation failed: {e}",
                evidence={"error": str(e)},
                remediation="Please report this error to the maintainers.",
            )
    
    def _check_preconditions(self) -> Optional[RuleResult]:
        """
        Check if preconditions for rule evaluation are met.
        
        Returns:
            RuleResult with skip status if preconditions not met, None otherwise
        """
        # Override in subclasses if needed
        return None
    
    @abstractmethod
    def _evaluate_impl(self) -> RuleResult:
        """
        Implement rule-specific evaluation logic.
        
        Returns:
            RuleResult with evaluation outcome
        """
        pass
    
    def _create_pass_result(
        self,
        message: str,
        evidence: Optional[dict] = None,
    ) -> RuleResult:
        """Create a passing result."""
        return RuleResult(
            rule_id=self.rule_id,
            severity=self.severity,
            status=RuleStatus.PASS,
            message=message,
            evidence=evidence or {},
            remediation="",
            rule_tags=self.rule_tags,
        )
    
    def _create_fail_result(
        self,
        message: str,
        evidence: Optional[dict] = None,
        remediation: str = "",
    ) -> RuleResult:
        """Create a failing result."""
        return RuleResult(
            rule_id=self.rule_id,
            severity=self.severity,
            status=RuleStatus.FAIL,
            message=message,
            evidence=evidence or {},
            remediation=remediation,
            rule_tags=self.rule_tags,
        )
    
    def _create_skip_result(
        self,
        message: str,
        evidence: Optional[dict] = None,
    ) -> RuleResult:
        """Create a skipped result."""
        return RuleResult(
            rule_id=self.rule_id,
            severity=self.severity,
            status=RuleStatus.SKIP,
            message=message,
            evidence=evidence or {},
            remediation="",
            rule_tags=self.rule_tags,
        )
    
    def _matches_patterns(self, path: str, patterns: List[str]) -> bool:
        """Check if path matches any of the glob patterns."""
        path_obj = Path(path)
        for pattern in patterns:
            # Handle ** glob patterns by checking all path segments
            if '**' in pattern:
                # For ** patterns, try matching against the path and all subpaths
                # e.g., **/*.py should match both "main.py" and "src/main.py"
                pattern_parts = pattern.split('/')
                
                # Try matching the full path first
                if path_obj.match(pattern):
                    return True
                
                # If pattern starts with **, try matching without the **
                if pattern_parts[0] == '**':
                    rest_pattern = '/'.join(pattern_parts[1:])
                    if rest_pattern and path_obj.match(rest_pattern):
                        return True
                    # Also try matching against parent paths
                    for i in range(len(path_obj.parts)):
                        subpath = Path(*path_obj.parts[i:])
                        if subpath.match(rest_pattern):
                            return True
            else:
                # Simple pattern without **, use Path.match() or fnmatch
                if path_obj.match(pattern) or fnmatch.fnmatch(path, pattern):
                    return True
        return False
