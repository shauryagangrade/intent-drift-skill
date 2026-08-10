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

from providers.scope_provider import ScopeProvider
from providers.execution_provider import ExecutionProvider


def test_scope_provider_no_expansion():
    """Aligned case: current plan uses the same concepts as the original goal."""
    p = ScopeProvider()
    ev = p.collect(_ctx(
        "reduce memory usage at runtime",
        "reduce memory usage at runtime",
    ))
    assert ev[0].value >= 90


def test_scope_provider_detects_expansion():
    """Drifted case: current plan introduces many concepts not in the original goal."""
    p = ScopeProvider()
    ev = p.collect(_ctx(
        "reduce memory usage",
        "rewrite authentication database networking caching logging deployment pipeline monitoring",
    ))
    assert ev[0].value < 90


def test_scope_provider_empty_context():
    """Edge case: empty context dict should not raise, and should be treated as no goal/plan text."""
    p = ScopeProvider()
    ev = p.collect({})
    assert isinstance(ev, list)


def test_scope_provider_no_edited_files():
    """Edge case: execution_context present but edited_files missing entirely."""
    p = ScopeProvider()
    ctx = _ctx("add caching layer", "add caching layer", {"recent_commands": ["pytest"]})
    ev = p.collect(ctx)
    assert isinstance(ev, list)
    assert len(ev) > 0


def test_scope_provider_large_file_count_flagged():
    """Drifted case: large number of edited files should lower the score."""
    p = ScopeProvider()
    ctx = _ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": [f"file_{i}.py" for i in range(15)]},
    )
    ev = p.collect(ctx)
    file_evidence = [e for e in ev if "files modified" in e.details or "file changes" in e.details]
    assert len(file_evidence) > 0


def test_execution_provider_commands_align_with_plan():
    """Aligned case: recent commands share keywords with the current plan."""
    p = ExecutionProvider()
    ctx = _ctx(
        "reduce memory usage",
        "implement cache eviction policy",
        {"recent_commands": ["implement cache eviction policy tests"]},
    )
    ev = p.collect(ctx)
    assert len(ev) > 0
    assert any(e.value >= 70 for e in ev)


def test_execution_provider_missing_keys():
    """Edge case: execution_context present but missing recent_commands/edited_files/reasoning_summary keys."""
    p = ExecutionProvider()
    ctx = _ctx("reduce memory usage", "implement cache eviction policy", {})
    ev = p.collect(ctx)
    assert isinstance(ev, list)


def test_execution_provider_empty_context():
    """Edge case: fully empty context dict should not raise."""
    p = ExecutionProvider()
    ev = p.collect({})
    assert isinstance(ev, list)


def test_execution_provider_reasoning_matches_plan():
    """Aligned case: reasoning_summary references the current plan, not the stale goal."""
    p = ExecutionProvider()
    ctx = _ctx(
        "reduce memory footprint",
        "implement caching eviction",
        {"reasoning_summary": "implementing caching eviction strategy now"},
    )
    ev = p.collect(ctx)
    reasoning_evidence = [e for e in ev if "reasoning" in e.details.lower()]
    assert len(reasoning_evidence) > 0


from providers.dependency_provider import DependencyProvider
from providers.file_graph_provider import FileGraphProvider
from providers.architecture_provider import ArchitectureProvider
from providers.requirement_coverage_provider import RequirementCoverageProvider


def test_dependency_provider_no_changes():
    """Aligned case: no install/remove commands means no dependency drift."""
    p = DependencyProvider()
    ev = p.collect(_ctx("add caching layer", "add caching layer", {"recent_commands": ["pytest", "git status"]}))
    assert ev[0].value >= 80


def test_dependency_provider_detects_install():
    """Case: install commands present, checked against goal keyword alignment."""
    p = DependencyProvider()
    ev = p.collect(_ctx(
        "add caching layer with redis",
        "implement redis cache",
        {"recent_commands": ["pip install redis"]},
    ))
    assert len(ev) > 0
    assert ev[0].value >= 50


def test_dependency_provider_detects_removal():
    """Drifted case: dependency removal should lower the score."""
    p = DependencyProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"recent_commands": ["pip uninstall redis"]},
    ))
    assert ev[0].value < 50


def test_dependency_provider_missing_keys():
    """Edge case: execution_context present but recent_commands/edited_files missing."""
    p = DependencyProvider()
    ev = p.collect(_ctx("add caching layer", "add caching layer", {}))
    assert isinstance(ev, list)
    assert len(ev) > 0


def test_dependency_provider_empty_context():
    """Edge case: fully empty context dict should not raise."""
    p = DependencyProvider()
    ev = p.collect({})
    assert isinstance(ev, list)


def test_file_graph_provider_no_edited_files():
    """Edge case: no edited_files should return a full-score 'nothing to analyze' result."""
    p = FileGraphProvider()
    ev = p.collect(_ctx("add caching layer", "add caching layer", {}))
    assert ev[0].value == 100.0


def test_file_graph_provider_few_files():
    """Aligned case: small number of edited files, focused change."""
    p = FileGraphProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": ["cache.py", "cache_test.py"]},
    ))
    assert len(ev) > 0
    assert ev[0].value > 50


def test_file_graph_provider_many_files_flagged():
    """Drifted case: large number of edited files should lower the score."""
    p = FileGraphProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": [f"file_{i}.py" for i in range(30)]},
    ))
    assert ev[0].value < 100


def test_file_graph_provider_empty_context():
    """Edge case: fully empty context dict should not raise."""
    p = FileGraphProvider()
    ev = p.collect({})
    assert isinstance(ev, list)


def test_architecture_provider_main_file_edit():
    """Case: editing a main/entry-point file should be flagged as significant architectural work."""
    p = ArchitectureProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": ["main.py"]},
    ))
    main_evidence = [e for e in ev if "main application" in e.details.lower()]
    assert len(main_evidence) > 0


def test_architecture_provider_single_directory_focused():
    """Aligned case: changes focused in a single directory should score high."""
    p = ArchitectureProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": ["cache/store.py", "cache/utils.py"]},
    ))
    dir_evidence = [e for e in ev if "directory" in e.details.lower()]
    assert len(dir_evidence) > 0
    assert dir_evidence[0].value >= 90


def test_architecture_provider_spread_across_directories():
    """Drifted case: changes spread across many directories should lower the score."""
    p = ArchitectureProvider()
    ev = p.collect(_ctx(
        "add caching layer",
        "add caching layer",
        {"edited_files": ["a/x.py", "b/y.py", "c/z.py", "d/w.py"]},
    ))
    dir_evidence = [e for e in ev if "directories" in e.details.lower()]
    assert len(dir_evidence) > 0
    assert dir_evidence[0].value < 100


def test_architecture_provider_no_edited_files():
    """Edge case: no edited_files should not raise and returns unknown-structure evidence."""
    p = ArchitectureProvider()
    ev = p.collect(_ctx("add caching layer", "add caching layer", {}))
    assert isinstance(ev, list)
    assert len(ev) > 0


def test_architecture_provider_empty_context():
    """Edge case: fully empty context dict should not raise."""
    p = ArchitectureProvider()
    ev = p.collect({})
    assert isinstance(ev, list)


def test_requirement_coverage_no_success_criteria():
    """Edge case: missing success_criteria key returns full score, nothing to check."""
    p = RequirementCoverageProvider()
    ev = p.collect(_ctx("add caching layer", "add caching layer"))
    assert ev[0].value == 100.0


def test_requirement_coverage_high_coverage():
    """Aligned case: current plan steps address all stated success criteria."""
    p = RequirementCoverageProvider()
    ctx = _ctx("add caching layer", "add caching layer")
    ctx["original_goal"]["success_criteria"] = ["responses cached", "latency reduced"]
    ctx["current_plan"]["steps"] = ["implement responses cached in redis", "verify latency reduced under load"]
    ev = p.collect(ctx)
    assert ev[0].value >= 80


def test_requirement_coverage_low_coverage():
    """Drifted case: current plan steps do not address the stated success criteria."""
    p = RequirementCoverageProvider()
    ctx = _ctx("add caching layer", "rewrite unrelated auth module")
    ctx["original_goal"]["success_criteria"] = ["responses cached", "latency reduced"]
    ctx["current_plan"]["steps"] = ["rewrite auth module", "add login page"]
    ev = p.collect(ctx)
    assert ev[0].value < 50


def test_requirement_coverage_empty_context():
    """Edge case: fully empty context dict should not raise."""
    p = RequirementCoverageProvider()
    ev = p.collect({})
    assert isinstance(ev, list)