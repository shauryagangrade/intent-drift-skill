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
    c = ContextCollector(repo_path=tmp_path_for())
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
