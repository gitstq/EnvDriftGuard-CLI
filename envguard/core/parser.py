"""
Environment configuration file parser for EnvGuard-CLI.

Supports parsing .env, .env.example, JSON, TOML, and YAML configuration
files into a normalized dictionary with metadata. Uses only the Python
standard library.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


class ParseError(Exception):
    """Exception raised when a configuration file cannot be parsed."""

    def __init__(self, filepath: str, message: str) -> None:
        """Initialize a ParseError.

        Args:
            filepath: The path to the file that failed to parse.
            message: A description of the parse error.
        """
        self.filepath = filepath
        self.message = message
        super().__init__(f"Failed to parse {filepath}: {message}")


class EnvEntry:
    """Represents a single environment variable entry with metadata.

    Attributes:
        key: The variable name.
        value: The variable value (raw string).
        line_number: The line number in the source file (1-indexed).
        source_file: The path to the source file.
        is_secret: Whether this entry is considered a secret.
        data_type: The inferred data type of the value.
        comment: Any inline comment associated with the entry.
        is_quoted: Whether the value was quoted in the source.
    """

    def __init__(
        self,
        key: str,
        value: str,
        line_number: int = 0,
        source_file: str = "",
        is_secret: bool = False,
        comment: str = "",
        is_quoted: bool = False,
    ) -> None:
        """Initialize an EnvEntry.

        Args:
            key: The variable name.
            value: The variable value (raw string).
            line_number: The line number in the source file.
            source_file: The path to the source file.
            is_secret: Whether this entry is considered a secret.
            comment: Any inline comment.
            is_quoted: Whether the value was quoted.
        """
        self.key = key
        self.value = value
        self.line_number = line_number
        self.source_file = source_file
        self.is_secret = is_secret
        self.data_type = self._infer_type(value)
        self.comment = comment
        self.is_quoted = is_quoted

    @staticmethod
    def _infer_type(value: str) -> str:
        """Infer the data type of a value string.

        Args:
            value: The value string to analyze.

        Returns:
            A string identifying the type: 'boolean', 'integer', 'float',
            'json', 'url', 'email', 'empty', or 'string'.
        """
        if not value or value.strip() == "":
            return "empty"

        stripped = value.strip().strip("\"'")

        # Boolean
        if stripped.lower() in ("true", "false", "yes", "no", "on", "off", "1", "0"):
            return "boolean"

        # Integer
        try:
            int(stripped)
            return "integer"
        except ValueError:
            pass

        # Float
        try:
            float(stripped)
            return "float"
        except ValueError:
            pass

        # JSON
        if stripped.startswith(("{", "[", "\"")):
            try:
                json.loads(stripped)
                return "json"
            except (json.JSONDecodeError, ValueError):
                pass

        # URL
        url_pattern = re.compile(
            r"^https?://[^\s]+|^ftp://[^\s]+|^wss?://[^\s]+|^amqp://[^\s]+"
            r"|^postgres(ql)?://[^\s]+|^mysql://[^\s]+|^redis://[^\s]+"
            r"|^mongo(db)?(\+srv)?://[^\s]+|^sqlite://[^\s]+"
        )
        if url_pattern.match(stripped):
            return "url"

        # Email
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if email_pattern.match(stripped):
            return "email"

        return "string"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary representation.

        Returns:
            A dictionary containing all entry attributes.
        """
        return {
            "key": self.key,
            "value": self.value,
            "line_number": self.line_number,
            "source_file": self.source_file,
            "is_secret": self.is_secret,
            "data_type": self.data_type,
            "comment": self.comment,
            "is_quoted": self.is_quoted,
        }

    def __repr__(self) -> str:
        """Return a string representation of the entry.

        Returns:
            A string representation.
        """
        return (
            f"EnvEntry(key={self.key!r}, value={self.value!r}, "
            f"line={self.line_number}, type={self.data_type})"
        )


class EnvParser:
    """Multi-format environment configuration file parser.

    Supports parsing .env files, JSON, TOML, and simple YAML files.
    Returns normalized EnvEntry objects with metadata.

    Usage:
        parser = EnvParser()
        entries = parser.parse_file(".env")
        for entry in entries:
            print(f"{entry.key}={entry.value} ({entry.data_type})")
    """

    # Patterns for secret detection in key names
    SECRET_KEY_PATTERNS: List[str] = [
        r"(?i)(password|passwd|pwd)",
        r"(?i)(secret|token|api_key|apikey|access_key|secret_key)",
        r"(?i)(private_key|private)",
        r"(?i)(auth|credential|cred)",
        r"(?i)(session|session_key)",
        r"(?i)(certificate|cert|ssl_key)",
        r"(?i)(encryption_key|signing_key)",
    ]

    def __init__(self, interpolate: bool = True) -> None:
        """Initialize the EnvParser.

        Args:
            interpolate: Whether to perform variable interpolation
                         (e.g., ${VAR} references).
        """
        self.interpolate = interpolate

    def parse_file(self, filepath: str) -> List[EnvEntry]:
        """Parse a configuration file and return a list of EnvEntry objects.

        The file type is determined by the file extension and name.

        Args:
            filepath: The path to the configuration file.

        Returns:
            A list of EnvEntry objects parsed from the file.

        Raises:
            ParseError: If the file cannot be parsed.
            FileNotFoundError: If the file does not exist.
        """
        filepath = os.path.abspath(filepath)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        basename = os.path.basename(filepath)
        _, ext = os.path.splitext(filepath)
        ext = ext.lower().lstrip(".")

        if basename.startswith(".env") or basename == "env":
            return self._parse_env_file(filepath)
        elif ext == "json":
            return self._parse_json_file(filepath)
        elif ext == "toml":
            return self._parse_toml_file(filepath)
        elif ext in ("yaml", "yml"):
            return self._parse_yaml_file(filepath)
        else:
            raise ParseError(
                filepath,
                f"Unsupported file format: {ext}. "
                "Supported formats: .env, .json, .toml, .yaml, .yml",
            )

    def parse_content(self, content: str, file_type: str = "env", source_file: str = "") -> List[EnvEntry]:
        """Parse configuration content from a string.

        Args:
            content: The configuration content as a string.
            file_type: The type of content ('env', 'json', 'toml', 'yaml').
            source_file: The source file path for metadata.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the content cannot be parsed.
        """
        if file_type == "env":
            return self._parse_env_content(content, source_file)
        elif file_type == "json":
            return self._parse_json_content(content, source_file)
        elif file_type == "toml":
            return self._parse_toml_content(content, source_file)
        elif file_type == "yaml":
            return self._parse_yaml_content(content, source_file)
        else:
            raise ParseError(
                source_file or "<string>",
                f"Unsupported content type: {file_type}",
            )

    def _parse_env_file(self, filepath: str) -> List[EnvEntry]:
        """Parse a .env file.

        Args:
            filepath: The path to the .env file.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the file cannot be read.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise ParseError(filepath, str(e))

        is_secret = self._is_secret_file(filepath)
        return self._parse_env_content(content, filepath, is_secret)

    def _parse_env_content(
        self,
        content: str,
        source_file: str = "",
        is_secret: bool = False,
    ) -> List[EnvEntry]:
        """Parse .env file content.

        Handles:
        - Comments (lines starting with #)
        - Empty lines
        - Quoted values (single and double quotes)
        - Multiline values (values ending with \\)
        - Inline comments
        - Variable interpolation (${VAR} and $VAR)
        - Export prefix (export KEY=VALUE)

        Args:
            content: The .env file content.
            source_file: The source file path for metadata.
            is_secret: Whether the file is a secret file.

        Returns:
            A list of EnvEntry objects.
        """
        entries: List[EnvEntry] = []
        lines = content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]
            line_number = i + 1

            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # Remove 'export ' prefix
            if stripped.lower().startswith("export "):
                stripped = stripped[7:].strip()

            # Parse KEY=VALUE
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", stripped)
            if not match:
                i += 1
                continue

            key = match.group(1)
            value_part = match.group(2).strip()

            # Extract inline comment
            comment = ""
            if value_part and not value_part.startswith(("'", '"')):
                comment_match = re.match(r'^(.*?)(\s*#\s*.*)$', value_part)
                if comment_match:
                    comment = comment_match.group(2).strip()
                    value_part = comment_match.group(1).strip()

            # Handle quoted values
            is_quoted = False
            if value_part and len(value_part) >= 2:
                quote_char = None
                if (value_part.startswith('"') and value_part.endswith('"')) or \
                   (value_part.startswith("'") and value_part.endswith("'")):
                    quote_char = value_part[0]
                    is_quoted = True

                if quote_char and len(value_part) >= 2:
                    # Check for multiline value
                    if value_part.endswith("\\"):
                        # Multiline quoted value
                        multiline_parts = [value_part[:-1]]
                        j = i + 1
                        while j < len(lines):
                            multiline_parts.append(lines[j])
                            if lines[j].rstrip().endswith(quote_char):
                                break
                            j += 1
                        value_part = "\n".join(multiline_parts)
                        # Remove surrounding quotes
                        if value_part.startswith(quote_char) and value_part.endswith(quote_char):
                            value_part = value_part[1:-1]
                        i = j
                    else:
                        value_part = value_part[1:-1]

            # Handle multiline unquoted values (ending with \)
            if not is_quoted and value_part.endswith("\\"):
                multiline_parts = [value_part[:-1]]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith("#"):
                        break
                    if next_line.endswith("\\"):
                        multiline_parts.append(next_line[:-1])
                    else:
                        multiline_parts.append(next_line)
                        break
                    j += 1
                value_part = "\n".join(multiline_parts)
                i = j

            # Perform variable interpolation
            if self.interpolate:
                value_part = self._interpolate(value_part, entries)

            # Determine if this specific key is a secret
            key_is_secret = is_secret or self._is_secret_key(key)

            entry = EnvEntry(
                key=key,
                value=value_part,
                line_number=line_number,
                source_file=source_file,
                is_secret=key_is_secret,
                comment=comment,
                is_quoted=is_quoted,
            )
            entries.append(entry)
            i += 1

        return entries

    def _interpolate(self, value: str, existing_entries: List[EnvEntry]) -> str:
        """Perform variable interpolation on a value string.

        Supports ${VAR} and $VAR syntax. Also supports ${VAR:-default}
        for default values.

        Args:
            value: The value string to interpolate.
            existing_entries: Previously parsed entries for reference.

        Returns:
            The interpolated value string.
        """
        # Build a lookup dict from existing entries
        env_map: Dict[str, str] = {e.key: e.value for e in existing_entries}
        # Also include actual environment variables
        env_map.update(os.environ)

        def replace_var(match: re.Match) -> str:
            """Replace a single variable reference."""
            var_name = match.group(1) if match.lastindex >= 1 else None
            default_value = match.group(2) if match.lastindex >= 2 else None

            if var_name and var_name in env_map:
                return env_map[var_name]
            if default_value is not None:
                return default_value
            if var_name:
                return match.group(0)
            return match.group(0)  # Leave unreplaced if not found

        # Replace ${VAR:-default} first
        value = re.sub(r"\$\{([A-Za-z0-9_]+):-([^}]*)\}", replace_var, value)
        # Replace ${VAR}
        value = re.sub(r"\$\{([A-Za-z0-9_]+)\}", replace_var, value)
        # Replace $VAR (only word characters after $)
        value = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", replace_var, value)

        return value

    def _parse_json_file(self, filepath: str) -> List[EnvEntry]:
        """Parse a JSON configuration file.

        Args:
            filepath: The path to the JSON file.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise ParseError(filepath, str(e))

        return self._parse_json_content(content, filepath)

    def _parse_json_content(self, content: str, source_file: str = "") -> List[EnvEntry]:
        """Parse JSON configuration content.

        Supports flat key-value objects and nested objects (flattened
        with underscore-separated keys).

        Args:
            content: The JSON content string.
            source_file: The source file path for metadata.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the JSON is invalid.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ParseError(source_file or "<json>", str(e))

        if not isinstance(data, dict):
            raise ParseError(
                source_file or "<json>",
                "JSON root must be an object (dict)",
            )

        entries: List[EnvEntry] = []
        self._flatten_json_dict(data, "", entries, source_file, 1)
        return entries

    def _flatten_json_dict(
        self,
        data: Dict[str, Any],
        prefix: str,
        entries: List[EnvEntry],
        source_file: str,
        line_number: int,
    ) -> None:
        """Recursively flatten a nested JSON dict into EnvEntry objects.

        Args:
            data: The dictionary to flatten.
            prefix: The current key prefix.
            entries: The list to append entries to.
            source_file: The source file path.
            line_number: The approximate line number.
        """
        for key, value in data.items():
            full_key = f"{prefix}_{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_json_dict(
                    value, full_key, entries, source_file, line_number
                )
            elif isinstance(value, (list, dict)):
                str_value = json.dumps(value)
                entry = EnvEntry(
                    key=full_key,
                    value=str_value,
                    line_number=line_number,
                    source_file=source_file,
                    is_secret=self._is_secret_key(full_key),
                )
                entries.append(entry)
                line_number += 1
            else:
                str_value = str(value) if value is not None else ""
                entry = EnvEntry(
                    key=full_key,
                    value=str_value,
                    line_number=line_number,
                    source_file=source_file,
                    is_secret=self._is_secret_key(full_key),
                )
                entries.append(entry)
                line_number += 1

    def _parse_toml_file(self, filepath: str) -> List[EnvEntry]:
        """Parse a TOML configuration file.

        Uses a minimal TOML parser implemented with only stdlib.

        Args:
            filepath: The path to the TOML file.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise ParseError(filepath, str(e))

        return self._parse_toml_content(content, filepath)

    def _parse_toml_content(self, content: str, source_file: str = "") -> List[EnvEntry]:
        """Parse TOML configuration content.

        Implements a minimal TOML parser supporting:
        - Comments (# ...)
        - Key-value pairs (key = value)
        - String values (double-quoted, single-quoted, literal)
        - Integer and float values
        - Boolean values
        - Arrays (inline)
        - Tables ([section] and [section.subsection])
        - Inline tables ({key = value, ...})

        Args:
            content: The TOML content string.
            source_file: The source file path for metadata.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the TOML is invalid.
        """
        entries: List[EnvEntry] = []
        lines = content.splitlines()
        current_section = ""

        for i, line in enumerate(lines):
            line_number = i + 1
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Table header [section]
            table_match = re.match(r"^\[([^\]]+)\]", stripped)
            if table_match:
                current_section = table_match.group(1).strip().strip('"')
                continue

            # Array of tables [[section]]
            array_table_match = re.match(r"^\[\[([^\]]+)\]\]", stripped)
            if array_table_match:
                current_section = array_table_match.group(1).strip().strip('"')
                continue

            # Key-value pair
            kv_match = re.match(r'^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*=\s*(.*)', stripped)
            if kv_match:
                key = kv_match.group(1).strip()
                value_str = kv_match.group(2).strip()

                # Remove inline comment (but not inside strings)
                value_str = self._remove_toml_comment(value_str)

                # Parse the value
                parsed_value = self._parse_toml_value(value_str)

                # Build full key with section prefix
                full_key = f"{current_section}_{key}" if current_section else key

                entry = EnvEntry(
                    key=full_key,
                    value=parsed_value,
                    line_number=line_number,
                    source_file=source_file,
                    is_secret=self._is_secret_key(full_key),
                )
                entries.append(entry)

        return entries

    def _remove_toml_comment(self, value: str) -> str:
        """Remove an inline comment from a TOML value string.

        Handles the case where # appears inside quoted strings.

        Args:
            value: The TOML value string.

        Returns:
            The value string with the comment removed.
        """
        in_single_quote = False
        in_double_quote = False
        in_literal_quote = False

        for i, ch in enumerate(value):
            if ch == "'" and not in_double_quote and not in_literal_quote:
                if i > 0 and value[i - 1] == "'":
                    in_single_quote = not in_single_quote
                elif i == 0 or value[i - 1] != "'":
                    in_single_quote = not in_single_quote
            elif ch == '"' and not in_single_quote and not in_literal_quote:
                in_double_quote = not in_double_quote
            elif ch == "#" and not in_single_quote and not in_double_quote and not in_literal_quote:
                return value[:i].rstrip()

        return value

    def _parse_toml_value(self, value: str) -> str:
        """Parse a TOML value string into a normalized string.

        Args:
            value: The TOML value string.

        Returns:
            The normalized string representation.
        """
        value = value.strip()

        # Double-quoted string
        if value.startswith('"') and value.endswith('"'):
            return self._unescape_toml_string(value[1:-1])

        # Single-quoted string (literal)
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]

        # Triple-quoted strings
        if value.startswith('"""') and value.endswith('"""'):
            return value[3:-3]
        if value.startswith("'''") and value.endswith("'''"):
            return value[3:-3]

        # Boolean
        if value.lower() in ("true", "false"):
            return value.lower()

        # Integer
        try:
            int(value)
            return value
        except ValueError:
            pass

        # Float
        try:
            float(value)
            return value
        except ValueError:
            pass

        # Array
        if value.startswith("[") and value.endswith("]"):
            return value

        # Inline table
        if value.startswith("{") and value.endswith("}"):
            return value

        return value

    @staticmethod
    def _unescape_toml_string(s: str) -> str:
        """Unescape a TOML double-quoted string.

        Handles standard escape sequences: \\n, \\t, \\\\, \\", etc.

        Args:
            s: The escaped string.

        Returns:
            The unescaped string.
        """
        escape_map = {
            "\\n": "\n",
            "\\t": "\t",
            "\\r": "\r",
            "\\\\": "\\",
            '\\"': '"',
            "\\b": "\b",
            "\\f": "\f",
        }
        result = []
        i = 0
        while i < len(s):
            if i + 1 < len(s) and s[i] == "\\":
                two_char = s[i:i + 2]
                if two_char in escape_map:
                    result.append(escape_map[two_char])
                    i += 2
                    continue
                # Unicode escape \uXXXX
                if i + 5 < len(s) and s[i + 1] == "u":
                    hex_str = s[i + 2:i + 6]
                    try:
                        code_point = int(hex_str, 16)
                        result.append(chr(code_point))
                        i += 6
                        continue
                    except ValueError:
                        pass
            result.append(s[i])
            i += 1
        return "".join(result)

    def _parse_yaml_file(self, filepath: str) -> List[EnvEntry]:
        """Parse a simple YAML configuration file.

        Uses a minimal YAML parser that handles basic key-value pairs,
        comments, and simple nesting. For complex YAML files, consider
        using JSON format instead.

        Args:
            filepath: The path to the YAML file.

        Returns:
            A list of EnvEntry objects.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise ParseError(filepath, str(e))

        return self._parse_yaml_content(content, filepath)

    def _parse_yaml_content(self, content: str, source_file: str = "") -> List[EnvEntry]:
        """Parse simple YAML configuration content.

        Supports:
        - Key-value pairs (key: value)
        - Comments (# ...)
        - Quoted string values
        - Boolean, integer, float values
        - Nested keys (using parent_key.sub_key notation)
        - List items (converted to comma-separated values)

        Does NOT support:
        - Complex anchors and aliases
        - Multi-document YAML (---)
        - Flow mappings
        - Complex multiline strings

        Args:
            content: The YAML content string.
            source_file: The source file path for metadata.

        Returns:
            A list of EnvEntry objects.
        """
        entries: List[EnvEntry] = []
        lines = content.splitlines()
        current_prefix = ""

        for i, line in enumerate(lines):
            line_number = i + 1
            stripped = line.strip()

            # Skip empty lines, comments, document markers
            if not stripped or stripped.startswith("#") or stripped.startswith("---"):
                continue

            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            if indent == 0:
                current_prefix = ""

            # List item
            if stripped.startswith("- "):
                value = stripped[2:].strip()
                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # List items are skipped as standalone entries
                continue

            # Key-value pair
            kv_match = re.match(r"^([A-Za-z0-9_][A-Za-z0-9_ .-]*?)\s*:\s*(.*)", stripped)
            if kv_match:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()

                # Remove inline comment
                if value and not value.startswith('"') and not value.startswith("'"):
                    comment_match = re.match(r'^(.*?)(\s*#\s*.*)$', value)
                    if comment_match:
                        value = comment_match.group(1).strip()

                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # Handle empty values
                if not value:
                    value = ""

                # Build full key with prefix
                full_key = f"{current_prefix}_{key}" if current_prefix else key

                entry = EnvEntry(
                    key=full_key,
                    value=value,
                    line_number=line_number,
                    source_file=source_file,
                    is_secret=self._is_secret_key(full_key),
                )
                entries.append(entry)

        return entries

    def _is_secret_file(self, filepath: str) -> bool:
        """Determine if a file is a secret-containing file.

        Args:
            filepath: The path to the file.

        Returns:
            True if the file is a secret file, False otherwise.
        """
        basename = os.path.basename(filepath)
        non_secret_suffixes = (".example", ".sample", ".template", ".defaults")
        if basename.startswith(".env"):
            for suffix in non_secret_suffixes:
                if basename.endswith(suffix):
                    return False
            return True
        return False

    def _is_secret_key(self, key: str) -> bool:
        """Determine if a key name suggests it holds a secret value.

        Args:
            key: The key name to check.

        Returns:
            True if the key appears to be a secret, False otherwise.
        """
        for pattern in self.SECRET_KEY_PATTERNS:
            if re.search(pattern, key):
                return True
        return False

    @staticmethod
    def entries_to_dict(entries: List[EnvEntry]) -> Dict[str, str]:
        """Convert a list of EnvEntry objects to a simple dictionary.

        Args:
            entries: The list of EnvEntry objects.

        Returns:
            A dictionary mapping keys to values.
        """
        return {entry.key: entry.value for entry in entries}
