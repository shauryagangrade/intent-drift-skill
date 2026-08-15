"""Tests for the auto context collector."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from scripts.collect_context import ContextCollector, sanitize_text


def test_sanitize_text_masks_secret_assignments():
    text = (
        "+export AWS_SECRET_ACCESS_KEY=supersecret123\n"
        "+db_password = hunter2\n"
        "+api_key=AKIAIOSFODNN7EXAMPLE\n"
        "+access_token: abc123def456ghi789\n"
    )
    out = sanitize_text(text)
    assert "supersecret123" not in out
    assert "hunter2" not in out
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "abc123def456ghi789" not in out


def test_sanitize_text_masks_authorization_and_bearer():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U\n"
    out = sanitize_text(text)
    assert "eyJhbGciOiJIUzI1NiJ9" not in out
    assert "REDACTED" in out


def test_sanitize_text_masks_token_prefixes_and_urls():
    text = "ghp_1234567890abcdef1234 deployed with sk-abcdefghijklmnop; see https://x.io/api?token=abc123def456"
    out = sanitize_text(text)
    assert "ghp_1234567890abcdef1234" not in out
    assert "sk-abcdefghijklmnop" not in out
    assert "abc123def456" not in out


def test_sanitize_text_masks_long_base64_blobs():
    blob = "VGhpcyBpcyBhIHZlcnkgbG9uZyBiYXNlNjQgZW5jb2RlZCBzZWNyZXQgdGhhdCBzaG91bGQgbm90IGxlYWs="
    out = sanitize_text(f"config = {blob}")
    assert blob not in out
    assert "REDACTED" in out


def test_sanitize_text_leaves_benign_content():
    text = (
        '+  "key": "value"\n+commit 9f61d9dc9cfb72a1901a1348280165f985559ac2\n+npm install numpy\n'
    )
    assert sanitize_text(text) == text


def test_collect_all_sanitizes_git_diff(monkeypatch):
    c = ContextCollector(repo_path=tmp_path_for())
    monkeypatch.setattr(
        c,
        "get_git_diff",
        lambda: "+export AWS_SECRET_ACCESS_KEY=supersecret123\n+normal code\n",
    )
    monkeypatch.setattr(c, "get_recent_commits", lambda: [])
    monkeypatch.setattr(c, "get_edited_files", lambda: [])
    monkeypatch.setattr(c, "get_recent_commands", lambda: [])
    monkeypatch.setattr(c, "get_file_changes", lambda: {"added": [], "modified": [], "deleted": []})
    monkeypatch.setattr(c, "get_timestamp", lambda: "2026-01-01T00:00:00")
    ctx = c.collect_all()
    assert "supersecret123" not in ctx["git_diff"]
    assert "normal code" in ctx["git_diff"]


def test_collect_all_sanitizes_recent_commands(monkeypatch):
    c = ContextCollector(repo_path=tmp_path_for(), include_shell_history=True)
    monkeypatch.setattr(c, "get_git_diff", lambda: "")
    monkeypatch.setattr(c, "get_recent_commits", lambda: [])
    monkeypatch.setattr(c, "get_edited_files", lambda: [])
    monkeypatch.setattr(
        c, "get_recent_commands", lambda: ["export AWS_SECRET_ACCESS_KEY=supersecret123"]
    )
    monkeypatch.setattr(c, "get_file_changes", lambda: {"added": [], "modified": [], "deleted": []})
    monkeypatch.setattr(c, "get_timestamp", lambda: "2026-01-01T00:00:00")
    ctx = c.collect_all()
    assert "supersecret123" not in ctx["recent_commands"][0]


def test_collect_all_skips_shell_history_by_default(monkeypatch):
    """collect_all must not read shell history unless explicitly opted in (#13)."""
    c = ContextCollector(repo_path=tmp_path_for())
    monkeypatch.setattr(c, "get_git_diff", lambda: "")
    monkeypatch.setattr(c, "get_recent_commits", lambda: [])
    monkeypatch.setattr(c, "get_edited_files", lambda: [])
    monkeypatch.setattr(
        c,
        "get_recent_commands",
        lambda: (_ for _ in ()).throw(AssertionError("shell history must not be read by default")),
    )
    monkeypatch.setattr(c, "get_file_changes", lambda: {"added": [], "modified": [], "deleted": []})
    monkeypatch.setattr(c, "get_timestamp", lambda: "2026-01-01T00:00:00")
    ctx = c.collect_all()
    assert ctx["recent_commands"] == []


def test_collect_all_includes_shell_history_when_opted_in(monkeypatch):
    c = ContextCollector(repo_path=tmp_path_for(), include_shell_history=True)
    monkeypatch.setattr(c, "get_git_diff", lambda: "")
    monkeypatch.setattr(c, "get_recent_commits", lambda: [])
    monkeypatch.setattr(c, "get_edited_files", lambda: [])
    monkeypatch.setattr(c, "get_recent_commands", lambda: ["git status", "npm test"])
    monkeypatch.setattr(c, "get_file_changes", lambda: {"added": [], "modified": [], "deleted": []})
    monkeypatch.setattr(c, "get_timestamp", lambda: "2026-01-01T00:00:00")
    ctx = c.collect_all()
    assert ctx["recent_commands"] == ["git status", "npm test"]


def test_collector_sanitize_disabled_keeps_raw(monkeypatch):
    c = ContextCollector(repo_path=tmp_path_for(), sanitize_secrets=False)
    monkeypatch.setattr(c, "get_git_diff", lambda: "+export AWS_SECRET_ACCESS_KEY=supersecret123\n")
    monkeypatch.setattr(c, "get_recent_commits", lambda: [])
    monkeypatch.setattr(c, "get_edited_files", lambda: [])
    monkeypatch.setattr(c, "get_recent_commands", lambda: [])
    monkeypatch.setattr(c, "get_file_changes", lambda: {"added": [], "modified": [], "deleted": []})
    monkeypatch.setattr(c, "get_timestamp", lambda: "2026-01-01T00:00:00")
    ctx = c.collect_all()
    assert "supersecret123" in ctx["git_diff"]


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


def test_recently_modified_skips_heavy_dirs(tmp_path, monkeypatch):
    """The non-git fallback walk must never descend into .git/node_modules/.venv."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("secret-ish but ignored")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("y")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("z")

    monkeypatch.setenv("GIT_DIR", str(tmp_path / ".git"))  # not a repo; forces fallback
    c = ContextCollector(repo_path=tmp_path, lookback_hours=1)
    edited = c._recently_modified_files()
    # Use os.path.join so the separator matches on Windows (src\app.py).
    assert str(Path("src") / "app.py") in edited
    assert not any("node_modules" in f or ".venv" in f or ".git" in f for f in edited)


def test_recently_modified_honors_lookback(tmp_path, monkeypatch):
    """Files older than the lookback window are not reported."""
    (tmp_path / "old.txt").write_text("old")
    old = tmp_path / "old.txt"
    import os

    os.utime(old, (0, 0))  # epoch: definitely outside any lookback window
    (tmp_path / "new.txt").write_text("new")

    monkeypatch.setenv("GIT_DIR", str(tmp_path / ".git"))
    c = ContextCollector(repo_path=tmp_path, lookback_hours=1)
    edited = c._recently_modified_files()
    assert "new.txt" in edited
    assert "old.txt" not in edited


def test_read_history_tail_reads_only_tail(tmp_path):
    from scripts.collect_context import HISTORY_TAIL_BYTES

    hist = tmp_path / ".zsh_history"
    # Build a file much larger than the tail window.
    header = "padding line\n" * (HISTORY_TAIL_BYTES // 14 + 100)
    header += "git status\n"
    header += "git log --oneline -5\n"
    hist.write_text(header)

    c = ContextCollector(repo_path=tmp_path)
    tail = c._read_history_tail(hist)
    # The last commands must be present in the tail.
    assert "git log --oneline -5" in tail
    assert tail.rstrip().endswith("git log --oneline -5")


def test_get_recent_commands_uses_tail(tmp_path, monkeypatch):
    """get_recent_commands returns only the last 20 commands."""
    hist = tmp_path / ".zsh_history"
    lines = [f"cmd-{i:02d}" for i in range(25)]
    lines += ["git status", "git log --oneline -3"]
    hist.write_text("\n".join(lines) + "\n")
    # Path.home() resolves via USERPROFILE on Windows (HOME is not consulted
    # there), so point both at the temp dir to keep the test cross-platform.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    c = ContextCollector(repo_path=tmp_path)
    commands = c.get_recent_commands()
    assert len(commands) == 20
    assert "git log --oneline -3" in commands  # the last command survives
    assert "cmd-00" not in commands  # the first commands are dropped
