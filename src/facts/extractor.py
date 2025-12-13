"""Extract normalized repository facts from context and filesystem."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import fnmatch

from integration.context import PolicyContext
from config.schema import Config

logger = logging.getLogger(__name__)


@dataclass
class RepoFacts:
    """Normalized facts about the repository for rule evaluation."""

    # Basic file information
    has_readme: bool = False
    readme_path: Optional[Path] = None
    readme_content: str = ""
    
    has_license: bool = False
    license_path: Optional[Path] = None
    license_content: str = ""
    
    has_gitignore: bool = False
    gitignore_path: Optional[Path] = None
    
    # CI/CD
    ci_workflow_files: List[Path] = field(default_factory=list)
    has_ci: bool = False
    
    # Source and test files
    source_files: List[Path] = field(default_factory=list)
    test_files: List[Path] = field(default_factory=list)
    
    # Language detection
    language_markers: Dict[str, List[Path]] = field(default_factory=dict)
    detected_languages: Set[str] = field(default_factory=set)
    
    # File size and type info
    large_files: List[Dict[str, any]] = field(default_factory=list)
    binary_files: List[Path] = field(default_factory=list)
    
    # Forbidden patterns
    forbidden_files: List[Path] = field(default_factory=list)
    
    # Repository metadata
    repo_tags: Dict[str, str] = field(default_factory=dict)
    
    # All files in repo (for pattern matching)
    all_files: List[Path] = field(default_factory=list)


class FactsExtractor:
    """Extract facts from repository for policy evaluation."""
    
    # Language marker files for detection
    LANGUAGE_MARKERS = {
        "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
        "javascript": ["package.json", "package-lock.json", "yarn.lock"],
        "typescript": ["tsconfig.json"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "php": ["composer.json", "composer.lock"],
        "csharp": ["*.csproj", "*.sln"],
    }
    
    # Default forbidden file patterns
    DEFAULT_FORBIDDEN_PATTERNS = [
        "**/.DS_Store",
        "**/Thumbs.db",
        "**/*.swp",
        "**/*.bak",
        "**/*~",
    ]
    
    # Binary file extensions
    BINARY_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".a", ".o", ".obj",
        ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",
        ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
        ".mp3", ".mp4", ".avi", ".mov", ".wmv",
        ".jar", ".war", ".ear", ".class",
        ".pyc", ".pyo", ".whl",
    }
    
    def __init__(
        self,
        config: Config,
        context: PolicyContext,
        target_path: Path,
    ):
        """
        Initialize facts extractor.
        
        Args:
            config: Policy configuration
            context: Policy context with integration results
            target_path: Path to repository
        """
        self.config = config
        self.context = context
        self.target_path = target_path.resolve()
        
    def extract(self) -> RepoFacts:
        """
        Extract all facts from repository.
        
        Returns:
            RepoFacts object with all extracted information
        """
        logger.info("Extracting repository facts")
        facts = RepoFacts()
        
        # Extract repository metadata
        facts.repo_tags = self.config.repo_tags
        
        # Get all files
        facts.all_files = self._get_all_files()
        logger.debug(f"Found {len(facts.all_files)} files in repository")
        
        # Extract basic file presence
        self._extract_readme(facts)
        self._extract_license(facts)
        self._extract_gitignore(facts)
        
        # Extract CI/CD information
        self._extract_ci_workflows(facts)
        
        # Detect languages
        self._detect_languages(facts)
        
        # Extract source and test files
        self._extract_source_files(facts)
        self._extract_test_files(facts)
        
        # Extract file size and type info
        self._extract_large_files(facts)
        self._extract_binary_files(facts)
        
        # Extract forbidden files
        self._extract_forbidden_files(facts)
        
        logger.info(f"Facts extracted: README={facts.has_readme}, LICENSE={facts.has_license}, "
                   f"CI={facts.has_ci}, languages={facts.detected_languages}, "
                   f"sources={len(facts.source_files)}, tests={len(facts.test_files)}")
        
        return facts
    
    def _get_all_files(self) -> List[Path]:
        """Get all files in repository (excluding .git)."""
        files = []
        for path in self.target_path.rglob("*"):
            # Skip .git directory
            if ".git" in path.parts:
                continue
            if path.is_file():
                try:
                    rel_path = path.relative_to(self.target_path)
                    files.append(rel_path)
                except ValueError:
                    continue
        return files
    
    def _extract_readme(self, facts: RepoFacts) -> None:
        """Extract README file information."""
        # Check for README variants
        readme_names = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
        for name in readme_names:
            readme_path = self.target_path / name
            if readme_path.exists():
                facts.has_readme = True
                facts.readme_path = Path(name)
                try:
                    facts.readme_content = readme_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"Failed to read README: {e}")
                logger.debug(f"Found README: {name}")
                break
    
    def _extract_license(self, facts: RepoFacts) -> None:
        """Extract LICENSE file information."""
        # Check for LICENSE variants
        license_names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "license", "License.txt"]
        for name in license_names:
            license_path = self.target_path / name
            if license_path.exists():
                facts.has_license = True
                facts.license_path = Path(name)
                try:
                    facts.license_content = license_path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"Failed to read LICENSE: {e}")
                logger.debug(f"Found LICENSE: {name}")
                break
    
    def _extract_gitignore(self, facts: RepoFacts) -> None:
        """Extract .gitignore file information."""
        gitignore_path = self.target_path / ".gitignore"
        if gitignore_path.exists():
            facts.has_gitignore = True
            facts.gitignore_path = Path(".gitignore")
            logger.debug("Found .gitignore")
    
    def _extract_ci_workflows(self, facts: RepoFacts) -> None:
        """Extract CI workflow information."""
        workflows_dir = self.target_path / ".github" / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                rel_path = workflow_file.relative_to(self.target_path)
                facts.ci_workflow_files.append(rel_path)
            
            # Also check for .yaml extension
            for workflow_file in workflows_dir.glob("*.yaml"):
                rel_path = workflow_file.relative_to(self.target_path)
                facts.ci_workflow_files.append(rel_path)
            
            facts.has_ci = len(facts.ci_workflow_files) > 0
            logger.debug(f"Found {len(facts.ci_workflow_files)} CI workflow files")
    
    def _detect_languages(self, facts: RepoFacts) -> None:
        """Detect programming languages based on marker files."""
        for lang, markers in self.LANGUAGE_MARKERS.items():
            for marker in markers:
                # Check if marker has glob pattern
                if "*" in marker:
                    # Use glob pattern matching
                    matching_files = [
                        f for f in facts.all_files
                        if fnmatch.fnmatch(str(f), marker)
                    ]
                    if matching_files:
                        facts.detected_languages.add(lang)
                        facts.language_markers.setdefault(lang, []).extend(matching_files)
                        logger.debug(f"Detected {lang} via pattern {marker}: {matching_files}")
                else:
                    # Check for exact file
                    marker_path = self.target_path / marker
                    if marker_path.exists():
                        facts.detected_languages.add(lang)
                        rel_path = Path(marker)
                        facts.language_markers.setdefault(lang, []).append(rel_path)
                        logger.debug(f"Detected {lang} via {marker}")
        
        # Also use repo_tags language if present
        if "language" in facts.repo_tags:
            lang = facts.repo_tags["language"].lower()
            facts.detected_languages.add(lang)
            logger.debug(f"Added language from repo_tags: {lang}")
    
    def _extract_source_files(self, facts: RepoFacts) -> None:
        """Extract source files based on configured patterns."""
        source_patterns = self.config.globs.source
        for file_path in facts.all_files:
            if self._matches_patterns(str(file_path), source_patterns):
                facts.source_files.append(file_path)
        
        logger.debug(f"Found {len(facts.source_files)} source files")
    
    def _extract_test_files(self, facts: RepoFacts) -> None:
        """Extract test files based on configured patterns."""
        test_patterns = self.config.globs.test
        for file_path in facts.all_files:
            if self._matches_patterns(str(file_path), test_patterns):
                facts.test_files.append(file_path)
        
        logger.debug(f"Found {len(facts.test_files)} test files")
    
    def _extract_large_files(self, facts: RepoFacts) -> None:
        """Extract large files exceeding configured threshold."""
        # Default threshold: 10MB
        threshold = getattr(self.config.rules, "large_file_threshold_mb", 10) * 1024 * 1024
        
        for file_path in facts.all_files:
            full_path = self.target_path / file_path
            try:
                size = full_path.stat().st_size
                if size > threshold:
                    facts.large_files.append({
                        "path": file_path,
                        "size_bytes": size,
                        "size_mb": size / (1024 * 1024),
                    })
            except OSError as e:
                logger.debug(f"Failed to stat file {file_path}: {e}")
        
        if facts.large_files:
            logger.debug(f"Found {len(facts.large_files)} large files")
    
    def _extract_binary_files(self, facts: RepoFacts) -> None:
        """Extract binary files based on extension."""
        for file_path in facts.all_files:
            if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
                facts.binary_files.append(file_path)
        
        if facts.binary_files:
            logger.debug(f"Found {len(facts.binary_files)} binary files")
    
    def _extract_forbidden_files(self, facts: RepoFacts) -> None:
        """Extract files matching forbidden patterns."""
        # Get forbidden patterns from config or use defaults
        forbidden_patterns = getattr(self.config.rules, "forbidden_patterns", None)
        if forbidden_patterns is None:
            forbidden_patterns = self.DEFAULT_FORBIDDEN_PATTERNS
        
        for file_path in facts.all_files:
            if self._matches_patterns(str(file_path), forbidden_patterns):
                facts.forbidden_files.append(file_path)
        
        if facts.forbidden_files:
            logger.debug(f"Found {len(facts.forbidden_files)} forbidden files")
    
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
