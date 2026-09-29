"""Unit tests for IntentDriftAnalyzer."""

import sys
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

import analyzer as analyzer_mod
import config as config_mod
import history
from analyzer import IntentDriftAnalyzer

# History is persisted per analysis; route it to a throwaway location so the
# unit tests never touch the real ~/.local/share/intent-drift/history.json.
_TMP_DIR = tempfile.mkdtemp(prefix="intent-drift-test-")


def _base_config():
    return {
        "original_goal": "Reduce the application's memory usage at runtime.",
        "current_plan": "Optimize startup initialization for faster application load.",
        "execution_context": "Edited: main.py, startup.py.",
        "auto_context": False,
        "include_shell_history": False,
        "format": "text",
        "threshold": 75,
        "history_path": str(Path(_TMP_DIR) / "history.json"),
    }


def test_parse_arguments_basic():
    a = IntentDriftAnalyzer()
    cfg = a.parse_arguments(
        [
            "--original-goal",
            "Do X",
            "--current-plan",
            "Do Y",
            "--context",
            "ctx",
            "--format",
            "json",
            "--threshold",
            "60",
        ]
    )
    assert cfg["original_goal"] == "Do X"
    assert cfg["current_plan"] == "Do Y"
    assert cfg["execution_context"] == "ctx"
    assert cfg["format"] == "json"
    assert cfg["threshold"] == 60


def test_parse_arguments_missing_value_raises():
    """A value-taking flag at the end of argv must not raise IndexError (#4)."""
    a = IntentDriftAnalyzer()
    for flag in ("--original-goal", "--current-plan", "--context", "--format", "--threshold"):
        try:
            a.parse_arguments([flag])
        except ValueError as exc:
            assert f"Missing value for {flag}" in str(exc)
        else:
            raise AssertionError(f"expected ValueError for {flag}")


def test_parse_arguments_unknown_flag_raises():
    a = IntentDriftAnalyzer()
    try:
        a.parse_arguments(["--definitely-not-a-flag"])
    except ValueError as exc:
        assert "Unknown option" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_arguments_invalid_format_raises():
    a = IntentDriftAnalyzer()
    try:
        a.parse_arguments(["--format", "xml"])
    except ValueError as exc:
        assert "Invalid value for --format" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_parse_arguments_invalid_threshold_raises():
    a = IntentDriftAnalyzer()
    try:
        a.parse_arguments(["--threshold", "fast"])
    except ValueError as exc:
        assert "Invalid value for --threshold" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_analyze_returns_report():
    a = IntentDriftAnalyzer()
    report = a.analyze(_base_config())
    assert hasattr(report, "overall_alignment")
    assert hasattr(report, "status")
    assert 0 <= report.overall_alignment <= 100


def test_analyze_degrades_when_history_persist_fails(tmp_path, monkeypatch, capsys):
    """A failed history write must not kill an otherwise good analysis (#65)."""

    def fail_mkstemp(*_args, **_kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(history.tempfile, "mkstemp", fail_mkstemp)
    cfg = _base_config()
    cfg["history_path"] = str(tmp_path / "history.json")

    report = IntentDriftAnalyzer().analyze(cfg)

    assert 0 <= report.overall_alignment <= 100
    # The report still carries the timeline; only the disk write was skipped.
    assert report.timeline
    err = capsys.readouterr().err
    assert "Warning: could not persist history" in err


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX read-only directory semantics")
def test_analyze_completes_when_history_cannot_be_persisted(tmp_path, capsys):
    """A read-only history dir must not kill an otherwise good analysis (#65)."""
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)  # read-only: the history file cannot be created here
    cfg = _base_config()
    cfg["history_path"] = str(locked / "history.json")

    report = IntentDriftAnalyzer().analyze(cfg)

    assert 0 <= report.overall_alignment <= 100
    assert report.timeline
    err = capsys.readouterr().err
    assert "Warning: could not persist history" in err


def test_analyze_seeds_timeline_from_history():
    """Each run appends its score to the persisted timeline (#20)."""
    a = IntentDriftAnalyzer()
    # Dedicated history file so the point counts are not affected by other tests.
    cfg = _base_config()
    cfg["history_path"] = str(Path(_TMP_DIR) / "seed-timeline.json")

    first = a.analyze(cfg)
    assert len(first.timeline) == 1
    assert first.timeline[0]["score"] == first.overall_alignment
    assert first.timeline[0]["note"] == str(first.status)

    second = a.analyze(cfg)
    assert len(second.timeline) == 2
    assert second.timeline[-1]["score"] == second.overall_alignment
    # The earlier point is preserved across runs.
    assert second.timeline[0]["score"] == first.overall_alignment


def test_analyze_tolerates_missing_history_file():
    """A fresh install (no history file yet) must not fail (#20)."""
    a = IntentDriftAnalyzer()
    cfg = _base_config()
    cfg["history_path"] = str(Path(_TMP_DIR) / "never-written" / "history.json")
    report = a.analyze(cfg)
    assert len(report.timeline) == 1


def test_parse_arguments_include_shell_history_flag():
    a = IntentDriftAnalyzer()
    cfg = a.parse_arguments(["--auto-context", "--include-shell-history"])
    assert cfg["auto_context"] is True
    assert cfg["include_shell_history"] is True

    # The flag is off unless explicitly passed.
    assert a.parse_arguments(["--auto-context"])["include_shell_history"] is False


def test_auto_context_default_does_not_read_shell_history(monkeypatch):
    """analyze(--auto-context) collects repo signals but never shell history (#13)."""
    from scripts.collect_context import ContextCollector

    def _forbid(*_args, **_kwargs):
        raise AssertionError("shell history must not be read by default")

    monkeypatch.setattr(ContextCollector, "get_recent_commands", _forbid)
    a = IntentDriftAnalyzer()
    cfg = _base_config()
    cfg["auto_context"] = True
    report = a.analyze(cfg)
    assert 0 <= report.overall_alignment <= 100


def test_auto_context_opt_in_reads_shell_history(monkeypatch):
    from scripts.collect_context import ContextCollector

    monkeypatch.setattr(ContextCollector, "get_recent_commands", lambda self: ["pytest"])
    a = IntentDriftAnalyzer()
    cfg = _base_config()
    cfg["auto_context"] = True
    cfg["include_shell_history"] = True
    report = a.analyze(cfg)
    assert 0 <= report.overall_alignment <= 100


def test_auto_context_passes_structured_execution_context(monkeypatch):
    """Providers receive the structured dict (edited_files, recent_commands, ...)."""
    from scripts.collect_context import ContextCollector

    monkeypatch.setattr(
        ContextCollector,
        "collect_all",
        lambda self: {
            "git_diff": "",
            "recent_commits": [],
            "edited_files": ["main.py"],
            "recent_commands": [],
            "file_changes": {"added": [], "modified": [], "deleted": []},
            "metadata": {"repo_path": "/tmp", "collected_at": "2026-01-01T00:00:00"},
        },
    )
    a = IntentDriftAnalyzer()
    cfg = _base_config()
    cfg["auto_context"] = True
    report = a.analyze(cfg)
    assert 0 <= report.overall_alignment <= 100


def test_export_text_contains_status():
    a = IntentDriftAnalyzer()
    report = a.analyze(_base_config())
    out = a.export_report(report, "text")
    assert "Status:" in out
    assert "Recommendation:" in out


def test_export_json_is_parseable():
    import json

    a = IntentDriftAnalyzer()
    report = a.analyze(_base_config())
    out = a.export_report(report, "json")
    data = json.loads(out)
    assert "overall_alignment" in data
    assert "evidence" in data


def test_parse_arguments_history_flag():
    a = IntentDriftAnalyzer()
    cfg = a.parse_arguments(["--history"])
    assert cfg["history"] is True


def test_parse_arguments_compare():
    a = IntentDriftAnalyzer()
    cfg = a.parse_arguments(["--compare", "3"])
    assert cfg["compare"] == 3


def test_parse_arguments_compare_rejects_bad_values():
    a = IntentDriftAnalyzer()
    for args in (["--compare", "fast"], ["--compare", "0"], ["--compare", "-2"]):
        try:
            a.parse_arguments(args)
        except ValueError as exc:
            assert "--compare" in str(exc)
        else:
            raise AssertionError(f"expected ValueError for {args}")


def test_parse_arguments_help_prints_usage_and_exits():
    import contextlib
    import io

    a = IntentDriftAnalyzer()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            a.parse_arguments(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "--original-goal" in buf.getvalue()
    assert "--auto-context" in buf.getvalue()
    assert "--format" in buf.getvalue()
    assert "--threshold" in buf.getvalue()
    assert "--history" in buf.getvalue()
    assert "--compare" in buf.getvalue()


def test_parse_arguments_version_prints_and_exits():
    import contextlib
    import io

    a = IntentDriftAnalyzer()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            a.parse_arguments(["-V"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "intent-drift" in buf.getvalue()


def _isolate_history(monkeypatch, tmp_path):
    """Point the XDG fallback at an empty decoy so a test can never read the
    developer's real ~/.local/share/intent-drift/history.json (#20, #57)."""
    decoy = tmp_path / "untouched-default.json"
    monkeypatch.setattr(history, "default_history_path", lambda: decoy)
    return decoy


def _merged_config_with_history_path(history_path):
    """The shape effective_config() consumes, with history_path relocated."""
    return {
        "analysis": {"threshold": 75},
        "export": {"default_format": "text", "file": None, "include_metadata": True},
        "context_collection": {"auto_enabled": False, "lookback_hours": 24},
        "history": {"history_path": str(history_path)},
    }


def test_history_flag_reads_configured_history_path(tmp_path, monkeypatch, capsys):
    """--history must read history.history_path from the merged config (#57)."""
    _isolate_history(monkeypatch, tmp_path)
    relocated = tmp_path / "custom-timeline.json"
    history.save_history(
        relocated,
        [{"timestamp": 1_700_000_000, "score": 81.5, "note": "relocated"}],
    )
    monkeypatch.setattr(sys, "argv", ["analyzer.py", "--history"])
    monkeypatch.setattr(
        analyzer_mod,
        "load_config",
        lambda: _merged_config_with_history_path(relocated),
    )
    with pytest.raises(SystemExit) as exc:
        analyzer_mod.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "81.5" in out
    assert "relocated" in out
    assert "untouched-default" not in out


def test_analysis_persists_to_configured_history_path(tmp_path, monkeypatch):
    """The write path must honor history.history_path, not just --history (#57)."""
    _isolate_history(monkeypatch, tmp_path)
    relocated = tmp_path / "written-timeline.json"
    monkeypatch.setattr(
        analyzer_mod,
        "load_config",
        lambda: _merged_config_with_history_path(relocated),
    )
    base = _base_config()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analyzer.py",
            "--original-goal",
            base["original_goal"],
            "--current-plan",
            base["current_plan"],
        ],
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "export_report",
        lambda self, report, format, include_metadata=True: "ok",
    )
    analyzer_mod.main()

    assert relocated.exists(), "analysis must append to the configured history_path"
    assert len(history.load_history(relocated)) == 1
    assert not (tmp_path / "untouched-default.json").exists()


def test_end_to_end_user_yaml_relocates_timeline(tmp_path, monkeypatch, capsys):
    """A real user.yaml must relocate the timeline and --history must read it (#57)."""
    _isolate_history(monkeypatch, tmp_path)
    user_yaml = tmp_path / "user.yaml"
    relocated = tmp_path / "relocated.json"
    user_yaml.write_text(f"history:\n  history_path: {relocated}\n", encoding="utf-8")

    # Exercise the real user.yaml -> effective_config -> analyzer chain rather
    # than a hand-built dict (#57).
    monkeypatch.setattr(config_mod, "USER_PATH", user_yaml)
    monkeypatch.setattr(analyzer_mod, "load_config", config_mod.load_config)

    base = _base_config()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analyzer.py",
            "--original-goal",
            base["original_goal"],
            "--current-plan",
            base["current_plan"],
        ],
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "export_report",
        lambda self, report, format, include_metadata=True: "ok",
    )
    analyzer_mod.main()

    assert relocated.exists(), "user.yaml history.history_path must relocate the timeline"

    # --history must then read back from that same relocated file.
    monkeypatch.setattr(sys, "argv", ["analyzer.py", "--history"])
    with pytest.raises(SystemExit) as exc:
        analyzer_mod.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Intent-drift history (1 run)" in out
    assert "untouched-default" not in out
