"""Unit tests for IntentDriftAnalyzer."""

import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

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
