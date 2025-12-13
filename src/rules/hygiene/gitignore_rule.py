"""Gitignore requirement rule."""

from typing import Optional

from rules.base import BaseRule
from rules.result import RuleResult, RuleSeverity


class GitignoreRule(BaseRule):
    """.gitignore requirement gated by language markers."""
    
    rule_id = "gitignore-required"
    default_severity = RuleSeverity.WARNING
    rule_tags = ["hygiene", "vcs"]
    
    def _check_preconditions(self) -> Optional[RuleResult]:
        """Check if repository has language markers that require .gitignore."""
        # Skip if no languages detected
        if not self.facts.detected_languages:
            return self._create_skip_result(
                message="No programming languages detected (no language markers found)",
                evidence={
                    "detected_languages": [],
                    "language_markers": {},
                },
            )
        
        return None
    
    def _evaluate_impl(self) -> RuleResult:
        """Evaluate .gitignore requirement."""
        if not self.facts.has_gitignore:
            languages_str = ", ".join(sorted(self.facts.detected_languages))
            
            return self._create_fail_result(
                message=f".gitignore file is missing (detected languages: {languages_str})",
                evidence={
                    "has_gitignore": False,
                    "detected_languages": list(self.facts.detected_languages),
                    "language_markers": {
                        lang: [str(p) for p in paths]
                        for lang, paths in self.facts.language_markers.items()
                    },
                },
                remediation=(
                    "Add a .gitignore file to the repository root.\n\n"
                    f"Detected languages: {languages_str}\n\n"
                    "Generate a .gitignore file for your languages:\n"
                    "  - https://www.toptal.com/developers/gitignore\n"
                    "  - https://github.com/github/gitignore\n\n"
                    "Common patterns to ignore:\n"
                    "  - Build artifacts (dist/, build/, target/)\n"
                    "  - Dependencies (node_modules/, venv/, vendor/)\n"
                    "  - IDE files (.idea/, .vscode/, *.swp)\n"
                    "  - OS files (.DS_Store, Thumbs.db)"
                ),
            )
        
        return self._create_pass_result(
            message=".gitignore file found",
            evidence={
                "has_gitignore": True,
                "gitignore_path": str(self.facts.gitignore_path),
                "detected_languages": list(self.facts.detected_languages),
            },
        )
