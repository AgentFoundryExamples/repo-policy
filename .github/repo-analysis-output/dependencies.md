# Dependency Graph

Multi-language intra-repository dependency analysis.

Supports Python, JavaScript/TypeScript, C/C++, Rust, Go, Java, C#, Swift, HTML/CSS, and SQL.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 56
- **Intra-repo dependencies**: 100
- **External stdlib dependencies**: 32
- **External third-party dependencies**: 6

## External Dependencies

### Standard Library / Core Modules

Total: 32 unique modules

- `abc.ABC`
- `abc.abstractmethod`
- `argparse`
- `argparse.Namespace`
- `dataclasses.dataclass`
- `dataclasses.field`
- `datetime.datetime`
- `datetime.timezone`
- `enum.Enum`
- `fnmatch`
- `hashlib`
- `json`
- `logging`
- `logging.getLogger`
- `os`
- `pathlib.Path`
- `re`
- `shutil`
- `subprocess`
- `subprocess.CalledProcessError`
- ... and 12 more (see JSON for full list)

### Third-Party Packages

Total: 6 unique packages

- `pydantic.BaseModel`
- `pydantic.Field`
- `pydantic.ValidationError`
- `pydantic.field_validator`
- `pytest`
- `yaml`

## Most Depended Upon Files (Intra-Repo)

- `src/rules/result.py` (15 dependents)
- `src/rules/base.py` (11 dependents)
- `src/integration/context.py` (10 dependents)
- `src/config/schema.py` (9 dependents)
- `src/integration/repo_analyzer.py` (7 dependents)
- `src/integration/license_headers.py` (7 dependents)
- `src/rules/engine.py` (6 dependents)
- `src/facts/extractor.py` (4 dependents)
- `src/config/loader.py` (3 dependents)
- `src/reporting/metadata.py` (3 dependents)

## Files with Most Dependencies (Intra-Repo)

- `src/cli/commands/check.py` (10 dependencies)
- `tests/reporting/test_json_generator.py` (6 dependencies)
- `tests/reporting/test_markdown_generator.py` (6 dependencies)
- `src/rules/base.py` (5 dependencies)
- `src/rules/engine.py` (5 dependencies)
- `src/cli/main.py` (4 dependencies)
- `src/reporting/markdown_generator.py` (4 dependencies)
- `src/rules/hygiene/__init__.py` (4 dependencies)
- `tests/reporting/test_metadata.py` (4 dependencies)
- `src/facts/extractor.py` (3 dependencies)
