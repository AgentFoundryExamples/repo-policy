"""Main CLI entry point for repo-policy."""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional

from config.loader import load_config
from config.schema import Preset


def setup_logging(verbose: bool = False) -> None:
    """
    Configure structured logging.
    
    Args:
        verbose: Enable verbose/debug logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for repo-policy CLI.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="repo-policy",
        description="Deterministic repository policy enforcement tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Global options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to config file (default: auto-discover repo-policy.yml)",
    )
    parser.add_argument(
        "--path",
        type=str,
        dest="target_path",
        metavar="PATH",
        help="Path to repository to analyze (default: .)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        metavar="PATH",
        help="Output directory for reports and artifacts (default: .repo-policy-output)",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help="Keep intermediate artifacts after run",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before run",
    )
    parser.add_argument(
        "--advice",
        action="store_true",
        help="Show advice and recommendations (stub)",
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
    )
    
    # 'check' command (default)
    check_parser = subparsers.add_parser(
        "check",
        help="Check repository against policies (default command)",
        description="Run policy checks against the repository",
    )
    check_parser.set_defaults(func=run_check)
    
    # 'init' command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new repo-policy configuration",
        description="Create a baseline repo-policy.yml configuration file",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing config file without prompting",
    )
    init_parser.add_argument(
        "--preset",
        type=str,
        choices=[p.value for p in Preset],
        help="Configuration preset to use (baseline, standard, strict)",
    )
    init_parser.set_defaults(func=run_init)
    
    return parser


def run_check(args: argparse.Namespace) -> int:
    """
    Run the check command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    from cli.commands.check import check_command
    return check_command(args)


def run_init(args: argparse.Namespace) -> int:
    """
    Run the init command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    from cli.commands.init import init_command
    return init_command(args)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for repo-policy CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
    
    # Default to 'check' command if no command specified
    if not args.command:
        args.command = "check"
        args.func = run_check
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
