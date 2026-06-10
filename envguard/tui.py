"""
Simple TUI (Terminal User Interface) dashboard for EnvGuard-CLI.

Provides an interactive terminal dashboard using only the Python
standard library (curses). Displays scan results in a scrollable
list with filtering and detail views.

Note: curses is part of the Python standard library on Unix-like systems.
On Windows, the windows-curses package may be needed, but this module
gracefully falls back to a non-interactive mode if curses is unavailable.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from envguard.core.detector import DriftDetector, Finding, ScanResult
from envguard.utils.colors import Colors
from envguard.utils.fs import FileSystemHelper


class TUIDashboard:
    """Interactive terminal dashboard for browsing scan results.

    Uses curses to provide a scrollable, filterable view of findings.

    Attributes:
        result: The scan result to display.
        colors: The colors manager.
        selected_index: The currently selected finding index.
        filter_severity: The current severity filter.
        filter_category: The current category filter.
        show_details: Whether to show details for the selected finding.
        scroll_offset: The scroll offset for the findings list.
    """

    SEVERITY_LEVELS = ["all", "critical", "warning", "info"]
    CATEGORIES = ["all", "missing_keys", "type_mismatch", "stale_values", "secrets_leak", "best_practices"]

    def __init__(self, result: ScanResult, no_color: bool = False) -> None:
        """Initialize the TUI dashboard.

        Args:
            result: The scan result to display.
            no_color: Whether to disable colors.
        """
        self.result = result
        self.colors = Colors(enabled=not no_color)
        self.selected_index: int = 0
        self.filter_severity: str = "all"
        self.filter_category: str = "all"
        self.show_details: bool = False
        self.scroll_offset: int = 0
        self._running: bool = True

    def get_filtered_findings(self) -> List[Finding]:
        """Get findings filtered by current filter settings.

        Returns:
            A list of filtered findings.
        """
        findings = self.result.findings

        if self.filter_severity != "all":
            findings = [f for f in findings if f.severity == self.filter_severity]

        if self.filter_category != "all":
            findings = [f for f in findings if f.category == self.filter_category]

        return findings

    def run(self) -> int:
        """Run the interactive dashboard.

        Attempts to use curses for a full interactive experience.
        Falls back to a simple keyboard-driven mode if curses
        is not available.

        Returns:
            Exit code (0).
        """
        try:
            import curses
            return self._run_curses()
        except ImportError:
            return self._run_simple()

    def _run_curses(self) -> int:
        """Run the dashboard using curses.

        Returns:
            Exit code (0).
        """
        import curses

        def _wrapper(stdscr: Any) -> None:
            self._curses_loop(stdscr)

        try:
            curses.wrapper(_wrapper)
        except Exception as e:
            print(f"TUI error: {e}", file=sys.stderr)

        return 0

    def _curses_loop(self, stdscr: Any) -> None:
        """Main curses event loop.

        Args:
            stdscr: The curses standard screen object.
        """
        import curses

        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        stdscr.timeout(100)

        max_y, max_x = stdscr.getmaxyx()

        while self._running:
            max_y, max_x = stdscr.getmaxyx()
            stdscr.clear()

            self._draw_curses_screen(stdscr, max_y, max_x)

            # Handle input
            try:
                key = stdscr.getch()
                self._handle_curses_key(key)
            except Exception:
                pass

            stdscr.refresh()

    def _draw_curses_screen(self, stdscr: Any, max_y: int, max_x: int) -> None:
        """Draw the curses dashboard screen.

        Args:
            stdscr: The curses standard screen.
            max_y: Maximum Y (rows).
            max_x: Maximum X (columns).
        """
        import curses

        findings = self.get_filtered_findings()

        # Header
        header = " EnvGuard Dashboard "
        try:
            stdscr.addstr(0, 0, header, curses.A_BOLD | curses.A_REVERSE)
        except curses.error:
            pass

        # Status line
        status = (
            f" Findings: {len(findings)}/{self.result.total_count} | "
            f"Filter: {self.filter_severity}/{self.filter_category} | "
            f"[q]uit [f]ilter [d]etails [up/down]scroll"
        )
        try:
            stdscr.addstr(1, 0, status[:max_x - 1])
        except curses.error:
            pass

        # Separator
        try:
            stdscr.addstr(2, 0, "-" * (max_x - 1))
        except curses.error:
            pass

        # Findings list
        visible_rows = max_y - 5
        if visible_rows < 1:
            visible_rows = 1

        start = self.scroll_offset
        end = min(start + visible_rows, len(findings))

        for i in range(start, end):
            row = i - start + 3
            if row >= max_y - 1:
                break

            finding = findings[i]
            is_selected = (i == self.selected_index)

            # Severity indicator
            sev_map = {"critical": "X", "warning": "!", "info": "i"}
            indicator = sev_map.get(finding.severity, "?")

            line = f" [{indicator}] {finding.rule_id} | {finding.key} | {finding.description}"
            if len(line) > max_x - 2:
                line = line[:max_x - 3] + "..."

            try:
                if is_selected:
                    stdscr.addstr(row, 0, line, curses.A_REVERSE)
                else:
                    stdscr.addstr(row, 0, line)
            except curses.error:
                pass

        # Details panel
        if self.show_details and findings and 0 <= self.selected_index < len(findings):
            self._draw_details_panel(stdscr, findings[self.selected_index], max_y, max_x)

    def _draw_details_panel(self, stdscr: Any, finding: Finding, max_y: int, max_x: int) -> None:
        """Draw the details panel for a selected finding.

        Args:
            stdscr: The curses standard screen.
            finding: The selected finding.
            max_y: Maximum Y (rows).
            max_x: Maximum X (columns).
        """
        import curses

        detail_lines = [
            "",
            f" Rule: {finding.rule_id} ({finding.severity})",
            f" Category: {finding.category}",
            f" Key: {finding.key}",
            f" Value: {finding.value[:50]}{'...' if len(finding.value) > 50 else ''}",
            f" File: {finding.source_file}:{finding.line_number}",
            f" Description: {finding.description}",
            f" Fix: {finding.fix_suggestion}",
        ]

        panel_y = max_y - len(detail_lines) - 1
        if panel_y < 3:
            panel_y = 3

        try:
            stdscr.addstr(panel_y, 0, "-" * (max_x - 1))
        except curses.error:
            pass

        for i, line in enumerate(detail_lines):
            row = panel_y + 1 + i
            if row >= max_y:
                break
            try:
                stdscr.addstr(row, 0, line[:max_x - 1])
            except curses.error:
                pass

    def _handle_curses_key(self, key: int) -> None:
        """Handle a key press in curses mode.

        Args:
            key: The curses key code.
        """
        findings = self.get_filtered_findings()

        if key == ord("q") or key == ord("Q"):
            self._running = False
        elif key == ord("d") or key == ord("D"):
            self.show_details = not self.show_details
        elif key == ord("f") or key == ord("F"):
            self._cycle_filter()
        elif key == curses.KEY_UP or key == ord("k"):
            if self.selected_index > 0:
                self.selected_index -= 1
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
        elif key == curses.KEY_DOWN or key == ord("j"):
            if self.selected_index < len(findings) - 1:
                self.selected_index += 1
                visible = self._get_visible_rows()
                if self.selected_index >= self.scroll_offset + visible:
                    self.scroll_offset = self.selected_index - visible + 1
        elif key == curses.KEY_PPAGE:  # Page Up
            self.scroll_offset = max(0, self.scroll_offset - 10)
            self.selected_index = min(self.selected_index, self.scroll_offset)
        elif key == curses.KEY_NPAGE:  # Page Down
            visible = self._get_visible_rows()
            self.scroll_offset = min(len(findings) - visible, self.scroll_offset + 10)
            self.selected_index = max(self.selected_index, self.scroll_offset)

    def _get_visible_rows(self) -> int:
        """Get the number of visible rows in the findings list.

        Returns:
            The number of visible rows (estimated).
        """
        return 20  # Default estimate

    def _cycle_filter(self) -> None:
        """Cycle through filter options."""
        # Cycle severity
        current_sev_idx = self.SEVERITY_LEVELS.index(self.filter_severity)
        next_sev_idx = (current_sev_idx + 1) % len(self.SEVERITY_LEVELS)
        self.filter_severity = self.SEVERITY_LEVELS[next_sev_idx]

        # Reset selection
        self.selected_index = 0
        self.scroll_offset = 0

    def _run_simple(self) -> int:
        """Run a simple non-curses interactive mode.

        Falls back to this when curses is not available.

        Returns:
            Exit code (0).
        """
        c = self.colors

        print(c.header("\n  EnvGuard Interactive Dashboard"))
        print(c.dim("  " + "=" * 50))
        print(c.dim("  (curses not available, running in simple mode)"))
        print("")

        while self._running:
            findings = self.get_filtered_findings()

            print(c.bold(f"  Filter: severity={self.filter_severity}, category={self.filter_category}"))
            print(f"  Showing {len(findings)}/{self.result.total_count} findings")
            print("")

            if not findings:
                print(c.success("  No findings match current filters."))
            else:
                for i, finding in enumerate(findings):
                    marker = " > " if i == self.selected_index else "   "
                    sev = c.severity_text(finding.severity, finding.severity.upper())
                    print(
                        f"{marker}{sev} [{finding.rule_id}] "
                        f"{finding.key}: {finding.description}"
                    )

            if findings and 0 <= self.selected_index < len(findings):
                finding = findings[self.selected_index]
                print("")
                print(c.dim("  " + "-" * 50))
                print(c.bold(f"  Details for [{finding.rule_id}]:"))
                print(f"  Key:        {finding.key}")
                print(f"  Severity:   {finding.severity}")
                print(f"  Category:   {finding.category}")
                print(f"  File:       {finding.source_file}:{finding.line_number}")
                print(f"  Value:      {finding.value[:60]}")
                print(f"  Description: {finding.description}")
                print(f"  Fix:        {finding.fix_suggestion}")

            print("")
            print(c.dim("  Commands: [n]ext [p]rev [f]ilter [q]uit"))

            try:
                cmd = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if cmd == "q":
                self._running = False
            elif cmd == "n":
                if self.selected_index < len(findings) - 1:
                    self.selected_index += 1
            elif cmd == "p":
                if self.selected_index > 0:
                    self.selected_index -= 1
            elif cmd == "f":
                current_idx = self.SEVERITY_LEVELS.index(self.filter_severity)
                next_idx = (current_idx + 1) % len(self.SEVERITY_LEVELS)
                self.filter_severity = self.SEVERITY_LEVELS[next_idx]
                self.selected_index = 0

        return 0


def run_dashboard(args: argparse.Namespace) -> int:
    """Run the TUI dashboard with the given arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    colors = Colors(enabled=not args.no_color)
    fs = FileSystemHelper()

    # Find and scan env files
    env_files = fs.find_env_files()
    config_files = fs.find_config_files()
    all_files = env_files + config_files

    if not all_files:
        print(colors.warn("No configuration files found to display."))
        return 0

    # Find template
    template_path: Optional[str] = None
    for f in env_files:
        basename = os.path.basename(f)
        if basename.endswith((".example", ".sample", ".template")):
            template_path = f
            break

    detector = DriftDetector(min_severity="info")

    try:
        result = detector.scan_files(all_files, template_path)
    except Exception as e:
        print(colors.error(f"Error scanning files: {e}"), file=sys.stderr)
        return 1

    dashboard = TUIDashboard(result, no_color=args.no_color)
    return dashboard.run()
