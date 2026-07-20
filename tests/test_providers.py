"""Tests for evidence providers."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from providers.goal_provider import GoalProvider
from providers.constraint_provider import ConstraintProvider
from providers.problematic_findings_provider import ProblematicFindingsProvider


def _ctx(goal, plan, exec_context=None):
    return {
        "original_goal": {"text": goal},
        "current_plan": {"text": plan},
        "execution_context": exec_context or {},
    }


def test_goal_provider_high_overlap():
    p = GoalProvider()
    ev = p.collect(_ctx("reduce memory usage at runtime", "reduce memory usage at runtime"))
    assert ev[0].value > 50


def test_goal_provider_low_overlap():
    p = GoalProvider()
    ev = p.collect(_ctx("reduce memory usage", "rewrite the auth layer"))
    assert ev[0].value < 50


def test_constraint_provider_satisfied():
    ctx = _ctx(
        "add caching",
        "implement cache",
        {"constraints": ["must stay under 100ms"]},
    )
    ctx["original_goal"]["constraints"] = ["must stay under 100ms"]
    ctx["current_plan"] = {"text": "implement cache", "steps": ["add cache", "stay under 100ms"]}
    p = ConstraintProvider()
    ev = p.collect(ctx)
    assert all(e.value >= 0 for e in ev)


def test_problematic_findings_detects_low_similarity():
    p = ProblematicFindingsProvider()
    ev = p.collect(_ctx("reduce memory usage", "rewrite the auth layer entirely"))
    assert any("drift" in e.details.lower() for e in ev)
