"""Persist analysis reports and expose the running score trend.

Timeline points are small dicts with the shape the exporters already render:
``{"timestamp": <epoch seconds>, "score": <0-100 float>, "note": <str>}``.

Reports are kept in a per-user JSON file (``~/.local/share/intent-drift/
history.json`` by default, overridable via ``XDG_DATA_HOME``), and every
analysis seeds ``report.timeline`` with the stored history so exporters can
show the score trend instead of an empty list.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def default_history_path() -> Path:
    """Return the per-user history file (``$XDG_DATA_HOME`` aware)."""
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "intent-drift" / "history.json"


def load_history(path: Path) -> list[dict[str, Any]]:
    """Load persisted timeline points.

    A missing file or unreadable/corrupt JSON yields ``[]`` rather than
    raising, so a fresh install or an interrupted write never breaks analysis.
    """
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [point for point in data if isinstance(point, dict)]


def save_history(path: Path, points: list[dict[str, Any]]) -> None:
    """Persist timeline points atomically (write temp file, then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(points, indent=2))
    tmp.replace(path)


def current_point(report: Any, note: str | None = None) -> dict[str, Any]:
    """Build the timeline point for the run just analyzed."""
    return {
        "timestamp": int(time.time()),
        "score": float(report.overall_alignment),
        "note": note or str(report.status),
    }


def format_history(points: list[dict[str, Any]]) -> str:
    """Render the persisted score history as a human-readable table."""
    if not points:
        return "No intent-drift history recorded yet. Run an analysis to start the timeline."
    lines = [f"Intent-drift history ({len(points)} run{'s' if len(points) != 1 else ''})", "-" * 40]
    for i, point in enumerate(points, 1):
        stamp = datetime.fromtimestamp(point.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
        lines.append(f"  {i}. [{stamp}] {point.get('score', 0):.1f}% - {point.get('note', '')}")
    return "\n".join(lines)


def format_compare(points: list[dict[str, Any]], compare_n: int) -> str:
    """Summarize the trend of the current run against the last ``compare_n``.

    Compares the newest point with the one ``compare_n`` runs earlier (or the
    earliest available when fewer runs exist), reporting the total delta, the
    per-run rate, and — once enough points exist — whether the drift is
    accelerating.
    """
    if len(points) < 2:
        return "Not enough history to compare (need at least 2 runs)."

    current = points[-1]
    window = min(compare_n, len(points) - 1)
    base = points[-1 - window]

    current_score = float(current.get("score", 0.0))
    base_score = float(base.get("score", 0.0))
    delta = current_score - base_score
    per_run = delta / window

    stamp = datetime.fromtimestamp(current.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")
    base_stamp = datetime.fromtimestamp(base.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M")

    lines = [
        f"Trend vs {window} run{'s' if window != 1 else ''} ago: "
        f"{base_score:.1f}% ({base_stamp}) -> {current_score:.1f}% ({stamp}) "
        f"(delta {delta:+.1f} pts, {per_run:+.1f} pts/run)"
    ]
    lines.append(f"Verdict: {_verdict(delta)}")

    if len(points) >= 3:
        latest_interval = float(points[-1].get("score", 0.0)) - float(points[-2].get("score", 0.0))
        lines.append(
            f"Drift acceleration: latest run {latest_interval:+.1f} pts "
            f"vs {per_run:+.1f} pts/run average -> {_acceleration(latest_interval, per_run)}"
        )

    return "\n".join(lines)


def _verdict(delta: float) -> str:
    if delta > 0.5:
        return "improving"
    if delta < -0.5:
        return "declining"
    return "steady"


def _acceleration(latest: float, average: float) -> str:
    # Same direction as the trend and moving faster than average = accelerating.
    if latest > 0 and latest > average > 0:
        return "accelerating improvement"
    if latest < 0 and latest < average < 0:
        return "accelerating decline"
    if latest > 0.5 and average <= 0:
        return "improvement after decline"
    if latest < -0.5 and average >= 0:
        return "decline after improvement"
    return "stable trend"
