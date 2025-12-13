"""Rule result data structures."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RuleStatus(str, Enum):
    """Rule evaluation status."""
    
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class RuleSeverity(str, Enum):
    """Rule severity levels."""
    
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleResult:
    """Result from evaluating a single rule."""
    
    rule_id: str
    severity: RuleSeverity
    status: RuleStatus
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation: str = ""
    rule_tags: List[str] = field(default_factory=list)
    
    def is_failure(self) -> bool:
        """Check if this result represents a failure."""
        return self.status == RuleStatus.FAIL
    
    def is_error(self) -> bool:
        """Check if this is an error-level failure."""
        return self.is_failure() and self.severity == RuleSeverity.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "tags": self.rule_tags,
        }
