"""Unit tests for the report history module (persistence + trend output)."""

import json
import sys
import threading
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

import history


def _point(score: float, note: str = "run", ts: int = 1700000000) -> dict:
    return {"timestamp": ts, "score": score, "note": note}


def test_load_history_missing_file_returns_empty(tmp_path):
    assert history.load_history(tmp_path / "nope" / "history.json") == []


def test_load_history_corrupt_json_returns_empty(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not json")
    assert history.load_history(path) == []


def test_load_history_non_list_returns_empty(tmp_path):
    path = tmp_path / "history.json"
    path.write_text('{"score": 50}')
    assert history.load_history(path) == []


def test_load_history_keeps_dict_points(tmp_path):
    path = tmp_path / "history.json"
    path.write_text(json.dumps([_point(80.0), "junk", _point(72.5)]))
    loaded = history.load_history(path)
    assert len(loaded) == 2
    assert loaded[0]["score"] == 80.0
    assert loaded[1]["note"] == "run"


def test_save_history_creates_parent_dirs_and_round_trips(tmp_path):
    path = tmp_path / "a" / "b" / "history.json"
    points = [_point(80.0), _point(72.5, ts=1700003600)]
    history.save_history(path, points)
    assert history.load_history(path) == points
    # The atomic temp file must not be left behind.
    assert not list(tmp_path.glob("a/b/.*.tmp"))


def test_save_history_concurrent_writers_never_corrupt_or_except(tmp_path):
    """Concurrent saves stay atomic and leave no temp litter (#66).

    Two writers persist different point sets to the same file in a tight
    loop. The old fixed-name temp (``history.json.tmp``) made writers share
    one file, so bytes could interleave (corrupt JSON) and a ``replace``
    could hit a temp the other writer already moved (ENOENT). With a unique
    temp per call plus an atomic ``os.replace``, every observed state is one
    writer's complete payload: no exception, valid JSON, no stray temp.
    """
    path = tmp_path / "history.json"
    sets = {
        "a": [_point(80.0, note="a"), _point(79.0, note="a2")],
        "b": [_point(70.0, note="b"), _point(69.0, note="b2")],
    }

    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def writer(name: str) -> None:
        try:
            barrier.wait()
            for _ in range(300):
                history.save_history(path, sets[name])
        except BaseException as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    # The file is always one writer's complete payload, never a byte mix.
    loaded = history.load_history(path)
    assert loaded in (sets["a"], sets["b"])
    # Valid JSON on disk.
    json.loads(path.read_text())
    # No temp files were left behind.
    assert not list(tmp_path.glob(".*.tmp"))


def test_current_point_uses_report_score_and_status():
    class FakeReport:
        overall_alignment = 72.5
        status = "Minor_Drift"

    point = history.current_point(FakeReport())
    assert point["score"] == 72.5
    assert point["note"] == "Minor_Drift"
    assert isinstance(point["timestamp"], int)


def test_current_point_custom_note():
    class FakeReport:
        overall_alignment = 60.0
        status = "Significant_Drift"

    point = history.current_point(FakeReport(), note="after refactor")
    assert point["note"] == "after refactor"


def test_format_history_empty():
    out = history.format_history([])
    assert "No intent-drift history recorded yet" in out


def test_format_history_renders_points():
    points = [_point(85.0, note="initial check", ts=1700000000), _point(72.5, ts=1700003600)]
    out = history.format_history(points)
    assert "Intent-drift history (2 runs)" in out
    assert "85.0% - initial check" in out
    assert "72.5% - run" in out


def test_format_compare_insufficient_history():
    assert "Not enough history" in history.format_compare([_point(80.0)], 1)


def test_format_compare_declining():
    points = [_point(85.0, ts=1700000000), _point(72.5, ts=1700003600)]
    out = history.format_compare(points, 1)
    assert "Trend vs 1 run ago" in out
    assert "85.0% " in out and "72.5%" in out
    assert "delta -12.5 pts" in out
    assert "Verdict: declining" in out


def test_format_compare_improving():
    points = [_point(60.0, ts=1700000000), _point(80.0, ts=1700003600)]
    assert "Verdict: improving" in history.format_compare(points, 1)


def test_format_compare_clamps_window_to_available_history():
    # Only 2 runs but --compare 5: compare against the single earlier run.
    points = [_point(85.0, ts=1700000000), _point(72.5, ts=1700003600)]
    out = history.format_compare(points, 5)
    assert "vs 1 run ago" in out


def test_format_compare_acceleration():
    # 3 points, --compare 2 spanning both steps: 90 -> 80 -> 72.
    points = [_point(90.0, ts=1700000000), _point(80.0, ts=1700003600), _point(72.0, ts=1700007200)]
    out = history.format_compare(points, 2)
    assert "Drift acceleration" in out
