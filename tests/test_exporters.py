"""Tests for report exporters (text, markdown, json)."""

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from intent_alignment.models import AlignmentReport, Evidence

from exporters import JSONExporter, MarkdownExporter, TextExporter


def _full_report():
    """A report with evidence, a timeline, and a component breakdown."""
    return AlignmentReport(
        overall_alignment=72.5,
        confidence=80.0,
        status="Minor_Drift",
        breakdown={
            "goal_provider": {"score": 90.0, "weight": 0.2},
            "scope_provider": {"score": 55.0, "weight": 0.15},
        },
        summary="Plan mostly follows the original goal with some scope creep.",
        evidence=[
            Evidence(
                source="goal_provider",
                value=90.0,
                confidence=0.8,
                details="High semantic similarity between goal and plan",
            ),
            Evidence(
                source="scope_provider",
                value=55.0,
                confidence=0.6,
                details="Moderate scope expansion detected",
            ),
        ],
        risk="Low",
        recommendation="Continue, but review scope expansion before merging.",
        timeline=[
            {"timestamp": 1700000000, "score": 80.0, "note": "initial check"},
            {"timestamp": 1700003600, "score": 72.5, "note": "after scope expansion"},
        ],
    )


def _empty_report():
    """A report with no evidence, no timeline, and no breakdown."""
    return AlignmentReport(
        overall_alignment=0.0,
        confidence=0.0,
        status="Unknown",
        breakdown={},
        summary="No data available to analyze.",
        evidence=[],
        risk="Unknown",
        recommendation="No recommendation available.",
        timeline=[],
    )


def _report_with_evidence_no_timeline():
    """A report that has evidence but an empty timeline (single-shot analysis)."""
    return AlignmentReport(
        overall_alignment=45.0,
        confidence=70.0,
        status="Significant_Drift",
        breakdown={"goal_provider": {"score": 45.0, "weight": 0.2}},
        summary="Plan diverges from the original goal.",
        evidence=[
            Evidence(
                source="goal_provider",
                value=45.0,
                confidence=0.7,
                details="Low semantic similarity between goal and plan",
            )
        ],
        risk="High",
        recommendation="Revisit the plan against the original goal.",
        timeline=[],
    )


# ---------------------------------------------------------------------------
# TextExporter
# ---------------------------------------------------------------------------


def test_text_exporter_full_report():
    out = TextExporter().export(_full_report())
    assert "Intent Alignment Report" in out
    assert "Overall Alignment: 72.5%" in out
    assert "Status: Minor_Drift" in out
    assert "Confidence: 80.0%" in out
    assert "Risk: Low" in out
    assert "Recommendation: Continue, but review scope expansion before merging." in out
    assert "goal_provider" in out
    assert "scope_provider" in out
    assert "Timeline (trend):" in out
    assert "initial check" in out
    assert "Component Breakdown:" in out


def test_text_exporter_empty_report():
    out = TextExporter().export(_empty_report())
    assert "Status: Unknown" in out
    assert "Evidence:" in out
    assert "No historical data available" in out
    assert "Component Breakdown:" in out


def test_text_exporter_no_timeline():
    out = TextExporter().export(_report_with_evidence_no_timeline())
    assert "goal_provider" in out
    assert "No historical data available" in out


# ---------------------------------------------------------------------------
# MarkdownExporter
# ---------------------------------------------------------------------------


def test_markdown_exporter_full_report():
    out = MarkdownExporter().export(_full_report())
    assert "# Intent Alignment Report" in out
    assert "## Summary" in out
    assert "## Analysis" in out
    assert "## Evidence" in out
    assert "## Recommendation" in out
    assert "## Component Breakdown" in out
    assert "## Timeline" in out
    assert "| Component | Score | Weight |" in out
    assert "goal_provider" in out
    assert "| Time | Score | Note |" in out


def test_markdown_exporter_empty_report():
    out = MarkdownExporter().export(_empty_report())
    assert "# Intent Alignment Report" in out
    assert "*No historical data available*" in out
    # No breakdown rows, but the table header/structure should still be present.
    assert "## Component Breakdown" in out


def test_markdown_exporter_no_evidence_section_present():
    out = MarkdownExporter().export(_empty_report())
    assert "## Evidence" in out


# ---------------------------------------------------------------------------
# JSONExporter
# ---------------------------------------------------------------------------


def test_json_exporter_full_report_parses():
    out = JSONExporter().export(_full_report())
    data = json.loads(out)
    assert data["overall_alignment"] == 72.5
    assert data["status"] == "Minor_Drift"
    assert data["risk"] == "Low"
    assert len(data["evidence"]) == 2
    assert data["evidence"][0]["source"] == "goal_provider"
    assert "goal_provider" in data["breakdown"]
    assert len(data["timeline"]) == 2
    assert "generated_at" in data


def test_json_exporter_empty_report_parses():
    out = JSONExporter().export(_empty_report())
    data = json.loads(out)
    assert data["evidence"] == []
    assert data["timeline"] == []
    assert data["breakdown"] == {}
    assert data["status"] == "Unknown"


def test_json_exporter_no_timeline_parses():
    out = JSONExporter().export(_report_with_evidence_no_timeline())
    data = json.loads(out)
    assert data["timeline"] == []
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["details"] == "Low semantic similarity between goal and plan"
