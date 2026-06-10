"""
Terminal color utilities using only the Python standard library.

Provides ANSI color codes for terminal output with automatic
disable support for non-TTY environments and Windows compatibility.
"""

import os
import sys


class Colors:
    """ANSI color code manager for terminal output.

    Supports automatic detection of color support and provides
    methods to wrap text in ANSI escape sequences.

    Attributes:
        enabled: Whether color output is currently enabled.
    """

    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bright foreground colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the Colors manager.

        Args:
            enabled: Whether to enable color output. If True, will still
                     check for TTY support unless force_enabled is used.
        """
        self._enabled = enabled and self._supports_color()

    @staticmethod
    def _supports_color() -> bool:
        """Check if the current terminal supports ANSI color codes.

        Returns:
            True if the terminal supports colors, False otherwise.
        """
        # Check for NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Check for forced color
        if os.environ.get("FORCE_COLOR"):
            return True

        # Windows: check for ANSI support
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequences on Windows 10+
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False

        # Unix-like: check if output is a TTY
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            return True

        # Check for common CI environments that support color
        ci_terms = {"CI", "GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS", "CIRCLECI"}
        return bool(ci_terms & set(os.environ.keys()))

    @property
    def enabled(self) -> bool:
        """Check if color output is enabled.

        Returns:
            True if colors are enabled, False otherwise.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable color output.

        Args:
            value: True to enable colors, False to disable.
        """
        self._enabled = value

    def style(self, text: str, *codes: str) -> str:
        """Apply ANSI color codes to text.

        Args:
            text: The text to style.
            *codes: ANSI color code strings to apply.

        Returns:
            The styled text with ANSI codes, or plain text if colors
            are disabled.
        """
        if not self._enabled or not codes:
            return text
        return "".join(codes) + text + self.RESET

    def red(self, text: str) -> str:
        """Return text styled in red.

        Args:
            text: The text to style.

        Returns:
            Red-styled text.
        """
        return self.style(text, self.RED)

    def green(self, text: str) -> str:
        """Return text styled in green.

        Args:
            text: The text to style.

        Returns:
            Green-styled text.
        """
        return self.style(text, self.GREEN)

    def yellow(self, text: str) -> str:
        """Return text styled in yellow.

        Args:
            text: The text to style.

        Returns:
            Yellow-styled text.
        """
        return self.style(text, self.YELLOW)

    def blue(self, text: str) -> str:
        """Return text styled in blue.

        Args:
            text: The text to style.

        Returns:
            Blue-styled text.
        """
        return self.style(text, self.BLUE)

    def magenta(self, text: str) -> str:
        """Return text styled in magenta.

        Args:
            text: The text to style.

        Returns:
            Magenta-styled text.
        """
        return self.style(text, self.MAGENTA)

    def cyan(self, text: str) -> str:
        """Return text styled in cyan.

        Args:
            text: The text to style.

        Returns:
            Cyan-styled text.
        """
        return self.style(text, self.CYAN)

    def bold(self, text: str) -> str:
        """Return text styled in bold.

        Args:
            text: The text to style.

        Returns:
            Bold-styled text.
        """
        return self.style(text, self.BOLD)

    def dim(self, text: str) -> str:
        """Return text styled as dim.

        Args:
            text: The text to style.

        Returns:
            Dim-styled text.
        """
        return self.style(text, self.DIM)

    def bright_red(self, text: str) -> str:
        """Return text styled in bright red.

        Args:
            text: The text to style.

        Returns:
            Bright red-styled text.
        """
        return self.style(text, self.BRIGHT_RED)

    def bright_green(self, text: str) -> str:
        """Return text styled in bright green.

        Args:
            text: The text to style.

        Returns:
            Bright green-styled text.
        """
        return self.style(text, self.BRIGHT_GREEN)

    def bright_yellow(self, text: str) -> str:
        """Return text styled in bright yellow.

        Args:
            text: The text to style.

        Returns:
            Bright yellow-styled text.
        """
        return self.style(text, self.BRIGHT_YELLOW)

    def bright_blue(self, text: str) -> str:
        """Return text styled in bright blue.

        Args:
            text: The text to style.

        Returns:
            Bright blue-styled text.
        """
        return self.style(text, self.BRIGHT_BLUE)

    def severity_color(self, severity: str) -> str:
        """Get the ANSI color code for a severity level.

        Args:
            severity: The severity level (critical, warning, info).

        Returns:
            The ANSI color code string for the severity level.
        """
        severity_map = {
            "critical": self.BRIGHT_RED,
            "warning": self.BRIGHT_YELLOW,
            "info": self.BRIGHT_BLUE,
        }
        return severity_map.get(severity.lower(), self.WHITE)

    def severity_text(self, severity: str, text: str) -> str:
        """Style text with the color corresponding to a severity level.

        Args:
            severity: The severity level (critical, warning, info).
            text: The text to style.

        Returns:
            The styled text.
        """
        return self.style(text, self.severity_color(severity))

    def success(self, text: str) -> str:
        """Return text styled as a success message (green).

        Args:
            text: The text to style.

        Returns:
            Green-styled text.
        """
        return self.style(text, self.BRIGHT_GREEN)

    def error(self, text: str) -> str:
        """Return text styled as an error message (bright red).

        Args:
            text: The text to style.

        Returns:
            Bright red-styled text.
        """
        return self.style(text, self.BRIGHT_RED)

    def warn(self, text: str) -> str:
        """Return text styled as a warning message (bright yellow).

        Args:
            text: The text to style.

        Returns:
            Bright yellow-styled text.
        """
        return self.style(text, self.BRIGHT_YELLOW)

    def header(self, text: str) -> str:
        """Return text styled as a header (bold cyan).

        Args:
            text: The text to style.

        Returns:
            Bold cyan-styled text.
        """
        return self.style(text, self.BOLD, self.CYAN)

    def table_header(self, text: str) -> str:
        """Return text styled as a table header (bold white).

        Args:
            text: The text to style.

        Returns:
            Bold white-styled text.
        """
        return self.style(text, self.BOLD, self.WHITE)
