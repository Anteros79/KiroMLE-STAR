"""
Command-line interface for the Security Audit & Hardening feature.

This module provides a CLI entry point for running security audits on
codebases. It supports various configuration options for customizing
the scan behavior.

Usage:
    python -m mle_star.security.cli [OPTIONS] [PROJECT_ROOT]
    
    # Or if installed as a package:
    mle-star-security-audit [OPTIONS] [PROJECT_ROOT]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .models import ScanConfig
from .scanner import SecurityScanner


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging for the CLI.
    
    Args:
        verbose: If True, set log level to DEBUG
        quiet: If True, set log level to WARNING (only show warnings and errors)
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Optional list of arguments. If None, uses sys.argv.
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="mle-star-security-audit",
        description="Run a comprehensive security audit on a codebase.",
        epilog="Example: mle-star-security-audit --output-path ./reports/audit.md ./my-project",
    )
    
    # Positional argument
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Root directory of the project to scan (default: current directory)",
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output-path",
        type=str,
        default=None,
        help="Path for the security audit report (default: PROJECT_ROOT/SECURITY_AUDIT.md)",
    )
    
    # Scan options
    parser.add_argument(
        "--skip-secrets",
        action="store_true",
        help="Skip scanning for hardcoded secrets",
    )
    parser.add_argument(
        "--skip-dependencies",
        action="store_true",
        help="Skip scanning for vulnerable dependencies",
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip scanning API endpoints for security issues",
    )
    parser.add_argument(
        "--skip-marking",
        action="store_true",
        help="Skip marking critical findings in source files with TODO comments",
    )
    
    # Directory options
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        nargs="+",
        default=None,
        help="Additional directories to exclude from scanning (e.g., --exclude-dirs build dist)",
    )
    parser.add_argument(
        "--api-dirs",
        type=str,
        nargs="+",
        default=None,
        help="Directories to scan for API endpoints (default: src/mle_star/api, routes, api)",
    )
    
    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run scan without modifying any files (report still generated)",
    )
    
    # Logging options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (debug level logging)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress informational output (only show warnings and errors)",
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    return parser.parse_args(args)


def create_config_from_args(args: argparse.Namespace) -> ScanConfig:
    """Create a ScanConfig from parsed command-line arguments.
    
    Args:
        args: Parsed arguments namespace
        
    Returns:
        ScanConfig object configured according to arguments
    """
    project_root = Path(args.project_root).resolve()
    
    # Default exclude directories
    exclude_dirs = {".git", ".venv", "node_modules", "__pycache__", ".next", ".hypothesis"}
    
    # Add user-specified exclude directories
    if args.exclude_dirs:
        exclude_dirs.update(args.exclude_dirs)
    
    # API directories
    api_directories = args.api_dirs if args.api_dirs else ["src/mle_star/api", "routes", "api"]
    
    return ScanConfig(
        project_root=project_root,
        exclude_dirs=exclude_dirs,
        exclude_files={"*.pyc", "*.lock"},
        scan_secrets=not args.skip_secrets,
        scan_dependencies=not args.skip_dependencies,
        scan_api=not args.skip_api,
        mark_critical=not args.skip_marking,
        api_directories=api_directories,
    )


def print_summary(result) -> None:
    """Print a summary of the scan results to stdout.
    
    Args:
        result: ScanResult object from the scan
    """
    total_findings = (
        len(result.secret_findings) +
        len(result.dependency_findings) +
        len(result.api_findings)
    )
    
    # Count by severity
    critical = 0
    high = 0
    medium = 0
    low = 0
    
    for f in result.secret_findings:
        if f.severity == "critical":
            critical += 1
        elif f.severity == "high":
            high += 1
        elif f.severity == "medium":
            medium += 1
        else:
            low += 1
    
    for f in result.dependency_findings:
        if f.severity == "critical":
            critical += 1
        elif f.severity == "high":
            high += 1
        elif f.severity == "medium":
            medium += 1
        else:
            low += 1
    
    for f in result.api_findings:
        if f.severity == "critical":
            critical += 1
        elif f.severity == "high":
            high += 1
        elif f.severity == "medium":
            medium += 1
        else:
            low += 1
    
    print("\n" + "=" * 60)
    print("SECURITY AUDIT SUMMARY")
    print("=" * 60)
    print(f"\nProject: {result.config.project_root}")
    print(f"Scan Duration: {result.scan_duration_seconds:.2f} seconds")
    print(f"Files Scanned: {result.scanned_files_count}")
    print(f"\nTotal Findings: {total_findings}")
    print(f"  - Critical: {critical}")
    print(f"  - High: {high}")
    print(f"  - Medium: {medium}")
    print(f"  - Low: {low}")
    print(f"\nBreakdown:")
    print(f"  - Hardcoded Secrets: {len(result.secret_findings)}")
    print(f"  - Vulnerable Dependencies: {len(result.dependency_findings)}")
    print(f"  - API Security Issues: {len(result.api_findings)}")
    
    if result.marked_files:
        print(f"\nFiles Marked: {len(result.marked_files)}")
    
    print("\n" + "=" * 60)
    
    # Determine exit status based on findings
    if critical > 0:
        print("⚠️  CRITICAL vulnerabilities found! Immediate action required.")
    elif high > 0:
        print("🔴 HIGH severity issues found. Address promptly.")
    elif medium > 0:
        print("🟡 MEDIUM severity issues found. Review recommended.")
    elif low > 0:
        print("🟢 LOW severity issues found. Consider addressing.")
    else:
        print("✅ No security issues found.")
    
    print("=" * 60 + "\n")


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Optional list of command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for errors, 2 for critical findings)
    """
    parsed_args = parse_args(args)
    
    # Setup logging
    setup_logging(verbose=parsed_args.verbose, quiet=parsed_args.quiet)
    
    logger = logging.getLogger(__name__)
    
    # Validate project root
    project_root = Path(parsed_args.project_root).resolve()
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 1
    
    if not project_root.is_dir():
        logger.error(f"Project root is not a directory: {project_root}")
        return 1
    
    # Create configuration
    config = create_config_from_args(parsed_args)
    
    # Determine output path
    output_path = None
    if parsed_args.output_path:
        output_path = Path(parsed_args.output_path).resolve()
    
    # Create scanner and run
    scanner = SecurityScanner(config)
    
    try:
        result = scanner.scan(
            project_root=project_root,
            output_path=output_path,
            skip_marking=parsed_args.skip_marking,
            dry_run=parsed_args.dry_run,
        )
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Print summary unless quiet mode
    if not parsed_args.quiet:
        print_summary(result)
        
        # Print report location
        if output_path:
            print(f"Report generated: {output_path}")
        else:
            print(f"Report generated: {project_root / 'SECURITY_AUDIT.md'}")
    
    # Determine exit code based on findings
    summary = scanner.get_findings_summary()
    if summary["critical"] > 0:
        return 2  # Critical findings
    elif summary["total"] > 0:
        return 0  # Findings but not critical (success with warnings)
    else:
        return 0  # No findings


if __name__ == "__main__":
    sys.exit(main())
