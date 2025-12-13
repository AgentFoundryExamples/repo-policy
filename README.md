# repo-policy

A deterministic repository policy enforcement tool with configurable rules and integrations.

## Features

- **Schema-driven configuration**: YAML-based config with validation
- **Flexible CLI**: Support for `check` (default) and `init` commands
- **Configurable rules engine**: Pluggable rules with include/exclude patterns and severity overrides
- **Documentation rules**: README presence and required sections
- **License rules**: LICENSE file, SPDX ID, and header enforcement
- **Hygiene rules**: CI workflows, .gitignore, forbidden files, and file size limits
- **Test coverage rules**: Tests vs sources linkage with language-aware detection
- **Preset configurations**: Baseline, standard, and strict presets
- **Structured logging**: Clear output with exit code handling
- **External tool integration**: Repo analyzer and license header checking
- **Deterministic artifact handling**: Clean, keep, or purge outputs

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

Initialize a new configuration:
```bash
repo-policy init
```

Run policy checks:
```bash
repo-policy check
```

For comprehensive usage information, see the [Usage Guide](docs/usage.md).

## Documentation

- **[Usage Guide](docs/usage.md)** - Complete CLI reference, commands, options, and exit codes
- **[Configuration Guide](docs/config.md)** - Configuration schema, rule catalog, presets, and examples
- **[CI/CD Integration](docs/ci.md)** - GitHub Actions, pre-commit hooks, and other CI platforms
- **[Repository Analysis Integration](docs/REPO_ANALYSIS.md)** - Repo analyzer tool integration
- **[License Header Integration](docs/LICENSE_HEADER.md)** - License header checking integration
- **[Report Format](docs/report-format.md)** - Report structure and parsing guide

## Usage

### Check Command (Default)

Run policy checks against your repository:

```bash
# Use default config (repo-policy.yml)
repo-policy check

# Specify custom config
repo-policy --config my-config.yml check

# Override target path and output directory
repo-policy --path /path/to/repo --outdir /tmp/output check

# Clean output directory before run
repo-policy --clean check

# Keep intermediate artifacts
repo-policy --keep-artifacts check
```

### Init Command

Create a baseline configuration file:

```bash
# Create default config
repo-policy init

# Use a preset
repo-policy init --preset baseline
repo-policy init --preset standard
repo-policy init --preset strict

# Force overwrite existing config
repo-policy init --force
```

## Configuration

The `repo-policy.yml` file supports the following options. For comprehensive documentation, see [Configuration Guide](docs/config.md).

### Configuration Presets

- **baseline**: Minimal requirements for basic repository hygiene
- **standard**: Recommended settings for most projects (default)
- **strict**: Comprehensive enforcement for high-quality projects

### Quick Configuration Example

```yaml
# Use a preset for quick start
preset: standard

# Target repository path
target_path: .

# Output directory
outdir: .repo-policy-output

# License configuration
license:
  spdx_id: Apache-2.0
  header_template_path: LICENSE_HEADER.md
  require_header: false

# File classification patterns
globs:
  source: ["**/*.py", "**/*.js", "**/*.ts"]
  test: ["**/test_*.py", "**/*.test.js"]

# Rule configuration
rules:
  include: ["*"]
  exclude: []
  severity_overrides:
    readme-required: warning
  # README section requirements (null = use defaults)
  readme_required_sections: ["Installation", "Usage", "License"]
  # Require tests if source files present
  tests_required_if_sources_present: true
  # Large file threshold in MB
  large_file_threshold_mb: 10
  # Forbidden file patterns (null = use defaults)
  forbidden_patterns: null

# Repository metadata
repo_tags:
  repo_type: library
  language: python
```

For complete schema reference, preset details, and examples, see [Configuration Guide](docs/config.md).

### Available Rules

The following rules are evaluated by default:

**Documentation Rules**
- `readme-required`: Verifies README file presence and required sections

**License Rules**
- `license-file-required`: Verifies LICENSE file presence
- `license-spdx-id-required`: Enforces SPDX ID in configuration
- `license-header-required`: Checks license headers in source files (when enabled)

**Hygiene Rules**
- `ci-required`: Verifies CI workflow presence and test execution
- `gitignore-required`: Requires .gitignore for projects with language markers
- `forbidden-files`: Detects forbidden file patterns (e.g., .DS_Store, Thumbs.db)
- `file-size-limit`: Warns about large files exceeding threshold

**Test Rules**
- `tests-required-with-sources`: Verifies tests exist when source files are present

Rules can be included/excluded using glob patterns and have their severity overridden (error/warning/info). See [Configuration Guide](docs/config.md#rule-catalog) for complete rule documentation.

### CLI Options

- `--config PATH`: Path to config file (default: auto-discover)
- `--path PATH`: Path to repository to analyze (default: .)
- `--outdir PATH`: Output directory (default: .repo-policy-output)
- `--keep-artifacts`: Keep intermediate artifacts after run
- `--clean`: Clean output directory before run
- `--advice`: Show advice and recommendations (stub)
- `-v, --verbose`: Enable verbose output

For detailed CLI reference, see [Usage Guide](docs/usage.md).

### Exit Codes

- `0`: Success (no error-level failures)
- `1`: Error (error-level policy failures or execution error)
- `130`: Interrupted by user (Ctrl+C)

**Note**: Only `error` severity failures cause non-zero exit codes. Warnings are reported but don't fail builds. See [CI Integration Guide](docs/ci.md#exit-code-behavior) for details.

## Development

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

Format code:
```bash
black src tests
```

Type checking:
```bash
mypy src
```

## CI/CD Integration

repo-policy can be integrated into various CI/CD platforms:

### GitHub Actions Example

```yaml
name: Policy Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install repo-policy
        run: pip install repo-policy
      
      - name: Run policy check
        run: repo-policy check --clean --keep-artifacts
      
      - name: Upload policy reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: policy-reports
          path: .repo-policy-output/
```

### Pre-Commit Hook Example

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: repo-policy
        name: Repository Policy Check
        entry: repo-policy check
        language: system
        pass_filenames: false
        always_run: true
```

For comprehensive CI/CD integration guides including GitLab CI, CircleCI, Jenkins, and more, see [CI Integration Guide](docs/ci.md).

## Integration Guides

- **[Repository Analysis Integration](docs/REPO_ANALYSIS.md)**: Learn how to integrate with the repo analyzer tool for metadata extraction
- **[License Header Integration](docs/LICENSE_HEADER.md)**: Learn how to check license headers in source files

## Architecture

The repo-policy tool is designed with a modular architecture:

- **CLI Layer** (`src/cli/`): Command-line interface and argument parsing
- **Configuration** (`src/config/`): Schema validation and config loading
- **Integration** (`src/integration/`): External tool integrations (repo analyzer, license headers)
- **Context** (`src/integration/context.py`): Policy context for storing integration results

Integration results are captured deterministically and made available to downstream rules for policy evaluation.



# Permanents (License, Contributing, Author)

Do not change any of the below sections

## License

This Agent Foundry Project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Contributing

Feel free to submit issues and enhancement requests!

## Author

Created by Agent Foundry and John Brosnihan
