"""Glob pattern matching utilities."""

import fnmatch
from pathlib import Path
from typing import List


def matches_patterns(path: str, patterns: List[str]) -> bool:
    """
    Check if path matches any of the glob patterns.
    
    Supports both simple glob patterns and ** recursive patterns.
    Examples:
        - "*.py" matches "main.py"
        - "**/*.py" matches "main.py" and "src/main.py"
        - "**/tests/**" matches "tests/test.py" and "src/tests/test.py"
    
    Args:
        path: File path to check (relative path)
        patterns: List of glob patterns to match against
        
    Returns:
        True if path matches any pattern, False otherwise
    """
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
