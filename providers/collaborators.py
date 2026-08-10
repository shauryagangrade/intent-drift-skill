"""Problematic findings provider for identifying concerning patterns."""

from typing import Any

from intent_alignment.models import Evidence

from .base import EvidenceProvider
from .constraint_provider import ConstraintProvider
from .execution_provider import ExecutionProvider
from .file_graph_provider import FileGraphProvider
from .goal_provider import GoalProvider
from .scope_provider import ScopeProvider


class ProblematicFindingsProvider(EvidenceProvider):
    """Identifies problematic patterns and findings across providers."""

    def __init__(self) -> None:
        """Initialize the problematic findings provider."""
        super().__init__(name="problematic_findings_provider", weight=0.07)
        # Keep refs to other providers for cross-referencing
        self.goal_provider = GoalProvider()
        self.constraint_provider = ConstraintProvider()
        self.scope_provider = ScopeProvider()
        self.execution_provider = ExecutionProvider()
        self.file_graph_provider = FileGraphProvider()

    def collect(self, context: dict[str, Any]) -> list[Evidence]:
        """Collect evidence about problematic patterns and findings.

        Args:
            context: Dictionary containing original_goal, current_plan, and execution_context

        Returns:
            List of evidence items about problematic patterns
        """
        evidence = []

        # Cross-analyze goal and scope providers for misalignment
        goal_evidence = self.goal_provider.collect(context)
        scope_evidence = self.scope_provider.collect(context)

        # Check for significant scope expansion detected by scope but not goal
        problematic = False
        details_parts = []

        # Analyze all evidence for concerning patterns
        for provider_evidence in [goal_evidence, scope_evidence]:
            for e in provider_evidence:
                if (
                    "significantly misaligned" in e.details.lower()
                    or "Scope expansion detected" in e.details
                ):
                    problematic = True
                    details_parts.append(f"From {e.source}: {e.details}")

        if problematic:
            evidence.append(
                Evidence(
                    source=self.name,
                    value=25.0,  # Low score for problematic findings
                    confidence=0.8,
                    details=(
                        "; ".join(details_parts)
                        if details_parts
                        else "Multiple concerning patterns detected"
                    ),
                )
            )

        # Check for execution/gain conflict
        execution_evidence = self.execution_provider.collect(context)
        goal_evidence = self.goal_provider.collect(context)

        for e in execution_evidence:
            if "Recommend" in e.details and "original goal" in e.details:
                evidence.append(
                    Evidence(source=self.name, value=40.0, confidence=0.7, details=e.details)
                )

        return evidence
