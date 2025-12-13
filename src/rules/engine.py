"""Rule evaluation engine."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Type

from config.schema import Config
from facts.extractor import FactsExtractor, RepoFacts
from integration.context import PolicyContext
from rules.base import BaseRule
from rules.result import RuleResult

logger = logging.getLogger(__name__)


@dataclass
class RuleEngineResult:
    """Result from running the rule engine."""
    
    results: List[RuleResult] = field(default_factory=list)
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    skipped_rules: int = 0
    error_count: int = 0
    warning_count: int = 0
    
    def has_errors(self) -> bool:
        """Check if there are any error-level failures."""
        return self.error_count > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "skipped_rules": self.skipped_rules,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "results": [r.to_dict() for r in self.results],
        }


class RuleEngine:
    """Engine for evaluating policy rules."""
    
    def __init__(
        self,
        config: Config,
        context: PolicyContext,
        target_path: Path,
    ):
        """
        Initialize rule engine.
        
        Args:
            config: Policy configuration
            context: Policy context with integration results
            target_path: Path to repository
        """
        self.config = config
        self.context = context
        self.target_path = target_path
        
        # Extract facts
        extractor = FactsExtractor(config, context, target_path)
        self.facts = extractor.extract()
        
        # Rule registry
        self.rules: List[Type[BaseRule]] = []
    
    def register_rule(self, rule_class: Type[BaseRule]) -> None:
        """
        Register a rule class.
        
        Args:
            rule_class: Rule class to register
        """
        self.rules.append(rule_class)
        logger.debug(f"Registered rule: {rule_class.rule_id}")
    
    def register_rules(self, rule_classes: List[Type[BaseRule]]) -> None:
        """
        Register multiple rule classes.
        
        Args:
            rule_classes: List of rule classes to register
        """
        for rule_class in rule_classes:
            self.register_rule(rule_class)
    
    def evaluate_all(self) -> RuleEngineResult:
        """
        Evaluate all registered rules.
        
        Returns:
            RuleEngineResult with all rule results
        """
        logger.info(f"Evaluating {len(self.rules)} rules")
        
        engine_result = RuleEngineResult()
        engine_result.total_rules = len(self.rules)
        
        for rule_class in self.rules:
            # Instantiate rule
            rule = rule_class(
                config=self.config,
                facts=self.facts,
                context=self.context,
                target_path=self.target_path,
            )
            
            # Evaluate rule
            logger.debug(f"Evaluating rule: {rule.rule_id}")
            result = rule.evaluate()
            engine_result.results.append(result)
            
            # Update counts
            if result.status.value == "pass":
                engine_result.passed_rules += 1
            elif result.status.value == "fail":
                engine_result.failed_rules += 1
                if result.is_error():
                    engine_result.error_count += 1
                else:
                    engine_result.warning_count += 1
            elif result.status.value == "warn":
                engine_result.failed_rules += 1
                engine_result.warning_count += 1
            elif result.status.value == "skip":
                engine_result.skipped_rules += 1
            
            # Log result
            log_level = logging.ERROR if result.is_error() else logging.WARNING if result.is_failure() else logging.INFO
            logger.log(
                log_level,
                f"[{result.status.value.upper()}] {rule.rule_id}: {result.message}"
            )
        
        logger.info(
            f"Rule evaluation complete: {engine_result.passed_rules} passed, "
            f"{engine_result.failed_rules} failed ({engine_result.error_count} errors, "
            f"{engine_result.warning_count} warnings), {engine_result.skipped_rules} skipped"
        )
        
        return engine_result
