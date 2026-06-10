"""
Unit tests for the EnvParser module.

Tests parsing of .env, JSON, TOML, and YAML configuration files
with various formats and edge cases.
"""

import json
import os
import tempfile
import unittest
from typing import List

from envguard.core.parser import EnvEntry, EnvParser, ParseError


class TestEnvEntry(unittest.TestCase):
    """Tests for the EnvEntry data class."""

    def test_basic_entry(self) -> None:
        """Test creating a basic EnvEntry."""
        entry = EnvEntry(
            key="DATABASE_URL",
            value="postgres://localhost:5432/mydb",
            line_number=1,
            source_file=".env",
        )
        self.assertEqual(entry.key, "DATABASE_URL")
        self.assertEqual(entry.value, "postgres://localhost:5432/mydb")
        self.assertEqual(entry.line_number, 1)
        self.assertEqual(entry.source_file, ".env")
        self.assertEqual(entry.data_type, "url")

    def test_type_inference_boolean(self) -> None:
        """Test type inference for boolean values."""
        for val in ("true", "false", "True", "False", "yes", "no", "1", "0"):
            entry = EnvEntry(key="TEST", value=val)
            self.assertEqual(entry.data_type, "boolean", f"Failed for value: {val}")

    def test_type_inference_integer(self) -> None:
        """Test type inference for integer values."""
        entry = EnvEntry(key="PORT", value="8080")
        self.assertEqual(entry.data_type, "integer")

    def test_type_inference_float(self) -> None:
        """Test type inference for float values."""
        entry = EnvEntry(key="RATE", value="3.14")
        self.assertEqual(entry.data_type, "float")

    def test_type_inference_url(self) -> None:
        """Test type inference for URL values."""
        entry = EnvEntry(key="URL", value="https://example.com/api")
        self.assertEqual(entry.data_type, "url")

    def test_type_inference_email(self) -> None:
        """Test type inference for email values."""
        entry = EnvEntry(key="EMAIL", value="admin@example.com")
        self.assertEqual(entry.data_type, "email")

    def test_type_inference_json(self) -> None:
        """Test type inference for JSON values."""
        entry = EnvEntry(key="CONFIG", value='{"key": "value"}')
        self.assertEqual(entry.data_type, "json")

    def test_type_inference_empty(self) -> None:
        """Test type inference for empty values."""
        entry = EnvEntry(key="EMPTY", value="")
        self.assertEqual(entry.data_type, "empty")

    def test_type_inference_string(self) -> None:
        """Test type inference for plain string values."""
        entry = EnvEntry(key="NAME", value="hello world")
        self.assertEqual(entry.data_type, "string")

    def test_to_dict(self) -> None:
        """Test converting an entry to a dictionary."""
        entry = EnvEntry(key="KEY", value="val", line_number=5, source_file="test.env")
        d = entry.to_dict()
        self.assertEqual(d["key"], "KEY")
        self.assertEqual(d["value"], "val")
        self.assertEqual(d["line_number"], 5)
        self.assertEqual(d["source_file"], "test.env")

    def test_repr(self) -> None:
        """Test string representation of an entry."""
        entry = EnvEntry(key="KEY", value="val")
        repr_str = repr(entry)
        self.assertIn("KEY", repr_str)
        self.assertIn("val", repr_str)


class TestEnvParserBasic(unittest.TestCase):
    """Tests for basic EnvParser functionality."""

    def setUp(self) -> None:
        """Set up test parser."""
        self.parser = EnvParser(interpolate=True)

    def test_parse_simple_env_content(self) -> None:
        """Test parsing a simple .env content string."""
        content = "KEY1=value1\nKEY2=value2\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].key, "KEY1")
        self.assertEqual(entries[0].value, "value1")
        self.assertEqual(entries[1].key, "KEY2")
        self.assertEqual(entries[1].value, "value2")

    def test_parse_comments(self) -> None:
        """Test that comment lines are skipped."""
        content = "# This is a comment\nKEY=value\n# Another comment\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].key, "KEY")

    def test_parse_empty_lines(self) -> None:
        """Test that empty lines are skipped."""
        content = "\n\nKEY1=val1\n\n\nKEY2=val2\n\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 2)

    def test_parse_export_prefix(self) -> None:
        """Test that 'export ' prefix is handled."""
        content = "export KEY=value\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].key, "KEY")
        self.assertEqual(entries[0].value, "value")

    def test_parse_quoted_values(self) -> None:
        """Test parsing double and single quoted values."""
        content = 'KEY1="hello world"\nKEY2=\'single quotes\'\n'
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].value, "hello world")
        self.assertTrue(entries[0].is_quoted)
        self.assertEqual(entries[1].value, "single quotes")
        self.assertTrue(entries[1].is_quoted)

    def test_parse_inline_comments(self) -> None:
        """Test parsing inline comments."""
        content = "KEY=value # this is a comment\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].value, "value")
        self.assertIn("#", entries[0].comment)

    def test_parse_quoted_value_with_equals(self) -> None:
        """Test parsing quoted values containing equals signs."""
        content = 'KEY="value=with=equals"\n'
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].value, "value=with=equals")

    def test_line_numbers(self) -> None:
        """Test that line numbers are correctly tracked."""
        content = "# comment\nKEY=value\nANOTHER=val\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(entries[0].line_number, 2)
        self.assertEqual(entries[1].line_number, 3)

    def test_secret_key_detection(self) -> None:
        """Test that secret keys are detected."""
        secret_keys = [
            "DATABASE_PASSWORD", "API_KEY", "SECRET_TOKEN",
            "PRIVATE_KEY", "AUTH_CREDENTIAL", "SESSION_KEY",
            "SSL_CERTIFICATE", "ENCRYPTION_KEY",
        ]
        for key in secret_keys:
            self.assertTrue(
                self.parser._is_secret_key(key),
                f"Failed to detect secret key: {key}"
            )

    def test_non_secret_key_detection(self) -> None:
        """Test that non-secret keys are not flagged."""
        non_secret_keys = ["APP_NAME", "DEBUG", "PORT", "HOST", "LOG_LEVEL"]
        for key in non_secret_keys:
            self.assertFalse(
                self.parser._is_secret_key(key),
                f"Incorrectly flagged as secret: {key}"
            )


class TestEnvParserFile(unittest.TestCase):
    """Tests for file-based parsing."""

    def setUp(self) -> None:
        """Set up test parser and temp directory."""
        self.parser = EnvParser(interpolate=False)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_temp_file(self, filename: str, content: str) -> str:
        """Write content to a temp file and return the path.

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

    def test_parse_env_file(self) -> None:
        """Test parsing a .env file."""
        content = "DATABASE_URL=postgres://localhost/db\nPORT=5432\nDEBUG=false\n"
        filepath = self._write_temp_file(".env", content)
        entries = self.parser.parse_file(filepath)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].key, "DATABASE_URL")
        self.assertEqual(entries[1].key, "PORT")
        self.assertEqual(entries[2].key, "DEBUG")

    def test_parse_env_example_file(self) -> None:
        """Test parsing a .env.example file."""
        content = "DATABASE_URL=<your-database-url>\nAPI_KEY=<your-api-key>\n"
        filepath = self._write_temp_file(".env.example", content)
        entries = self.parser.parse_file(filepath)
        self.assertEqual(len(entries), 2)

    def test_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing files."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file("/nonexistent/path/.env")

    def test_parse_json_file(self) -> None:
        """Test parsing a JSON configuration file."""
        data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "mydb",
            },
            "debug": True,
            "port": 8080,
        }
        filepath = self._write_temp_file("config.json", json.dumps(data))
        entries = self.parser.parse_file(filepath)
        keys = [e.key for e in entries]
        self.assertIn("database_host", keys)
        self.assertIn("database_port", keys)
        self.assertIn("database_name", keys)
        self.assertIn("debug", keys)
        self.assertIn("port", keys)

    def test_parse_toml_file(self) -> None:
        """Test parsing a TOML configuration file."""
        content = (
            '[server]\n'
            'host = "localhost"\n'
            'port = 8080\n'
            'debug = true\n'
            '\n'
            '[database]\n'
            'url = "postgres://localhost/db"\n'
            'max_connections = 10\n'
        )
        filepath = self._write_temp_file("config.toml", content)
        entries = self.parser.parse_file(filepath)
        keys = [e.key for e in entries]
        self.assertIn("server_host", keys)
        self.assertIn("server_port", keys)
        self.assertIn("server_debug", keys)
        self.assertIn("database_url", keys)
        self.assertIn("database_max_connections", keys)

    def test_parse_yaml_file(self) -> None:
        """Test parsing a simple YAML configuration file."""
        content = (
            "database:\n"
            "  host: localhost\n"
            "  port: 5432\n"
            "debug: true\n"
            "port: 8080\n"
        )
        filepath = self._write_temp_file("config.yaml", content)
        entries = self.parser.parse_file(filepath)
        keys = [e.key for e in entries]
        self.assertTrue(len(entries) > 0)

    def test_unsupported_format(self) -> None:
        """Test that unsupported formats raise ParseError."""
        filepath = self._write_temp_file("config.xml", "<config/>")
        with self.assertRaises(ParseError):
            self.parser.parse_file(filepath)

    def test_entries_to_dict(self) -> None:
        """Test converting entries to a dictionary."""
        content = "KEY1=val1\nKEY2=val2\n"
        entries = self.parser._parse_env_content(content)
        d = EnvParser.entries_to_dict(entries)
        self.assertEqual(d, {"KEY1": "val1", "KEY2": "val2"})


class TestEnvParserInterpolation(unittest.TestCase):
    """Tests for variable interpolation."""

    def test_simple_interpolation(self) -> None:
        """Test simple ${VAR} interpolation."""
        parser = EnvParser(interpolate=True)
        content = "BASE_URL=https://example.com\nAPI_URL=${BASE_URL}/api\n"
        entries = parser._parse_env_content(content)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1].value, "https://example.com/api")

    def test_interpolation_with_default(self) -> None:
        """Test ${VAR:-default} interpolation."""
        parser = EnvParser(interpolate=True)
        content = "URL=${MISSING:-http://localhost}\n"
        entries = parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].value, "http://localhost")

    def test_no_interpolation(self) -> None:
        """Test that interpolation can be disabled."""
        parser = EnvParser(interpolate=False)
        content = "URL=${MISSING}\n"
        entries = parser._parse_env_content(content)
        self.assertEqual(entries[0].value, "${MISSING}")


class TestEnvParserEdgeCases(unittest.TestCase):
    """Tests for edge cases in parsing."""

    def setUp(self) -> None:
        """Set up test parser."""
        self.parser = EnvParser(interpolate=False)

    def test_empty_content(self) -> None:
        """Test parsing empty content."""
        entries = self.parser._parse_env_content("")
        self.assertEqual(len(entries), 0)

    def test_only_comments(self) -> None:
        """Test parsing content with only comments."""
        content = "# comment 1\n# comment 2\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 0)

    def test_special_characters_in_values(self) -> None:
        """Test values with special characters."""
        content = 'PASSWORD="p@$$w0rd!#$%"\n'
        entries = self.parser._parse_env_content(content)
        self.assertEqual(entries[0].value, "p@$$w0rd!#$%")

    def test_multiline_value(self) -> None:
        """Test multiline values with backslash continuation."""
        content = "LONG_VALUE=hello \\\nworld \\\nthere\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertIn("hello", entries[0].value)
        self.assertIn("world", entries[0].value)
        self.assertIn("there", entries[0].value)

    def test_key_with_numbers(self) -> None:
        """Test keys containing numbers."""
        content = "REDIS_DB_1=localhost\nV2_API_KEY=key\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].key, "REDIS_DB_1")
        self.assertEqual(entries[1].key, "V2_API_KEY")

    def test_value_with_spaces(self) -> None:
        """Test values with spaces (must be quoted)."""
        content = 'NAME="John Doe"\n'
        entries = self.parser._parse_env_content(content)
        self.assertEqual(entries[0].value, "John Doe")

    def test_empty_value(self) -> None:
        """Test keys with empty values."""
        content = "EMPTY=\n"
        entries = self.parser._parse_env_content(content)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].value, "")

    def test_toml_escape_sequences(self) -> None:
        """Test TOML string escape sequences."""
        parser = EnvParser()
        result = EnvParser._unescape_toml_string("hello\\nworld")
        self.assertEqual(result, "hello\nworld")

        result = EnvParser._unescape_toml_string("tab\\there")
        self.assertEqual(result, "tab\there")


if __name__ == "__main__":
    unittest.main()
