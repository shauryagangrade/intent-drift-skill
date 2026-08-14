#!/usr/bin/env python3
"""Context collection utilities for automatic context gathering."""

import re
import subprocess
from pathlib import Path
from typing import Any

_REDACTED = "***REDACTED***"

# Well-known token prefixes: GitHub (ghp_/gho_/ghu_/ghs_/ghr_/github_pat_),
# OpenAI (sk-), AWS (AKIA/ASIA), Slack (xox*), GitLab (glpat-), and JWTs.
_TOKEN_PREFIX = re.compile(
    r"(?i)\b(gh[pousr]_[a-zA-Z0-9]{10,}|github_pat_[a-zA-Z0-9_]{20,}|sk-[a-zA-Z0-9]{16,}|"
    r"AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|xox[baprs]-[a-zA-Z0-9-]{10,}|glpat-[a-zA-Z0-9_-]{20,}|"
    r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})"
)

# Authorization header / assignment values (mask the whole value).
_AUTHORIZATION = re.compile(r"(?im)(\bAuthorization\s*[:=]\s*)([^\r\n]+)")

# Standalone bearer tokens not already covered by the Authorization rule.
_BEARER = re.compile(r"(?i)(\bbearer\s+)([a-zA-Z0-9._~+/=-]{16,})")

# Assignments whose key names a secret: NAME=value or NAME: value, where the
# value stops at whitespace, quotes, '&', or '#' (covers diff lines, shell
# exports, and URL query parameters).
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b[a-z0-9_.-]*(?:secret|token|password|passwd|api[_-]?key|access[_-]?key|"
    r"private[_-]?key|client[_-]?secret|credential|auth[_-]?key)[a-z0-9_.-]*\s*[:=]\s*)"
    r"([^&\s\"'#]+)"
)

# A bare `key=`/`key:` with a long (16+ char) value is usually a real secret;
# short values such as "name" or "value" are left alone to avoid false
# positives on dict literals and config examples.
_SUSPICIOUS_KEY = re.compile(r"(?i)(\b[a-z0-9_.-]*key\s*[:=]\s*)([^&\s\"'#]{16,})")

# Long base64-looking blobs. Only blobs containing '+' or '/' (true base64)
# or ending in '=' padding are masked, so pure-hex strings (e.g. SHAs) in
# diffs are preserved.
_LONG_BASE64 = re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/])")


def sanitize_text(text: str) -> str:
    """Mask secret-like content in collected context.

    Masks well-known token prefixes, Authorization/Bearer values, assignments
    whose key names a secret (password, token, api key, credential, ...), bare
    ``key=`` values that are long enough to be real keys, and long base64
    blobs. Benign prose, identifiers, and hashes are left unchanged.
    """
    text = _TOKEN_PREFIX.sub(_REDACTED, text)
    text = _AUTHORIZATION.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _BEARER.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _SECRET_ASSIGNMENT.sub(lambda m: m.group(1) + _REDACTED, text)
    text = _SUSPICIOUS_KEY.sub(lambda m: m.group(1) + _REDACTED, text)

    def _mask_base64(match: re.Match[str]) -> str:
        blob = match.group(0)
        if "+" in blob or "/" in blob or blob.endswith("="):
            return _REDACTED
        return blob

    return _LONG_BASE64.sub(_mask_base64, text)


class ContextCollector:
    """Collects execution context from git, file system, and shell history."""

    def __init__(self, repo_path: Path | None = None, sanitize_secrets: bool = True):
        """Initialize the context collector.

        Args:
            repo_path: Path to the repository to analyze (defaults to cwd)
            sanitize_secrets: Mask secret-like content in collected context
                (default True; disable with False to keep raw output)
        """
        self.repo_path = repo_path or Path.cwd()
        self.sanitize_secrets = sanitize_secrets

    def collect_all(self) -> dict[str, Any]:
        """Collect all available context.

        Returns:
            Dictionary with execution context data
        """
        context: dict[str, Any] = {}

        # Git-based context
        context["git_diff"] = self.get_git_diff()
        context["recent_commits"] = self.get_recent_commits()
        context["edited_files"] = self.get_edited_files()

        # Shell command history
        context["recent_commands"] = self.get_recent_commands()

        # File changes
        context["file_changes"] = self.get_file_changes()

        # Analysis metadata
        context["metadata"] = {
            "repo_path": str(self.repo_path),
            "collected_at": self.get_timestamp(),
        }

        # Mask secret-like content before the context is handed to the
        # analyzer and exporters (default-on scrub).
        if self.sanitize_secrets:
            context["git_diff"] = sanitize_text(context["git_diff"])
            context["recent_commits"] = [
                sanitize_text(commit) for commit in context["recent_commits"]
            ]
            context["recent_commands"] = [
                sanitize_text(command) for command in context["recent_commands"]
            ]

        return context

    def get_git_diff(self) -> str:
        """Get git diff for uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return ""

    def get_recent_commits(self, count: int = 5) -> list[str]:
        """Get recent commit messages."""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"-{count}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return []

    def get_edited_files(self) -> list[str]:
        """Get list of recently edited files."""
        edited = []

        # Git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # Format: XY filename
                        parts = line.split()
                        if len(parts) >= 2:
                            edited.append(parts[-1])
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Also check for recently modified files
        try:
            import time

            now = time.time()
            for path in self.repo_path.rglob("*"):
                if path.is_file() and path.stat().st_mtime > (now - 3600):  # Last hour
                    edited.append(str(path.relative_to(self.repo_path)))
        except (OSError, PermissionError):
            pass

        return list(set(edited))  # Remove duplicates

    def get_recent_commands(self) -> list[str]:
        """Get recent shell commands from history."""
        commands = []

        # Check common shell history files
        history_files = [
            Path.home() / ".bash_history",
            Path.home() / ".zsh_history",
            Path.home() / ".history",
        ]

        for hist_file in history_files:
            if hist_file.exists():
                try:
                    with open(hist_file, errors="ignore") as f:
                        lines = f.readlines()
                        # Get last 20 commands
                        commands.extend(lines[-20:])
                except (OSError, PermissionError):
                    continue

        # Clean and filter
        cleaned = []
        for cmd in commands:
            cmd = cmd.strip()
            if cmd and not cmd.startswith("#"):
                # Remove timestamps from zsh history
                if cmd[0].isdigit() and ";" in cmd[:20]:
                    cmd = cmd.split(";", 1)[-1]
                cleaned.append(cmd)

        return cleaned[-20:] if cleaned else []

    def get_file_changes(self) -> dict[str, Any]:
        """Analyze file changes for insights."""
        changes: dict[str, list[str]] = {"added": [], "modified": [], "deleted": []}

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    status = line[:2]
                    filename = line[3:]

                    if status[0] == "A" or status[1] == "A":
                        changes["added"].append(filename)
                    elif status[0] == "D" or status[1] == "D":
                        changes["deleted"].append(filename)
                    elif status[0] in ("M", "R") or status[1] in ("M", "R"):
                        changes["modified"].append(filename)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return changes

    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()
