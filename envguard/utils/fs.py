"""
File system utility functions for EnvGuard-CLI.

Provides helpers for file discovery, reading, and path operations
related to environment configuration files.
"""

import os
from typing import Dict, List, Optional, Tuple


class FileSystemHelper:
    """Utility class for file system operations.

    Provides methods for discovering environment files, reading
    file contents, and managing paths.
    """

    # Common environment file names to look for
    ENV_FILE_PATTERNS: List[str] = [
        ".env",
        ".env.local",
        ".env.development",
        ".env.development.local",
        ".env.test",
        ".env.test.local",
        ".env.production",
        ".env.production.local",
        ".env.staging",
        ".env.staging.local",
        ".env.example",
        ".env.sample",
        ".env.template",
        ".env.defaults",
    ]

    CONFIG_FILE_PATTERNS: List[str] = [
        "config.json",
        "config.toml",
        "settings.json",
        "settings.toml",
        "app.json",
        "app.toml",
    ]

    ENVGUARD_CONFIG_NAMES: List[str] = [
        ".envguardrc",
        ".envguardrc.json",
        ".envguardrc.toml",
        "envguard.config.json",
    ]

    def __init__(self, base_path: Optional[str] = None) -> None:
        """Initialize the FileSystemHelper.

        Args:
            base_path: The base directory path. Defaults to current
                       working directory.
        """
        self.base_path = os.path.abspath(base_path or os.getcwd())

    def find_env_files(self, directory: Optional[str] = None) -> List[str]:
        """Find all environment files in the given directory.

        Args:
            directory: The directory to search in. Defaults to base_path.

        Returns:
            A list of absolute paths to found environment files.
        """
        search_dir = directory or self.base_path
        found: List[str] = []
        for pattern in self.ENV_FILE_PATTERNS:
            full_path = os.path.join(search_dir, pattern)
            if os.path.isfile(full_path):
                found.append(full_path)
        return sorted(found)

    def find_config_files(self, directory: Optional[str] = None) -> List[str]:
        """Find all configuration files in the given directory.

        Args:
            directory: The directory to search in. Defaults to base_path.

        Returns:
            A list of absolute paths to found configuration files.
        """
        search_dir = directory or self.base_path
        found: List[str] = []
        for pattern in self.CONFIG_FILE_PATTERNS:
            full_path = os.path.join(search_dir, pattern)
            if os.path.isfile(full_path):
                found.append(full_path)
        return sorted(found)

    def find_envguard_config(self, directory: Optional[str] = None) -> Optional[str]:
        """Find the EnvGuard configuration file.

        Args:
            directory: The directory to search in. Defaults to base_path.

        Returns:
            The absolute path to the config file, or None if not found.
        """
        search_dir = directory or self.base_path
        for name in self.ENVGUARD_CONFIG_NAMES:
            full_path = os.path.join(search_dir, name)
            if os.path.isfile(full_path):
                return full_path
        return None

    def read_file(self, filepath: str) -> str:
        """Read the contents of a file.

        Args:
            filepath: The path to the file to read.

        Returns:
            The file contents as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def read_file_lines(self, filepath: str) -> List[str]:
        """Read a file and return its lines.

        Args:
            filepath: The path to the file to read.

        Returns:
            A list of lines from the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readlines()

    def get_file_extension(self, filepath: str) -> str:
        """Get the file extension of a file.

        Args:
            filepath: The path to the file.

        Returns:
            The file extension (lowercase, without the dot), or
            an empty string if there is no extension.
        """
        _, ext = os.path.splitext(filepath)
        return ext.lower().lstrip(".")

    def get_file_type(self, filepath: str) -> str:
        """Determine the type of a configuration file.

        Args:
            filepath: The path to the file.

        Returns:
            A string identifying the file type: 'env', 'json', 'toml',
            'yaml', or 'unknown'.
        """
        basename = os.path.basename(filepath)
        ext = self.get_file_extension(filepath)

        if basename.startswith(".env"):
            return "env"
        elif ext == "json":
            return "json"
        elif ext == "toml":
            return "toml"
        elif ext in ("yaml", "yml"):
            return "yaml"
        return "unknown"

    def is_env_file(self, filepath: str) -> bool:
        """Check if a file is an environment file.

        Args:
            filepath: The path to the file.

        Returns:
            True if the file is an environment file, False otherwise.
        """
        basename = os.path.basename(filepath)
        return basename.startswith(".env") or basename == "env"

    def is_secret_file(self, filepath: str) -> bool:
        """Check if a file is meant to contain secrets.

        Files like .env, .env.local, .env.production are considered
        secret files. Files like .env.example, .env.template are not.

        Args:
            filepath: The path to the file.

        Returns:
            True if the file is a secret file, False otherwise.
        """
        basename = os.path.basename(filepath)
        non_secret_suffixes = (
            ".example",
            ".sample",
            ".template",
            ".defaults",
        )
        if basename.startswith(".env"):
            for suffix in non_secret_suffixes:
                if basename.endswith(suffix):
                    return False
            return True
        return False

    def ensure_directory(self, filepath: str) -> None:
        """Ensure the parent directory of a file exists.

        Args:
            filepath: The path to a file whose parent directory
                      should be created if it does not exist.
        """
        parent = os.path.dirname(filepath)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    @staticmethod
    def resolve_path(path: str) -> str:
        """Resolve a path to an absolute path.

        Args:
            path: The path to resolve.

        Returns:
            The resolved absolute path.
        """
        return os.path.abspath(os.path.expanduser(path))
