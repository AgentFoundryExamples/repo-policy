# CI/CD Integration Guide

This guide covers integrating `repo-policy` into various CI/CD platforms for automated policy enforcement.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [GitHub Actions](#github-actions)
- [Pre-Commit Hooks](#pre-commit-hooks)
- [Generic CI Integration](#generic-ci-integration)
- [Exit Code Behavior](#exit-code-behavior)
- [Artifact Management](#artifact-management)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Running `repo-policy` in CI provides automated enforcement of repository policies:

- **Prevents policy violations** from being merged
- **Provides immediate feedback** to developers
- **Generates artifacts** for audit and compliance
- **Enforces consistency** across all repositories

### Key Features for CI

- **Deterministic**: Same input always produces same output
- **Fast**: Typical run completes in seconds
- **No network required**: All checks run locally (except for tool installation)
- **Fail-safe**: Clear exit codes for CI integration
- **Artifact generation**: JSON and Markdown reports for downstream processing

## Prerequisites

### Required

- Python 3.8 or higher
- `repo-policy` package installed
- `repo-policy.yml` configuration file in repository

### Optional (for full policy enforcement)

- `repo-analyzer`: For repository metadata analysis
- `license-header`: For license header checking

If optional tools are not installed, related rules will be skipped with warnings.

## GitHub Actions

### Basic Workflow

Create `.github/workflows/policy-check.yml`:

```yaml
name: Repository Policy Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git-based checks
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install repo-policy
        run: |
          pip install repo-policy
      
      - name: Run policy check
        run: |
          repo-policy check --keep-artifacts
      
      - name: Upload policy reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: policy-reports
          path: .repo-policy-output/
          retention-days: 30
```

### With External Tools

Install optional tools for full enforcement:

```yaml
name: Repository Policy Check (Full)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install repo-policy
          pip install "git+https://github.com/AgentFoundryExamples/repo-summarizer-v1.git@main"
          pip install "git+https://github.com/AgentFoundryExamples/license-header.git@main"
      
      - name: Run policy check
        run: |
          repo-policy check --clean --keep-artifacts
      
      - name: Upload policy reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: policy-reports-${{ github.sha }}
          path: .repo-policy-output/
          retention-days: 90
```

### With PR Comments

Post the Markdown report as a PR comment:

```yaml
name: Repository Policy Check with PR Comment

on:
  pull_request:
    branches: [main]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install repo-policy
        run: |
          pip install repo-policy
      
      - name: Run policy check
        id: policy
        continue-on-error: true
        run: |
          repo-policy check --keep-artifacts
          echo "exit_code=$?" >> $GITHUB_OUTPUT
      
      - name: Comment PR with report
        uses: actions/github-script@v7
        if: always()
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.repo-policy-output/policy_report.md', 'utf8');
            
            // Find existing comment
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            
            const botComment = comments.find(comment => 
              comment.user.type === 'Bot' && 
              comment.body.includes('# Policy Check Report')
            );
            
            const commentBody = `${report}\n\n---\n*Updated at ${new Date().toISOString()}*`;
            
            if (botComment) {
              // Update existing comment
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: botComment.id,
                body: commentBody,
              });
            } else {
              // Create new comment
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: commentBody,
              });
            }
      
      - name: Fail if policy check failed
        if: steps.policy.outputs.exit_code != '0'
        run: |
          echo "Policy check failed with exit code ${{ steps.policy.outputs.exit_code }}"
          exit 1
```

### Matrix Strategy for Monorepos

Check multiple services in parallel:

```yaml
name: Monorepo Policy Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api, web, worker, common]
      fail-fast: false
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install repo-policy
        run: |
          pip install repo-policy
      
      - name: Run policy check for ${{ matrix.service }}
        run: |
          repo-policy --path ./services/${{ matrix.service }} \
                      --outdir ./.repo-policy-output/${{ matrix.service }} \
                      check --clean --keep-artifacts
      
      - name: Upload reports for ${{ matrix.service }}
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: policy-reports-${{ matrix.service }}
          path: .repo-policy-output/${{ matrix.service }}/
```

### Scheduled Compliance Checks

Run periodic checks for ongoing compliance:

```yaml
name: Scheduled Policy Audit

on:
  schedule:
    # Run every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch:  # Allow manual trigger

jobs:
  policy-audit:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install repo-policy
        run: |
          pip install repo-policy
      
      - name: Run policy check
        run: |
          repo-policy check --clean --keep-artifacts
      
      - name: Upload audit reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: policy-audit-${{ github.run_number }}
          path: .repo-policy-output/
          retention-days: 365
      
      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Policy audit failed - ${new Date().toISOString().split('T')[0]}`,
              body: `Scheduled policy audit failed. Check the [workflow run](${context.payload.repository.html_url}/actions/runs/${context.runId}) for details.`,
              labels: ['compliance', 'policy-failure'],
            });
```

## Pre-Commit Hooks

Pre-commit hooks enable local policy enforcement before pushing changes.

### Using pre-commit Framework

#### 1. Install pre-commit

```bash
pip install pre-commit
```

#### 2. Create `.pre-commit-config.yaml`

```yaml
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

#### 3. Install the hook

```bash
pre-commit install
```

#### 4. Test the hook

```bash
# Test on all files
pre-commit run --all-files

# Test on staged files only (normal commit flow)
git add .
git commit -m "test commit"
```

### Advanced Pre-Commit Configuration

Customize the pre-commit behavior:

```yaml
repos:
  - repo: local
    hooks:
      - id: repo-policy-fast
        name: Repository Policy Check (Fast)
        entry: repo-policy
        args: [check, --clean]
        language: system
        pass_filenames: false
        always_run: true
        verbose: true
        
      - id: repo-policy-full
        name: Repository Policy Check (Full)
        entry: bash -c 'repo-policy check --keep-artifacts || (cat .repo-policy-output/policy_report.md && exit 1)'
        language: system
        pass_filenames: false
        stages: [manual]
```

### Manual Git Hook

If not using pre-commit framework, create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Pre-commit hook for repo-policy

echo "Running repository policy check..."

# Run policy check
if ! repo-policy check --clean; then
    echo ""
    echo "❌ Policy check failed!"
    echo "Review the report at: .repo-policy-output/policy_report.md"
    echo ""
    echo "To bypass this check (not recommended):"
    echo "  git commit --no-verify"
    exit 1
fi

echo "✅ Policy check passed!"
exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Selective Pre-Commit Checks

Run lightweight checks locally, comprehensive checks in CI:

**Local (pre-commit):**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: repo-policy-local
        name: Repository Policy Check (Local)
        entry: repo-policy
        args: [--config, repo-policy.local.yml, check]
        language: system
        pass_filenames: false
```

**Local config (repo-policy.local.yml):**
```yaml
# Faster, warning-only checks for local dev
rules:
  severity_overrides:
    license-header-required: warning
    tests-required-with-sources: warning
  
integration:
  enable_repo_analyzer: false  # Skip slow checks locally
```

**CI config (repo-policy.yml):**
```yaml
# Full enforcement in CI
preset: strict
```

## Generic CI Integration

For CI platforms without specific examples:

### Basic Integration Pattern

```bash
#!/bin/bash
# Generic CI script

# Install repo-policy
pip install repo-policy

# Install optional tools (if needed)
pip install "git+https://github.com/AgentFoundryExamples/repo-summarizer-v1.git@main"
pip install "git+https://github.com/AgentFoundryExamples/license-header.git@main"

# Run policy check
repo-policy check --clean --keep-artifacts

# Capture exit code
EXIT_CODE=$?

# Archive artifacts (platform-specific)
# - Upload .repo-policy-output/ directory
# - Retain for audit purposes

# Exit with policy check status
exit $EXIT_CODE
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
policy-check:
  stage: test
  image: python:3.11
  
  before_script:
    - pip install repo-policy
  
  script:
    - repo-policy check --clean --keep-artifacts
  
  artifacts:
    when: always
    paths:
      - .repo-policy-output/
    expire_in: 30 days
  
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

### CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  policy-check:
    docker:
      - image: python:3.11
    
    steps:
      - checkout
      
      - run:
          name: Install repo-policy
          command: pip install repo-policy
      
      - run:
          name: Run policy check
          command: repo-policy check --clean --keep-artifacts
      
      - store_artifacts:
          path: .repo-policy-output/
          destination: policy-reports

workflows:
  version: 2
  build:
    jobs:
      - policy-check
```

### Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install repo-policy'
            }
        }
        
        stage('Policy Check') {
            steps {
                sh 'repo-policy check --clean --keep-artifacts'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '.repo-policy-output/**/*', allowEmptyArchive: false
        }
    }
}
```

### Azure Pipelines

Create `azure-pipelines.yml`:

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Use Python 3.11'
  
  - script: |
      pip install repo-policy
    displayName: 'Install repo-policy'
  
  - script: |
      repo-policy check --clean --keep-artifacts
    displayName: 'Run policy check'
  
  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      PathtoPublish: '.repo-policy-output'
      ArtifactName: 'policy-reports'
```

## Exit Code Behavior

Understanding exit codes is critical for CI integration.

### Exit Codes

| Code | Status | Meaning | CI Behavior |
|------|--------|---------|-------------|
| `0` | Success | No error-level failures | ✅ Build passes |
| `1` | Failure | Error-level policy violations | ❌ Build fails |
| `130` | Interrupted | User interrupted (Ctrl+C) | ⚠️ Build aborted |

### Severity vs Exit Code

**Important**: Only `error` severity failures cause non-zero exit codes.

```yaml
# Warnings don't fail the build
rules:
  severity_overrides:
    readme-required: warning  # Exit code 0 even if fails
    ci-required: error        # Exit code 1 if fails
```

### Example: Warnings in CI

```bash
repo-policy check
# Exits with code 0 even if warnings are present

# Parse report to detect warnings
WARNINGS=$(jq '.summary.warning_count' .repo-policy-output/policy_report.json)
if [ "$WARNINGS" -gt 0 ]; then
    echo "⚠️ Found $WARNINGS warning(s)"
    # Optionally post to PR, send notification, etc.
fi
```

### Handling Failures Gracefully

```yaml
# GitHub Actions: Continue on failure
- name: Run policy check
  id: policy
  continue-on-error: true
  run: repo-policy check

- name: Upload reports even on failure
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: policy-reports
    path: .repo-policy-output/

- name: Fail the build if policy failed
  if: steps.policy.outcome == 'failure'
  run: exit 1
```

## Artifact Management

### Artifact Types

repo-policy generates the following artifacts:

```
.repo-policy-output/
├── policy_report.json       # Required: Machine-readable report
├── policy_report.md         # Required: Human-readable report
├── analyzer/                # Optional: Repo analyzer outputs
│   ├── tree.json
│   ├── dependencies.json
│   └── metadata.json
└── license-headers/         # Optional: License header reports
    ├── license-header-check-report.json
    └── license-header-check-report.md
```

### Recommended CI Flags

```bash
# Clean before run + keep artifacts for upload
repo-policy check --clean --keep-artifacts
```

- `--clean`: Removes previous artifacts (ensures fresh run)
- `--keep-artifacts`: Retains integration tool outputs (for debugging)

### Artifact Retention

Recommended retention periods:

- **PR checks**: 30 days (for review and debugging)
- **Main branch**: 90 days (for audit trail)
- **Compliance audits**: 365+ days (for regulatory requirements)

### Parsing Reports in CI

#### Extract Summary Statistics

```bash
# Using jq to parse JSON report
TOTAL=$(jq '.summary.total_rules' .repo-policy-output/policy_report.json)
PASSED=$(jq '.summary.passed_rules' .repo-policy-output/policy_report.json)
FAILED=$(jq '.summary.failed_rules' .repo-policy-output/policy_report.json)
ERRORS=$(jq '.summary.error_count' .repo-policy-output/policy_report.json)
WARNINGS=$(jq '.summary.warning_count' .repo-policy-output/policy_report.json)

echo "Policy Check Summary:"
echo "  Total Rules: $TOTAL"
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
```

#### Post to Slack/Teams

```bash
# Example: Post summary to Slack
STATUS=$(jq -r 'if .summary.error_count > 0 then "❌ FAILED" else "✅ PASSED" end' \
    .repo-policy-output/policy_report.json)
ERRORS=$(jq '.summary.error_count' .repo-policy-output/policy_report.json)
WARNINGS=$(jq '.summary.warning_count' .repo-policy-output/policy_report.json)

curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"Policy Check $STATUS\",
    \"attachments\": [{
      \"color\": \"$([ $ERRORS -gt 0 ] && echo 'danger' || echo 'good')\",
      \"fields\": [
        {\"title\": \"Errors\", \"value\": \"$ERRORS\", \"short\": true},
        {\"title\": \"Warnings\", \"value\": \"$WARNINGS\", \"short\": true}
      ]
    }]
  }"
```

## Best Practices

### 1. Clean Output Directory in CI

Always use `--clean` to ensure reproducibility:

```bash
repo-policy check --clean --keep-artifacts
```

### 2. Full Checkout for Git Checks

Use full git history for accurate git-based checks:

```yaml
# GitHub Actions
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history
```

### 3. Cache Dependencies

Speed up CI by caching Python packages:

```yaml
# GitHub Actions
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

### 4. Upload Artifacts Always

Upload artifacts even on failure for debugging:

```yaml
- name: Upload reports
  if: always()  # Run even if policy check fails
  uses: actions/upload-artifact@v4
```

### 5. Separate Warnings from Errors

Allow warnings without failing builds:

```yaml
rules:
  severity_overrides:
    # Warnings for aspirational rules
    ci-required: warning
    
    # Errors for mandatory rules
    license-file-required: error
    readme-required: error
```

### 6. Test Configuration Changes

When modifying `repo-policy.yml`, test locally first:

```bash
# Test locally
repo-policy check --verbose

# Review changes
git diff repo-policy.yml

# Push to PR for CI validation
git add repo-policy.yml
git commit -m "Update policy configuration"
git push
```

### 7. Progressive Rollout

Introduce new rules gradually:

**Week 1**: Add as warnings
```yaml
rules:
  severity_overrides:
    new-rule: warning
```

**Week 2-3**: Fix violations, monitor

**Week 4**: Upgrade to error
```yaml
rules:
  severity_overrides:
    new-rule: error
```

### 8. Document Exceptions

If excluding rules, document why:

```yaml
rules:
  exclude:
    - license-header-required  # Temporary: migrating to new license
  
  severity_overrides:
    tests-required-with-sources: warning  # In progress: adding tests
```

## Troubleshooting

### Policy Check Fails in CI but Passes Locally

**Cause**: Different environments or stale artifacts

**Solution**:
```bash
# Clean local artifacts
repo-policy check --clean

# Use same Python version as CI
python --version

# Check configuration
repo-policy --verbose check
```

### External Tools Not Found in CI

**Cause**: Optional tools not installed

**Solution**: Add installation steps
```yaml
- name: Install external tools
  run: |
    pip install "git+https://github.com/AgentFoundryExamples/repo-summarizer-v1.git@main"
    pip install "git+https://github.com/AgentFoundryExamples/license-header.git@main"
```

### Artifacts Not Uploaded

**Cause**: Artifact path doesn't exist or permission issues

**Solution**:
```yaml
- name: Verify artifacts exist
  if: always()
  run: ls -la .repo-policy-output/

- name: Upload artifacts
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: policy-reports
    path: .repo-policy-output/
    if-no-files-found: warn  # Don't fail if missing
```

### Inconsistent Results Across Runs

**Cause**: Non-deterministic inputs (timestamps, git state)

**Solution**: Use `--clean` and full git checkout
```bash
repo-policy check --clean --keep-artifacts
```

### Timeout in CI

**Cause**: Slow external tools or large repository

**Solution**: Adjust timeouts or disable slow checks
```yaml
integration:
  enable_repo_analyzer: false  # Skip if too slow
```

### False Positives

**Cause**: Rule not applicable to your repository

**Solution**: Override severity or exclude rule
```yaml
rules:
  severity_overrides:
    problematic-rule: warning
  # or
  exclude:
    - problematic-rule
```

## See Also

- [Usage Guide](usage.md) - CLI commands and options
- [Configuration Guide](config.md) - Configuration schema and rules
- [Repository Analysis Integration](REPO_ANALYSIS.md) - Repo analyzer details
- [License Header Integration](LICENSE_HEADER.md) - License header checking
- [Report Format](report-format.md) - Report structure and parsing
