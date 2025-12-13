# Usage Guide

This guide covers the complete usage of the `repo-policy` command-line tool.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [check](#check-command)
  - [init](#init-command)
- [Global Options](#global-options)
- [Exit Codes](#exit-codes)
- [Artifact Management](#artifact-management)
- [Monorepo and Subdirectory Usage](#monorepo-and-subdirectory-usage)
- [Advanced Usage](#advanced-usage)

## Installation

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/AgentFoundryExamples/repo-policy.git
cd repo-policy
pip install -e .
```

### Development Installation

Install with development dependencies (includes testing, formatting, and type checking tools):

```bash
pip install -e ".[dev]"
```

### Prerequisites

The tool has minimal dependencies, but certain rules require external tools:

- **repo-analyzer**: Required for repository metadata analysis
  ```bash
  pip install "git+https://github.com/AgentFoundryExamples/repo-summarizer-v1.git@main"
  ```

- **license-header**: Required for license header enforcement
  ```bash
  pip install "git+https://github.com/AgentFoundryExamples/license-header.git@main"
  ```

Both tools are optional but recommended for full policy enforcement. If not installed, related rules will be skipped.

## Quick Start

1. Initialize a configuration file:
   ```bash
   repo-policy init
   ```

2. Review and customize `repo-policy.yml`

3. Run policy checks:
   ```bash
   repo-policy check
   ```

4. Review the generated reports in `.repo-policy-output/`

## Commands

### check Command

The `check` command (default) runs policy checks against your repository.

#### Basic Usage

```bash
# Use default configuration
repo-policy check

# Specify custom config file
repo-policy --config my-config.yml check

# Check a different repository
repo-policy --path /path/to/repo check

# Override output directory
repo-policy --outdir /tmp/policy-output check
```

#### With Artifact Management

```bash
# Clean output directory before run
repo-policy --clean check

# Keep intermediate artifacts after run
repo-policy --keep-artifacts check

# Combine both flags
repo-policy --clean --keep-artifacts check
```

#### Verbose Output

```bash
# Enable detailed logging
repo-policy --verbose check
repo-policy -v check
```

#### Advice Mode (Placeholder)

```bash
# Show advice and recommendations (future feature)
repo-policy --advice check
```

### init Command

The `init` command creates a new `repo-policy.yml` configuration file.

#### Basic Usage

```bash
# Create default configuration
repo-policy init

# Use a preset configuration
repo-policy init --preset baseline
repo-policy init --preset standard
repo-policy init --preset strict

# Force overwrite existing configuration
repo-policy init --force
```

#### Preset Profiles

- **baseline**: Minimal requirements for basic repository hygiene
- **standard**: Recommended settings for most projects
- **strict**: Comprehensive enforcement for high-quality projects

See [Configuration Guide](config.md) for detailed preset descriptions.

## Global Options

These options can be used with any command:

### `--config PATH`

Path to the configuration file. If not specified, the tool searches for `repo-policy.yml` in the current directory and parent directories.

```bash
repo-policy --config custom-config.yml check
```

### `--path PATH`

Path to the repository to analyze. Defaults to the current directory (`.`).

```bash
# Check a different repository
repo-policy --path /path/to/repo check

# Check a subdirectory
repo-policy --path ./services/api check
```

### `--outdir PATH`

Output directory for reports and artifacts. Defaults to `.repo-policy-output`.

```bash
repo-policy --outdir /tmp/reports check
```

### `--keep-artifacts`

Keep intermediate artifacts after the run completes. By default, artifacts from external tools are removed.

```bash
repo-policy --keep-artifacts check
```

Preserves:
- Repository analyzer outputs (`analyzer/`)
- License header check reports (`license-headers/`)

### `--clean`

Clean the output directory before running. Removes all previous artifacts and reports.

```bash
repo-policy --clean check
```

**Important**: Clean only affects files within the configured `outdir` and never deletes files outside that directory.

### `--advice`

Show advice and recommendations. This is a placeholder for future functionality.

```bash
repo-policy --advice check
```

### `-v, --verbose`

Enable verbose output with detailed logging.

```bash
repo-policy --verbose check
repo-policy -v check
```

## Exit Codes

The `repo-policy` tool uses the following exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | No error-level policy failures |
| `1` | Error | One or more error-level policy failures or execution error |
| `130` | Interrupted | User interrupted with Ctrl+C |

### Understanding Exit Codes

- **Exit Code 0**: All checks passed or only warnings were found
  - Rules can fail with `warning` severity without causing a non-zero exit code
  - The report will still show warnings for review

- **Exit Code 1**: At least one rule failed with `error` severity
  - CI builds should fail on this exit code
  - Review `policy_report.md` for details

- **Exit Code 130**: User interrupted the process
  - Artifacts may be incomplete
  - Re-run the check to get complete results

### Example: Exit Code Handling in Scripts

```bash
#!/bin/bash
repo-policy check

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Policy check passed"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "❌ Policy check failed"
    exit 1
elif [ $EXIT_CODE -eq 130 ]; then
    echo "⚠️ Policy check interrupted"
    exit 130
fi
```

## Artifact Management

The tool generates several types of artifacts during execution:

### Output Structure

```
.repo-policy-output/
├── policy_report.json       # Machine-readable report
├── policy_report.md         # Human-readable report
├── analyzer/                # Repository analyzer outputs (optional)
│   ├── tree.json
│   ├── dependencies.json
│   └── metadata.json
└── license-headers/         # License header check reports (optional)
    ├── license-header-check-report.json
    └── license-header-check-report.md
```

### Artifact Lifecycle

#### Default Behavior

By default, intermediate artifacts are **removed** after the run:
- Repository analyzer outputs are deleted
- License header check reports are deleted
- Only `policy_report.json` and `policy_report.md` are kept

#### With `--keep-artifacts`

When `--keep-artifacts` is used, all artifacts are **preserved**:
- Useful for debugging and troubleshooting
- Allows manual inspection of integration tool outputs
- Required for some advanced workflows

#### With `--clean`

When `--clean` is used, the output directory is **emptied** before the run:
- Removes previous reports and artifacts
- Ensures a fresh analysis
- Safe to use - only affects the configured `outdir`

### Best Practices

- Use `--keep-artifacts` during development and debugging
- Use `--clean` in CI to ensure reproducibility
- Use separate `--outdir` for concurrent runs

## Monorepo and Subdirectory Usage

The tool can be used with monorepos and subdirectories by specifying the `--path` option.

### Checking a Subdirectory

```bash
# Check a specific service in a monorepo
repo-policy --path ./services/api check

# Check multiple services (run separately)
repo-policy --path ./services/api --outdir ./output/api check
repo-policy --path ./services/web --outdir ./output/web check
```

### Configuration Discovery

The tool searches for `repo-policy.yml` in the specified path and parent directories:

1. `./services/api/repo-policy.yml`
2. `./services/repo-policy.yml`
3. `./repo-policy.yml`

To use a specific configuration:

```bash
repo-policy --config ./services/api/repo-policy.yml --path ./services/api check
```

### Monorepo Best Practices

1. **Shared Configuration**: Place a base `repo-policy.yml` at the root
   ```yaml
   # Root repo-policy.yml
   preset: standard
   ```

2. **Service-Specific Overrides**: Add service-specific configs
   ```yaml
   # services/api/repo-policy.yml
   preset: strict
   rules:
     severity_overrides:
       readme-required: warning
   ```

3. **CI Integration**: Check each service separately
   ```yaml
   # .github/workflows/policy.yml
   strategy:
     matrix:
       service: [api, web, worker]
   steps:
     - run: repo-policy --path ./services/${{ matrix.service }} check
   ```

## Advanced Usage

### Configuration Overrides

Command-line options override configuration file settings:

```bash
# Override target_path from config
repo-policy --path /other/repo check

# Override outdir from config
repo-policy --outdir /tmp/output check
```

### Combining Multiple Flags

```bash
# Full cleanup and artifact retention
repo-policy --clean --keep-artifacts --verbose check

# Check subdirectory with custom output
repo-policy --path ./services/api --outdir ./output/api --clean check
```

### Integration with External Tools

The tool automatically detects and uses external tools if available:

```bash
# Verify tool availability
which repo-analyzer
which license-header

# Run policy check (tools will be auto-detected)
repo-policy check
```

To disable specific integrations, edit `repo-policy.yml`:

```yaml
integration:
  enable_repo_analyzer: false
  enable_license_headers: false
```

### Concurrent Runs

Run multiple checks concurrently with distinct output directories:

```bash
# Terminal 1
repo-policy --outdir /tmp/run1 check

# Terminal 2
repo-policy --outdir /tmp/run2 check
```

Each run uses its own isolated output directory, preventing artifact collisions.

### Scripting and Automation

#### Parse JSON Report

```bash
#!/bin/bash
repo-policy check

# Extract summary statistics
TOTAL=$(jq '.summary.total_rules' .repo-policy-output/policy_report.json)
PASSED=$(jq '.summary.passed_rules' .repo-policy-output/policy_report.json)
FAILED=$(jq '.summary.failed_rules' .repo-policy-output/policy_report.json)

echo "Total: $TOTAL, Passed: $PASSED, Failed: $FAILED"
```

#### Conditional Execution

```bash
#!/bin/bash
# Only upload reports if check fails
if ! repo-policy check; then
    echo "Policy check failed, uploading reports..."
    aws s3 cp .repo-policy-output/policy_report.md s3://my-bucket/reports/
fi
```

## Troubleshooting

### Configuration Not Found

```
Error: Configuration file not found
```

**Solution**: Create a configuration file or specify the path:
```bash
repo-policy init
# or
repo-policy --config /path/to/config.yml check
```

### External Tools Not Found

```
Warning: repo-analyzer tool not found. Skipping analyzer integration.
Warning: license-header tool not found. Skipping header checks.
```

**Solution**: Install the required tools:
```bash
pip install "git+https://github.com/AgentFoundryExamples/repo-summarizer-v1.git@main"
pip install "git+https://github.com/AgentFoundryExamples/license-header.git@main"
```

### Permission Denied

```
Error: Permission denied: .repo-policy-output
```

**Solution**: Ensure you have write permissions to the output directory:
```bash
# Use a different output directory
repo-policy --outdir /tmp/policy-output check
```

### Verbose Logging

Enable verbose output to see detailed execution logs:

```bash
repo-policy --verbose check
```

## See Also

- [Configuration Guide](config.md) - Configuration schema and options
- [CI Integration Guide](ci.md) - Using repo-policy in CI/CD
- [Repository Analysis Integration](REPO_ANALYSIS.md) - Repo analyzer integration
- [License Header Integration](LICENSE_HEADER.md) - License header checking
- [Report Format](report-format.md) - Report structure and parsing
