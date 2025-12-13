# repo-policy

A deterministic repository policy enforcement tool with configurable rules and integrations.

## Features

- **Schema-driven configuration**: YAML-based config with validation
- **Flexible CLI**: Support for `check` (default) and `init` commands
- **Configurable rules**: Include/exclude patterns and severity overrides
- **License management**: SPDX ID tracking and header requirements
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

The `repo-policy.yml` file supports the following options:

```yaml
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
    license-header-missing: warning

# Repository metadata
repo_tags:
  repo_type: library
  language: python

# Preset
preset: null  # baseline, standard, or strict
```

### CLI Options

- `--config PATH`: Path to config file (default: auto-discover)
- `--path PATH`: Path to repository to analyze (default: .)
- `--outdir PATH`: Output directory (default: .repo-policy-output)
- `--keep-artifacts`: Keep intermediate artifacts after run
- `--clean`: Clean output directory before run
- `--advice`: Show advice and recommendations (stub)
- `-v, --verbose`: Enable verbose output

### Exit Codes

- `0`: Success (no error-level failures)
- `1`: Error (error-level policy failures or execution error)
- `130`: Interrupted by user (Ctrl+C)

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
