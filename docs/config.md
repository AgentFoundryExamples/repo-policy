# Configuration Guide

This guide provides a comprehensive reference for configuring `repo-policy`.

## Table of Contents

- [Overview](#overview)
- [Configuration File](#configuration-file)
- [Configuration Schema](#configuration-schema)
  - [Top-Level Settings](#top-level-settings)
  - [License Configuration](#license-configuration)
  - [File Classification](#file-classification)
  - [Rule Configuration](#rule-configuration)
  - [Integration Settings](#integration-settings)
  - [Repository Metadata](#repository-metadata)
- [Configuration Presets](#configuration-presets)
- [Rule Catalog](#rule-catalog)
- [Severity Overrides](#severity-overrides)
- [Include/Exclude Patterns](#includeexclude-patterns)
- [Examples](#examples)

## Overview

The `repo-policy` tool is configured via a YAML file named `repo-policy.yml`. The configuration file controls:

- Which rules to run and at what severity
- How to classify source and test files
- License requirements and header enforcement
- Integration with external tools
- Repository metadata and tags

## Configuration File

### Location

By default, the tool searches for `repo-policy.yml` in:
1. Current directory
2. Parent directories (up to git root)

You can override this with the `--config` flag:

```bash
repo-policy --config custom-config.yml check
```

### Creating a Configuration

Use the `init` command to create a new configuration:

```bash
# Create default configuration
repo-policy init

# Create with a preset
repo-policy init --preset standard
```

## Configuration Schema

### Top-Level Settings

```yaml
# Target repository path (default: current directory)
target_path: .

# Output directory for reports and artifacts
outdir: .repo-policy-output

# Configuration preset (optional)
# Valid values: baseline, standard, strict
preset: null

# Runtime options (can be overridden via CLI)
keep_artifacts: false
clean: false
advice: false
```

#### `target_path`

The path to the repository to analyze. Can be overridden with `--path` CLI flag.

```yaml
target_path: /path/to/repository
```

#### `outdir`

Directory where reports and artifacts are written. Can be overridden with `--outdir` CLI flag.

```yaml
outdir: .repo-policy-output
```

#### `preset`

Apply a predefined configuration preset. See [Configuration Presets](#configuration-presets) for details.

```yaml
preset: standard  # baseline, standard, or strict
```

#### `keep_artifacts`

Keep intermediate artifacts after run. Can be overridden with `--keep-artifacts` CLI flag.

```yaml
keep_artifacts: true
```

#### `clean`

Clean output directory before run. Can be overridden with `--clean` CLI flag.

```yaml
clean: false
```

#### `advice`

Enable advice and recommendations (placeholder for future feature). Can be overridden with `--advice` CLI flag.

```yaml
advice: false
```

### License Configuration

```yaml
license:
  # SPDX license identifier
  # See https://spdx.org/licenses/ for valid identifiers
  spdx_id: Apache-2.0
  
  # Path to license header template file
  header_template_path: LICENSE_HEADER.md
  
  # Require license headers in source files
  require_header: false
  
  # File patterns to include in header checks
  include_globs:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.java"
  
  # File patterns to exclude from header checks
  exclude_globs:
    - "**/test_*.py"
    - "**/*_test.py"
    - "**/vendor/**"
```

#### `spdx_id`

The SPDX license identifier for your project. Required by the `license-spdx-id-required` rule.

**Common values:**
- `Apache-2.0`
- `MIT`
- `GPL-3.0`
- `BSD-3-Clause`
- `ISC`

See [SPDX License List](https://spdx.org/licenses/) for all valid identifiers.

#### `header_template_path`

Path to a file containing the license header template. The template should contain the raw license text without comment markers. The license-header tool automatically wraps it with appropriate comment syntax for each file type.

```yaml
license:
  header_template_path: LICENSE_HEADER.md
```

#### `require_header`

Whether to enforce license headers in source files. Set to `true` to enable the `license-header-required` rule.

```yaml
license:
  require_header: true
```

#### `include_globs` and `exclude_globs`

Control which files are checked for license headers. Uses glob patterns.

```yaml
license:
  include_globs:
    - "**/*.py"      # All Python files
    - "src/**/*.js"  # JavaScript files in src/
  exclude_globs:
    - "**/test_*.py"     # Test files
    - "**/vendor/**"     # Vendor directory
    - "**/__pycache__/**"
```

### File Classification

```yaml
globs:
  # Source file patterns
  source:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.java"
    - "**/*.go"
    - "**/*.rs"
    - "**/*.c"
    - "**/*.cpp"
  
  # Test file patterns
  test:
    - "**/test_*.py"
    - "**/*_test.py"
    - "**/*.test.js"
    - "**/*.spec.ts"
```

These glob patterns are used by rules to identify source and test files in your repository.

#### Source Patterns

Patterns that match source code files. Used by rules like `tests-required-with-sources`.

```yaml
globs:
  source:
    - "**/*.py"   # All Python files
    - "src/**/*.js"  # JS files in src/
```

#### Test Patterns

Patterns that match test files. Used to verify test coverage.

```yaml
globs:
  test:
    - "**/test_*.py"      # Python test files
    - "**/*.test.js"      # JavaScript test files
    - "**/__tests__/**"   # Test directories
```

### Rule Configuration

```yaml
rules:
  # Rules to include (glob patterns, default: all)
  include:
    - "*"
  
  # Rules to exclude (glob patterns)
  exclude: []
  
  # Override severity for specific rules
  # Valid severities: error, warning, info
  severity_overrides:
    readme-required: warning
    ci-required: error
  
  # README section requirements (null = use defaults)
  readme_required_sections:
    - Installation
    - Usage
    - License
  
  # Require tests if source files present
  tests_required_if_sources_present: true
  
  # Large file threshold in MB
  large_file_threshold_mb: 10
  
  # Forbidden file patterns (null = use defaults)
  forbidden_patterns: null
```

#### `include` and `exclude`

Control which rules are evaluated using glob patterns. See [Include/Exclude Patterns](#includeexclude-patterns) for details.

```yaml
rules:
  include:
    - "license-*"  # All license rules
    - "readme-*"   # All readme rules
  exclude:
    - "ci-*"       # Exclude CI rules
```

#### `severity_overrides`

Override the default severity for specific rules. Valid severities: `error`, `warning`, `info`.

```yaml
rules:
  severity_overrides:
    readme-required: warning  # Downgrade from error to warning
    ci-required: error        # Upgrade to error
```

**Important**: Only `error` severity failures cause a non-zero exit code. `warning` and `info` failures are reported but don't fail the build.

#### `readme_required_sections`

List of section headings required in README files. Set to `null` to use default sections.

```yaml
rules:
  readme_required_sections:
    - Installation
    - Usage
    - Configuration
    - License
```

**Default sections (when null):**
- Installation
- Usage
- License

#### `tests_required_if_sources_present`

Whether to require test files when source files are present. Used by the `tests-required-with-sources` rule.

```yaml
rules:
  tests_required_if_sources_present: true
```

Set to `false` to disable this check:

```yaml
rules:
  tests_required_if_sources_present: false
```

#### `large_file_threshold_mb`

Size threshold in megabytes for the `file-size-limit` rule. Files exceeding this size trigger warnings.

```yaml
rules:
  large_file_threshold_mb: 5  # Warn about files > 5MB
```

#### `forbidden_patterns`

List of file patterns that should not exist in the repository. Set to `null` to use defaults.

```yaml
rules:
  forbidden_patterns:
    - ".DS_Store"
    - "Thumbs.db"
    - "*.tmp"
    - "*.swp"
```

**Default patterns (when null):**
- `.DS_Store` (macOS)
- `Thumbs.db` (Windows)
- `desktop.ini` (Windows)
- `*.tmp`

### Integration Settings

```yaml
integration:
  # Enable/disable repo analyzer integration
  enable_repo_analyzer: true
  
  # Path to repo-analyzer binary (auto-detect if null)
  repo_analyzer_binary: null
  
  # Analyzer workspace mode: 'temp_workspace' or 'direct_output'
  repo_analyzer_workspace_mode: direct_output
  
  # Enable/disable license header checking
  enable_license_headers: true
  
  # Path to license-header binary (auto-detect if null)
  license_header_binary: null
```

#### `enable_repo_analyzer`

Whether to run the repo-analyzer integration. If disabled, analyzer-dependent rules will be skipped.

```yaml
integration:
  enable_repo_analyzer: true
```

#### `repo_analyzer_binary`

Path to the repo-analyzer binary. If `null`, the tool searches `PATH`.

```yaml
integration:
  repo_analyzer_binary: /usr/local/bin/repo-analyzer
```

#### `repo_analyzer_workspace_mode`

How the analyzer executes:
- `direct_output`: Analyzer writes directly to output directory (faster, default)
- `temp_workspace`: Analyzer runs in isolated temporary directory (safer)

```yaml
integration:
  repo_analyzer_workspace_mode: direct_output
```

See [Repository Analysis Integration](REPO_ANALYSIS.md#workspace-modes) for details.

#### `enable_license_headers`

Whether to run license header checking. If disabled, the `license-header-required` rule will be skipped.

```yaml
integration:
  enable_license_headers: true
```

#### `license_header_binary`

Path to the license-header binary. If `null`, the tool searches `PATH`.

```yaml
integration:
  license_header_binary: /usr/local/bin/license-header
```

### Repository Metadata

```yaml
repo_tags:
  repo_type: library
  language: python
  team: platform
  tier: production
```

Repository tags are metadata about your repository. They're included in reports and can be used for filtering and organization.

**Common tags:**

- `repo_type`: library, application, tool, service, etc.
- `language`: python, javascript, go, java, rust, etc.
- `team`: Team or organization owning the repository
- `tier`: production, staging, development, experimental, etc.

Tags are informational and don't affect rule evaluation.

## Configuration Presets

Presets provide predefined configurations for common use cases.

### baseline

Minimal requirements for basic repository hygiene.

**Recommended for:**
- Experimental or prototype projects
- Personal projects
- Projects in early development

**Characteristics:**
- Most rules set to `warning` severity
- Lenient file size limits
- Optional test requirements
- Basic documentation checks

**Example:**
```yaml
preset: baseline
```

### standard

Recommended settings for most projects.

**Recommended for:**
- Production applications
- Open source projects
- Team-maintained projects

**Characteristics:**
- Balanced error and warning severities
- Reasonable file size limits
- Test requirements enabled
- Full documentation checks
- License enforcement recommended

**Example:**
```yaml
preset: standard
```

### strict

Comprehensive enforcement for high-quality projects.

**Recommended for:**
- Critical infrastructure
- Security-sensitive projects
- Projects with compliance requirements
- Open source libraries

**Characteristics:**
- Most rules set to `error` severity
- Strict file size limits
- Mandatory test coverage
- Complete documentation requirements
- Mandatory license headers

**Example:**
```yaml
preset: strict
```

### Using Presets

Apply a preset during initialization:

```bash
repo-policy init --preset strict
```

Or set it in your configuration file:

```yaml
preset: strict

# Override specific settings
rules:
  severity_overrides:
    readme-required: warning  # Relax one rule
```

**Note**: Preset settings can be overridden by explicit configuration values.

## Rule Catalog

The following rules are available in repo-policy:

### Documentation Rules

#### `readme-required`

Verifies that a README file exists and contains required sections.

**Default Severity:** `error`

**Configuration:**
```yaml
rules:
  readme_required_sections:
    - Installation
    - Usage
    - License
```

**Evidence:**
- `has_readme`: Whether README exists
- `found_sections`: Sections found in README
- `missing_sections`: Required sections not found

---

### License Rules

#### `license-file-required`

Verifies that a LICENSE file exists in the repository root.

**Default Severity:** `error`

**Evidence:**
- `license_file_found`: Whether LICENSE file exists
- `license_file_path`: Path to LICENSE file (if found)

---

#### `license-spdx-id-required`

Verifies that a valid SPDX license identifier is configured.

**Default Severity:** `error`

**Configuration:**
```yaml
license:
  spdx_id: Apache-2.0
```

**Evidence:**
- `spdx_id`: Configured SPDX identifier
- `is_valid`: Whether identifier is valid

---

#### `license-header-required`

Checks that source files have the required license headers.

**Default Severity:** `error`

**Requirements:**
- `license.require_header` must be `true`
- `license-header` tool must be installed
- Header template file must exist

**Configuration:**
```yaml
license:
  require_header: true
  header_template_path: LICENSE_HEADER.md
  include_globs:
    - "**/*.py"
  exclude_globs:
    - "**/test_*.py"
```

**Evidence:**
- `compliant_files`: Files with correct headers
- `non_compliant_files`: Files missing headers
- `scanned`: Total files scanned
- `eligible`: Files eligible for checking

---

### Hygiene Rules

#### `ci-required`

Verifies that CI workflow files exist and contain test commands.

**Default Severity:** `warning`

**Evidence:**
- `has_ci`: Whether CI workflows exist
- `has_test_commands`: Whether test commands detected (heuristic)
- `workflow_files`: List of CI workflow files

---

#### `gitignore-required`

Requires a `.gitignore` file for projects with language markers.

**Default Severity:** `warning`

**Evidence:**
- `has_gitignore`: Whether .gitignore exists
- `has_language_markers`: Whether language-specific files detected

---

#### `forbidden-files`

Detects forbidden file patterns (e.g., `.DS_Store`, `Thumbs.db`).

**Default Severity:** `warning`

**Configuration:**
```yaml
rules:
  forbidden_patterns:
    - ".DS_Store"
    - "Thumbs.db"
    - "*.tmp"
```

**Evidence:**
- `forbidden_files`: List of forbidden files found
- `patterns_checked`: Patterns that were checked

---

#### `file-size-limit`

Warns about files exceeding the configured size threshold.

**Default Severity:** `warning`

**Configuration:**
```yaml
rules:
  large_file_threshold_mb: 10
```

**Evidence:**
- `large_files`: List of files exceeding threshold
- `threshold_mb`: Configured threshold
- `max_size_mb`: Size of largest file

---

### Test Rules

#### `tests-required-with-sources`

Verifies that test files exist when source files are present.

**Default Severity:** `error`

**Configuration:**
```yaml
rules:
  tests_required_if_sources_present: true

globs:
  source:
    - "**/*.py"
  test:
    - "**/test_*.py"
```

**Evidence:**
- `has_sources`: Whether source files found
- `has_tests`: Whether test files found
- `source_count`: Number of source files
- `test_count`: Number of test files

## Severity Overrides

Severity overrides allow you to adjust the severity of specific rules without modifying the rule implementation.

### Severity Levels

- **error**: Failures cause non-zero exit code and fail CI builds
- **warning**: Failures are reported but don't fail builds
- **info**: Informational messages for awareness

### Configuring Overrides

```yaml
rules:
  severity_overrides:
    # Downgrade errors to warnings
    readme-required: warning
    license-file-required: warning
    
    # Upgrade warnings to errors
    ci-required: error
    gitignore-required: error
    
    # Downgrade to info
    file-size-limit: info
```

### Use Cases

#### Development vs Production

Different severity for different environments:

**Development:**
```yaml
# repo-policy.dev.yml
rules:
  severity_overrides:
    license-header-required: warning
    tests-required-with-sources: warning
```

**Production:**
```yaml
# repo-policy.prod.yml
rules:
  severity_overrides:
    license-header-required: error
    tests-required-with-sources: error
```

#### Gradual Enforcement

Introduce rules gradually without breaking existing workflows:

```yaml
# Week 1: Introduce as warnings
rules:
  severity_overrides:
    license-header-required: warning

# Week 4: Upgrade to errors after teams have fixed issues
rules:
  severity_overrides:
    license-header-required: error
```

## Include/Exclude Patterns

Control which rules are evaluated using glob patterns.

### Pattern Syntax

- `*`: Match any characters except `/`
- `**`: Match any characters including `/`
- `?`: Match a single character
- `[abc]`: Match any character in set
- `{a,b}`: Match either pattern

### Examples

#### Include Specific Rules

```yaml
rules:
  include:
    - "license-*"  # All license rules
```

This includes:
- `license-file-required`
- `license-spdx-id-required`
- `license-header-required`

#### Exclude Specific Rules

```yaml
rules:
  include:
    - "*"  # All rules
  exclude:
    - "ci-*"  # Exclude CI rules
```

#### Complex Patterns

```yaml
rules:
  include:
    - "license-*"      # All license rules
    - "readme-*"       # All readme rules
    - "tests-*"        # All test rules
  exclude:
    - "license-header-required"  # Exclude header checking
```

### Rule Selection Logic

1. Start with all available rules
2. Apply `include` patterns (whitelist)
3. Apply `exclude` patterns (blacklist)
4. Result is the final set of rules to evaluate

### Common Patterns

#### Minimal Checks

```yaml
rules:
  include:
    - "readme-required"
    - "license-file-required"
  exclude: []
```

#### Everything Except Headers

```yaml
rules:
  include:
    - "*"
  exclude:
    - "*-header-*"
```

#### Only Documentation Rules

```yaml
rules:
  include:
    - "readme-*"
  exclude: []
```

## Examples

### Minimal Configuration

```yaml
target_path: .
outdir: .repo-policy-output

license:
  spdx_id: MIT
  require_header: false

rules:
  include:
    - "readme-required"
    - "license-file-required"
```

### Standard Open Source Project

```yaml
target_path: .
outdir: .repo-policy-output
preset: standard

license:
  spdx_id: Apache-2.0
  header_template_path: LICENSE_HEADER.md
  require_header: true
  include_globs:
    - "**/*.py"
    - "**/*.js"
  exclude_globs:
    - "**/test_*.py"

globs:
  source:
    - "**/*.py"
    - "**/*.js"
  test:
    - "**/test_*.py"
    - "**/*.test.js"

rules:
  include:
    - "*"
  exclude: []
  severity_overrides:
    ci-required: error
  readme_required_sections:
    - Installation
    - Usage
    - Contributing
    - License
  tests_required_if_sources_present: true
  large_file_threshold_mb: 10

repo_tags:
  repo_type: library
  language: python
  license: Apache-2.0
```

### Strict Enterprise Configuration

```yaml
target_path: .
outdir: .repo-policy-output
preset: strict

license:
  spdx_id: Proprietary
  header_template_path: LICENSE_HEADER.md
  require_header: true
  include_globs:
    - "**/*.py"
    - "**/*.java"
    - "**/*.ts"
  exclude_globs:
    - "**/vendor/**"
    - "**/node_modules/**"

globs:
  source:
    - "**/*.py"
    - "**/*.java"
    - "**/*.ts"
  test:
    - "**/test_*.py"
    - "**/*Test.java"
    - "**/*.test.ts"

rules:
  include:
    - "*"
  exclude: []
  severity_overrides:
    readme-required: error
    license-file-required: error
    license-spdx-id-required: error
    license-header-required: error
    ci-required: error
    gitignore-required: error
    tests-required-with-sources: error
  readme_required_sections:
    - Overview
    - Installation
    - Configuration
    - Usage
    - Testing
    - Deployment
    - Security
    - License
  tests_required_if_sources_present: true
  large_file_threshold_mb: 5
  forbidden_patterns:
    - ".DS_Store"
    - "Thumbs.db"
    - "*.tmp"
    - "*.log"
    - "*.bak"

integration:
  enable_repo_analyzer: true
  enable_license_headers: true
  repo_analyzer_workspace_mode: temp_workspace

repo_tags:
  repo_type: service
  language: java
  team: platform-engineering
  tier: production
  compliance: soc2
```

### Monorepo Configuration

```yaml
# Root configuration
target_path: .
outdir: .repo-policy-output
preset: standard

license:
  spdx_id: MIT
  require_header: false

rules:
  include:
    - "*"
  exclude:
    - "license-header-required"  # Per-service choice
  severity_overrides:
    tests-required-with-sources: warning  # Some services still adding tests

repo_tags:
  repo_type: monorepo
  language: polyglot
```

### Development-Friendly Configuration

```yaml
target_path: .
outdir: .repo-policy-output
preset: baseline

license:
  spdx_id: MIT
  require_header: false

rules:
  include:
    - "*"
  exclude: []
  severity_overrides:
    readme-required: warning
    license-file-required: warning
    ci-required: warning
    tests-required-with-sources: warning
  tests_required_if_sources_present: false
  large_file_threshold_mb: 50

integration:
  enable_repo_analyzer: false
  enable_license_headers: false

repo_tags:
  repo_type: experiment
  language: python
```

## See Also

- [Usage Guide](usage.md) - CLI commands and options
- [CI Integration Guide](ci.md) - Using repo-policy in CI/CD
- [Repository Analysis Integration](REPO_ANALYSIS.md) - Repo analyzer details
- [License Header Integration](LICENSE_HEADER.md) - License header checking
- [Report Format](report-format.md) - Report structure and parsing
