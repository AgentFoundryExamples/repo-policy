# repo-policy Examples

This directory contains example configurations and integrations for `repo-policy`.

## Configuration Examples

### Preset-Based Configurations

- **[repo-policy.baseline.yml](repo-policy.baseline.yml)** - Minimal requirements for basic repository hygiene
  - Most rules as warnings
  - Lenient file size limits
  - Optional test requirements
  - Recommended for: experimental projects, personal projects, early development

- **[repo-policy.standard.yml](repo-policy.standard.yml)** - Recommended settings for most projects
  - Balanced error and warning severities
  - Reasonable file size limits
  - Test requirements enabled
  - Recommended for: production applications, open source projects, team-maintained code

- **[repo-policy.strict.yml](repo-policy.strict.yml)** - Comprehensive enforcement for high-quality projects
  - Most rules as errors
  - Strict file size limits
  - Mandatory test coverage
  - Recommended for: critical infrastructure, security-sensitive code, compliance requirements

### Usage

Copy one of the example configurations to your repository:

```bash
# Copy baseline configuration
cp examples/repo-policy.baseline.yml repo-policy.yml

# Or generate with preset
repo-policy init --preset standard
```

Then customize as needed for your project.

## CI/CD Integration Examples

### GitHub Actions

- **[github-actions-basic.yml](github-actions-basic.yml)** - Basic workflow with policy check
  - Runs on push and pull request
  - Uploads policy reports as artifacts
  - No external tools required

- **[github-actions-full.yml](github-actions-full.yml)** - Full workflow with all features
  - Installs repo-analyzer and license-header tools
  - Displays summary in workflow
  - Extended artifact retention

- **[github-actions-pr-comment.yml](github-actions-pr-comment.yml)** - Workflow with PR comments
  - Posts policy report as PR comment
  - Updates existing comment on subsequent runs
  - Full GitHub integration

### Pre-Commit Hooks

- **[pre-commit-config.yaml](pre-commit-config.yaml)** - Pre-commit hook configuration
  - Local enforcement before commits
  - No network required
  - Fast feedback for developers

### Other CI Platforms

- **[gitlab-ci.yml](gitlab-ci.yml)** - GitLab CI configuration
- **[circleci-config.yml](circleci-config.yml)** - CircleCI configuration

## Environment Variables

- **[.env.example](.env.example)** - Environment variables reference
  - Documents available environment variables
  - Notes that v0 requires no secrets
  - Provides CI integration guidance

## Getting Started

### 1. Choose a Configuration

Start with one of the preset configurations:

```bash
# Copy example to your repo
cp examples/repo-policy.standard.yml repo-policy.yml

# Or initialize with preset
repo-policy init --preset standard
```

### 2. Set Up CI Integration

Choose a CI platform and copy the workflow:

**GitHub Actions:**
```bash
mkdir -p .github/workflows
cp examples/github-actions-basic.yml .github/workflows/policy-check.yml
```

**GitLab CI:**
```bash
cp examples/gitlab-ci.yml .gitlab-ci.yml
```

**CircleCI:**
```bash
mkdir -p .circleci
cp examples/circleci-config.yml .circleci/config.yml
```

### 3. Set Up Pre-Commit Hook (Optional)

For local enforcement:

```bash
# Install pre-commit
pip install pre-commit

# Copy configuration
cp examples/pre-commit-config.yaml .pre-commit-config.yaml

# Install the hook
pre-commit install

# Test it
pre-commit run --all-files
```

### 4. Customize Configuration

Edit `repo-policy.yml` to match your project:

```yaml
# Adjust license
license:
  spdx_id: MIT  # or Apache-2.0, GPL-3.0, etc.
  require_header: true

# Configure file patterns
globs:
  source:
    - "**/*.py"
    - "**/*.js"
  test:
    - "**/test_*.py"
    - "**/*.test.js"

# Adjust rule severities
rules:
  severity_overrides:
    readme-required: error
    tests-required-with-sources: warning
```

### 5. Run Policy Check

Test locally:

```bash
repo-policy check --verbose
```

Review reports:

```bash
cat .repo-policy-output/policy_report.md
```

## Common Scenarios

### Starting a New Project

Use baseline configuration with gradual enforcement:

```bash
repo-policy init --preset baseline
repo-policy check
```

### Migrating Existing Project

Start with warnings, then gradually upgrade to errors:

```yaml
# Week 1: All warnings
rules:
  severity_overrides:
    license-header-required: warning
    tests-required-with-sources: warning

# Week 4: After fixes, upgrade to errors
rules:
  severity_overrides:
    license-header-required: error
    tests-required-with-sources: error
```

### Monorepo

Configure per-service with shared base:

```bash
# Root configuration (shared)
cp examples/repo-policy.standard.yml repo-policy.yml

# Service-specific (overrides)
cp examples/repo-policy.strict.yml services/api/repo-policy.yml
```

Check each service:

```bash
repo-policy --path services/api check
repo-policy --path services/web check
```

### High-Security Project

Use strict configuration with all rules as errors:

```bash
repo-policy init --preset strict
repo-policy check
```

### Open Source Project

Use standard configuration with comprehensive documentation:

```yaml
preset: standard

rules:
  readme_required_sections:
    - Installation
    - Usage
    - Contributing
    - License
  severity_overrides:
    license-header-required: error
    ci-required: error
```

## Documentation

For comprehensive documentation, see:

- [Usage Guide](../docs/usage.md) - CLI commands and options
- [Configuration Guide](../docs/config.md) - Configuration schema and rules
- [CI Integration Guide](../docs/ci.md) - Detailed CI/CD integration
- [Repository Analysis Integration](../docs/REPO_ANALYSIS.md) - Repo analyzer details
- [License Header Integration](../docs/LICENSE_HEADER.md) - License header checking

## Support

For issues, questions, or contributions:

- Report issues at: https://github.com/AgentFoundryExamples/repo-policy/issues
- See main documentation: [README.md](../README.md)
