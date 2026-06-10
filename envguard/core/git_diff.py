"""
Git diff analyzer for EnvGuard-CLI.

Compares environment configuration files across git commits, branches,
and history to track configuration evolution and detect drift.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class GitError(Exception):
    """Exception raised when a git operation fails."""

    def __init__(self, message: str) -> None:
        """Initialize a GitError.

        Args:
            message: Description of the git error.
        """
        self.message = message
        super().__init__(message)


@dataclass
class GitEnvChange:
    """Represents a single environment variable change between git states.

    Attributes:
        key: The environment variable name.
        old_value: The previous value (empty string if added).
        new_value: The new value (empty string if removed).
        change_type: The type of change ('added', 'removed', 'modified').
        commit_hash: The git commit hash where the change occurred.
        commit_message: The commit message.
        commit_date: The commit date string.
        file_path: The file path relative to the repository root.
    """

    key: str
    old_value: str
    new_value: str
    change_type: str
    commit_hash: str = ""
    commit_message: str = ""
    commit_date: str = ""
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the change to a dictionary.

        Returns:
            A dictionary representation of the change.
        """
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_type": self.change_type,
            "commit_hash": self.commit_hash,
            "commit_message": self.commit_message,
            "commit_date": self.commit_date,
            "file_path": self.file_path,
        }


@dataclass
class GitDiffResult:
    """Result of a git diff analysis for environment files.

    Attributes:
        changes: List of environment variable changes.
        from_ref: The source git reference.
        to_ref: The target git reference.
        files_compared: List of files that were compared.
        total_added: Number of added keys.
        total_removed: Number of removed keys.
        total_modified: Number of modified keys.
    """

    changes: List[GitEnvChange] = field(default_factory=list)
    from_ref: str = ""
    to_ref: str = ""
    files_compared: List[str] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0
    total_modified: int = 0

    def __post_init__(self) -> None:
        """Calculate summary statistics."""
        self.total_added = sum(1 for c in self.changes if c.change_type == "added")
        self.total_removed = sum(1 for c in self.changes if c.change_type == "removed")
        self.total_modified = sum(1 for c in self.changes if c.change_type == "modified")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            A dictionary representation of the result.
        """
        return {
            "summary": {
                "from_ref": self.from_ref,
                "to_ref": self.to_ref,
                "total_changes": len(self.changes),
                "added": self.total_added,
                "removed": self.total_removed,
                "modified": self.total_modified,
                "files_compared": self.files_compared,
            },
            "changes": [c.to_dict() for c in self.changes],
        }


class GitDiffAnalyzer:
    """Analyzes environment file changes across git history.

    Uses git commands to compare environment configurations between
    commits, branches, and points in time.

    Usage:
        analyzer = GitDiffAnalyzer()
        result = analyzer.diff_commits("HEAD~5", "HEAD", ".env")
        for change in result.changes:
            print(f"{change.change_type}: {change.key}")
    """

    def __init__(self, repo_path: Optional[str] = None) -> None:
        """Initialize the GitDiffAnalyzer.

        Args:
            repo_path: Path to the git repository. Defaults to current
                       working directory.

        Raises:
            GitError: If the path is not a git repository.
        """
        self.repo_path = os.path.abspath(repo_path or os.getcwd())
        if not self._is_git_repo():
            raise GitError(f"Not a git repository: {self.repo_path}")

    def _run_git(self, *args: str) -> str:
        """Run a git command and return its output.

        Args:
            *args: Git command arguments.

        Returns:
            The command output as a string.

        Raises:
            GitError: If the command fails.
        """
        cmd = ["git", "-C", self.repo_path] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise GitError(
                    f"git command failed: {' '.join(args)}\n"
                    f"stderr: {result.stderr.strip()}"
                )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise GitError(f"git command timed out: {' '.join(args)}")
        except FileNotFoundError:
            raise GitError("git is not installed or not in PATH")

    def _is_git_repo(self) -> bool:
        """Check if the current path is a git repository.

        Returns:
            True if it is a git repository, False otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def diff_commits(
        self,
        from_ref: str,
        to_ref: str,
        file_pattern: str = ".env*",
    ) -> GitDiffResult:
        """Compare environment files between two git references.

        Args:
            from_ref: The source git reference (commit, branch, tag).
            to_ref: The target git reference.
            file_pattern: Glob pattern for env files to compare.

        Returns:
            A GitDiffResult with all detected changes.
        """
        result = GitDiffResult(from_ref=from_ref, to_ref=to_ref)

        # Get list of env files that changed between refs
        changed_files = self._get_changed_files(from_ref, to_ref, file_pattern)
        result.files_compared = changed_files

        if not changed_files:
            return result

        # Get the diff content for each file
        for filepath in changed_files:
            changes = self._parse_env_diff(from_ref, to_ref, filepath)
            result.changes.extend(changes)

        return result

    def diff_branches(
        self,
        branch_a: str,
        branch_b: str,
        file_pattern: str = ".env*",
    ) -> GitDiffResult:
        """Compare environment files between two branches.

        Args:
            branch_a: The first branch name.
            branch_b: The second branch name.
            file_pattern: Glob pattern for env files to compare.

        Returns:
            A GitDiffResult with all detected changes.
        """
        return self.diff_commits(branch_a, branch_b, file_pattern)

    def diff_last_commits(
        self,
        n: int = 5,
        file_pattern: str = ".env*",
    ) -> List[GitDiffResult]:
        """Compare environment files across the last N commits.

        Args:
            n: The number of commits to go back.
            file_pattern: Glob pattern for env files to compare.

        Returns:
            A list of GitDiffResult objects, one per commit pair.
        """
        results: List[GitDiffResult] = []

        # Get the last N commits
        log_output = self._run_git(
            "log", f"--max-count={n}", "--format=%H", "--name-only", "--", file_pattern
        )

        if not log_output:
            return results

        lines = log_output.splitlines()
        commits: List[str] = []
        for line in lines:
            line = line.strip()
            if line and not os.path.basename(line).startswith("."):
                commits.append(line)

        # Compare consecutive commits
        for i in range(len(commits) - 1):
            result = self.diff_commits(commits[i + 1], commits[i], file_pattern)
            results.append(result)

        return results

    def get_env_history(
        self,
        filepath: str,
        max_commits: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get the history of changes to a specific env file.

        Args:
            filepath: Path to the environment file.
            max_commits: Maximum number of commits to examine.

        Returns:
            A list of dictionaries, each containing commit info and
            the env file content at that commit.
        """
        log_output = self._run_git(
            "log", f"--max-count={max_commits}", "--format=%H|%s|%ai", "--", filepath
        )

        if not log_output:
            return []

        history: List[Dict[str, Any]] = []
        for line in log_output.splitlines():
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue

            commit_hash, message, date = parts

            try:
                content = self._run_git("show", f"{commit_hash}:{filepath}")
            except GitError:
                content = ""

            history.append({
                "commit_hash": commit_hash,
                "commit_message": message,
                "commit_date": date,
                "file_content": content,
                "file_path": filepath,
            })

        return history

    def _get_changed_files(
        self,
        from_ref: str,
        to_ref: str,
        file_pattern: str,
    ) -> List[str]:
        """Get a list of env files that changed between two refs.

        Args:
            from_ref: The source git reference.
            to_ref: The target git reference.
            file_pattern: Glob pattern for files.

        Returns:
            A list of changed file paths.
        """
        try:
            output = self._run_git(
                "diff", "--name-only", f"--diff-filter=ACMR",
                from_ref, to_ref, "--", file_pattern
            )
        except GitError:
            return []

        if not output:
            return []

        return [f.strip() for f in output.splitlines() if f.strip()]

    def _parse_env_diff(
        self,
        from_ref: str,
        to_ref: str,
        filepath: str,
    ) -> List[GitEnvChange]:
        """Parse the git diff output for an env file.

        Args:
            from_ref: The source git reference.
            to_ref: The target git reference.
            filepath: The file path to diff.

        Returns:
            A list of GitEnvChange objects.
        """
        changes: List[GitEnvChange] = []

        try:
            diff_output = self._run_git(
                "diff", from_ref, to_ref, "--", filepath
            )
        except GitError:
            return changes

        # Get commit info for the to_ref
        commit_hash = ""
        commit_message = ""
        commit_date = ""
        try:
            commit_hash = self._run_git("rev-parse", "--short", to_ref)
            log_line = self._run_git(
                "log", "-1", "--format=%s|%ai", to_ref, "--", filepath
            )
            parts = log_line.split("|", 1)
            if len(parts) == 2:
                commit_message, commit_date = parts
        except GitError:
            pass

        # Parse the unified diff
        current_key = ""
        current_value_lines: List[str] = []
        in_hunk = False
        old_keys: Dict[str, str] = {}
        new_keys: Dict[str, str] = {}

        for line in diff_output.splitlines():
            # Hunk header
            if line.startswith("@@"):
                in_hunk = True
                continue

            if not in_hunk:
                continue

            # Added line
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                kv_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", content)
                if kv_match:
                    key = kv_match.group(1)
                    value = kv_match.group(2).strip().strip("\"'")
                    new_keys[key] = value

            # Removed line
            elif line.startswith("-") and not line.startswith("---"):
                content = line[1:]
                kv_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", content)
                if kv_match:
                    key = kv_match.group(1)
                    value = kv_match.group(2).strip().strip("\"'")
                    old_keys[key] = value

        # Detect changes
        all_keys = set(old_keys.keys()) | set(new_keys.keys())

        for key in sorted(all_keys):
            old_val = old_keys.get(key, "")
            new_val = new_keys.get(key, "")

            if key in new_keys and key not in old_keys:
                change_type = "added"
            elif key in old_keys and key not in new_keys:
                change_type = "removed"
            elif old_val != new_val:
                change_type = "modified"
            else:
                continue

            changes.append(GitEnvChange(
                key=key,
                old_value=old_val,
                new_value=new_val,
                change_type=change_type,
                commit_hash=commit_hash,
                commit_message=commit_message,
                commit_date=commit_date,
                file_path=filepath,
            ))

        return changes

    def get_current_branch(self) -> str:
        """Get the name of the current git branch.

        Returns:
            The current branch name, or 'HEAD' if detached.
        """
        try:
            return self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        except GitError:
            return "HEAD"

    def get_default_branch(self) -> str:
        """Get the default branch name (main or master).

        Returns:
            The default branch name.
        """
        for branch in ("main", "master"):
            try:
                self._run_git("rev-parse", "--verify", branch)
                return branch
            except GitError:
                continue
        return "main"
