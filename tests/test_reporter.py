"""
Unit tests for the Reporter module.

Tests report generation in table, JSON, SARIF, and Markdown formats.
"""

import json
import os
import tempfile
import unittest

from envguard.core.detector import Finding, ScanResult
from envguard.core.git_diff import GitDiffResult, GitEnvChange
from envguard.core.reporter import Reporter
from envguard.utils.colors import Colors


class TestReporterTable(unittest.TestCase):
    """Tests for table format output."""

    def setUp(self) -> None:
        """Set up test reporter."""
        self.reporter = Reporter(output_format="table", no_color=True)

    def test_empty_result(self) -> None:
        """Test table output for empty results."""
        result = ScanResult()
        output = self.reporter.print_result(result)
        self.assertIn("EnvGuard", output)
        self.assertIn("No findings detected", output)

    def test_result_with_findings(self) -> None:
        """Test table output with findings."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="TEST001",
                    severity="critical",
                    category="test",
                    description="Critical test finding",
                    fix_suggestion="Fix the critical issue",
                    key="TEST_KEY",
                    value="test_value",
                    source_file=".env",
                    line_number=5,
                ),
                Finding(
                    rule_id="TEST002",
                    severity="warning",
                    category="test",
                    description="Warning test finding",
                    fix_suggestion="Fix the warning",
                    key="WARN_KEY",
                    value="warn_value",
                    source_file=".env",
                    line_number=10,
                ),
            ],
            scanned_files=[".env"],
            total_keys=10,
            scan_time_ms=5.0,
        )
        output = self.reporter.print_result(result)
        self.assertIn("TEST001", output)
        self.assertIn("TEST002", output)
        self.assertIn("CRITICAL", output)
        self.assertIn("WARNING", output)
        self.assertIn("Fix Suggestions", output)

    def test_severity_filter(self) -> None:
        """Test that severity filtering works in table output."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R1", severity="critical", category="c",
                    description="d", fix_suggestion="f", key="K",
                ),
                Finding(
                    rule_id="R2", severity="info", category="c",
                    description="d", fix_suggestion="f", key="K",
                ),
            ],
        )
        reporter = Reporter(output_format="table", no_color=True, min_severity="warning")
        output = reporter.print_result(result)
        self.assertIn("R1", output)
        self.assertNotIn("R2", output)


class TestReporterJSON(unittest.TestCase):
    """Tests for JSON format output."""

    def setUp(self) -> None:
        """Set up test reporter."""
        self.reporter = Reporter(output_format="json", no_color=True)

    def test_empty_result_json(self) -> None:
        """Test JSON output for empty results."""
        result = ScanResult()
        output = self.reporter.print_result(result)
        data = json.loads(output)
        self.assertIn("summary", data)
        self.assertIn("findings", data)
        self.assertEqual(data["summary"]["total_findings"], 0)

    def test_result_with_findings_json(self) -> None:
        """Test JSON output with findings."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R001",
                    severity="critical",
                    category="test_cat",
                    description="Test description",
                    fix_suggestion="Fix it",
                    key="MY_KEY",
                    value="super_secret_value",
                    source_file=".env",
                    line_number=3,
                ),
            ],
            scanned_files=[".env"],
            total_keys=5,
            scan_time_ms=2.5,
        )
        output = self.reporter.print_result(result)
        data = json.loads(output)

        self.assertEqual(data["summary"]["total_findings"], 1)
        self.assertEqual(data["summary"]["critical"], 1)
        self.assertEqual(len(data["findings"]), 1)

        finding = data["findings"][0]
        self.assertEqual(finding["rule_id"], "R001")
        self.assertEqual(finding["severity"], "critical")
        self.assertEqual(finding["key"], "MY_KEY")
        # Value should be masked
        self.assertIn("*", finding["value"])

    def test_json_output_to_file(self) -> None:
        """Test writing JSON output to a file."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R1", severity="info", category="c",
                    description="d", fix_suggestion="f", key="K",
                ),
            ],
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            reporter = Reporter(output_format="json", no_color=True, output_file=temp_path)
            reporter.print_result(result)

            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["summary"]["total_findings"], 1)
        finally:
            os.unlink(temp_path)


class TestReporterSARIF(unittest.TestCase):
    """Tests for SARIF format output."""

    def setUp(self) -> None:
        """Set up test reporter."""
        self.reporter = Reporter(output_format="sarif", no_color=True)

    def test_sarif_structure(self) -> None:
        """Test SARIF output has correct structure."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R001",
                    severity="critical",
                    category="test_cat",
                    description="Test finding",
                    fix_suggestion="Fix it",
                    key="MY_KEY",
                    source_file=".env",
                    line_number=5,
                ),
            ],
        )
        output = self.reporter.print_result(result)
        data = json.loads(output)

        self.assertEqual(data["version"], "2.1.0")
        self.assertIn("$schema", data)
        self.assertEqual(len(data["runs"]), 1)

        run = data["runs"][0]
        self.assertIn("tool", run)
        self.assertEqual(run["tool"]["driver"]["name"], "EnvGuard")
        self.assertIn("results", run)
        self.assertEqual(len(run["results"]), 1)

        sarif_result = run["results"][0]
        self.assertEqual(sarif_result["ruleId"], "R001")
        self.assertEqual(sarif_result["level"], "error")  # critical -> error

    def test_sarif_severity_mapping(self) -> None:
        """Test SARIF severity level mapping."""
        result = ScanResult(
            findings=[
                Finding(rule_id="R1", severity="critical", category="c", description="d", fix_suggestion="f"),
                Finding(rule_id="R2", severity="warning", category="c", description="d", fix_suggestion="f"),
                Finding(rule_id="R3", severity="info", category="c", description="d", fix_suggestion="f"),
            ],
        )
        output = self.reporter.print_result(result)
        data = json.loads(output)
        results = data["runs"][0]["results"]

        levels = {r["ruleId"]: r["level"] for r in results}
        self.assertEqual(levels["R1"], "error")
        self.assertEqual(levels["R2"], "warning")
        self.assertEqual(levels["R3"], "note")

    def test_sarif_empty_result(self) -> None:
        """Test SARIF output for empty results."""
        result = ScanResult()
        output = self.reporter.print_result(result)
        data = json.loads(output)
        self.assertEqual(len(data["runs"][0]["results"]), 0)


class TestReporterMarkdown(unittest.TestCase):
    """Tests for Markdown format output."""

    def setUp(self) -> None:
        """Set up test reporter."""
        self.reporter = Reporter(output_format="markdown", no_color=True)

    def test_markdown_structure(self) -> None:
        """Test Markdown output has correct structure."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R001",
                    severity="critical",
                    category="test_cat",
                    description="Test finding",
                    fix_suggestion="Fix it",
                    key="MY_KEY",
                    source_file=".env",
                    line_number=5,
                ),
            ],
            scanned_files=[".env"],
            total_keys=10,
        )
        output = self.reporter.print_result(result)

        self.assertIn("# EnvGuard", output)
        self.assertIn("## Summary", output)
        self.assertIn("## Findings", output)
        self.assertIn("## Fix Suggestions", output)
        self.assertIn("R001", output)
        self.assertIn("MY_KEY", output)

    def test_markdown_empty_result(self) -> None:
        """Test Markdown output for empty results."""
        result = ScanResult()
        output = self.reporter.print_result(result)
        self.assertIn("No findings detected", output)

    def test_markdown_table_format(self) -> None:
        """Test Markdown table formatting."""
        result = ScanResult(
            findings=[
                Finding(
                    rule_id="R1", severity="warning", category="c",
                    description="Test desc", fix_suggestion="Fix", key="K",
                    source_file=".env", line_number=3,
                ),
            ],
        )
        output = self.reporter.print_result(result)
        self.assertIn("|", output)
        self.assertIn("---", output)


class TestReporterGitDiff(unittest.TestCase):
    """Tests for git diff report output."""

    def setUp(self) -> None:
        """Set up test reporter."""
        self.reporter = Reporter(output_format="table", no_color=True)

    def test_git_diff_empty(self) -> None:
        """Test git diff output for no changes."""
        result = GitDiffResult(from_ref="HEAD~5", to_ref="HEAD")
        output = self.reporter.print_git_diff(result)
        self.assertIn("No environment changes detected", output)

    def test_git_diff_with_changes(self) -> None:
        """Test git diff output with changes."""
        result = GitDiffResult(
            from_ref="main",
            to_ref="feature",
            changes=[
                GitEnvChange(
                    key="NEW_KEY",
                    old_value="",
                    new_value="new_value",
                    change_type="added",
                    commit_hash="abc123",
                ),
                GitEnvChange(
                    key="OLD_KEY",
                    old_value="old_value",
                    new_value="",
                    change_type="removed",
                    commit_hash="def456",
                ),
                GitEnvChange(
                    key="CHANGED_KEY",
                    old_value="old",
                    new_value="new",
                    change_type="modified",
                    commit_hash="ghi789",
                ),
            ],
            files_compared=[".env"],
        )
        output = self.reporter.print_git_diff(result)
        self.assertIn("NEW_KEY", output)
        self.assertIn("OLD_KEY", output)
        self.assertIn("CHANGED_KEY", output)
        self.assertIn("ADDED", output)
        self.assertIn("REMOVED", output)
        self.assertIn("MODIFIED", output)

    def test_git_diff_json(self) -> None:
        """Test git diff JSON output."""
        reporter = Reporter(output_format="json", no_color=True)
        result = GitDiffResult(
            changes=[
                GitEnvChange(
                    key="K", old_value="old", new_value="new",
                    change_type="modified", commit_hash="abc",
                ),
            ],
        )
        output = reporter.print_git_diff(result)
        data = json.loads(output)
        self.assertEqual(data["summary"]["modified"], 1)
        self.assertEqual(len(data["changes"]), 1)

    def test_git_diff_markdown(self) -> None:
        """Test git diff Markdown output."""
        reporter = Reporter(output_format="markdown", no_color=True)
        result = GitDiffResult(
            from_ref="main",
            to_ref="feature",
            changes=[
                GitEnvChange(
                    key="K", old_value="", new_value="v",
                    change_type="added", commit_hash="abc",
                ),
            ],
        )
        output = reporter.print_git_diff(result)
        self.assertIn("# EnvGuard", output)
        self.assertIn("## Summary", output)
        self.assertIn("## Changes", output)


class TestColors(unittest.TestCase):
    """Tests for the Colors utility class."""

    def test_colors_disabled(self) -> None:
        """Test that colors can be disabled."""
        colors = Colors(enabled=False)
        self.assertFalse(colors.enabled)
        self.assertEqual(colors.red("text"), "text")

    def test_style_method(self) -> None:
        """Test the style method."""
        colors = Colors(enabled=True)
        styled = colors.style("text", colors.RED)
        self.assertIn("text", styled)
        self.assertIn("\033[", styled)

    def test_severity_color(self) -> None:
        """Test severity color mapping."""
        colors = Colors(enabled=True)
        self.assertIn("\033[", colors.severity_color("critical"))
        self.assertIn("\033[", colors.severity_color("warning"))
        self.assertIn("\033[", colors.severity_color("info"))

    def test_static_methods(self) -> None:
        """Test static formatting methods."""
        badge = Reporter.format_severity_badge("critical", no_color=True)
        self.assertEqual(badge, "[CRITICAL]")


if __name__ == "__main__":
    unittest.main()
