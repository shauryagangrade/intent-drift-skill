#!/usr/bin/env python3
"""Context collection utilities for automatic context gathering."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import json
import os

class ContextCollector:
    """Collects execution context from git, file system, and shell history."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize the context collector.

        Args:
            repo_path: Path to the repository to analyze (defaults to cwd)
        """
        self.repo_path = repo_path or Path.cwd()

    def collect_all(self) -> Dict[str, Any]:
        """Collect all available context.

        Returns:
            Dictionary with execution context data
        """
        context = {}

        # Git-based context
        context['git_diff'] = self.get_git_diff()
        context['recent_commits'] = self.get_recent_commits()
        context['edited_files'] = self.get_edited_files()

        # Shell command history
        context['recent_commands'] = self.get_recent_commands()

        # File changes
        context['file_changes'] = self.get_file_changes()

        # Analysis metadata
        context['metadata'] = {
            'repo_path': str(self.repo_path),
            'collected_at': self.get_timestamp()
        }

        return context

    def get_git_diff(self) -> str:
        """Get git diff for uncommitted changes."""
        try:
            result = subprocess.run(
                ['git', 'diff', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return ""

    def get_recent_commits(self, count: int = 5) -> List[str]:
        """Get recent commit messages."""
        try:
            result = subprocess.run(
                ['git', 'log', f'--oneline', f'-{count}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return []

    def get_edited_files(self) -> List[str]:
        """Get list of recently edited files."""
        edited = []

        # Git status
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
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
            for path in self.repo_path.rglob('*'):
                if path.is_file() and path.stat().st_mtime > (now - 3600):  # Last hour
                    edited.append(str(path.relative_to(self.repo_path)))
        except (OSError, PermissionError):
            pass

        return list(set(edited))  # Remove duplicates

    def get_recent_commands(self) -> List[str]:
        """Get recent shell commands from history."""
        commands = []

        # Check common shell history files
        history_files = [
            Path.home() / '.bash_history',
            Path.home() / '.zsh_history',
            Path.home() / '.history'
        ]

        for hist_file in history_files:
            if hist_file.exists():
                try:
                    with open(hist_file, 'r', errors='ignore') as f:
                        lines = f.readlines()
                        # Get last 20 commands
                        commands.extend(lines[-20:])
                except (OSError, PermissionError):
                    continue

        # Clean and filter
        cleaned = []
        for cmd in commands:
            cmd = cmd.strip()
            if cmd and not cmd.startswith('#'):
                # Remove timestamps from zsh history
                if cmd[0].isdigit() and ';' in cmd[:20]:
                    cmd = cmd.split(';', 1)[-1]
                cleaned.append(cmd)

        return cleaned[-20:] if cleaned else []

    def get_file_changes(self) -> Dict[str, Any]:
        """Analyze file changes for insights."""
        changes = {
            'added': [],
            'modified': [],
            'deleted': []
        }

        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    status = line[:2]
                    filename = line[3:]

                    if status[0] == 'A' or status[1] == 'A':
                        changes['added'].append(filename)
                    elif status[0] == 'D' or status[1] == 'D':
                        changes['deleted'].append(filename)
                    elif status[0] in ('M', 'R') or status[1] in ('M', 'R'):
                        changes['modified'].append(filename)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return changes

    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()