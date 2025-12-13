# Dependency Graph

Multi-language intra-repository dependency analysis.

Supports Python, JavaScript/TypeScript, C/C++, Rust, Go, Java, C#, Swift, HTML/CSS, and SQL.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 25
- **Intra-repo dependencies**: 23
- **External stdlib dependencies**: 19
- **External third-party dependencies**: 6

## External Dependencies

### Standard Library / Core Modules

Total: 19 unique modules

- `argparse`
- `argparse.Namespace`
- `dataclasses.dataclass`
- `dataclasses.field`
- `enum.Enum`
- `json`
- `logging`
- `os`
- `pathlib.Path`
- `shutil`
- `subprocess`
- `sys`
- `tempfile`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `unittest.mock.MagicMock`
- `unittest.mock.patch`

### Third-Party Packages

Total: 6 unique packages

- `pydantic.BaseModel`
- `pydantic.Field`
- `pydantic.ValidationError`
- `pydantic.field_validator`
- `pytest`
- `yaml`

## Most Depended Upon Files (Intra-Repo)

- `src/config/schema.py` (5 dependents)
- `src/integration/repo_analyzer.py` (4 dependents)
- `src/integration/license_headers.py` (4 dependents)
- `src/config/loader.py` (3 dependents)
- `src/integration/context.py` (2 dependents)
- `src/cli/commands/check.py` (2 dependents)
- `src/cli/commands/init.py` (2 dependents)
- `src/cli/main.py` (1 dependents)

## Files with Most Dependencies (Intra-Repo)

- `src/cli/commands/check.py` (4 dependencies)
- `src/cli/main.py` (4 dependencies)
- `tests/integration/test_context.py` (3 dependencies)
- `src/integration/context.py` (2 dependencies)
- `tests/cli/test_init.py` (2 dependencies)
- `tests/config/test_loader.py` (2 dependencies)
- `src/cli/commands/init.py` (1 dependencies)
- `tests/cli/test_check.py` (1 dependencies)
- `tests/cli/test_main.py` (1 dependencies)
- `tests/config/test_schema.py` (1 dependencies)
