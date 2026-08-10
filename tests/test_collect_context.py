"""Tests for the auto context collector."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from scripts.collect_context import ContextCollector


def test_collector_runs_without_error(tmp_path):
    # Use a temp dir that is not a git repo; collector should degrade gracefully
    c = ContextCollector(repo_path=tmp_path)
    ctx = c.collect_all()
    assert "edited_files" in ctx
    assert "recent_commands" in ctx
    assert "metadata" in ctx
    assert "repo_path" in ctx["metadata"]


def test_get_recent_commands_safe():
    c = ContextCollector(repo_path=tmp_path_for())
    # Should not raise even with no history files
    assert isinstance(c.get_recent_commands(), list)


def tmp_path_for():
    import tempfile

    return Path(tempfile.mkdtemp())
