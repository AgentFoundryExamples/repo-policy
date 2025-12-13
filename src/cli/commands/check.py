# Copyright 2025 John Brosnihan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Check command implementation."""

import logging
import argparse
import shutil
from pathlib import Path

from config.loader import load_config
from integration.repo_analyzer import RepoAnalyzerRunner
from integration.license_headers import LicenseHeaderChecker
from integration.context import PolicyContext

logger = logging.getLogger(__name__)


def check_command(args: argparse.Namespace) -> int:
    """
    Execute the check command to run policy checks.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error-level failures)
    """
    logger.info("Starting policy check")

    # Build CLI args dict for config loader
    cli_args = {
        "target_path": args.target_path,
        "outdir": args.outdir,
        "keep_artifacts": args.keep_artifacts,
        "clean": args.clean,
        "advice": args.advice,
    }

    # Load configuration
    try:
        config = load_config(config_path=args.config, cli_args=cli_args)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Resolve target path
    target_path = Path(config.target_path).resolve()
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        return 1

    logger.info(f"Target path: {target_path}")
    logger.info(f"Output directory: {config.outdir}")

    # Clean output directory if requested
    if config.clean:
        outdir = Path(config.outdir)
        if outdir.exists():
            logger.info(f"Cleaning output directory: {outdir}")
            # Remove only contents, not the directory itself
            try:
                for item in outdir.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except OSError as e:
                        logger.warning(f"Failed to remove {item}: {e}")
                logger.debug(f"Cleaned {outdir}")
            except OSError as e:
                logger.error(f"Error cleaning output directory {outdir}: {e}")
                return 1

    # Create output directory
    outdir = Path(config.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {outdir}")

    # Initialize policy context
    context = PolicyContext()

    # Run repo analyzer integration
    if config.integration.enable_repo_analyzer:
        logger.info("Running repo analyzer integration...")
        analyzer = RepoAnalyzerRunner(
            analyzer_binary=config.integration.repo_analyzer_binary,
            workspace_mode=config.integration.repo_analyzer_workspace_mode,
        )

        analyzer_result = analyzer.run(
            target_path=target_path,
            outdir=outdir,
            keep_artifacts=config.keep_artifacts,
        )

        context.analyzer_result = analyzer_result

        if analyzer_result.success:
            logger.info("Repo analyzer completed successfully")
            if analyzer_result.output_files:
                logger.debug(f"Analyzer outputs: {analyzer_result.output_files}")
        elif analyzer_result.error_message:
            logger.warning(f"Repo analyzer failed: {analyzer_result.error_message}")
        else:
            logger.warning("Repo analyzer failed")
    else:
        logger.info("Repo analyzer integration disabled")

    # Run license header integration
    if config.integration.enable_license_headers and config.license.require_header:
        logger.info("Running license header check...")
        checker = LicenseHeaderChecker(
            binary_path=config.integration.license_header_binary,
        )

        header_result = checker.check(
            target_path=target_path,
            outdir=outdir,
            spdx_id=config.license.spdx_id,
            header_template_path=config.license.header_template_path,
            include_globs=config.license.include_globs,
            exclude_globs=config.license.exclude_globs,
            keep_artifacts=config.keep_artifacts,
        )

        context.license_header_result = header_result

        if header_result.success:
            logger.info("License header check passed")
            if header_result.summary:
                logger.info(f"Summary: {header_result.summary}")
        elif header_result.error_message:
            logger.warning(f"License header check failed: {header_result.error_message}")
        else:
            logger.warning(
                f"License header check found {len(header_result.non_compliant_files)} "
                f"non-compliant files"
            )
    elif not config.license.require_header:
        logger.info("License header enforcement disabled (require_header: false)")
        # Create a skipped result
        from integration.license_headers import LicenseHeaderResult

        context.license_header_result = LicenseHeaderResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
        )
    else:
        logger.info("License header integration disabled")

    # Show advice if requested
    if config.advice:
        logger.info("Advice mode enabled (stub)")
        # Stub: advice logic would be implemented here

    # Run policy checks (stub)
    logger.info("Running policy checks")
    logger.debug(f"Rules to include: {config.rules.include}")
    logger.debug(f"Rules to exclude: {config.rules.exclude}")
    logger.debug(f"Severity overrides: {config.rules.severity_overrides}")

    # Log integration context
    logger.info(f"License SPDX ID: {config.license.spdx_id or 'not set'}")
    logger.info(f"Require headers: {config.license.require_header}")
    logger.info(f"Repository tags: {config.repo_tags}")

    # Store context metadata
    context.metadata["config"] = {
        "target_path": str(target_path),
        "outdir": str(outdir),
        "license_spdx_id": config.license.spdx_id,
        "require_header": config.license.require_header,
        "repo_tags": config.repo_tags,
    }

    # Determine if there are errors
    has_errors = False

    # Check if license headers failed
    if (
        context.license_header_result
        and not context.license_header_result.skipped
        and not context.license_header_result.success
    ):
        has_errors = True

    # Log final context
    logger.debug(f"Policy context: {context.to_dict()}")

    # Report results
    if has_errors:
        logger.error("Policy check failed with error-level violations")
        return 1
    else:
        logger.info("Policy check completed successfully")
        return 0
