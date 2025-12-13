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
"""Tests for facts extractor."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from facts.extractor import FactsExtractor, RepoFacts
from config.schema import Config


def test_repo_facts_initialization():
    """Test RepoFacts data structure initialization."""
    facts = RepoFacts()
    
    assert facts.has_readme is False
    assert facts.has_license is False
    assert facts.has_gitignore is False
    assert facts.has_ci is False
    assert len(facts.source_files) == 0
    assert len(facts.test_files) == 0
    assert len(facts.detected_languages) == 0


def test_facts_extractor_detects_readme(tmp_path):
    """Test README detection."""
    # Create a README
    (tmp_path / "README.md").write_text("# Test Project")
    
    # Setup config and context
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert facts.has_readme is True
    assert facts.readme_path == Path("README.md")
    assert "Test Project" in facts.readme_content


def test_facts_extractor_detects_license(tmp_path):
    """Test LICENSE detection."""
    # Create a LICENSE
    (tmp_path / "LICENSE").write_text("Apache 2.0")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert facts.has_license is True
    assert facts.license_path == Path("LICENSE")


def test_facts_extractor_detects_gitignore(tmp_path):
    """Test .gitignore detection."""
    (tmp_path / ".gitignore").write_text("*.pyc")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert facts.has_gitignore is True
    assert facts.gitignore_path == Path(".gitignore")


def test_facts_extractor_detects_ci_workflows(tmp_path):
    """Test CI workflow detection."""
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text("name: CI")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert facts.has_ci is True
    assert len(facts.ci_workflow_files) == 1
    assert Path(".github/workflows/ci.yml") in facts.ci_workflow_files


def test_facts_extractor_detects_python_language(tmp_path):
    """Test Python language detection via pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[build-system]")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert "python" in facts.detected_languages
    assert "python" in facts.language_markers


def test_facts_extractor_finds_source_files(tmp_path):
    """Test source file detection."""
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.js").write_text("console.log('hello')")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert len(facts.source_files) == 2
    assert Path("main.py") in facts.source_files
    assert Path("utils.js") in facts.source_files


def test_facts_extractor_finds_test_files(tmp_path):
    """Test test file detection."""
    (tmp_path / "test_main.py").write_text("def test_foo(): pass")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_utils.py").write_text("def test_bar(): pass")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert len(facts.test_files) == 2


def test_facts_extractor_finds_large_files(tmp_path):
    """Test large file detection."""
    # Create a large file (11MB)
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert len(facts.large_files) == 1
    assert facts.large_files[0]["path"] == Path("large.bin")
    assert facts.large_files[0]["size_mb"] > 10


def test_facts_extractor_finds_binary_files(tmp_path):
    """Test binary file detection."""
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert len(facts.binary_files) == 2


def test_facts_extractor_finds_forbidden_files(tmp_path):
    """Test forbidden file detection."""
    (tmp_path / ".DS_Store").write_text("mac metadata")
    (tmp_path / "Thumbs.db").write_text("windows thumbnail cache")
    
    config = Config(target_path=str(tmp_path))
    context = MagicMock()
    
    extractor = FactsExtractor(config, context, tmp_path)
    facts = extractor.extract()
    
    assert len(facts.forbidden_files) == 2
