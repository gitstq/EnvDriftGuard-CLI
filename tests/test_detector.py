"""
Unit tests for the DriftDetector module.

Tests drift detection, rule checking, file comparison,
and scan result handling.
"""

import os
import tempfile
import unittest
from typing import List, Set

from envguard.core.detector import DriftDetector, Finding, ScanResult
from envguard.core.parser import EnvEntry, EnvParser
from envguard.rules.default_rules import Rule, get_all_rules, get_rules_by_category


class TestFinding(unittest.TestCase):
    """Tests for the Finding data class."""

    def test_basic_finding(self) -> None:
        """Test creating a basic Finding."""
        finding = Finding(
            rule_id="TEST001",
            severity="critical",
            category="test",
            description="Test finding",
            fix_suggestion="Fix it",
            key="TEST_KEY",
            value="secret_value",
        )
        self.assertEqual(finding.rule_id, "TEST001")
        self.assertEqual(finding.severity, "critical")
        self.assertEqual(finding.key, "TEST_KEY")

    def test_mask_value(self) -> None:
        """Test value masking for secrets."""
        finding = Finding(
            rule_id="TEST001",
            severity="critical",
            category="test",
            description="Test",
            fix_suggestion="Fix",
            value="my_secret_value",
        )
        d = finding.to_dict()
        # my_secret_value (15 chars) -> my + 11 asterisks + ue
        self.assertEqual(d["value"], "my***********ue")

    def test_mask_short_value(self) -> None:
        """Test value masking for short values."""
        finding = Finding(
            rule_id="TEST001",
            severity="critical",
            category="test",
            description="Test",
            fix_suggestion="Fix",
            value="ab",
        )
        d = finding.to_dict()
        self.assertEqual(d["value"], "****")

    def test_mask_empty_value(self) -> None:
        """Test value masking for empty values."""
        finding = Finding(
            rule_id="TEST001",
            severity="critical",
            category="test",
            description="Test",
            fix_suggestion="Fix",
            value="",
        )
        d = finding.to_dict()
        self.assertEqual(d["value"], "")

    def test_finding_repr(self) -> None:
        """Test string representation of a finding."""
        finding = Finding(
            rule_id="R001",
            severity="warning",
            category="test_cat",
            description="Test description",
            fix_suggestion="Fix it",
            key="MY_KEY",
        )
        repr_str = repr(finding)
        self.assertIn("R001", repr_str)
        self.assertIn("warning", repr_str)
        self.assertIn("MY_KEY", repr_str)


class TestScanResult(unittest.TestCase):
    """Tests for the ScanResult data class."""

    def test_empty_result(self) -> None:
        """Test an empty scan result."""
        result = ScanResult()
        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.critical_count, 0)
        self.assertEqual(result.warning_count, 0)
        self.assertEqual(result.info_count, 0)

    def test_counts(self) -> None:
        """Test finding count properties."""
        result = ScanResult(findings=[
            Finding(rule_id="R1", severity="critical", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R2", severity="critical", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R3", severity="warning", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R4", severity="warning", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R5", severity="warning", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R6", severity="info", category="c", description="d", fix_suggestion="f"),
        ])
        self.assertEqual(result.critical_count, 2)
        self.assertEqual(result.warning_count, 3)
        self.assertEqual(result.info_count, 1)
        self.assertEqual(result.total_count, 6)

    def test_filter_by_severity(self) -> None:
        """Test filtering findings by severity."""
        result = ScanResult(findings=[
            Finding(rule_id="R1", severity="critical", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R2", severity="warning", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R3", severity="info", category="c", description="d", fix_suggestion="f"),
        ])
        critical = result.get_by_severity("critical")
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0].rule_id, "R1")

    def test_filter_by_category(self) -> None:
        """Test filtering findings by category."""
        result = ScanResult(findings=[
            Finding(rule_id="R1", severity="critical", category="missing_keys", description="d", fix_suggestion="f"),
            Finding(rule_id="R2", severity="warning", category="type_mismatch", description="d", fix_suggestion="f"),
        ])
        missing = result.get_by_category("missing_keys")
        self.assertEqual(len(missing), 1)

    def test_has_severity(self) -> None:
        """Test severity level checking."""
        result = ScanResult(findings=[
            Finding(rule_id="R1", severity="critical", category="c", description="d", fix_suggestion="f"),
            Finding(rule_id="R2", severity="info", category="c", description="d", fix_suggestion="f"),
        ])
        self.assertTrue(result.has_severity("critical"))
        self.assertTrue(result.has_severity("warning"))
        self.assertTrue(result.has_severity("info"))
        self.assertFalse(ScanResult().has_severity("critical"))

    def test_to_dict(self) -> None:
        """Test converting scan result to dictionary."""
        result = ScanResult(
            findings=[
                Finding(rule_id="R1", severity="critical", category="c", description="d", fix_suggestion="f", key="K"),
            ],
            scanned_files=[".env"],
            total_keys=5,
            scan_time_ms=10.5,
        )
        d = result.to_dict()
        self.assertIn("summary", d)
        self.assertIn("findings", d)
        self.assertEqual(d["summary"]["total_findings"], 1)
        self.assertEqual(d["summary"]["total_keys"], 5)


class TestRules(unittest.TestCase):
    """Tests for the built-in detection rules."""

    def test_get_all_rules(self) -> None:
        """Test that all rules are loaded."""
        rules = get_all_rules()
        self.assertGreaterEqual(len(rules), 42)

    def test_rule_categories(self) -> None:
        """Test that rules cover all expected categories."""
        rules = get_all_rules()
        categories = {r.category for r in rules}
        expected = {"missing_keys", "type_mismatch", "stale_values", "secrets_leak", "best_practices"}
        self.assertTrue(expected.issubset(categories))

    def test_rule_severities(self) -> None:
        """Test that all rules have valid severities."""
        rules = get_all_rules()
        valid_severities = {"critical", "warning", "info"}
        for rule in rules:
            self.assertIn(rule.severity, valid_severities, f"Invalid severity for {rule.id}")

    def test_rule_ids_unique(self) -> None:
        """Test that all rule IDs are unique."""
        rules = get_all_rules()
        ids = [r.id for r in rules]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate rule IDs found")

    def test_get_rules_by_category(self) -> None:
        """Test filtering rules by category."""
        missing = get_rules_by_category("missing_keys")
        self.assertGreaterEqual(len(missing), 10)

    def test_rule_to_dict(self) -> None:
        """Test converting a rule to dictionary."""
        rules = get_all_rules()
        d = rules[0].to_dict()
        self.assertIn("id", d)
        self.assertIn("severity", d)
        self.assertIn("category", d)
        self.assertIn("description", d)
        self.assertIn("fix_suggestion", d)

    def test_rule_check(self) -> None:
        """Test rule checking with context."""
        rules = get_all_rules()
        for rule in rules:
            # Each rule should have at least an id and check method
            self.assertIsNotNone(rule.id)
            self.assertTrue(hasattr(rule, "check"))


class TestDriftDetector(unittest.TestCase):
    """Tests for the DriftDetector class."""

    def setUp(self) -> None:
        """Set up test detector and temp directory."""
        self.detector = DriftDetector(min_severity="info")
        self.temp_dir = tempfile.mkdtemp()
        self.parser = EnvParser(interpolate=False)

    def tearDown(self) -> None:
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_temp_file(self, filename: str, content: str) -> str:
        """Write content to a temp file.

        Args:
            filename: The name of the temp file.
            content: The file content.

        Returns:
            The absolute path to the temp file.
        """
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_scan_simple_env(self) -> None:
        """Test scanning a simple .env file."""
        content = "DATABASE_URL=postgres://localhost/db\nPORT=8080\nDEBUG=true\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        self.assertIsInstance(result, ScanResult)
        self.assertGreater(result.total_keys, 0)

    def test_scan_detects_debug_enabled(self) -> None:
        """Test that DEBUG=true is detected as a best practice violation."""
        content = "DEBUG=true\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        debug_findings = [f for f in result.findings if f.key == "DEBUG"]
        self.assertTrue(any(f.rule_id == "BEST007" for f in debug_findings))

    def test_scan_detects_empty_required_keys(self) -> None:
        """Test that empty required keys are detected."""
        content = "DATABASE_URL=\nAPI_KEY=\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        empty_findings = [f for f in result.findings if f.rule_id == "BEST004"]
        self.assertGreater(len(empty_findings), 0)

    def test_scan_detects_naming_convention(self) -> None:
        """Test that non-snake-case keys are detected."""
        content = "myKey=value\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        naming_findings = [f for f in result.findings if f.rule_id == "BEST002"]
        self.assertGreater(len(naming_findings), 0)

    def test_scan_detects_default_password(self) -> None:
        """Test that default passwords are detected."""
        content = "DB_PASSWORD=admin\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        password_findings = [f for f in result.findings if f.rule_id == "BEST001"]
        self.assertGreater(len(password_findings), 0)

    def test_scan_detects_placeholder_values(self) -> None:
        """Test that placeholder values are detected."""
        content = "API_KEY=changeme\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        placeholder_findings = [f for f in result.findings if f.rule_id == "STALE005"]
        self.assertGreater(len(placeholder_findings), 0)

    def test_scan_detects_duplicate_keys(self) -> None:
        """Test that duplicate keys are detected."""
        content = "KEY=value1\nKEY=value2\n"
        entries = self.parser._parse_env_content(content)
        result = self.detector.scan_entries(entries)
        dup_findings = [f for f in result.findings if f.rule_id == "BEST003"]
        self.assertGreater(len(dup_findings), 0)

    def test_ignore_keys(self) -> None:
        """Test that ignored keys are skipped."""
        content = "DEBUG=true\nIGNORED_KEY=value\n"
        filepath = self._write_temp_file(".env", content)
        detector = DriftDetector(ignore_keys={"DEBUG"}, min_severity="info")
        result = detector.scan_file(filepath)
        debug_findings = [f for f in result.findings if f.key == "DEBUG"]
        self.assertEqual(len(debug_findings), 0)

    def test_min_severity_filter(self) -> None:
        """Test that minimum severity filter works."""
        content = "DEBUG=true\nAPP_NAME=test\n"
        filepath = self._write_temp_file(".env", content)
        detector = DriftDetector(min_severity="critical")
        result = detector.scan_file(filepath)
        for finding in result.findings:
            self.assertEqual(finding.severity, "critical")

    def test_compare_files(self) -> None:
        """Test comparing two env files."""
        content_a = "KEY1=value1\nKEY2=value2\nKEY3=value3\n"
        content_b = "KEY1=value1\nKEY2=changed\nKEY4=value4\n"

        filepath_a = self._write_temp_file(".env.a", content_a)
        filepath_b = self._write_temp_file(".env.b", content_b)

        result = self.detector.compare_files(filepath_a, filepath_b)
        self.assertGreater(result.total_count, 0)

        # Check for different values (DIFF003)
        modified = [f for f in result.findings if f.rule_id == "DIFF003"]
        self.assertGreater(len(modified), 0)

        # Check for keys only in one file
        added = [f for f in result.findings if f.rule_id == "DIFF002"]
        removed = [f for f in result.findings if f.rule_id == "DIFF001"]
        self.assertGreater(len(added), 0)
        self.assertGreater(len(removed), 0)

    def test_compare_identical_files(self) -> None:
        """Test comparing identical files produces no findings."""
        content = "KEY1=value1\nKEY2=value2\n"
        filepath_a = self._write_temp_file(".env.a", content)
        filepath_b = self._write_temp_file(".env.b", content)

        result = self.detector.compare_files(filepath_a, filepath_b)
        self.assertEqual(result.total_count, 0)

    def test_scan_with_template(self) -> None:
        """Test scanning with a template file for missing key detection."""
        template_content = "DATABASE_URL=\nAPI_KEY=\nSECRET_KEY=\n"
        local_content = "DATABASE_URL=postgres://localhost/db\n"

        template_path = self._write_temp_file(".env.example", template_content)
        local_path = self._write_temp_file(".env", local_content)

        result = self.detector.scan_file(local_path, template_path)
        missing_findings = [f for f in result.findings if f.rule_id == "MISS004"]
        self.assertGreater(len(missing_findings), 0)

    def test_scan_secrets_in_non_secret_file(self) -> None:
        """Test that secrets in .env.example are detected."""
        content = "API_KEY=sk_live_abcdef1234567890\n"
        filepath = self._write_temp_file(".env.example", content)
        result = self.detector.scan_file(filepath)
        secret_findings = [f for f in result.findings if f.category == "secrets_leak"]
        self.assertGreater(len(secret_findings), 0)

    def test_scan_no_false_positives_for_secrets_in_secret_file(self) -> None:
        """Test that secrets in .env files are NOT flagged as leaks."""
        content = "API_KEY=sk_live_abcdef1234567890\nPASSWORD=mypassword\n"
        filepath = self._write_temp_file(".env", content)
        result = self.detector.scan_file(filepath)
        secret_findings = [f for f in result.findings if f.category == "secrets_leak"]
        self.assertEqual(len(secret_findings), 0)

    def test_scan_multiple_files(self) -> None:
        """Test scanning multiple files."""
        content1 = "KEY1=val1\n"
        content2 = "KEY2=val2\n"
        filepath1 = self._write_temp_file(".env", content1)
        filepath2 = self._write_temp_file("config.json", '{"KEY2": "val2"}')

        result = self.detector.scan_files([filepath1, filepath2])
        self.assertEqual(result.total_keys, 2)

    def test_scan_nonexistent_file(self) -> None:
        """Test scanning a nonexistent file returns an error finding."""
        result = self.detector.scan_files(["/nonexistent/.env"])
        self.assertGreater(result.total_count, 0)
        error_findings = [f for f in result.findings if f.rule_id == "SCAN001"]
        self.assertGreater(len(error_findings), 0)


if __name__ == "__main__":
    unittest.main()
