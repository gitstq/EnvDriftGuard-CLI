"""
CLI entry point for EnvGuard-CLI.

Provides command-line interface for environment drift detection,
file comparison, git diff analysis, and report generation.

Usage:
    envguard scan [--format table|json|sarif|markdown] [--severity critical|warning|info]
    envguard compare <file1> <file2>
    envguard git-diff [--from REF] [--to REF]
    envguard check [--fail-on critical|warning|any]
    envguard report
    envguard dashboard
"""

import argparse
import os
import sys
from typing import List, Optional, Set

from envguard import __version__
from envguard.core.detector import DriftDetector, ScanResult
from envguard.core.git_diff import GitDiffAnalyzer, GitError
from envguard.core.parser import EnvParser
from envguard.core.reporter import Reporter
from envguard.utils.colors import Colors
from envguard.utils.fs import FileSystemHelper


def _build_common_parser() -> argparse.ArgumentParser:
    """Build an argument parser with common options.

    Returns:
        An ArgumentParser with common options.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "sarif", "markdown"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--severity", "-s",
        choices=["critical", "warning", "info"],
        default="info",
        help="Minimum severity level to report (default: info)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )
    return parser


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute the scan command.

    Scans the current directory for environment files and runs
    drift detection on them.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for findings, 2 for errors).
    """
    colors = Colors(enabled=not args.no_color)
    fs = FileSystemHelper()

    # Find env files
    env_files = fs.find_env_files()
    config_files = fs.find_config_files()

    if not env_files and not config_files:
        if args.verbose:
            print(colors.warn("No environment or configuration files found in current directory."))
        return 0

    all_files = env_files + config_files

    if args.verbose:
        print(colors.dim(f"Found {len(all_files)} configuration file(s):"))
        for f in all_files:
            print(colors.dim(f"  - {f}"))

    # Parse ignore keys
    ignore_keys: Set[str] = set()
    if args.ignore:
        ignore_keys = set(k.strip() for k in args.ignore.split(","))

    # Find template file
    template_path: Optional[str] = None
    if args.template:
        template_path = os.path.abspath(args.template)
    else:
        # Auto-detect template
        for f in env_files:
            basename = os.path.basename(f)
            if basename.endswith((".example", ".sample", ".template")):
                template_path = f
                break

    # Create detector and scan
    detector = DriftDetector(
        ignore_keys=ignore_keys,
        min_severity=args.severity,
    )

    try:
        result = detector.scan_files(all_files, template_path)
    except Exception as e:
        print(colors.error(f"Error during scan: {e}"), file=sys.stderr)
        return 2

    # Generate report
    reporter = Reporter(
        output_format=args.format,
        no_color=args.no_color,
        output_file=args.output,
        min_severity=args.severity,
    )
    reporter.print_result(result)

    # Return exit code based on findings
    if args.fail_on == "critical" and result.critical_count > 0:
        return 1
    elif args.fail_on == "warning" and (result.critical_count > 0 or result.warning_count > 0):
        return 1
    elif args.fail_on == "any" and result.total_count > 0:
        return 1

    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Execute the compare command.

    Compares two environment files and reports differences.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for no differences, 1 for differences, 2 for errors).
    """
    colors = Colors(enabled=not args.no_color)

    file_a = os.path.abspath(args.file1)
    file_b = os.path.abspath(args.file2)

    if not os.path.isfile(file_a):
        print(colors.error(f"File not found: {file_a}"), file=sys.stderr)
        return 2
    if not os.path.isfile(file_b):
        print(colors.error(f"File not found: {file_b}"), file=sys.stderr)
        return 2

    # Parse ignore keys
    ignore_keys: Set[str] = set()
    if args.ignore:
        ignore_keys = set(k.strip() for k in args.ignore.split(","))

    detector = DriftDetector(
        ignore_keys=ignore_keys,
        min_severity=args.severity,
    )

    try:
        result = detector.compare_files(file_a, file_b)
    except Exception as e:
        print(colors.error(f"Error during comparison: {e}"), file=sys.stderr)
        return 2

    reporter = Reporter(
        output_format=args.format,
        no_color=args.no_color,
        output_file=args.output,
        min_severity=args.severity,
    )
    reporter.print_result(result)

    return 1 if result.total_count > 0 else 0


def cmd_git_diff(args: argparse.Namespace) -> int:
    """Execute the git-diff command.

    Shows environment file changes in git history.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 2 for errors).
    """
    colors = Colors(enabled=not args.no_color)

    try:
        analyzer = GitDiffAnalyzer()
    except GitError as e:
        print(colors.error(str(e)), file=sys.stderr)
        return 2

    from_ref = args.from_ref or "HEAD~5"
    to_ref = args.to_ref or "HEAD"
    file_pattern = args.file_pattern or ".env*"

    if args.verbose:
        print(colors.dim(f"Comparing {from_ref} -> {to_ref} (pattern: {file_pattern})"))

    try:
        result = analyzer.diff_commits(from_ref, to_ref, file_pattern)
    except GitError as e:
        print(colors.error(f"Git diff failed: {e}"), file=sys.stderr)
        return 2

    reporter = Reporter(
        output_format=args.format,
        no_color=args.no_color,
        output_file=args.output,
        min_severity=args.severity,
    )
    reporter.print_git_diff(result)

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Execute the check command (CI mode).

    Runs drift detection and exits with non-zero code if findings
    are detected at or above the specified severity.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for clean, 1 for findings, 2 for errors).
    """
    colors = Colors(enabled=not args.no_color)
    fs = FileSystemHelper()

    env_files = fs.find_env_files()
    config_files = fs.find_config_files()
    all_files = env_files + config_files

    if not all_files:
        if args.verbose:
            print(colors.dim("No configuration files found."))
        return 0

    # Parse ignore keys
    ignore_keys: Set[str] = set()
    if args.ignore:
        ignore_keys = set(k.strip() for k in args.ignore.split(","))

    # Find template
    template_path: Optional[str] = None
    if args.template:
        template_path = os.path.abspath(args.template)
    else:
        for f in env_files:
            basename = os.path.basename(f)
            if basename.endswith((".example", ".sample", ".template")):
                template_path = f
                break

    detector = DriftDetector(
        ignore_keys=ignore_keys,
        min_severity=args.fail_on if args.fail_on != "any" else "info",
    )

    try:
        result = detector.scan_files(all_files, template_path)
    except Exception as e:
        print(colors.error(f"Error during check: {e}"), file=sys.stderr)
        return 2

    # Always output JSON in CI mode unless format is specified
    if args.format == "table":
        output_format = "json" if not args.verbose else "table"
    else:
        output_format = args.format

    reporter = Reporter(
        output_format=output_format,
        no_color=True,
        output_file=args.output,
        min_severity=args.fail_on if args.fail_on != "any" else "info",
    )
    reporter.print_result(result)

    # Determine exit code
    if args.fail_on == "critical" and result.critical_count > 0:
        if args.verbose:
            print(colors.error(f"CI CHECK FAILED: {result.critical_count} critical finding(s)"))
        return 1
    elif args.fail_on == "warning" and (result.critical_count > 0 or result.warning_count > 0):
        if args.verbose:
            print(colors.error(
                f"CI CHECK FAILED: {result.critical_count} critical, "
                f"{result.warning_count} warning finding(s)"
            ))
        return 1
    elif args.fail_on == "any" and result.total_count > 0:
        if args.verbose:
            print(colors.error(f"CI CHECK FAILED: {result.total_count} finding(s)"))
        return 1

    if args.verbose:
        print(colors.success("CI CHECK PASSED"))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Execute the report command.

    Generates a comprehensive report of all environment files.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 2 for errors).
    """
    colors = Colors(enabled=not args.no_color)
    fs = FileSystemHelper()

    env_files = fs.find_env_files()
    config_files = fs.find_config_files()
    all_files = env_files + config_files

    if not all_files:
        print(colors.warn("No configuration files found to report on."))
        return 0

    # Parse ignore keys
    ignore_keys: Set[str] = set()
    if args.ignore:
        ignore_keys = set(k.strip() for k in args.ignore.split(","))

    # Find template
    template_path: Optional[str] = None
    if args.template:
        template_path = os.path.abspath(args.template)
    else:
        for f in env_files:
            basename = os.path.basename(f)
            if basename.endswith((".example", ".sample", ".template")):
                template_path = f
                break

    detector = DriftDetector(
        ignore_keys=ignore_keys,
        min_severity=args.severity,
    )

    try:
        result = detector.scan_files(all_files, template_path)
    except Exception as e:
        print(colors.error(f"Error generating report: {e}"), file=sys.stderr)
        return 2

    # Default to markdown for report command
    output_format = args.format if args.format != "table" else "markdown"
    output_file = args.output or "envguard-report.md"

    reporter = Reporter(
        output_format=output_format,
        no_color=args.no_color,
        output_file=output_file,
        min_severity=args.severity,
    )
    reporter.print_result(result)

    print(colors.success(f"Report written to: {output_file}"))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """Execute the dashboard command.

    Launches the interactive TUI dashboard.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 2 for errors).
    """
    try:
        from envguard.tui import run_dashboard
        return run_dashboard(args)
    except ImportError as e:
        print(f"Cannot load TUI module: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"TUI error: {e}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser.

    Returns:
        The configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="EnvGuard-CLI: Lightweight environment configuration drift detection engine.",
        epilog="Examples:\n"
               "  envguard scan\n"
               "  envguard scan --format json --severity warning\n"
               "  envguard compare .env .env.example\n"
               "  envguard git-diff --from main --to HEAD\n"
               "  envguard check --fail-on critical\n"
               "  envguard report --format markdown\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common options added to each subcommand
    common = _build_common_parser()

    # scan command
    scan_parser = subparsers.add_parser(
        "scan",
        parents=[common],
        help="Scan current directory for environment drift",
        description="Scan environment files in the current directory for configuration drift.",
    )
    scan_parser.add_argument(
        "--template", "-t",
        type=str,
        default=None,
        help="Path to template file (.env.example)",
    )
    scan_parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of keys to ignore",
    )
    scan_parser.add_argument(
        "--fail-on",
        choices=["critical", "warning", "any"],
        default="critical",
        help="Fail condition for exit code (default: critical)",
    )

    # compare command
    compare_parser = subparsers.add_parser(
        "compare",
        parents=[common],
        help="Compare two environment files directly",
        description="Compare two environment files and report differences.",
    )
    compare_parser.add_argument(
        "file1",
        type=str,
        help="Path to the first environment file",
    )
    compare_parser.add_argument(
        "file2",
        type=str,
        help="Path to the second environment file",
    )
    compare_parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of keys to ignore",
    )

    # git-diff command
    gitdiff_parser = subparsers.add_parser(
        "git-diff",
        parents=[common],
        help="Show environment changes in git history",
        description="Show environment file changes between git references.",
    )
    gitdiff_parser.add_argument(
        "--from", dest="from_ref",
        type=str,
        default=None,
        help="Source git reference (default: HEAD~5)",
    )
    gitdiff_parser.add_argument(
        "--to", dest="to_ref",
        type=str,
        default=None,
        help="Target git reference (default: HEAD)",
    )
    gitdiff_parser.add_argument(
        "--file-pattern",
        type=str,
        default=".env*",
        help="File pattern to match (default: .env*)",
    )

    # check command (CI mode)
    check_parser = subparsers.add_parser(
        "check",
        parents=[common],
        help="Run as CI check (exit code based on findings)",
        description="Run drift detection in CI mode. Exits with code 1 if findings are detected.",
    )
    check_parser.add_argument(
        "--template", "-t",
        type=str,
        default=None,
        help="Path to template file (.env.example)",
    )
    check_parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of keys to ignore",
    )
    check_parser.add_argument(
        "--fail-on",
        choices=["critical", "warning", "any"],
        default="critical",
        help="Fail condition for exit code (default: critical)",
    )

    # report command
    report_parser = subparsers.add_parser(
        "report",
        parents=[common],
        help="Generate a full report",
        description="Generate a comprehensive report of all environment files.",
    )
    report_parser.add_argument(
        "--template", "-t",
        type=str,
        default=None,
        help="Path to template file (.env.example)",
    )
    report_parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of keys to ignore",
    )

    # dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Launch interactive TUI dashboard",
        description="Launch an interactive terminal dashboard to browse scan results.",
    )
    dashboard_parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the EnvGuard CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors/findings).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    handlers = {
        "scan": cmd_scan,
        "compare": cmd_compare,
        "git-diff": cmd_git_diff,
        "check": cmd_check,
        "report": cmd_report,
        "dashboard": cmd_dashboard,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
