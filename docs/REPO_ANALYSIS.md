# Repository Analysis Integration

This document describes the integration between repo-policy and the repo analyzer tool.

## Overview

The repo analyzer integration provides metadata about the repository structure, including:
- File tree information
- Dependency analysis
- Repository statistics
- Language detection

This metadata is used by policy rules to make informed decisions about repository compliance.

## Configuration

Configure the analyzer integration in your `repo-policy.yml`:

```yaml
integration:
  # Enable/disable repo analyzer integration
  enable_repo_analyzer: true
  
  # Path to repo-analyzer binary (auto-detect if not specified)
  repo_analyzer_binary: null
  
  # Workspace mode: 'temp_workspace' or 'direct_output'
  repo_analyzer_workspace_mode: direct_output
```

### Workspace Modes

#### Direct Output Mode (default)

In direct output mode, the analyzer writes outputs directly to a subdirectory within the configured `outdir`:

```
.repo-policy-output/
  analyzer/
    tree.json
    dependencies.json
    metadata.json
```

**Advantages:**
- Faster (no cloning required)
- Lower disk usage
- Simpler execution path

**Use when:**
- You trust the analyzer not to modify the working tree
- You want to inspect outputs easily
- Performance is important

#### Temp Workspace Mode

In temp workspace mode, the repository is cloned to a temporary directory, analyzed there, and outputs are optionally copied back:

```
/tmp/repo-policy-analyzer-XXXXX/
  repo/          # Cloned repository
  output/        # Analyzer outputs
```

**Advantages:**
- Complete isolation from working tree
- Guaranteed not to dirty the repository
- Safe for untrusted analyzers

**Use when:**
- Maximum safety is required
- You're unsure if the analyzer modifies files
- Running in CI where working tree must stay clean

**Note:** Temp directories are always cleaned up, even on failure.

## Artifact Management

### Keep Artifacts

Use `--keep-artifacts` to retain analyzer outputs after the policy check:

```bash
repo-policy --keep-artifacts check
```

This preserves the analyzer outputs in `.repo-policy-output/analyzer/` for inspection and troubleshooting.

### Clean Artifacts

Use `--clean` to remove previous artifacts before running:

```bash
repo-policy --clean check
```

This ensures a fresh analysis by removing all previous outputs from `outdir`.

**Important:** Clean only affects files within the configured `outdir` and will never delete user files outside that directory.

## Output Files

The analyzer may produce the following output files (depending on the analyzer version):

| File | Description |
|------|-------------|
| `tree.json` | Repository file tree structure |
| `dependencies.json` | Dependency graph and metadata |
| `metadata.json` | Repository metadata and statistics |
| `summary.json` | Summary of analysis results |

## Metadata Captured

The integration captures the following metadata for each analyzer run:

- **Version**: Analyzer tool version
- **Command**: Full command line executed
- **Exit Status**: Process exit code
- **Stdout/Stderr**: Captured output for troubleshooting
- **Output Files**: Paths to generated output files
- **Error Messages**: Actionable error messages on failure

This metadata is available to policy rules and included in reports.

## Error Handling

### Analyzer Not Found

If the repo-analyzer binary is not found in PATH:

```
repo-analyzer tool not found. Please install it or provide the binary path in configuration.
```

**Resolution:**
1. Install repo-analyzer in your PATH
2. Or specify the binary path in configuration:
   ```yaml
   integration:
     repo_analyzer_binary: /path/to/repo-analyzer
   ```

### Analyzer Crashes

If the analyzer crashes or fails:

```
Repo analyzer failed: <error message>
```

**Resolution:**
1. Check analyzer logs in stderr output
2. Run with `--keep-artifacts` to inspect outputs
3. Try temp workspace mode for isolation
4. Check analyzer documentation for error details

**Note:** Failures are logged but do not abort the entire policy check. Other rules continue to execute.

### Timeout

The analyzer has a 5-minute timeout. If it exceeds this:

```
repo-analyzer timed out after 5 minutes
```

**Resolution:**
1. Ensure your repository is not too large
2. Check for performance issues in the analyzer
3. Consider excluding large directories

## Cleanup Guarantees

The integration guarantees:

1. **Temp directories are always cleaned up**, even on failure
2. **Working tree is never modified** by the analyzer
3. **Artifacts respect `--keep-artifacts` flag**
4. **`--clean` only affects configured `outdir`**
5. **No leftover files** outside the specified output directory

## Example Usage

### Basic Usage (Direct Output)

```bash
repo-policy check
```

### With Artifact Retention

```bash
repo-policy --keep-artifacts check
```

### With Temp Workspace (Maximum Isolation)

```yaml
# In repo-policy.yml
integration:
  repo_analyzer_workspace_mode: temp_workspace
```

```bash
repo-policy --keep-artifacts check
```

### Concurrent Runs

Run multiple checks concurrently with distinct output directories:

```bash
# Terminal 1
repo-policy --outdir /tmp/run1

# Terminal 2
repo-policy --outdir /tmp/run2
```

Each run uses its own isolated output directory, preventing artifact collisions.

## Integration with Rules

Policy rules can access analyzer data through the policy context:

```python
from integration.context import PolicyContext

def evaluate_rule(context: PolicyContext):
    if context.has_analyzer_data():
        # Access analyzer results
        result = context.analyzer_result
        
        # Check output files
        if "dependencies" in result.output_files:
            deps_file = result.output_files["dependencies"]
            # Process dependency data
    else:
        # Analyzer data not available
        return {"status": "skipped", "reason": "No analyzer data"}
```

## Troubleshooting

### Debug Logging

Enable verbose output for detailed analyzer logs:

```bash
repo-policy -v check
```

### Inspect Outputs

Keep artifacts to inspect analyzer outputs:

```bash
repo-policy --keep-artifacts check
ls -la .repo-policy-output/analyzer/
```

### Test Analyzer Directly

Test the analyzer outside of repo-policy:

```bash
repo-analyzer --path . --output /tmp/test-output
```

## See Also

- [Usage Guide](usage.md) - CLI commands and options
- [Configuration Guide](config.md) - Configuration schema and settings
- [CI Integration Guide](ci.md) - Using repo-policy in CI/CD pipelines
- [License Header Integration](LICENSE_HEADER.md) - License header checking integration
- [Report Format](report-format.md) - Report structure and parsing
- Main repo-policy documentation in [README.md](../README.md)
