# License Header CLI

A deterministic license header enforcement tool for source files. This CLI tool helps maintain consistent license headers across your codebase by applying and validating headers in source files.

## ⚠️ Version 1.0.0 Release Notes

### V1 Header Format End-of-Life

**Important:** V1 headers (with embedded comment markers) are **no longer supported** for regular operations as of version 1.0.0. All users must migrate to V2 format before using new features.

#### What You Need to Know

- **V1 headers are deprecated**: The `header_version: "v1"` configuration is only allowed in `upgrade` mode
- **V2 is required**: All `apply` and `check` operations require V2 headers (raw license text without comment markers)
- **No retroactive V1 support**: Files with V1 headers will not be automatically detected or updated without using the upgrade command

#### Before Using V2 Features

**You must run the upgrade command to migrate existing V1 headers:**

```bash
# 1. Preview the upgrade (ALWAYS run this first)
license-header upgrade --from-header OLD_HEADER.txt --to-header LICENSE_HEADER --dry-run

# 2. Perform the upgrade
license-header upgrade --from-header OLD_HEADER.txt --to-header LICENSE_HEADER

# 3. Verify results
license-header check
```

See the [Upgrade License Headers](#upgrade-license-headers) section for detailed migration instructions.

## Features

- **Apply Mode**: Automatically add or update license headers in source files
- **Check Mode**: Verify that all source files have correct license headers
- **Upgrade Mode**: Migrate from V1 headers (with comment markers) to V2 format
- **Multi-Language Support**: Automatically wraps headers with appropriate comment syntax for Python, C, C++, C#, TypeScript, JavaScript, Java, and Rust
- **Comment-Agnostic Headers**: Store raw license text in header files; comment wrapping is handled automatically
- **Deterministic**: Consistent, reproducible results across different environments
- **GitHub Actions Ready**: Designed for easy integration into CI/CD pipelines

## Requirements

- Python 3.11 or higher

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/AgentFoundryTest/license-header.git
cd license-header

# Install the package
pip install -e .
```

### For Development

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Usage

The CLI provides three main commands: `apply`, `check`, and `upgrade`.

### Quick Start

1. Create a `LICENSE_HEADER` file in your repository root with your **raw license text** (no comment markers):

```
Copyright (c) 2025 Your Organization
Licensed under the MIT License
```

The tool will automatically wrap this with appropriate comment syntax for each file type:
- Python (`.py`): `# Copyright (c) 2025 Your Organization`
- JavaScript/TypeScript (`.js`, `.ts`): `// Copyright (c) 2025 Your Organization`
- C/C++ (`.c`, `.cpp`, `.h`): `// Copyright (c) 2025 Your Organization`
- Java (`.java`): `// Copyright (c) 2025 Your Organization`
- Rust (`.rs`): `// Copyright (c) 2025 Your Organization`
- C# (`.cs`): `// Copyright (c) 2025 Your Organization`

2. Optionally, create a `license-header.config.json` configuration file:

```json
{
  "header_file": "LICENSE_HEADER",
  "include_extensions": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".rs"],
  "exclude_paths": ["node_modules", ".git", "venv"],
  "wrap_comments": true,
  "fallback_comment_style": "hash"
}
```

3. Run the tool:

```bash
# Check headers (read-only)
license-header check

# Apply headers with preview
license-header apply --dry-run

# Apply headers
license-header apply

# Upgrade from old header format to new (see Upgrade Command section)
license-header upgrade --from-header OLD_HEADER --to-header NEW_HEADER --dry-run
```

### Apply License Headers

Apply license headers to source files in your project:

```bash
# Apply headers to current directory
license-header apply

# Apply headers to specific path
license-header apply --path /path/to/project

# Preview changes without modifying files (recommended first)
license-header apply --dry-run

# Specify custom header file
license-header apply --header path/to/header.txt

# Include only specific file extensions
license-header apply --include-extension .py --include-extension .js

# Exclude specific paths
license-header apply --exclude-path dist --exclude-path build

# Generate JSON and Markdown reports (files modified in-place)
license-header apply --output reports/
```

**Dry Run Mode:**

The `--dry-run` flag shows exactly which files would be modified without touching the filesystem:

```bash
$ license-header apply --dry-run

Summary:
  Scanned: 150
  Eligible: 100
  Added: 5              # Files that would get headers
  Compliant: 95         # Files already compliant
  Skipped: 50
  Failed: 0

[DRY RUN] Files that would be modified:
  - src/main.py
  - src/utils.py
  - tests/test_app.py
  ... and 2 more

[DRY RUN] No files were actually modified.
```

**Summary Counters:**

The apply command prints deterministic summary counters to the console:

```
Summary:
  Scanned: 150          # Total files scanned (eligible + skipped)
  Eligible: 100         # Files that match extensions and aren't excluded
  Added: 5              # Files that had headers added
  Compliant: 95         # Files that already had correct headers
  Skipped: 50           # Binary, excluded, symlink, and other skipped files
  Failed: 0             # Files that couldn't be processed
```

### Check License Headers

Verify that source files have correct license headers without modifying any files:

```bash
# Check current directory
license-header check

# Check specific path
license-header check --path /path/to/project

# Generate JSON and Markdown reports
license-header check --output reports/

# Preview check without generating reports
license-header check --dry-run --output reports/

# Use custom configuration
license-header check --config my-config.json
```

**Check Mode Behavior:**

- **Exit Codes**: Exits with code 1 (failure) if any files are missing headers or fail to be checked. Exits with code 0 (success) only when all eligible files have correct headers.
- **Non-Compliant Files**: Lists all files that are missing the required license header.
- **Reports**: When `--output` is specified, generates both JSON and Markdown reports with detailed results.
- **Dry Run**: With `--dry-run`, performs the check but skips report generation (useful for preview).

**Summary Counters:**

The check command prints deterministic summary counters to the console:

```
Summary:
  Scanned: 150          # Total files scanned (eligible + skipped)
  Eligible: 100         # Files that match extensions and aren't excluded
  Compliant: 95         # Files with correct headers
  Non-compliant: 5      # Files missing headers
  Skipped: 50           # Binary, excluded, symlink, and other skipped files
  Failed: 0             # Files that couldn't be read
```

### Upgrade License Headers

The `upgrade` command provides a safe, deterministic workflow for transitioning repositories from legacy V1 headers (with embedded comment markers) or older V2 headers to the new V2 format.

#### Why Upgrade?

V1 headers contain embedded comment markers in the header file itself (e.g., `# Copyright...`), which causes issues with multi-language repositories. The V2 format stores raw license text without comment markers, allowing the tool to automatically wrap headers with the appropriate comment syntax for each file type.

#### Basic Usage

```bash
# Preview what would be upgraded (ALWAYS run this first)
license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt --dry-run

# Perform the actual upgrade
license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt

# Upgrade with reports
license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt --output reports/
```

#### Required Arguments

| Argument | Description |
|----------|-------------|
| `--from-header` | **Required.** Path to the source header file to replace. Can be a V1 header (with comment markers) or an older V2 raw header. |
| `--to-header` | **Required.** Path to the target V2 header file (raw license text without comment markers). |

#### Optional Arguments

| Argument | Description |
|----------|-------------|
| `--path` | Path to scan for files (default: current directory) |
| `--output` | Directory to save JSON and Markdown reports |
| `--include-extension` | File extensions to include (can be specified multiple times) |
| `--exclude-path` | Paths/patterns to exclude (can be specified multiple times) |
| `--dry-run` | Preview changes without modifying files |
| `--fallback-comment-style` | Comment style for unknown file types (`hash`, `slash`, `none`) |
| `--use-block-comments` | Use block comments (`/* */`) instead of line comments |

#### Upgrade Behavior

1. **Files with source header**: The old header is removed and replaced with the new header, wrapped in appropriate comment syntax.
2. **Files already with target header**: Skipped with a clear message.
3. **Files without source header**: Reported but not modified.
4. **Partial/corrupted headers**: Raise actionable errors rather than silently mutating files.

#### Safety Considerations

⚠️ **IMPORTANT**: Always run with `--dry-run` first to preview changes.

- The upgrade command requires explicit `--from-header` and `--to-header` arguments to prevent accidental modifications.
- Files are modified atomically to prevent partial writes.
- Original file permissions are preserved.
- Detailed reports (JSON and Markdown) can be generated for audit purposes.

#### Summary Counters

The upgrade command prints deterministic summary counters to the console:

```
Summary:
  Scanned: 150          # Total files scanned (eligible + skipped)
  Upgraded: 10          # Files that were upgraded
  Already target: 50    # Files already with target header (skipped)
  No source header: 40  # Files without source header (not modified)
  Skipped: 50           # Binary, excluded, symlink, and other skipped files
  Failed: 0             # Files that couldn't be processed
```

#### Example: Migrating from V1 to V2

**Step 1**: Create your old V1 header file (copy your existing header):

```
# OLD_HEADER.txt (V1 format with comment markers)
# Copyright 2024 My Company
# Licensed under MIT
```

**Step 2**: Create your new V2 header file (raw text without comment markers):

```
# NEW_HEADER.txt (V2 format without comment markers)
Copyright 2025 My Company
Licensed under Apache 2.0
```

**Step 3**: Preview the upgrade:

```bash
license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt --dry-run
```

**Step 4**: Perform the upgrade:

```bash
license-header upgrade --from-header OLD_HEADER.txt --to-header NEW_HEADER.txt --output reports/
```

**Step 5**: Verify the results in the generated reports or by running `license-header check`.

## Multi-Language Comment Wrapping

The tool automatically wraps raw license header text with appropriate comment syntax for each supported file type. This enables using a single, comment-agnostic header file across multi-language repositories.

### Supported Languages

| Language | Extensions | Comment Style |
|----------|------------|---------------|
| Python | `.py`, `.pyi`, `.pyw` | `# comment` |
| C | `.c`, `.h` | `// comment` or `/* block */` |
| C++ | `.cpp`, `.hpp`, `.cc`, `.hh`, `.cxx`, `.hxx` | `// comment` or `/* block */` |
| C# | `.cs` | `// comment` or `/* block */` |
| Java | `.java` | `// comment` or `/* block */` |
| JavaScript | `.js`, `.mjs`, `.cjs` | `// comment` or `/* block */` |
| TypeScript | `.ts`, `.mts`, `.cts`, `.tsx` | `// comment` or `/* block */` |
| Rust | `.rs` | `// comment` or `/* block */` |

### Header File Format

Your `LICENSE_HEADER` file should contain **raw license text without comment markers**:

```
Copyright (c) 2025 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
```

The tool will automatically wrap this with appropriate comments:

**For Python files (`.py`):**
```python
# Copyright (c) 2025 Your Organization
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# ...
```

**For JavaScript/TypeScript files (`.js`, `.ts`):**
```javascript
// Copyright (c) 2025 Your Organization
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// ...
```

### Block Comment Mode

Use `--use-block-comments` for C-style block comments:

```bash
license-header apply --use-block-comments
```

**Result for C/Java/JavaScript files:**
```c
/*
 * Copyright (c) 2025 Your Organization
 *
 * Licensed under the Apache License...
 */
```

### Fallback Comment Style

For unknown file extensions, use `--fallback-comment-style`:

```bash
# Use hash comments for unknown extensions (default)
license-header apply --fallback-comment-style hash

# Use slash comments for unknown extensions
license-header apply --fallback-comment-style slash

# Don't wrap unknown extensions (use raw header text)
license-header apply --fallback-comment-style none
```

### Disabling Comment Wrapping

To use headers as-is (legacy mode), use `--no-wrap-comments`:

```bash
license-header apply --no-wrap-comments
```

This is useful when your header file already contains comment markers.

### Configuration Options

| Option | CLI Flag | Config File Key | Default | Description |
|--------|----------|----------------|---------|-------------|
| **Wrap Comments** | `--no-wrap-comments` | `wrap_comments` | `true` | Enable/disable automatic comment wrapping |
| **Fallback Style** | `--fallback-comment-style` | `fallback_comment_style` | `hash` | Comment style for unknown extensions (`hash`, `slash`, `none`) |
| **Block Comments** | `--use-block-comments` | `use_block_comments` | `false` | Use block comments instead of line comments |

### Backward Compatibility

The tool automatically detects if a header file already contains comment markers and skips wrapping in that case. This ensures backward compatibility with existing header files that include language-specific comment syntax.

## Configuration

The tool supports configuration through both CLI options and a JSON configuration file. CLI options always take precedence over configuration file settings.

### Configuration File

Create a `license-header.config.json` file in your repository root:

```json
{
  "header_file": "LICENSE_HEADER",
  "header_version": "v2",
  "include_extensions": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".rs"],
  "exclude_paths": ["node_modules", ".git", "__pycache__", "venv", "env", ".venv", "dist", "build"],
  "output_dir": null,
  "wrap_comments": true,
  "fallback_comment_style": "hash",
  "use_block_comments": false,
  "language_comment_overrides": {},
  "upgrade_from_header": null,
  "upgrade_to_header": null
}
```

### Configuration Options

| Option | CLI Flag | Config File Key | Default | Description |
|--------|----------|----------------|---------|-------------|
| **Header File** | `--header` | `header_file` | `LICENSE_HEADER` if present, else required | Path to the license header file (relative to repo root or absolute) |
| **Header Version** | N/A | `header_version` | `v2` | Header format version (`v1` or `v2`). Only `v2` allowed for regular runs; `v1` requires upgrade mode. |
| **Include Extensions** | `--include-extension` | `include_extensions` | `[".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".cs", ".rs"]` | File extensions to process. CLI flag can be specified multiple times. |
| **Exclude Paths** | `--exclude-path` | `exclude_paths` | `["node_modules", ".git", "__pycache__", "venv", "env", ".venv", "dist", "build"]` | Paths/patterns to exclude from processing. CLI flag can be specified multiple times. |
| **Output Directory** | `--output` | `output_dir` | None (no reports) | Directory to save report files (JSON and Markdown) - files are always modified in-place |
| **Target Path** | `--path` | N/A | `.` (current directory) | Path to scan for source files |
| **Dry Run** | `--dry-run` | N/A | `false` | Preview results without modifying files (both apply and check modes) |
| **Config File** | `--config` | N/A | `license-header.config.json` if present | Path to custom configuration file |
| **Wrap Comments** | `--no-wrap-comments` | `wrap_comments` | `true` | Enable/disable automatic comment wrapping |
| **Fallback Style** | `--fallback-comment-style` | `fallback_comment_style` | `hash` | Comment style for unknown extensions (`hash`, `slash`, or `none`) |
| **Block Comments** | `--use-block-comments` | `use_block_comments` | `false` | Use block comments instead of line comments |
| **Language Overrides** | N/A | `language_comment_overrides` | `{}` | Per-language comment style overrides (see below) |
| **Upgrade From** | `--from-header` | `upgrade_from_header` | None | Source header path for upgrade mode |
| **Upgrade To** | `--to-header` | `upgrade_to_header` | None | Target header path for upgrade mode |

### V2 Header Version

The tool uses V2 headers by default. V2 headers store raw license text without comment markers, allowing the tool to automatically wrap headers with appropriate comment syntax for each file type.

**Key differences between V1 and V2:**

| Aspect | V1 Headers | V2 Headers |
|--------|------------|------------|
| Format | Embedded comment markers | Raw license text |
| Multi-language | Single comment style | Automatic per-language wrapping |
| Configuration | `header_version: "v1"` | `header_version: "v2"` (default) |
| Regular runs | Not allowed | Required |
| Upgrade mode | Source only | Target only |

**Validation Rules:**

- `header_version: "v1"` is **only allowed** in `upgrade` mode (for migrating old headers)
- `header_version: "v2"` is **required** for `apply` and `check` modes
- Unknown version strings (e.g., `"v3"`) fail validation with an actionable error

### Language Comment Overrides

The `language_comment_overrides` option allows you to customize comment styles for specific file extensions. This is useful when you want to override the built-in defaults for certain languages.

```json
{
  "language_comment_overrides": {
    ".py": "hash",
    ".js": "slash",
    ".c": "block",
    ".txt": "none"
  }
}
```

**Valid comment style values:**

| Style | Description | Example |
|-------|-------------|---------|
| `hash` | Hash-style line comments | `# comment` |
| `slash` | C-style line comments | `// comment` |
| `block` | C-style block comments | `/* comment */` |
| `none` | No comment wrapping | Raw text as-is |

**Validation Rules:**

- Extension keys must start with `.` (e.g., `.py`, not `py`)
- Style values must be one of: `hash`, `slash`, `block`, `none`
- Empty override maps (`{}`) are valid and fall back to built-in defaults

### Upgrade Configuration

When using the `upgrade` command, you can configure the source and target headers via the config file or CLI flags.

```json
{
  "header_file": "LICENSE_HEADER",
  "upgrade_from_header": "OLD_HEADER.txt",
  "upgrade_to_header": "NEW_HEADER.txt"
}
```

**Validation Rules:**

- In `upgrade` mode, both `upgrade_from_header` and `upgrade_to_header` are **required**
- Relative paths must be within the repository root (paths like `../outside.txt` are rejected)
- In `apply` or `check` mode, these fields are ignored with a warning

### Repository Traversal

The tool uses a deterministic repository scanner to identify eligible source files based on configured extensions and exclude patterns.

#### Traversal Behavior

- **Iterative scanning**: Uses non-recursive directory walking to handle deep directory trees without stack overflow
- **Deterministic ordering**: Results are consistently sorted for reproducible behavior across platforms
- **Default excludes**: Automatically skips common noise directories:
  - `.git` - Git repository metadata
  - `.venv`, `venv`, `env` - Python virtual environments
  - `node_modules` - Node.js dependencies
  - `__pycache__` - Python bytecode cache
  - `dist` - Distribution/build output
  - `build` - Build artifacts
- **Binary detection**: Automatically detects and skips binary files by checking for null bytes
- **Symlink handling**: Symbolic links are detected and skipped to avoid infinite loops and duplicate processing
- **Permission errors**: Files that cannot be read due to permission errors are logged and skipped without aborting the scan
- **Case-insensitive extensions**: File extensions are matched case-insensitively (e.g., `.py`, `.PY`, and `.Py` all match)

#### Customizing Exclusions

You can add custom exclude patterns to the default list:

```bash
# Exclude additional directories via CLI
license-header apply --exclude-path vendor --exclude-path generated

# Or via configuration file
{
  "exclude_paths": ["vendor", "generated", "third_party"]
}
```

**Note:** Custom exclude patterns are added to (not replacing) the default excludes.

#### Pattern Matching

Exclude patterns support both simple directory names and glob patterns:

**Simple directory names** (e.g., `node_modules`, `vendor`):
- Match if the directory appears anywhere in the file path
- Example: `vendor` matches `vendor/lib.py`, `src/vendor/pkg.js`, `deep/nested/vendor/file.c`

**Glob patterns** support standard wildcards:
- `*.pyc` - matches files with .pyc extension anywhere in the repository
- `generated/*.py` - matches .py files directly inside `generated` directory
- `**/vendor` - matches `vendor` directory at any level (including root)
- `src/*/temp` - matches `temp` directories inside any subdirectory of `src`
- `build/**/*.js` - matches all .js files anywhere under `build` directory

**Examples:**
```bash
# Exclude all .pyc files
license-header apply --exclude-path "*.pyc"

# Exclude generated Python files
license-header apply --exclude-path "generated/*.py"

# Exclude all vendor directories at any level
license-header apply --exclude-path "**/vendor"

# Exclude temp directories in specific locations
license-header apply --exclude-path "src/*/temp"
```

#### Edge Cases

The scanner handles several edge cases robustly:

- **Deep directory trees**: Can handle directories nested >1000 levels deep without recursion limits
- **Circular symlinks**: Detected and skipped without causing infinite loops or crashes
- **Read permission errors**: Logged as warnings but do not abort the scan
- **Case-insensitive filesystems**: Extensions are matched consistently regardless of case
- **Binary files with text extensions**: Files are checked for binary content even if they have text file extensions
- **Paths outside repository**: Files outside the repository root are automatically excluded

### Configuration Precedence

Configuration is loaded and merged in the following order (later sources override earlier ones):

1. **Default values** - Built-in defaults for extensions and exclude paths
2. **Configuration file** - Settings from `license-header.config.json` (or custom config file)
3. **CLI arguments** - Command-line flags (highest precedence)

### Examples

#### Using only CLI flags

```bash
license-header apply \
  --header LICENSE_HEADER \
  --include-extension .py \
  --include-extension .js \
  --exclude-path node_modules \
  --exclude-path dist \
  --dry-run
```

#### Using configuration file with CLI overrides

```bash
# Config file provides defaults, CLI overrides specific options
license-header apply --include-extension .py --dry-run
```

#### Using custom configuration file

```bash
license-header check --config configs/custom-config.json
```

### Path Validation

The tool enforces security restrictions on file paths:

- **Header file paths** must be within the repository root or absolute paths that don't traverse above the repo
- **Output directory paths** must be within the repository root
- Relative paths are resolved relative to the repository root (detected by finding `.git` directory)
- Paths that attempt to traverse above the repository root (e.g., `../../etc/passwd`) are rejected with an error

### Edge Cases

- **Missing header file**: Tool exits with descriptive error message and non-zero exit code
- **Header without trailing newline**: Header content is normalized to ensure exactly one trailing newline for consistent behavior
- **Invalid JSON config**: Tool exits with parse error details
- **Unknown file extensions**: Logged as warnings but don't prevent execution
- **Invalid exclude patterns**: Logged as warnings but don't prevent execution

## Reports

The tool can generate both JSON and Markdown reports for both `apply` and `check` operations. Reports are written to the directory specified by the `--output` flag.

### Report Generation

```bash
# Generate reports for check mode
license-header check --output reports/

# Generate reports for apply mode
license-header apply --output reports/

# Dry-run prevents report generation
license-header check --dry-run --output reports/  # Reports NOT generated
```

### Report Formats

#### JSON Reports

JSON reports are named `license-header-{mode}-report.json` and contain:

```json
{
  "timestamp": "2025-11-21T07:14:41.836368+00:00",
  "mode": "check",
  "summary": {
    "scanned": 150,
    "eligible": 100,
    "compliant": 95,
    "non_compliant": 5,
    "skipped": 50,
    "failed": 0
  },
  "files": {
    "compliant": ["src/main.py", "src/utils.py"],
    "non_compliant": ["src/new.py", "tests/test_new.py"],
    "skipped": ["data/binary.bin"],
    "failed": []
  }
}
```

For `apply` mode, the structure is similar but uses `modified` instead of `non_compliant`:

```json
{
  "timestamp": "2025-11-21T07:14:41.836368+00:00",
  "mode": "apply",
  "summary": {
    "scanned": 150,
    "eligible": 100,
    "modified": 5,
    "compliant": 95,
    "skipped": 50,
    "failed": 0
  },
  "files": {
    "modified": ["src/new.py", "tests/test_new.py"],
    "compliant": ["src/main.py", "src/utils.py"],
    "skipped": ["data/binary.bin"],
    "failed": []
  }
}
```

#### Markdown Reports

Markdown reports are named `license-header-{mode}-report.md` and provide a human-readable summary:

```markdown
# License Header Check Report

**Generated:** 2025-11-21T07:14:41.836684+00:00

## Summary

- **Scanned:** 150
- **Eligible:** 100
- **Compliant:** 95
- **Non-Compliant:** 5
- **Skipped:** 50
- **Failed:** 0

## Non-Compliant Files

- `src/new.py`
- `tests/test_new.py`

## Compliant Files

- `src/main.py`
- `src/utils.py`
- ... and 93 more
```

**Note:** Large file lists (>100 files) are truncated in Markdown reports for readability. The full list is always available in the JSON report.

### Report Error Handling

The tool validates the output directory before generating reports:

- **Missing directory**: Automatically created if it doesn't exist
- **Unwritable directory**: Clear error message without leaking files elsewhere
- **File instead of directory**: Clear error message
- **Permission errors**: Detailed error message with the specific issue

Reports are only generated when:
- The `--output` flag is specified
- The command is NOT in dry-run mode (`--dry-run` prevents report generation)
- The output directory is valid and writable

### Report Usage in CI

Reports are particularly useful in CI/CD pipelines:

```yaml
- name: Check license headers
  run: |
    license-header check --output reports/
  
- name: Upload reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: license-reports
    path: reports/
```

## Header Detection and Application

The tool uses intelligent header detection to ensure idempotent and safe header insertion.

### Header Detection Heuristics

The tool determines if a file already has the required header by:

1. **Shebang Awareness**: If a file starts with a shebang (`#!`), the header check begins after the shebang line
2. **Exact Match**: The header must match exactly (character-for-character) with the configured header text
3. **Whitespace Normalization**: Headers are normalized to ensure exactly one trailing newline for consistent comparison
4. **Leading Whitespace Tolerance**: The tool skips leading blank lines when checking for headers

### Header Insertion Behavior

When applying headers to files:

1. **Shebang Preservation**: If a file starts with `#!/...`, the header is inserted immediately after the shebang line
2. **Start-of-File Insertion**: For files without shebangs, the header is inserted at the very beginning
3. **Atomic Writes**: Files are modified atomically using a temporary file and rename operation to prevent partial writes
4. **Encoding Preservation**: BOM (Byte Order Mark) is detected and preserved for files with UTF-8 BOM, UTF-16, or UTF-32 encoding
5. **Permission Preservation**: Original file permissions are maintained when modifying files in-place

### Idempotency Guarantees

The tool provides strong idempotency guarantees:

- **Byte-Identical Results**: Files that already have the correct header remain byte-identical after repeated runs
- **No Double Insertion**: The header detection prevents adding the same header multiple times
- **Deterministic Output**: The same input always produces the same output, regardless of how many times you run the tool
- **Safe for Repeated Runs**: You can safely run `license-header apply` multiple times without corrupting files

### Example Workflow

```bash
# First run - adds headers to files without them
$ license-header apply
Modified 10 file(s)

# Second run - no changes needed
$ license-header apply
Already compliant: 10
Modified files: 0
```

### Edge Case Handling

The tool handles several edge cases:

- **BOM Files**: UTF-8 BOM and other BOMs are detected and preserved
- **Shebang Files**: Scripts with shebangs get headers inserted after the shebang line
- **Large Files**: Files larger than 10MB are handled efficiently without loading entire content into memory multiple times
- **Partial Header Matches**: Files with partial matches are treated as missing headers and get the full header added
- **Read-Only Directories**: Permission errors are surfaced with clear error messages
- **Multiline Headers**: Headers spanning multiple lines are fully supported

## Getting Help

```bash
# Show version
license-header --version

# Show general help
license-header --help

# Show command-specific help
license-header apply --help
license-header check --help
```

## GitHub Actions Integration

The tool is designed for seamless integration with GitHub Actions CI/CD pipelines.

### Basic Check Workflow

Enforce license headers on all pushes and pull requests:

```yaml
name: License Header Check

on: [push, pull_request]

jobs:
  check-headers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install license-header
        run: pip install -e .
      
      - name: Check license headers
        run: license-header check
```

**Key Points:**
- The workflow **fails** if any files are missing license headers (check mode fails by default)
- Exit code 1 causes the GitHub Actions workflow to fail
- No files are modified; this is a read-only check

### Check with Reports

Generate and upload detailed reports as artifacts:

```yaml
name: License Header Check with Reports

on: [push, pull_request]

jobs:
  check-headers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install license-header
        run: pip install -e .
      
      - name: Check license headers
        run: license-header check --output reports/
      
      - name: Upload reports
        if: always()  # Upload even if check fails
        uses: actions/upload-artifact@v3
        with:
          name: license-header-reports
          path: reports/
          retention-days: 30
```

**Benefits:**
- Reports available as downloadable artifacts
- JSON reports can be processed by other tools
- Markdown reports provide human-readable summaries
- `if: always()` ensures reports are uploaded even when check fails

### Auto-Fix Workflow (Optional)

Automatically apply headers and commit changes:

```yaml
name: Auto-Fix License Headers

on:
  push:
    branches: [main]

jobs:
  auto-fix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install license-header
        run: pip install -e .
      
      - name: Apply license headers
        run: license-header apply
      
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff-index --quiet HEAD || git commit -m "chore: auto-apply license headers"
          git push
```

**Caution:** This workflow modifies code automatically. Consider:
- Running only on specific branches
- Requiring manual approval
- Using pull request workflows instead

### CI Best Practices

1. **Use check mode** to fail builds on missing headers (fails by default)
2. **Generate reports** for debugging when checks fail
3. **Use `--dry-run` locally** before committing to see what would change
4. **Pin Python version** (e.g., `3.11`) for reproducibility
5. **Cache dependencies** to speed up workflow execution

## Testing

The test suite validates all core functionality including multi-language support, header detection, and upgrade workflows.

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=license_header --cov-report=term-missing

# Run specific test file
pytest tests/test_apply.py

# Run specific test class
pytest tests/test_apply.py::TestMultiLanguageCommentStyles

# Run tests excluding slow tests
pytest -m "not slow"
```

### Test Categories

The test suite covers:

| Category | Description | Test Files |
|----------|-------------|------------|
| **Apply** | Header insertion, idempotency, shebang preservation | `test_apply.py` |
| **Check** | Header detection, compliance validation | `test_check.py` |
| **Scanner** | File discovery, binary detection, exclude patterns | `test_scanner.py` |
| **CLI** | Command-line interface, argument parsing | `test_cli.py` |
| **Languages** | Comment style wrapping, multi-language support | `test_languages.py` |
| **Config** | Configuration loading, validation, merging | `test_config.py` |
| **Reports** | JSON/Markdown report generation | `test_reports.py` |

### Test Fixtures

Tests use `pytest`'s `tmp_path` fixture for creating temporary test directories. This ensures:

- **Isolation**: Each test runs in its own temporary directory
- **Cleanup**: Temporary files are automatically removed after tests
- **Cross-platform**: Works consistently on Linux, macOS, and Windows

### Adding New Tests

When adding tests for new functionality:

1. Use `tmp_path` fixture for file system operations
2. Test both success and error cases
3. Verify idempotency where applicable
4. Test edge cases (empty files, large files, special characters)
5. For multi-language features, test all supported extensions

## Development Status

This project is under active development. All core features are implemented and tested.

### Current Status

- ✅ CLI structure with `apply` and `check` commands
- ✅ Structured logging
- ✅ Python version validation (3.11+)
- ✅ Error handling for unknown commands
- ✅ Configuration file support with JSON format
- ✅ CLI options for all configuration parameters
- ✅ Configuration merging with proper precedence
- ✅ Path validation and security checks
- ✅ Header file loading and validation
- ✅ Repository traversal with deterministic file scanning
- ✅ File extension filtering and exclude pattern matching
- ✅ Binary file detection
- ✅ Symlink handling and circular reference detection
- ✅ Header detection and insertion logic
- ✅ Idempotent header application with shebang preservation
- ✅ Check mode with non-zero exit on non-compliant files
- ✅ Dry-run support for both apply and check
- ✅ JSON and Markdown report generation
- ✅ Deterministic summary counters
- ✅ GitHub Actions integration examples
- ✅ Header transition/upgrade command for V1 to V2 migration
- ✅ Comment marker stripping and normalized body comparison for header detection
- ✅ Upgrade reports (JSON and Markdown) with detailed file status

### Known Limitations

- **Single Header per Project**: Currently, the tool uses a single header file for all source files. Per-file or per-extension custom headers are not yet supported. All files processed by the tool will receive the same header content.
- **Report File Limits**: Markdown reports truncate large file lists to the first 100 entries for readability. Full file lists are always available in the JSON reports.



# Permanents (License, Contributing, Author)

Do not change any of the below sections

## License

All Agent Foundry work is licensed under the GPLv3 License - see the LICENSE file for details.

## Contributing

Feel free to submit issues and enhancement requests!

## Author

Created by Agent Foundry and John Brosnihan
