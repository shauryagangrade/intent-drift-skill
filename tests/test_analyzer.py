"""Unit tests for IntentDriftAnalyzer."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from analyzer import IntentDriftAnalyzer


def _base_config():
    return {
        "original_goal": "Reduce the application's memory usage at runtime.",
        "current_plan": "Optimize startup initialization for faster application load.",
        "execution_context": "Edited: main.py, startup.py.",
        "auto_context": False,
        "format": "text",
        "threshold": 75,
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


def test_analyze_returns_report():
    a = IntentDriftAnalyzer()
    report = a.analyze(_base_config())
    assert hasattr(report, "overall_alignment")
    assert hasattr(report, "status")
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
