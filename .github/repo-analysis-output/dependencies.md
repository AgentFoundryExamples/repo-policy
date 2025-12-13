# Dependency Graph

Multi-language intra-repository dependency analysis.

Supports Python, JavaScript/TypeScript, C/C++, Rust, Go, Java, C#, Swift, HTML/CSS, and SQL.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 48
- **Intra-repo dependencies**: 74
- **External stdlib dependencies**: 26
- **External third-party dependencies**: 6

## External Dependencies

### Standard Library / Core Modules

Total: 26 unique modules

- `abc.ABC`
- `abc.abstractmethod`
- `argparse`
- `argparse.Namespace`
- `dataclasses.dataclass`
- `dataclasses.field`
- `enum.Enum`
- `fnmatch`
- `json`
- `logging`
- `logging.getLogger`
- `os`
- `pathlib.Path`
- `re`
- `shutil`
- `subprocess`
- `sys`
- `tempfile`
- `typing.Any`
- `typing.Dict`
- ... and 6 more (see JSON for full list)

### Third-Party Packages

Total: 6 unique packages

- `pydantic.BaseModel`
- `pydantic.Field`
- `pydantic.ValidationError`
- `pydantic.field_validator`
- `pytest`
- `yaml`

## Most Depended Upon Files (Intra-Repo)

- `src/rules/result.py` (12 dependents)
- `src/rules/base.py` (11 dependents)
- `src/config/schema.py` (9 dependents)
- `src/integration/context.py` (5 dependents)
- `src/integration/repo_analyzer.py` (4 dependents)
- `src/integration/license_headers.py` (4 dependents)
- `src/facts/extractor.py` (4 dependents)
- `src/config/loader.py` (3 dependents)
- `src/rules/engine.py` (2 dependents)
- `src/cli/commands/check.py` (2 dependents)

## Files with Most Dependencies (Intra-Repo)

- `src/cli/commands/check.py` (9 dependencies)
- `src/rules/base.py` (5 dependencies)
- `src/rules/engine.py` (5 dependencies)
- `src/cli/main.py` (4 dependencies)
- `src/rules/hygiene/__init__.py` (4 dependencies)
- `src/facts/extractor.py` (3 dependencies)
- `src/rules/__init__.py` (3 dependencies)
- `src/rules/license/__init__.py` (3 dependencies)
- `tests/integration/test_context.py` (3 dependencies)
- `src/integration/context.py` (2 dependencies)
