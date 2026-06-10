"""
Report generation for EnvGuard-CLI.

Generates output in multiple formats: terminal table, JSON, SARIF,
and Markdown. Uses only the Python standard library.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TextIO

from envguard.core.detector import Finding, ScanResult
from envguard.core.git_diff import GitDiffResult
from envguard.utils.colors import Colors


class Reporter:
    """Multi-format report generator for scan results.

    Supports terminal table, JSON, SARIF, and Markdown output formats.

    Usage:
        reporter = Reporter(format="table")
        reporter.print_result(scan_result)
    """

    SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}
    SEVERITY_ICONS = {
        "critical": "X",
        "warning": "!",
        "info": "i",
    }

    def __init__(
        self,
        output_format: str = "table",
        no_color: bool = False,
        output_file: Optional[str] = None,
        min_severity: str = "info",
    ) -> None:
        """Initialize the Reporter.

        Args:
            output_format: The output format ('table', 'json', 'sarif', 'markdown').
            no_color: Whether to disable color output.
            output_file: Optional file path to write output to.
            min_severity: Minimum severity level to include.
        """
        self.output_format = output_format.lower()
        self.colors = Colors(enabled=not no_color)
        self.output_file = output_file
        self.min_severity = min_severity
        self._min_level = self.SEVERITY_ORDER.get(min_severity.lower(), 0)

    def print_result(self, result: ScanResult) -> str:
        """Generate and print a report for a scan result.

        Args:
            result: The scan result to report.

        Returns:
            The generated report as a string.
        """
        if self.output_format == "json":
            report = self._generate_json(result)
        elif self.output_format == "sarif":
            report = self._generate_sarif(result)
        elif self.output_format == "markdown":
            report = self._generate_markdown(result)
        else:
            report = self._generate_table(result)

        if self.output_file:
            self._write_to_file(report)
        else:
            sys.stdout.write(report)

        return report

    def print_git_diff(self, result: GitDiffResult) -> str:
        """Generate and print a report for a git diff result.

        Args:
            result: The git diff result to report.

        Returns:
            The generated report as a string.
        """
        if self.output_format == "json":
            report = json.dumps(result.to_dict(), indent=2)
        elif self.output_format == "markdown":
            report = self._generate_git_diff_markdown(result)
        else:
            report = self._generate_git_diff_table(result)

        if self.output_file:
            self._write_to_file(report)
        else:
            sys.stdout.write(report)

        return report

    def _generate_table(self, result: ScanResult) -> str:
        """Generate a terminal table report.

        Args:
            result: The scan result.

        Returns:
            The table report as a string.
        """
        lines: List[str] = []
        c = self.colors

        # Header
        lines.append("")
        lines.append(c.header("  EnvGuard - Environment Drift Detection Report"))
        lines.append(c.dim("  " + "=" * 60))
        lines.append("")

        # Summary
        lines.append(f"  Scanned files: {', '.join(result.scanned_files) or 'None'}")
        lines.append(f"  Total keys examined: {result.total_keys}")
        lines.append(f"  Scan time: {result.scan_time_ms:.1f}ms")
        lines.append("")

        # Findings summary
        lines.append(c.bold("  Findings Summary:"))
        crit = result.critical_count
        warn = result.warning_count
        info = result.info_count

        if crit > 0:
            lines.append(f"    {c.bright_red('X')} Critical:  {crit}")
        else:
            lines.append(f"    {c.green('X')} Critical:  {crit}")

        if warn > 0:
            lines.append(f"    {c.bright_yellow('!')} Warnings:  {warn}")
        else:
            lines.append(f"    {c.green('!')} Warnings:  {warn}")

        lines.append(f"    {c.bright_blue('i')} Info:      {info}")
        lines.append("")

        if not result.findings:
            lines.append(c.success("  No findings detected. Your environment looks clean!"))
            lines.append("")
            return "\n".join(lines)

        # Filter findings by minimum severity
        filtered = [
            f for f in result.findings
            if self.SEVERITY_ORDER.get(f.severity, 0) >= self._min_level
        ]

        if not filtered:
            lines.append(c.success(
                f"  No findings at or above '{self.min_severity}' severity."
            ))
            lines.append("")
            return "\n".join(lines)

        # Table header
        lines.append(c.bold("  Detailed Findings:"))
        lines.append("")

        col_id = c.table_header("Rule ID")
        col_sev = c.table_header("Severity")
        col_key = c.table_header("Key")
        col_desc = c.table_header("Description")
        col_file = c.table_header("File")

        header_line = (
            f"  {col_id:<10} {col_sev:<10} "
            f"{col_key:<25} {col_desc:<40} {col_file}"
        )
        lines.append(header_line)
        lines.append(c.dim("  " + "-" * min(len(header_line), 120)))

        # Table rows
        for finding in filtered:
            sev_text = c.severity_text(finding.severity, finding.severity.upper())
            key_text = finding.key[:24] if finding.key else "-"
            desc_text = finding.description[:39] if finding.description else "-"
            file_text = os.path.basename(finding.source_file) if finding.source_file else "-"

            line = (
                f"  {finding.rule_id:<10} {sev_text:<22} "
                f"{key_text:<25} {desc_text:<40} {file_text}"
            )
            lines.append(line)

        lines.append("")

        # Fix suggestions
        lines.append(c.bold("  Fix Suggestions:"))
        lines.append("")
        seen_fixes: set = set()
        for finding in filtered:
            if finding.fix_suggestion and finding.fix_suggestion not in seen_fixes:
                seen_fixes.add(finding.fix_suggestion)
                sev_text = c.severity_text(finding.severity, finding.severity.upper())
                lines.append(
                    f"  {sev_text} [{finding.rule_id}] {finding.fix_suggestion}"
                )

        lines.append("")
        lines.append(c.dim("  " + "-" * 60))
        lines.append("")

        return "\n".join(lines)

    def _generate_json(self, result: ScanResult) -> str:
        """Generate a JSON report.

        Args:
            result: The scan result.

        Returns:
            The JSON report as a string.
        """
        data = result.to_dict()
        data["tool"] = {
            "name": "envguard",
            "version": "1.0.0",
        }
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _generate_sarif(self, result: ScanResult) -> str:
        """Generate a SARIF (Static Analysis Results Interchange Format) report.

        SARIF is used for CI/CD integration with tools like GitHub Code Scanning.

        Args:
            result: The scan result.

        Returns:
            The SARIF report as a string.
        """
        sarif: Dict[str, Any] = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "EnvGuard",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/envguard/envguard-cli",
                            "rules": [],
                        }
                    },
                    "results": [],
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "startTimeUtc": datetime.now(timezone.utc).isoformat(),
                        }
                    ],
                }
            ],
        }

        rules_dict: Dict[str, Dict[str, Any]] = {}
        sarif_results: List[Dict[str, Any]] = []

        for finding in result.findings:
            if self.SEVERITY_ORDER.get(finding.severity, 0) < self._min_level:
                continue

            # Add rule definition if not already present
            if finding.rule_id not in rules_dict:
                rule_def = {
                    "id": finding.rule_id,
                    "shortDescription": {
                        "text": finding.description,
                    },
                    "helpUri": f"https://github.com/envguard/envguard-cli/rules/{finding.rule_id}",
                    "properties": {
                        "category": finding.category,
                    },
                }
                rules_dict[finding.rule_id] = rule_def

            # Map severity to SARIF level
            level_map = {
                "critical": "error",
                "warning": "warning",
                "info": "note",
            }
            sarif_level = level_map.get(finding.severity, "note")

            # Build result
            sarif_result: Dict[str, Any] = {
                "ruleId": finding.rule_id,
                "level": sarif_level,
                "message": {
                    "text": finding.description,
                },
                "locations": [],
            }

            if finding.source_file:
                location: Dict[str, Any] = {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.source_file,
                        },
                    },
                }
                if finding.line_number > 0:
                    location["physicalLocation"]["region"] = {
                        "startLine": finding.line_number,
                    }
                sarif_result["locations"].append(location)

            sarif_results.append(sarif_result)

        sarif["runs"][0]["tool"]["driver"]["rules"] = list(rules_dict.values())
        sarif["runs"][0]["results"] = sarif_results

        return json.dumps(sarif, indent=2, ensure_ascii=False)

    def _generate_markdown(self, result: ScanResult) -> str:
        """Generate a Markdown report.

        Args:
            result: The scan result.

        Returns:
            The Markdown report as a string.
        """
        lines: List[str] = []

        lines.append("# EnvGuard - Environment Drift Detection Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"**Tool:** EnvGuard v1.0.0")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Scanned Files | {', '.join(result.scanned_files) or 'None'} |")
        lines.append(f"| Total Keys | {result.total_keys} |")
        lines.append(f"| Critical | {result.critical_count} |")
        lines.append(f"| Warnings | {result.warning_count} |")
        lines.append(f"| Info | {result.info_count} |")
        lines.append(f"| Scan Time | {result.scan_time_ms:.1f}ms |")
        lines.append("")

        if not result.findings:
            lines.append("## Findings")
            lines.append("")
            lines.append("No findings detected. Your environment looks clean!")
            lines.append("")
            return "\n".join(lines)

        # Filter findings
        filtered = [
            f for f in result.findings
            if self.SEVERITY_ORDER.get(f.severity, 0) >= self._min_level
        ]

        # Findings table
        lines.append("## Findings")
        lines.append("")
        lines.append("| Rule | Severity | Key | Description | File | Line |")
        lines.append("|------|----------|-----|-------------|------|------|")

        for finding in filtered:
            sev_badge = {
                "critical": ":red_circle:",
                "warning": ":yellow_circle:",
                "info": ":blue_circle:",
            }.get(finding.severity, ":white_circle:")

            file_name = os.path.basename(finding.source_file) if finding.source_file else "-"
            desc = finding.description.replace("|", "\\|")

            lines.append(
                f"| {finding.rule_id} | {sev_badge} {finding.severity} | "
                f"`{finding.key}` | {desc} | {file_name} | {finding.line_number} |"
            )

        lines.append("")

        # Fix suggestions
        lines.append("## Fix Suggestions")
        lines.append("")
        seen_fixes: set = set()
        for finding in filtered:
            if finding.fix_suggestion and finding.fix_suggestion not in seen_fixes:
                seen_fixes.add(finding.fix_suggestion)
                lines.append(f"- **[{finding.rule_id}]** {finding.fix_suggestion}")

        lines.append("")

        return "\n".join(lines)

    def _generate_git_diff_table(self, result: GitDiffResult) -> str:
        """Generate a terminal table for git diff results.

        Args:
            result: The git diff result.

        Returns:
            The table report as a string.
        """
        lines: List[str] = []
        c = self.colors

        lines.append("")
        lines.append(c.header("  EnvGuard - Git Environment Diff Report"))
        lines.append(c.dim("  " + "=" * 60))
        lines.append("")
        lines.append(f"  Comparing: {c.bold(result.from_ref)} -> {c.bold(result.to_ref)}")
        lines.append(f"  Files compared: {', '.join(result.files_compared) or 'None'}")
        lines.append("")

        # Summary
        lines.append(c.bold("  Changes Summary:"))
        lines.append(f"    {c.green('+')} Added:    {result.total_added}")
        lines.append(f"    {c.red('-')} Removed:  {result.total_removed}")
        lines.append(f"    {c.bright_yellow('~')} Modified: {result.total_modified}")
        lines.append("")

        if not result.changes:
            lines.append(c.success("  No environment changes detected."))
            lines.append("")
            return "\n".join(lines)

        # Table
        col_type = c.table_header("Change")
        col_key = c.table_header("Key")
        col_old = c.table_header("Old Value")
        col_new = c.table_header("New Value")
        col_commit = c.table_header("Commit")

        header_line = f"  {col_type:<10} {col_key:<25} {col_old:<25} {col_new:<25} {col_commit}"
        lines.append(header_line)
        lines.append(c.dim("  " + "-" * min(len(header_line), 120)))

        for change in result.changes:
            if change.change_type == "added":
                type_text = c.green("+ ADDED")
            elif change.change_type == "removed":
                type_text = c.red("- REMOVED")
            else:
                type_text = c.bright_yellow("~ MODIFIED")

            old_val = change.old_value[:24] if change.old_value else "-"
            new_val = change.new_value[:24] if change.new_value else "-"
            commit = change.commit_hash[:8] if change.commit_hash else "-"

            line = f"  {type_text:<22} {change.key:<25} {old_val:<25} {new_val:<25} {commit}"
            lines.append(line)

        lines.append("")
        return "\n".join(lines)

    def _generate_git_diff_markdown(self, result: GitDiffResult) -> str:
        """Generate a Markdown report for git diff results.

        Args:
            result: The git diff result.

        Returns:
            The Markdown report as a string.
        """
        lines: List[str] = []

        lines.append("# EnvGuard - Git Environment Diff Report")
        lines.append("")
        lines.append(f"**Comparing:** `{result.from_ref}` -> `{result.to_ref}`")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Added | {result.total_added} |")
        lines.append(f"| Removed | {result.total_removed} |")
        lines.append(f"| Modified | {result.total_modified} |")
        lines.append(f"| Files | {', '.join(result.files_compared) or 'None'} |")
        lines.append("")

        if not result.changes:
            lines.append("No environment changes detected.")
            lines.append("")
            return "\n".join(lines)

        lines.append("## Changes")
        lines.append("")
        lines.append("| Change | Key | Old Value | New Value | Commit |")
        lines.append("|--------|-----|-----------|-----------|--------|")

        for change in result.changes:
            change_icon = {
                "added": ":green_circle:",
                "removed": ":red_circle:",
                "modified": ":yellow_circle:",
            }.get(change.change_type, ":white_circle:")

            old_val = change.old_value[:30] if change.old_value else "-"
            new_val = change.new_value[:30] if change.new_value else "-"
            commit = change.commit_hash[:8] if change.commit_hash else "-"

            lines.append(
                f"| {change_icon} {change.change_type} | "
                f"`{change.key}` | `{old_val}` | `{new_val}` | {commit} |"
            )

        lines.append("")
        return "\n".join(lines)

    def _write_to_file(self, content: str) -> None:
        """Write report content to a file.

        Args:
            content: The content to write.
        """
        if not self.output_file:
            return

        filepath = os.path.abspath(self.output_file)
        parent = os.path.dirname(filepath)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def format_severity_badge(severity: str, no_color: bool = False) -> str:
        """Format a severity level as a display badge.

        Args:
            severity: The severity level.
            no_color: Whether to disable colors.

        Returns:
            The formatted severity badge string.
        """
        if no_color:
            return f"[{severity.upper()}]"

        colors = Colors(enabled=True)
        return colors.severity_text(severity, f"[{severity.upper()}]")
