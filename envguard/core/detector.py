"""
Drift detection engine for EnvGuard-CLI.

Compares environment configurations against rules, templates, and
best practices to detect configuration drift, missing keys,
type mismatches, stale values, and secrets leaks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from envguard.core.parser import EnvEntry, EnvParser
from envguard.rules.default_rules import Rule, get_all_rules


@dataclass
class Finding:
    """Represents a single detection finding.

    Attributes:
        rule_id: The ID of the rule that was violated.
        severity: The severity level of the finding.
        category: The category of the finding.
        description: Human-readable description of the finding.
        fix_suggestion: Suggested fix for the issue.
        key: The environment key that triggered the finding.
        value: The value of the key (masked if it is a secret).
        source_file: The file where the finding was detected.
        line_number: The line number in the source file.
        extra: Additional metadata about the finding.
    """

    rule_id: str
    severity: str
    category: str
    description: str
    fix_suggestion: str
    key: str = ""
    value: str = ""
    source_file: str = ""
    line_number: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the finding to a dictionary.

        Returns:
            A dictionary representation of the finding.
        """
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "fix_suggestion": self.fix_suggestion,
            "key": self.key,
            "value": self._mask_value(self.value),
            "source_file": self.source_file,
            "line_number": self.line_number,
        }

    @staticmethod
    def _mask_value(value: str) -> str:
        """Mask a secret value for safe display.

        Shows only the first and last characters, replacing the rest
        with asterisks.

        Args:
            value: The value to mask.

        Returns:
            The masked value string.
        """
        if not value:
            return ""
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    def __repr__(self) -> str:
        """Return a string representation of the finding.

        Returns:
            A string representation.
        """
        return (
            f"Finding({self.rule_id} [{self.severity}] {self.key}: "
            f"{self.description})"
        )


@dataclass
class ScanResult:
    """Represents the complete result of a drift detection scan.

    Attributes:
        findings: List of all findings from the scan.
        scanned_files: List of files that were scanned.
        total_keys: Total number of keys examined.
        scan_time_ms: Time taken to perform the scan in milliseconds.
    """

    findings: List[Finding] = field(default_factory=list)
    scanned_files: List[str] = field(default_factory=list)
    total_keys: int = 0
    scan_time_ms: float = 0.0

    @property
    def critical_count(self) -> int:
        """Get the number of critical findings.

        Returns:
            The count of critical findings.
        """
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def warning_count(self) -> int:
        """Get the number of warning findings.

        Returns:
            The count of warning findings.
        """
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        """Get the number of info findings.

        Returns:
            The count of info findings.
        """
        return sum(1 for f in self.findings if f.severity == "info")

    @property
    def total_count(self) -> int:
        """Get the total number of findings.

        Returns:
            The total count of findings.
        """
        return len(self.findings)

    def get_by_severity(self, severity: str) -> List[Finding]:
        """Get findings filtered by severity level.

        Args:
            severity: The severity level to filter by.

        Returns:
            A list of findings matching the severity.
        """
        return [f for f in self.findings if f.severity == severity]

    def get_by_category(self, category: str) -> List[Finding]:
        """Get findings filtered by category.

        Args:
            category: The category to filter by.

        Returns:
            A list of findings matching the category.
        """
        return [f for f in self.findings if f.category == category]

    def get_by_key(self, key: str) -> List[Finding]:
        """Get findings for a specific key.

        Args:
            key: The key to filter by.

        Returns:
            A list of findings for the key.
        """
        return [f for f in self.findings if f.key == key]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scan result to a dictionary.

        Returns:
            A dictionary representation of the scan result.
        """
        return {
            "summary": {
                "total_findings": self.total_count,
                "critical": self.critical_count,
                "warning": self.warning_count,
                "info": self.info_count,
                "total_keys": self.total_keys,
                "scanned_files": self.scanned_files,
                "scan_time_ms": round(self.scan_time_ms, 2),
            },
            "findings": [f.to_dict() for f in self.findings],
        }

    def has_severity(self, min_severity: str) -> bool:
        """Check if the result has findings at or above a severity level.

        Args:
            min_severity: The minimum severity to check for.

        Returns:
            True if findings exist at or above the severity level.
        """
        severity_order = {"info": 0, "warning": 1, "critical": 2}
        min_level = severity_order.get(min_severity.lower(), 0)
        for finding in self.findings:
            finding_level = severity_order.get(finding.severity, 0)
            if finding_level >= min_level:
                return True
        return False


class DriftDetector:
    """Environment configuration drift detection engine.

    Compares parsed environment entries against built-in rules to
    detect configuration drift, missing keys, type mismatches,
    stale values, and secrets leaks.

    Usage:
        detector = DriftDetector()
        result = detector.scan_entries(entries)
        for finding in result.findings:
            print(finding)
    """

    def __init__(
        self,
        rules: Optional[List[Rule]] = None,
        ignore_keys: Optional[Set[str]] = None,
        min_severity: str = "info",
    ) -> None:
        """Initialize the DriftDetector.

        Args:
            rules: Optional list of rules to use. If None, uses all
                   built-in rules.
            ignore_keys: Optional set of key names to ignore.
            min_severity: Minimum severity level to report.
        """
        self._rules = rules or get_all_rules()
        self._ignore_keys = ignore_keys or set()
        self._min_severity = min_severity
        self._severity_order = {"info": 0, "warning": 1, "critical": 2}

    @property
    def rules(self) -> List[Rule]:
        """Get the active rules.

        Returns:
            The list of active rules.
        """
        return self._rules

    @property
    def ignore_keys(self) -> Set[str]:
        """Get the ignored keys.

        Returns:
            The set of ignored key names.
        """
        return self._ignore_keys

    def scan_entries(
        self,
        entries: List[EnvEntry],
        template_entries: Optional[List[EnvEntry]] = None,
        is_secret_file: bool = True,
    ) -> ScanResult:
        """Scan a list of environment entries for drift and violations.

        Args:
            entries: The list of EnvEntry objects to scan.
            template_entries: Optional template entries for comparison.
            is_secret_file: Whether the entries come from a secret file.

        Returns:
            A ScanResult containing all findings.
        """
        import time

        start_time = time.time()
        findings: List[Finding] = []
        scanned_files: Set[str] = set()

        # Build lookup structures
        entry_map: Dict[str, EnvEntry] = {}
        key_counts: Dict[str, int] = {}
        for entry in entries:
            entry_map[entry.key] = entry
            key_counts[entry.key] = key_counts.get(entry.key, 0) + 1
            if entry.source_file:
                scanned_files.add(entry.source_file)

        # Build template lookup
        template_map: Dict[str, EnvEntry] = {}
        if template_entries:
            for entry in template_entries:
                template_map[entry.key] = entry

        # Check for missing keys (template vs local)
        if template_entries:
            findings.extend(self._check_missing_keys(entries, template_entries))

        # Check each entry against all rules
        for entry in entries:
            if entry.key in self._ignore_keys:
                continue

            entry_findings = self._check_entry(entry, entry_map, key_counts, is_secret_file)
            findings.extend(entry_findings)

        end_time = time.time()

        return ScanResult(
            findings=findings,
            scanned_files=sorted(scanned_files),
            total_keys=len(entries),
            scan_time_ms=(end_time - start_time) * 1000,
        )

    def scan_file(
        self,
        filepath: str,
        template_path: Optional[str] = None,
    ) -> ScanResult:
        """Scan a single environment file for drift and violations.

        Args:
            filepath: The path to the environment file to scan.
            template_path: Optional path to a template file for comparison.

        Returns:
            A ScanResult containing all findings.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        parser = EnvParser()
        entries = parser.parse_file(filepath)

        template_entries: Optional[List[EnvEntry]] = None
        if template_path:
            template_entries = parser.parse_file(template_path)

        is_secret = self._is_secret_file(filepath)

        return self.scan_entries(entries, template_entries, is_secret)

    def scan_files(
        self,
        filepaths: List[str],
        template_path: Optional[str] = None,
    ) -> ScanResult:
        """Scan multiple environment files and merge results.

        Args:
            filepaths: A list of paths to environment files.
            template_path: Optional path to a template file.

        Returns:
            A ScanResult containing all findings from all files.
        """
        import time

        start_time = time.time()
        all_findings: List[Finding] = []
        all_scanned_files: Set[str] = set()
        total_keys = 0

        parser = EnvParser()
        template_entries: Optional[List[EnvEntry]] = None
        if template_path:
            template_entries = parser.parse_file(template_path)

        for filepath in filepaths:
            try:
                entries = parser.parse_file(filepath)
                is_secret = self._is_secret_file(filepath)
                result = self.scan_entries(entries, template_entries, is_secret)
                all_findings.extend(result.findings)
                all_scanned_files.update(result.scanned_files)
                total_keys += result.total_keys
            except (FileNotFoundError, OSError) as e:
                all_findings.append(Finding(
                    rule_id="SCAN001",
                    severity="warning",
                    category="scan_error",
                    description=f"Could not scan file: {e}",
                    fix_suggestion="Ensure the file exists and is readable",
                    source_file=filepath,
                ))

        end_time = time.time()

        return ScanResult(
            findings=all_findings,
            scanned_files=sorted(all_scanned_files),
            total_keys=total_keys,
            scan_time_ms=(end_time - start_time) * 1000,
        )

    def compare_entries(
        self,
        entries_a: List[EnvEntry],
        entries_b: List[EnvEntry],
        label_a: str = "File A",
        label_b: str = "File B",
    ) -> ScanResult:
        """Compare two sets of environment entries and report differences.

        Args:
            entries_a: The first set of entries.
            entries_b: The second set of entries.
            label_a: Label for the first set.
            label_b: Label for the second set.

        Returns:
            A ScanResult with comparison findings.
        """
        import time

        start_time = time.time()
        findings: List[Finding] = []

        map_a: Dict[str, EnvEntry] = {e.key: e for e in entries_a}
        map_b: Dict[str, EnvEntry] = {e.key: e for e in entries_b}

        keys_a: Set[str] = set(map_a.keys())
        keys_b: Set[str] = set(map_b.keys())

        # Keys only in A
        for key in sorted(keys_a - keys_b):
            entry = map_a[key]
            findings.append(Finding(
                rule_id="DIFF001",
                severity="info",
                category="comparison",
                description=f"Key '{key}' exists in {label_a} but not in {label_b}",
                fix_suggestion=f"Add '{key}' to {label_b} or remove from {label_a}",
                key=key,
                value=entry.value,
                source_file=entry.source_file,
                line_number=entry.line_number,
            ))

        # Keys only in B
        for key in sorted(keys_b - keys_a):
            entry = map_b[key]
            findings.append(Finding(
                rule_id="DIFF002",
                severity="info",
                category="comparison",
                description=f"Key '{key}' exists in {label_b} but not in {label_a}",
                fix_suggestion=f"Add '{key}' to {label_a} or remove from {label_b}",
                key=key,
                value=entry.value,
                source_file=entry.source_file,
                line_number=entry.line_number,
            ))

        # Keys in both but with different values
        for key in sorted(keys_a & keys_b):
            entry_a = map_a[key]
            entry_b = map_b[key]
            if entry_a.value != entry_b.value:
                severity = "warning"
                # Upgrade severity if the difference involves secrets
                if entry_a.is_secret or entry_b.is_secret:
                    severity = "critical"
                findings.append(Finding(
                    rule_id="DIFF003",
                    severity=severity,
                    category="comparison",
                    description=f"Key '{key}' has different values between {label_a} and {label_b}",
                    fix_suggestion=f"Ensure '{key}' is consistent across both files",
                    key=key,
                    value=entry_a.value,
                    source_file=entry_a.source_file,
                    line_number=entry_a.line_number,
                    extra={
                        "value_a": entry_a.value,
                        "value_b": entry_b.value,
                        "file_a": entry_a.source_file,
                        "file_b": entry_b.source_file,
                    },
                ))

        end_time = time.time()

        return ScanResult(
            findings=findings,
            scanned_files=sorted(set(
                [e.source_file for e in entries_a + entries_b if e.source_file]
            )),
            total_keys=len(keys_a | keys_b),
            scan_time_ms=(end_time - start_time) * 1000,
        )

    def compare_files(self, file_a: str, file_b: str) -> ScanResult:
        """Compare two environment files and report differences.

        Args:
            file_a: Path to the first file.
            file_b: Path to the second file.

        Returns:
            A ScanResult with comparison findings.
        """
        parser = EnvParser()
        entries_a = parser.parse_file(file_a)
        entries_b = parser.parse_file(file_b)

        label_a = file_a
        label_b = file_b

        return self.compare_entries(entries_a, entries_b, label_a, label_b)

    def _check_missing_keys(
        self,
        entries: List[EnvEntry],
        template_entries: List[EnvEntry],
    ) -> List[Finding]:
        """Check for missing keys between entries and template.

        Args:
            entries: The local environment entries.
            template_entries: The template entries.

        Returns:
            A list of findings for missing keys.
        """
        findings: List[Finding] = []

        entry_keys: Set[str] = {e.key for e in entries}
        template_keys: Set[str] = {e.key for e in template_entries}

        # Keys in template but missing in local
        for template_entry in template_entries:
            if template_entry.key not in entry_keys:
                if template_entry.key in self._ignore_keys:
                    continue
                findings.append(Finding(
                    rule_id="MISS004",
                    severity="warning",
                    category="missing_keys",
                    description=f"Key '{template_entry.key}' is defined in template but missing in local environment",
                    fix_suggestion=f"Add '{template_entry.key}' to your local environment file",
                    key=template_entry.key,
                    value="",
                    source_file=template_entry.source_file,
                    line_number=template_entry.line_number,
                ))

        # Keys in local but missing in template
        for entry in entries:
            if entry.key not in template_keys:
                if entry.key in self._ignore_keys:
                    continue
                findings.append(Finding(
                    rule_id="MISS005",
                    severity="info",
                    category="missing_keys",
                    description=f"Key '{entry.key}' exists locally but is not defined in template",
                    fix_suggestion=f"Consider adding '{entry.key}' to the template file",
                    key=entry.key,
                    value=entry.value,
                    source_file=entry.source_file,
                    line_number=entry.line_number,
                ))

        return findings

    def _check_entry(
        self,
        entry: EnvEntry,
        entry_map: Dict[str, EnvEntry],
        key_counts: Dict[str, int],
        is_secret_file: bool,
    ) -> List[Finding]:
        """Check a single entry against all applicable rules.

        Args:
            entry: The entry to check.
            entry_map: Map of all entries for cross-referencing.
            key_counts: Count of each key for duplicate detection.
            is_secret_file: Whether the entry comes from a secret file.

        Returns:
            A list of findings for this entry.
        """
        findings: List[Finding] = []

        # Build context for rule checks
        context: Dict[str, Any] = {
            "key": entry.key,
            "value": entry.value,
            "data_type": entry.data_type,
            "line_number": entry.line_number,
            "source_file": entry.source_file,
            "is_secret": entry.is_secret,
            "is_secret_file": is_secret_file,
            "is_quoted": entry.is_quoted,
            "comment": entry.comment,
            "is_duplicate": key_counts.get(entry.key, 0) > 1,
            "is_important": self._is_important_key(entry.key),
            "is_missing": False,
            "is_missing_in_local": False,
            "is_missing_in_template": False,
        }

        # Check against all rules
        for rule in self._rules:
            # Skip if below minimum severity
            rule_level = self._severity_order.get(rule.severity, 0)
            min_level = self._severity_order.get(self._min_severity, 0)
            if rule_level < min_level:
                continue

            # Skip missing-key rules for non-missing entries
            if rule.category == "missing_keys" and not context.get("is_missing"):
                # Only apply missing key rules through _check_missing_keys
                continue

            # Skip comparison rules
            if rule.category == "comparison":
                continue

            # Skip secrets leak rules for secret files (expected to have secrets)
            if rule.category == "secrets_leak" and is_secret_file:
                continue

            try:
                if rule.check(context):
                    finding = Finding(
                        rule_id=rule.id,
                        severity=rule.severity,
                        category=rule.category,
                        description=rule.description,
                        fix_suggestion=rule.fix_suggestion,
                        key=entry.key,
                        value=entry.value,
                        source_file=entry.source_file,
                        line_number=entry.line_number,
                    )
                    findings.append(finding)
            except Exception:
                # Skip rules that raise errors during checking
                continue

        return findings

    @staticmethod
    def _is_secret_file(filepath: str) -> bool:
        """Determine if a file is a secret-containing file.

        Args:
            filepath: The path to the file.

        Returns:
            True if the file is a secret file.
        """
        import os
        basename = os.path.basename(filepath)
        non_secret_suffixes = (".example", ".sample", ".template", ".defaults")
        if basename.startswith(".env"):
            for suffix in non_secret_suffixes:
                if basename.endswith(suffix):
                    return False
            return True
        return False

    @staticmethod
    def _is_important_key(key: str) -> bool:
        """Determine if a key is important enough to warrant documentation.

        Args:
            key: The key name.

        Returns:
            True if the key is important.
        """
        import re
        important_patterns = (
            r"(URL|URI|ENDPOINT|HOST|PORT|DATABASE|KEY|SECRET|TOKEN|PASSWORD)",
            r"(API|AUTH|CERT|SSL|TLS|ENCRYPTION|SIGNING)",
            r"(REDIS|MONGO|POSTGRES|MYSQL|AMQP|RABBITMQ|KAFKA)",
        )
        for pattern in important_patterns:
            if re.search(pattern, key, re.IGNORECASE):
                return True
        return False
