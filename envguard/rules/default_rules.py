"""
Built-in detection rules for EnvGuard-CLI.

Contains 42 rules across 5 categories:
- Missing Keys (10 rules)
- Type Mismatch (8 rules)
- Stale Values (8 rules)
- Secrets Leak (8 rules)
- Best Practices (8 rules)

Each rule has a unique ID, severity level, category, description,
and fix suggestion.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Pattern
import re


@dataclass
class Rule:
    """Represents a single detection rule.

    Attributes:
        id: Unique rule identifier (e.g., 'MISS001').
        severity: Severity level ('critical', 'warning', 'info').
        category: Rule category string.
        description: Human-readable description of what the rule checks.
        fix_suggestion: Suggested fix for the detected issue.
        key_pattern: Optional regex pattern for key names to match.
        value_pattern: Optional regex pattern for values to match.
        check_func: Optional custom check function.
    """

    id: str
    severity: str
    category: str
    description: str
    fix_suggestion: str
    key_pattern: Optional[str] = None
    value_pattern: Optional[str] = None
    check_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    _compiled_key_pattern: Optional[Pattern] = field(init=False, repr=False, default=None)
    _compiled_value_pattern: Optional[Pattern] = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        """Compile regex patterns after initialization."""
        if self.key_pattern:
            self._compiled_key_pattern = re.compile(self.key_pattern, re.IGNORECASE)
        if self.value_pattern:
            self._compiled_value_pattern = re.compile(self.value_pattern, re.IGNORECASE)

    def matches_key(self, key: str) -> bool:
        """Check if a key matches this rule's key pattern.

        Args:
            key: The key name to check.

        Returns:
            True if the key matches the pattern, False otherwise.
        """
        if self._compiled_key_pattern is None:
            return True
        return bool(self._compiled_key_pattern.search(key))

    def matches_value(self, value: str) -> bool:
        """Check if a value matches this rule's value pattern.

        Args:
            value: The value string to check.

        Returns:
            True if the value matches the pattern, False otherwise.
        """
        if self._compiled_value_pattern is None:
            return True
        return bool(self._compiled_value_pattern.search(value))

    def check(self, context: Dict[str, Any]) -> bool:
        """Run the rule check against a context dictionary.

        If a custom check function is defined, it is used.
        Otherwise, key and value patterns are checked.

        Args:
            context: A dictionary containing 'key', 'value', and
                     other optional fields.

        Returns:
            True if the rule is violated, False otherwise.
        """
        if self.check_func:
            return self.check_func(context)

        key = context.get("key", "")
        value = context.get("value", "")

        if not self.matches_key(key):
            return False
        if not self.matches_value(value):
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the rule to a dictionary.

        Returns:
            A dictionary representation of the rule.
        """
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "fix_suggestion": self.fix_suggestion,
        }


def get_all_rules() -> List[Rule]:
    """Get all built-in detection rules.

    Returns:
        A list of all Rule objects.
    """
    rules: List[Rule] = []

    # =========================================================================
    # MISSING KEYS (10 rules)
    # =========================================================================

    rules.append(Rule(
        id="MISS001",
        severity="critical",
        category="missing_keys",
        description="Required DATABASE_URL is missing from local environment",
        fix_suggestion="Add DATABASE_URL to your .env file with the correct connection string",
        key_pattern=r"DATABASE_URL",
        check_func=lambda ctx: (
            ctx.get("is_missing", False)
            and ctx.get("key", "") == "DATABASE_URL"
        ),
    ))

    rules.append(Rule(
        id="MISS002",
        severity="critical",
        category="missing_keys",
        description="Required SECRET_KEY is missing from local environment",
        fix_suggestion="Generate a secure SECRET_KEY and add it to your .env file",
        key_pattern=r"SECRET_KEY",
        check_func=lambda ctx: (
            ctx.get("is_missing", False)
            and ctx.get("key", "") == "SECRET_KEY"
        ),
    ))

    rules.append(Rule(
        id="MISS003",
        severity="critical",
        category="missing_keys",
        description="Required API_KEY is missing from local environment",
        fix_suggestion="Add the required API_KEY to your .env file",
        key_pattern=r"API_KEY",
        check_func=lambda ctx: (
            ctx.get("is_missing", False)
            and "API_KEY" in ctx.get("key", "")
        ),
    ))

    rules.append(Rule(
        id="MISS004",
        severity="warning",
        category="missing_keys",
        description="Key present in template but missing in local environment",
        fix_suggestion="Add the missing key to your local .env file with an appropriate value",
        check_func=lambda ctx: ctx.get("is_missing_in_local", False),
    ))

    rules.append(Rule(
        id="MISS005",
        severity="warning",
        category="missing_keys",
        description="Key present in local but missing in template file",
        fix_suggestion="Add the key to your .env.example template so team members are aware of it",
        check_func=lambda ctx: ctx.get("is_missing_in_template", False),
    ))

    rules.append(Rule(
        id="MISS006",
        severity="critical",
        category="missing_keys",
        description="Required HOST/PORT configuration is missing",
        fix_suggestion="Add HOST and PORT settings to your environment configuration",
        key_pattern=r"(^HOST$|^PORT$)",
        check_func=lambda ctx: (
            ctx.get("is_missing", False)
            and ctx.get("key", "") in ("HOST", "PORT")
        ),
    ))

    rules.append(Rule(
        id="MISS007",
        severity="warning",
        category="missing_keys",
        description="Environment-specific key missing (e.g., NODE_ENV, APP_ENV)",
        fix_suggestion="Set APP_ENV or NODE_ENV to indicate the current environment",
        key_pattern=r"(APP_ENV|NODE_ENV|RACK_ENV|DJANGO_SETTINGS_MODULE)",
        check_func=lambda ctx: ctx.get("is_missing", False),
    ))

    rules.append(Rule(
        id="MISS008",
        severity="warning",
        category="missing_keys",
        description="Logging configuration key is missing",
        fix_suggestion="Add LOG_LEVEL to control application logging verbosity",
        key_pattern=r"LOG_LEVEL",
        check_func=lambda ctx: ctx.get("is_missing", False),
    ))

    rules.append(Rule(
        id="MISS009",
        severity="info",
        category="missing_keys",
        description="Optional feature flag key is missing",
        fix_suggestion="Consider adding the feature flag to enable/disable this feature",
        key_pattern=r"FEATURE_.*_ENABLED",
        check_func=lambda ctx: ctx.get("is_missing", False),
    ))

    rules.append(Rule(
        id="MISS010",
        severity="warning",
        category="missing_keys",
        description="Timezone configuration is missing",
        fix_suggestion="Set TZ or TIMEZONE to ensure consistent datetime handling",
        key_pattern=r"(TZ$|TIMEZONE$)",
        check_func=lambda ctx: ctx.get("is_missing", False),
    ))

    # =========================================================================
    # TYPE MISMATCH (8 rules)
    # =========================================================================

    rules.append(Rule(
        id="TYPE001",
        severity="warning",
        category="type_mismatch",
        description="PORT value should be an integer",
        fix_suggestion="Set PORT to a numeric value (e.g., PORT=8080)",
        key_pattern=r"PORT",
        check_func=lambda ctx: (
            ctx.get("key", "") == "PORT"
            and ctx.get("data_type", "") != "integer"
            and ctx.get("value", "") != ""
        ),
    ))

    rules.append(Rule(
        id="TYPE002",
        severity="warning",
        category="type_mismatch",
        description="DEBUG/ENABLED flag should be a boolean value",
        fix_suggestion="Set DEBUG to true/false, yes/no, or 1/0",
        key_pattern=r"(DEBUG|ENABLED|DISABLED)",
        check_func=lambda ctx: (
            bool(re.search(r"(DEBUG|ENABLED|DISABLED)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("data_type", "") not in ("boolean", "empty")
            and ctx.get("value", "") != ""
        ),
    ))

    rules.append(Rule(
        id="TYPE003",
        severity="warning",
        category="type_mismatch",
        description="URL value does not match expected URL format",
        fix_suggestion="Ensure the value is a valid URL starting with http://, https://, or another protocol",
        key_pattern=r"(URL|URI|ENDPOINT|HOST)",
        check_func=lambda ctx: (
            bool(re.search(r"(URL|URI|ENDPOINT|HOST)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("data_type", "") not in ("url", "empty")
            and ctx.get("value", "") != ""
            and not ctx.get("value", "").startswith(("${", "$"))
        ),
    ))

    rules.append(Rule(
        id="TYPE004",
        severity="warning",
        category="type_mismatch",
        description="Email value does not match expected email format",
        fix_suggestion="Provide a valid email address (e.g., user@example.com)",
        key_pattern=r"(EMAIL|MAIL_FROM|MAIL_TO|ADMIN_EMAIL|NOTIFY_EMAIL)",
        check_func=lambda ctx: (
            bool(re.search(r"(EMAIL|MAIL|ADMIN_EMAIL|NOTIFY_EMAIL)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("data_type", "") not in ("email", "empty")
            and ctx.get("value", "") != ""
        ),
    ))

    rules.append(Rule(
        id="TYPE005",
        severity="info",
        category="type_mismatch",
        description="JSON value does not appear to be valid JSON",
        fix_suggestion="Ensure the value is valid JSON (properly formatted objects or arrays)",
        key_pattern=r"(CONFIG|SETTINGS|OPTIONS|EXTRA|METADATA|HEADERS)",
        check_func=lambda ctx: (
            bool(re.search(r"(CONFIG|SETTINGS|OPTIONS|EXTRA|METADATA|HEADERS)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("data_type", "") not in ("json", "empty")
            and ctx.get("value", "") != ""
            and len(ctx.get("value", "")) > 1
            and ctx.get("value", "").startswith(("{", "["))
        ),
    ))

    rules.append(Rule(
        id="TYPE006",
        severity="warning",
        category="type_mismatch",
        description="Numeric value expected but non-numeric value found",
        fix_suggestion="Set the value to a valid number (integer or float)",
        key_pattern=r"(TIMEOUT|TTL|MAX_.*_SIZE|LIMIT|RETRY|EXPIRY|DURATION|INTERVAL)",
        check_func=lambda ctx: (
            bool(re.search(r"(TIMEOUT|TTL|MAX_|LIMIT|RETRY|EXPIRY|DURATION|INTERVAL)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("data_type", "") not in ("integer", "float", "empty")
            and ctx.get("value", "") != ""
        ),
    ))

    rules.append(Rule(
        id="TYPE007",
        severity="info",
        category="type_mismatch",
        description="Comma-separated list expected but value format is unusual",
        fix_suggestion="Use comma-separated values for list-type configuration",
        key_pattern=r"(ALLOWED_ORIGINS|CORS|WHITELIST|BLACKLIST|ALLOWED_HOSTS)",
        check_func=lambda ctx: (
            bool(re.search(r"(ALLOWED_ORIGINS|CORS|WHITELIST|BLACKLIST|ALLOWED_HOSTS)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("value", "") != ""
            and "," not in ctx.get("value", "")
            and ctx.get("data_type", "") not in ("json", "empty")
        ),
    ))

    rules.append(Rule(
        id="TYPE008",
        severity="warning",
        category="type_mismatch",
        description="Path value does not look like a valid file system path",
        fix_suggestion="Provide a valid file system path (absolute or relative)",
        key_pattern=r"(PATH|DIR|DIRECTORY|FOLDER|FILE|ROOT)",
        check_func=lambda ctx: (
            bool(re.search(r"(PATH|DIR|DIRECTORY|FOLDER|FILE|ROOT)", ctx.get("key", ""), re.IGNORECASE))
            and ctx.get("value", "") != ""
            and ctx.get("data_type", "") not in ("url", "empty")
            and not ctx.get("value", "").startswith(("/", "./", "../", "~", "${", "$"))
            and not ctx.get("value", "").startswith(("C:", "D:", "E:"))
        ),
    ))

    # =========================================================================
    # STALE VALUES (8 rules)
    # =========================================================================

    rules.append(Rule(
        id="STALE001",
        severity="warning",
        category="stale_values",
        description="Version string appears outdated (contains 'old' version patterns)",
        fix_suggestion="Update the version to the latest stable release",
        key_pattern=r"(VERSION|APP_VERSION|API_VERSION)",
        value_pattern=r"(0\.\d+\.\d+|1\.0\.0|v0\.|alpha|beta|rc\d)",
    ))

    rules.append(Rule(
        id="STALE002",
        severity="critical",
        category="stale_values",
        description="Date value appears to be in the past (possibly expired)",
        fix_suggestion="Update the date or renew the associated certificate/token",
        key_pattern=r"(EXPIR|EXPIRY|VALID_UNTIL|NOT_AFTER|CERT_EXPIRY)",
        check_func=lambda ctx: _check_expired_date(ctx),
    ))

    rules.append(Rule(
        id="STALE003",
        severity="warning",
        category="stale_values",
        description="Deprecated key name detected",
        fix_suggestion="Rename the key to the current naming convention",
        key_pattern=r"(OLD_|DEPRECATED_|LEGACY_|UNUSED_|BACKUP_)",
    ))

    rules.append(Rule(
        id="STALE004",
        severity="warning",
        category="stale_values",
        description="Domain value references old/deprecated domain",
        fix_suggestion="Update the domain to the current production domain",
        value_pattern=r"(localhost|127\.0\.0\.1|0\.0\.0\.0|example\.com|test\.com|myapp\.herokuapp\.com)",
        key_pattern=r"(DOMAIN|HOST|URL|SITE|ENDPOINT|SERVER)",
    ))

    rules.append(Rule(
        id="STALE005",
        severity="info",
        category="stale_values",
        description="Value contains 'changeme' or 'todo' placeholder",
        fix_suggestion="Replace the placeholder with an actual value",
        value_pattern=r"(changeme|change.me|todo|fixme|xxx|placeholder|dummy|sample|test_value|YOUR_.*_HERE)",
    ))

    rules.append(Rule(
        id="STALE006",
        severity="warning",
        category="stale_values",
        description="Value contains example/default credentials",
        fix_suggestion="Replace with actual, unique credentials",
        value_pattern=r"(admin|password123|secret123|test123|default123|letmein|welcome)",
        key_pattern=r"(PASSWORD|SECRET|TOKEN|KEY|CREDENTIAL)",
    ))

    rules.append(Rule(
        id="STALE007",
        severity="info",
        category="stale_values",
        description="Value references a staging or development environment in production config",
        fix_suggestion="Update the value for the correct environment",
        value_pattern=r"(staging|development|dev\.|local|test)",
        key_pattern=r"(REDIS_URL|MONGO_URL|DATABASE_URL|API_URL|BASE_URL|BACKEND_URL)",
    ))

    rules.append(Rule(
        id="STALE008",
        severity="warning",
        category="stale_values",
        description="Value contains an old API version prefix",
        fix_suggestion="Update to the latest API version",
        value_pattern=r"(\/api\/v1[^0-9]|\/v1\/|api/v1)",
    ))

    # =========================================================================
    # SECRETS LEAK (8 rules)
    # =========================================================================

    rules.append(Rule(
        id="SECRET001",
        severity="critical",
        category="secrets_leak",
        description="Hardcoded password detected in configuration",
        fix_suggestion="Move the password to a secure secret and reference it via environment variable",
        key_pattern=r"(PASSWORD|PASSWD|PWD)",
        value_pattern=r"\S+",
        check_func=lambda ctx: (
            bool(re.search(r"(PASSWORD|PASSWD|PWD)", ctx.get("key", ""), re.IGNORECASE))
            and len(ctx.get("value", "")) > 0
            and not ctx.get("value", "").startswith(("${", "$"))
            and not ctx.get("is_secret_file", True)
        ),
    ))

    rules.append(Rule(
        id="SECRET002",
        severity="critical",
        category="secrets_leak",
        description="API key or token found in non-secret file (e.g., .env.example)",
        fix_suggestion="Remove the actual key value from the template file; use a placeholder instead",
        check_func=lambda ctx: (
            bool(re.search(r"(API_KEY|APIKEY|ACCESS_KEY|TOKEN|AUTH_TOKEN)", ctx.get("key", ""), re.IGNORECASE))
            and len(ctx.get("value", "")) > 10
            and not ctx.get("value", "").startswith(("${", "$"))
            and not ctx.get("is_secret_file", True)
        ),
    ))

    rules.append(Rule(
        id="SECRET003",
        severity="critical",
        category="secrets_leak",
        description="Private key or certificate content detected in configuration",
        fix_suggestion="Store private keys in a secure vault; never commit them to version control",
        value_pattern=r"-----BEGIN.*(PRIVATE KEY|CERTIFICATE|RSA)-----",
    ))

    rules.append(Rule(
        id="SECRET004",
        severity="critical",
        category="secrets_leak",
        description="Secret token found in .env.example or template file",
        fix_suggestion="Replace the actual token with a placeholder like '<your-token-here>'",
        check_func=lambda ctx: (
            not ctx.get("is_secret_file", True)
            and len(ctx.get("value", "")) > 8
            and ctx.get("value", "").startswith(("<", "{", "["))
            is False
            and not ctx.get("value", "").startswith(("${", "$"))
            and bool(re.search(
                r"(SECRET|TOKEN|KEY|PASSWORD|CREDENTIAL|AUTH)",
                ctx.get("key", ""),
                re.IGNORECASE,
            ))
            and not ctx.get("value", "").startswith(("<", "your_", "example", "placeholder"))
        ),
    ))

    rules.append(Rule(
        id="SECRET005",
        severity="critical",
        category="secrets_leak",
        description="AWS access key or secret key detected",
        fix_suggestion="Remove AWS credentials from configuration files; use IAM roles or a secrets manager",
        value_pattern=r"AKIA[0-9A-Z]{16}",
    ))

    rules.append(Rule(
        id="SECRET006",
        severity="critical",
        category="secrets_leak",
        description="Generic secret/credential value detected in non-secret file",
        fix_suggestion="Move secrets to a dedicated .env file excluded from version control",
        check_func=lambda ctx: (
            not ctx.get("is_secret_file", True)
            and len(ctx.get("value", "")) > 15
            and bool(re.search(
                r"(SECRET|CREDENTIAL|PRIVATE|AUTH|SIGNING)",
                ctx.get("key", ""),
                re.IGNORECASE,
            ))
            and not ctx.get("value", "").startswith(("${", "$", "<", "your_"))
            and not any(
                placeholder in ctx.get("value", "").lower()
                for placeholder in ("example", "placeholder", "changeme", "todo", "xxx")
            )
        ),
    ))

    rules.append(Rule(
        id="SECRET007",
        severity="critical",
        category="secrets_leak",
        description="Connection string with embedded credentials detected",
        fix_suggestion="Use environment variable references for credentials in connection strings",
        value_pattern=r"(?i)(mongodb|postgres|mysql|redis|amqp)://[^\s:]+:[^\s@]+@[^\s]+",
    ))

    rules.append(Rule(
        id="SECRET008",
        severity="warning",
        category="secrets_leak",
        description="Potential webhook URL with secret token detected in non-secret file",
        fix_suggestion="Move webhook URLs with tokens to a secure secret file",
        check_func=lambda ctx: (
            not ctx.get("is_secret_file", True)
            and "webhook" in ctx.get("key", "").lower()
            and len(ctx.get("value", "")) > 20
            and not ctx.get("value", "").startswith(("${", "$", "<", "your_"))
        ),
    ))

    # =========================================================================
    # BEST PRACTICES (8 rules)
    # =========================================================================

    rules.append(Rule(
        id="BEST001",
        severity="critical",
        category="best_practices",
        description="Default password detected (common weak password)",
        fix_suggestion="Use a strong, unique password instead of a default value",
        value_pattern=r"^(admin|password|123456|root|toor|pass|test|guest|default)$",
        key_pattern=r"(PASSWORD|PASSWD|PWD|SECRET)",
    ))

    rules.append(Rule(
        id="BEST002",
        severity="info",
        category="best_practices",
        description="Key naming does not follow UPPER_SNAKE_CASE convention",
        fix_suggestion="Rename the key to use UPPER_SNAKE_CASE (e.g., MY_KEY_NAME)",
        check_func=lambda ctx: (
            ctx.get("key", "") != ""
            and not re.match(r"^[A-Z][A-Z0-9_]*$", ctx.get("key", ""))
            and not ctx.get("key", "").startswith("[")
        ),
    ))

    rules.append(Rule(
        id="BEST003",
        severity="warning",
        category="best_practices",
        description="Duplicate key detected (same key defined multiple times)",
        fix_suggestion="Remove the duplicate key definition; keep only the intended value",
        check_func=lambda ctx: ctx.get("is_duplicate", False),
    ))

    rules.append(Rule(
        id="BEST004",
        severity="warning",
        category="best_practices",
        description="Required key has an empty value",
        fix_suggestion="Provide a value for the required configuration key",
        check_func=lambda ctx: (
            ctx.get("data_type", "") == "empty"
            and ctx.get("value", "") == ""
            and bool(re.search(
                r"(URL|KEY|SECRET|TOKEN|HOST|PORT|DATABASE|PASSWORD)",
                ctx.get("key", ""),
                re.IGNORECASE,
            ))
        ),
    ))

    rules.append(Rule(
        id="BEST005",
        severity="info",
        category="best_practices",
        description="Key name is too short (less than 3 characters)",
        fix_suggestion="Use descriptive key names for clarity (e.g., DB_HOST instead of H)",
        check_func=lambda ctx: (
            len(ctx.get("key", "")) < 3
            and ctx.get("key", "") != ""
        ),
    ))

    rules.append(Rule(
        id="BEST006",
        severity="info",
        category="best_practices",
        description="Value contains trailing whitespace",
        fix_suggestion="Remove trailing whitespace from the value",
        check_func=lambda ctx: (
            ctx.get("value", "") != ctx.get("value", "").rstrip()
            and ctx.get("value", "") != ""
        ),
    ))

    rules.append(Rule(
        id="BEST007",
        severity="warning",
        category="best_practices",
        description="DEBUG mode is enabled (should be disabled in production)",
        fix_suggestion="Set DEBUG=false for production environments",
        key_pattern=r"^DEBUG$",
        value_pattern=r"^(true|yes|1|on)$",
    ))

    rules.append(Rule(
        id="BEST008",
        severity="info",
        category="best_practices",
        description="No comment or description found for important configuration key",
        fix_suggestion="Add a comment above the key to document its purpose and expected values",
        check_func=lambda ctx: (
            ctx.get("comment", "") == ""
            and ctx.get("is_important", False)
        ),
    ))

    return rules


def get_rules_by_category(category: str) -> List[Rule]:
    """Get all rules in a specific category.

    Args:
        category: The category name to filter by.

    Returns:
        A list of rules matching the category.
    """
    return [r for r in get_all_rules() if r.category == category]


def get_rules_by_severity(severity: str) -> List[Rule]:
    """Get all rules at a specific severity level.

    Args:
        severity: The severity level to filter by.

    Returns:
        A list of rules matching the severity level.
    """
    return [r for r in get_all_rules() if r.severity == severity]


def get_rule_by_id(rule_id: str) -> Optional[Rule]:
    """Get a rule by its unique identifier.

    Args:
        rule_id: The rule ID to look up.

    Returns:
        The matching Rule, or None if not found.
    """
    for r in get_all_rules():
        if r.id == rule_id:
            return r
    return None


# Helper functions for custom check logic

def _check_expired_date(ctx: Dict[str, Any]) -> bool:
    """Check if a date value appears to be in the past.

    Args:
        ctx: The check context dictionary.

    Returns:
        True if the date appears expired, False otherwise.
    """
    value = ctx.get("value", "")
    if not value or value.startswith(("${", "$")):
        return False

    import datetime

    # Try common date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
    ]

    for fmt in date_formats:
        try:
            date = datetime.datetime.strptime(value, fmt)
            return date < datetime.datetime.now()
        except (ValueError, TypeError):
            continue

    return False
