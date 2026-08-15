"""Tests for config loading: defaults.yaml + user.yaml merge (#11)."""

import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

# History is persisted per analysis; route it to a throwaway location so the
# unit tests never touch the real ~/.local/share/intent-drift/history.json.
_TMP_DIR = tempfile.mkdtemp(prefix="intent-drift-test-")

import analyzer as analyzer_mod
import config as config_mod
from analyzer import IntentDriftAnalyzer


def _write_yaml(path: Path, data: dict) -> Path:
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _base_config():
    return {
        "original_goal": "Reduce the application's memory usage at runtime.",
        "current_plan": "Optimize startup initialization for faster application load.",
        "execution_context": "Edited: main.py, startup.py.",
        "auto_context": False,
        "format": "text",
        "threshold": 75,
        # History is persisted per analysis; route it away from the real
        # ~/.local/share/intent-drift/history.json (#20).
        "history_path": str(Path(_TMP_DIR) / "history.json"),
    }


@pytest.mark.parametrize(
    ("base", "overlay", "expected"),
    [
        # Nested dicts merge recursively; the overlay wins per key while base
        # keys the overlay doesn't mention survive.
        (
            {"analysis": {"threshold": 75, "weights": {"a": 1}}},
            {"analysis": {"weights": {"b": 2}}},
            {"analysis": {"threshold": 75, "weights": {"a": 1, "b": 2}}},
        ),
        # An overlay list replaces the base list wholesale (no element merge).
        ({"tags": ["a", "b"]}, {"tags": ["c"]}, {"tags": ["c"]}),
        # An overlay None replaces the base value; it is not treated as absent.
        ({"x": 1}, {"x": None}, {"x": None}),
        # An overlay scalar replaces a nested dict wholesale.
        ({"x": {"nested": 1}}, {"x": 5}, {"x": 5}),
        # Base-only keys are preserved.
        ({"a": 1, "b": 2}, {"a": 9}, {"a": 9, "b": 2}),
        # An empty overlay is a no-op.
        ({"a": {"b": 1}}, {}, {"a": {"b": 1}}),
        # New overlay keys (including new nested subtrees) are added.
        ({"a": 1}, {"new": {"k": 1}}, {"a": 1, "new": {"k": 1}}),
    ],
)
def test_deep_merge_semantics(base, overlay, expected):
    """Pin the documented _deep_merge behavior directly (#79)."""
    assert config_mod._deep_merge(base, overlay) == expected


def test_deep_merge_does_not_mutate_inputs():
    """_deep_merge returns a new dict and never mutates either input (#79)."""
    base = {
        "analysis": {"threshold": 75, "weights": {"a": 1}},
        "tags": ["x"],
    }
    overlay = {
        "analysis": {"threshold": 60, "weights": {"b": 2}},
        "tags": ["y"],
    }
    base_before = deepcopy(base)
    overlay_before = deepcopy(overlay)

    result = config_mod._deep_merge(base, overlay)

    assert base == base_before
    assert overlay == overlay_before
    assert result is not base
    assert result == {
        "analysis": {"threshold": 60, "weights": {"a": 1, "b": 2}},
        "tags": ["y"],
    }


def test_load_defaults_reads_packaged_defaults_yaml():
    merged = config_mod.load_config()
    assert merged["analysis"]["threshold"] == 75
    assert merged["export"]["default_format"] == "text"
    assert merged["export"]["file"] is None
    assert merged["export"]["include_metadata"] is True
    assert merged["context_collection"]["lookback_hours"] == 24
    # Privacy: shell history must be off unless the user opts in (#13).
    assert merged["context_collection"]["methods"]["recent_commands"] is False


def test_user_yaml_overrides_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    user = tmp_path / "user.yaml"
    _write_yaml(
        defaults,
        {"analysis": {"threshold": 75}, "export": {"default_format": "text"}},
    )
    _write_yaml(
        user,
        {"analysis": {"threshold": 60}, "export": {"default_format": "json"}},
    )
    merged = config_mod.load_config(defaults_path=defaults, user_path=user)
    assert merged["analysis"]["threshold"] == 60
    assert merged["export"]["default_format"] == "json"


def test_user_yaml_deep_merge_keeps_unset_keys(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    user = tmp_path / "user.yaml"
    _write_yaml(
        defaults,
        {
            "analysis": {"threshold": 75, "weights": {"goal_provider": 0.5}},
            "export": {"default_format": "text"},
        },
    )
    _write_yaml(user, {"analysis": {"threshold": 60}})
    merged = config_mod.load_config(defaults_path=defaults, user_path=user)
    assert merged["analysis"]["threshold"] == 60
    # Keys the user file doesn't mention keep their default values: the file's
    # single weight overrides that entry while the built-in weights survive.
    weights = merged["analysis"]["weights"]
    assert weights["goal_provider"] == 0.5
    assert weights["constraint_provider"] == 0.20


def test_missing_user_yaml_uses_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    _write_yaml(defaults, {"analysis": {"threshold": 55}})
    merged = config_mod.load_config(defaults_path=defaults, user_path=tmp_path / "nope.yaml")
    assert merged["analysis"]["threshold"] == 55


def test_missing_defaults_file_falls_back_to_builtin_defaults(tmp_path):
    merged = config_mod.load_config(
        defaults_path=tmp_path / "nope.yaml", user_path=tmp_path / "nope2.yaml"
    )
    assert merged["analysis"]["threshold"] == 75
    assert merged["export"]["include_metadata"] is True


def test_cli_overrides_user_config(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    user = tmp_path / "user.yaml"
    _write_yaml(defaults, {"analysis": {"threshold": 75}})
    _write_yaml(user, {"analysis": {"threshold": 60}})
    base = config_mod.effective_config(
        config_mod.load_config(defaults_path=defaults, user_path=user)
    )
    a = IntentDriftAnalyzer()
    assert a.parse_arguments(["--threshold", "40"], defaults=base)["threshold"] == 40
    # Without the flag, the user value wins over the default.
    assert a.parse_arguments([], defaults=base)["threshold"] == 60


def test_config_auto_enabled_becomes_auto_context(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    _write_yaml(defaults, {"context_collection": {"auto_enabled": True}})
    base = config_mod.effective_config(config_mod.load_config(defaults_path=defaults))
    a = IntentDriftAnalyzer()
    assert a.parse_arguments([], defaults=base)["auto_context"] is True
    assert a.parse_arguments(["--auto-context"], defaults=base)["auto_context"] is True


def test_invalid_threshold_range_raises(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    _write_yaml(defaults, {"analysis": {"threshold": 150}})
    try:
        config_mod.load_config(defaults_path=defaults)
    except ValueError as exc:
        assert "analysis.threshold" in str(exc)
    else:
        raise AssertionError("expected ValueError for out-of-range threshold")


def test_invalid_format_raises(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    _write_yaml(defaults, {"export": {"default_format": "xml"}})
    try:
        config_mod.load_config(defaults_path=defaults)
    except ValueError as exc:
        assert "export.default_format" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown format")


def test_invalid_weights_raise(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    _write_yaml(defaults, {"analysis": {"weights": {"goal_provider": "heavy"}}})
    try:
        config_mod.load_config(defaults_path=defaults)
    except ValueError as exc:
        assert "analysis.weights.goal_provider" in str(exc)
    else:
        raise AssertionError("expected ValueError for non-numeric weight")


def test_malformed_yaml_raises(tmp_path):
    bad = tmp_path / "defaults.yaml"
    bad.write_text("analysis: [unclosed", encoding="utf-8")
    try:
        config_mod.load_config(defaults_path=bad)
    except ValueError as exc:
        assert "Invalid YAML" in str(exc)
    else:
        raise AssertionError("expected ValueError for malformed YAML")


def test_export_report_honors_include_metadata():
    a = IntentDriftAnalyzer()
    report = a.analyze(_base_config())

    assert "Report generated at" in a.export_report(report, "text")
    assert "Report generated at" not in a.export_report(report, "text", include_metadata=False)

    assert "Report generated at" in a.export_report(report, "markdown")
    assert "Report generated at" not in a.export_report(report, "markdown", include_metadata=False)

    full = json.loads(a.export_report(report, "json"))
    assert "generated_at" in full
    slim = json.loads(a.export_report(report, "json", include_metadata=False))
    assert "generated_at" not in slim


def test_main_writes_to_export_file(tmp_path, monkeypatch, capsys):
    out_file = tmp_path / "nested" / "report.txt"

    monkeypatch.setattr(
        sys,
        "argv",
        ["analyzer.py", "--original-goal", "G", "--current-plan", "P"],
    )
    monkeypatch.setattr(
        analyzer_mod,
        "load_config",
        lambda: {
            "analysis": {"threshold": 75},
            "export": {
                "default_format": "text",
                "file": str(out_file),
                "include_metadata": False,
            },
            "context_collection": {"auto_enabled": False, "lookback_hours": 24},
        },
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "analyze",
        lambda self, config: SimpleNamespace(overall_alignment=90),
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "export_report",
        lambda self, report, format, include_metadata=True: "report body",
    )

    analyzer_mod.main()

    assert out_file.read_text(encoding="utf-8") == "report body\n"
    assert capsys.readouterr().out == ""


def test_main_prints_to_stdout_when_no_export_file(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["analyzer.py", "--original-goal", "G", "--current-plan", "P"],
    )
    monkeypatch.setattr(
        analyzer_mod,
        "load_config",
        lambda: {
            "analysis": {"threshold": 75},
            "export": {"default_format": "text", "file": None, "include_metadata": True},
            "context_collection": {"auto_enabled": False, "lookback_hours": 24},
        },
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "analyze",
        lambda self, config: SimpleNamespace(overall_alignment=90),
    )
    monkeypatch.setattr(
        IntentDriftAnalyzer,
        "export_report",
        lambda self, report, format, include_metadata=True: "report body",
    )

    analyzer_mod.main()

    assert capsys.readouterr().out == "report body\n"
