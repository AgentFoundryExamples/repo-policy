# License Header Integration

This document describes the integration between repo-policy and the license-header tool.

## Overview

The license header integration checks whether source files have the required license headers, providing deterministic compliance data for policy evaluation. The tool is always run in **dry-run/check mode** to ensure files are never modified.

## Configuration

Configure the license header integration in your `repo-policy.yml`:

```yaml
# License configuration
license:
  # SPDX license identifier
  spdx_id: Apache-2.0
  
  # Path to header template file (relative to repository root)
  header_template_path: LICENSE_HEADER.md
  
  # Enable header enforcement
  require_header: true
  
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

# Integration settings
integration:
  # Enable/disable license header checking
  enable_license_headers: true
  
  # Path to license-header binary (auto-detect if not specified)
  license_header_binary: null
```

## Header Template

The header template file should contain the raw license text without comment markers. The license-header tool automatically wraps it with appropriate comment syntax for each file type.

Example `LICENSE_HEADER.md`:

```
Copyright 2025 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

The tool will automatically format this for each file type:
- Python files: `# Copyright 2025...`
- JavaScript/TypeScript: `// Copyright 2025...`
- Java files: `// Copyright 2025...`
- Etc.

## Dry-Run Mode

**Important:** The license-header tool is always invoked in **check mode** (dry-run) by repo-policy. This means:

✅ Files are **never modified**
✅ Headers are **only checked**, not applied
✅ Results are **deterministic** and reproducible
✅ Safe to run in any environment (CI, dev, production)

To apply headers (if needed), use the license-header tool directly:

```bash
license-header apply
```

## Artifact Management

### Keep Artifacts

Use `--keep-artifacts` to retain license header check reports:

```bash
repo-policy check --keep-artifacts
```

This preserves the reports in `.repo-policy-output/license-headers/`:

```
.repo-policy-output/
  license-headers/
    license-header-check-report.json
    license-header-check-report.md
```

### Clean Artifacts

Use `--clean` to remove previous reports before running:

```bash
repo-policy check --clean
```

## Check Results

The integration captures comprehensive compliance data:

### Compliant Files
Files that have the correct license header

### Non-Compliant Files
Files missing the required license header

### Skipped Files
Files excluded by patterns or detected as binary

### Failed Files
Files that could not be read or processed

### Summary Statistics

```json
{
  "scanned": 150,
  "eligible": 100,
  "compliant": 95,
  "non_compliant": 5,
  "skipped": 50,
  "failed": 0
}
```

## Metadata Captured

The integration captures the following metadata:

- **Version**: License-header tool version
- **Command**: Full command line executed
- **Exit Status**: Process exit code (0 = all compliant, 1 = some non-compliant)
- **Stdout/Stderr**: Captured output
- **File Lists**: Compliant, non-compliant, skipped, failed files
- **Summary Stats**: Counts for each category
- **Error Messages**: Actionable error messages on failure

## Disabling Header Checks

To disable license header checking entirely:

```yaml
license:
  require_header: false
```

Or disable the integration:

```yaml
integration:
  enable_license_headers: false
```

When disabled, the tool is not invoked and the check is marked as **skipped** in the context.

## Error Handling

### Tool Not Found

If the license-header binary is not found:

```
license-header tool not found. Please install it or provide the binary path in configuration.
```

**Resolution:**
1. Install license-header in your PATH
2. Or specify the binary path:
   ```yaml
   integration:
     license_header_binary: /path/to/license-header
   ```

### Header Template Not Found

If the header template file is missing:

```
No header template file found. Expected LICENSE_HEADER or LICENSE_HEADER.md 
in repository root, or specify header_template_path in configuration.
```

**Resolution:**
1. Create `LICENSE_HEADER` or `LICENSE_HEADER.md` in repository root
2. Or specify custom path:
   ```yaml
   license:
     header_template_path: path/to/custom-header.txt
   ```

### Non-Compliant Files Found

If files are missing headers:

```
License header check found 5 non-compliant files
```

This is **not an error** from the tool itself, but indicates policy violations. The integration will mark this as a failure, causing the overall policy check to fail with exit code 1.

**Resolution:**
1. Review the list of non-compliant files
2. Use `license-header apply` to add headers
3. Or update `exclude_globs` to skip those files
4. Or set `require_header: false` if headers are optional

### Timeout

The checker has a 5-minute timeout:

```
license-header check timed out after 5 minutes
```

**Resolution:**
1. Ensure repository is not too large
2. Adjust include/exclude patterns to reduce scope
3. Check for performance issues in the tool

## File Pattern Configuration

### Include Globs

Specify which files to check:

```yaml
license:
  include_globs:
    - "**/*.py"     # All Python files
    - "**/*.js"     # All JavaScript files
    - "**/*.ts"     # All TypeScript files
    - "src/**/*.go" # Go files in src/
```

Patterns are converted to file extensions for the license-header tool.

### Exclude Globs

Specify which files to skip:

```yaml
license:
  exclude_globs:
    - "**/test_*.py"       # Test files
    - "**/*_test.py"       # More test files
    - "**/vendor/**"       # Vendor directory
    - "**/__pycache__/**"  # Cache directories
    - "dist/**"            # Build output
```

These patterns are passed directly to the license-header tool's exclude logic.

## Integration with Policy Rules

Policy rules can access license header data through the policy context:

```python
from integration.context import PolicyContext

def evaluate_license_header_rule(context: PolicyContext):
    if not context.has_license_header_data():
        return {"status": "skipped", "reason": "Header check disabled"}
    
    result = context.license_header_result
    
    if not result.success:
        return {
            "status": "failed",
            "reason": f"Found {len(result.non_compliant_files)} files without headers",
            "files": result.non_compliant_files,
        }
    
    return {
        "status": "passed",
        "reason": f"All {len(result.compliant_files)} files have correct headers",
    }
```

## Example Usage

### Basic Check

```bash
repo-policy check
```

Output:
```
Running license header check...
License header check passed
Summary: {'scanned': 100, 'compliant': 95, 'non_compliant': 5}
```

### With Report Artifacts

```bash
repo-policy check --keep-artifacts
```

Generates:
- `.repo-policy-output/license-headers/license-header-check-report.json`
- `.repo-policy-output/license-headers/license-header-check-report.md`

### Disable Header Enforcement

```yaml
# repo-policy.yml
license:
  require_header: false
```

```bash
repo-policy check
```

Output:
```
License header enforcement disabled (require_header: false)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Policy Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install tools
        run: |
          pip install license-header
          pip install repo-policy
      
      - name: Run policy check
        run: repo-policy check --keep-artifacts
      
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: policy-reports
          path: .repo-policy-output/
```

### Expected Behavior in CI

- **Exit Code 0**: All checks passed
- **Exit Code 1**: Policy violations (including missing headers)
- **Exit Code 130**: Interrupted by user

CI builds should fail on exit code 1, preventing merges with policy violations.

## Troubleshooting

### Enable Debug Logging

```bash
repo-policy check --verbose
```

### Inspect Reports

```bash
repo-policy check --keep-artifacts
cat .repo-policy-output/license-headers/license-header-check-report.json
```

### Test Tool Directly

```bash
license-header check --path . --header LICENSE_HEADER
```

### Common Issues

**Issue**: Tool not found
- **Solution**: Install via `pip install license-header`

**Issue**: Template not found
- **Solution**: Create `LICENSE_HEADER` in repository root

**Issue**: Too many non-compliant files
- **Solution**: Use `license-header apply` to add headers in bulk

**Issue**: Don't want to enforce headers on all files
- **Solution**: Adjust `exclude_globs` or set `require_header: false`

## See Also

- [Repository Analysis Integration](REPO_ANALYSIS.md)
- [Configuration Schema](../README.md#configuration)
- [License-header tool documentation](../LICENSE_HEADER.md)
- Main repo-policy documentation in README.md
