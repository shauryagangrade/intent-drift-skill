#!/usr/bin/env python3
"""Intent drift analysis skill for Claude Code agents."""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add the intent-alignment-engine to the path
engine_path = Path.home() / "Projects" / "intent-drift" / "intent-alignment-engine"
sys.path.insert(0, str(engine_path))

from intent_alignment.models import AlignmentContext, AlignmentReport
from intent_alignment.engine import IntentAlignmentEngine
class IntentDriftAnalyzer:
    """Core analyzer for intent drift detection."""

    def __init__(self):
        """Initialize the analyzer with the Intent Alignment Engine."""
        self.engine = IntentAlignmentEngine()

    def parse_arguments(self, args: list) -> Dict[str, Any]:
        """Parse command line arguments into a configuration dictionary."""
        config = {
            'original_goal': '',
            'current_plan': '',
            'execution_context': 'auto',
            'auto_context': False,
            'format': 'text',
            'threshold': 75
        }

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--original-goal':
                config['original_goal'] = args[i + 1].strip('"\'')
                i += 2
            elif arg == '--current-plan':
                config['current_plan'] = args[i + 1].strip('"\'')
                i += 2
            elif arg == '--context':
                config['execution_context'] = args[i + 1].strip('"\'')
                i += 2
            elif arg == '--auto-context':
                config['auto_context'] = True
                i += 1
            elif arg == '--format':
                format_type = args[i + 1].lower()
                if format_type in ['text', 'markdown', 'json']:
                    config['format'] = format_type
                i += 2
            elif arg == '--threshold':
                try:
                    config['threshold'] = int(args[i + 1])
                    i += 2
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1

        return config

    def analyze(self, config: Dict[str, Any]) -> AlignmentReport:
        """Perform intent drift analysis based on configuration."""
        # Prepare execution context
        execution_context = config['execution_context']

        if config['auto_context']:
            # Collect auto context from git and file system
            execution_context = self._collect_auto_context()

        # Create alignment context
        context = AlignmentContext(
            original_goal={"text": config['original_goal']},
            current_plan={"text": config['current_plan']},
            execution_context={"text": execution_context}
        )

        # Evaluate alignment
        report = self.engine.evaluate(context)

        # Check threshold
        if report.overall_alignment < config['threshold']:
            print(f"Warning: Alignment score {report.overall_alignment}% is below threshold {config['threshold']}%")

        return report

    def _collect_auto_context(self) -> str:
        """Collect context automatically from git and recent activities."""
        # In a real implementation, this would:
        # 1. Check git status/diff
        # 2. Look for recently modified files
        # 3. Check recent commands
        # 4. Analyze commit history
        # 5. Build a comprehensive execution context

        # For now, return a placeholder
        return "Auto-collected context from git and recent activities"

    @staticmethod
    def _score_of(item):
        """Return (score, weight) from a breakdown entry, dict or dataclass."""
        if hasattr(item, "score"):
            return getattr(item, "score"), getattr(item, "weight", 0.0)
        return item.get("score", 0.0), item.get("weight", 0.0)

    def export_report(self, report: AlignmentReport, format: str) -> str:
        """Export the analysis report in the specified format."""
        if format == 'json':
            return self._export_json(report)
        elif format == 'markdown':
            return self._export_markdown(report)
        else:
            return self._export_text(report)

    def _export_text(self, report: AlignmentReport) -> str:
        """Export report as formatted text."""
        output = []
        output.append("Intent Alignment Report")
        output.append("=" * 50)
        output.append(f"Overall Alignment: {report.overall_alignment}%")
        output.append(f"Status: {report.status}")
        output.append(f"Confidence: {report.confidence}%")
        output.append("")
        output.append("Summary:")
        output.append(report.summary)
        output.append("")
        output.append("Evidence:")
        for i, evidence in enumerate(report.evidence, 1):
            marker = "✅" if evidence.value > 0.7 else "⚠" if evidence.value > 0.4 else "❌"
            output.append(f"  {i}. [{evidence.source}] {marker} {evidence.details}")
        output.append("")
        output.append(f"Risk: {report.risk}")
        output.append(f"Recommendation: {report.recommendation}")
        output.append("")
        output.append("Component Scores:")
        for name, score in report.breakdown.items():
            sc, _ = self._score_of(score)
            output.append(f"  {name}: {sc:.1f}%")

        return "\n".join(output)

    def _export_markdown(self, report: AlignmentReport) -> str:
        """Export report as Markdown."""
        md = []
        md.append("# Intent Alignment Report")
        md.append("")
        md.append("## Summary")
        md.append(f"- **Overall Alignment**: {report.overall_alignment}%")
        md.append(f"- **Status**: {report.status}")
        md.append(f"- **Confidence**: {report.confidence}%")
        md.append(f"- **Risk**: {report.risk}")
        md.append("")
        md.append("## Analysis")
        md.append(f"{report.summary}")
        md.append("")
        md.append("## Evidence")
        for i, evidence in enumerate(report.evidence, 1):
            marker = "✅" if evidence.value > 0.7 else "⚠" if evidence.value > 0.4 else "❌"
            md.append(f"{i}. **{evidence.source}** {marker} {evidence.details} (confidence: {evidence.confidence * 100:.1f}%)")
        md.append("")
        md.append("## Recommendation")
        md.append(report.recommendation)
        md.append("")
        md.append("## Component Breakdown")
        md.append("| Component | Score |")
        md.append("|-----------|-------|")
        for name, score in report.breakdown.items():
            sc, _ = self._score_of(score)
            md.append(f"| {name} | {sc:.1f}% |")

        return "\n".join(md)

    def _export_json(self, report: AlignmentReport) -> str:
        """Export report as JSON via the JSONExporter."""
        from exporters import JSONExporter

        return JSONExporter().export(report)
def main():
    """Main entry point for the skill."""
    parser = IntentDriftAnalyzer()

    # Parse command line arguments
    config = parser.parse_arguments(sys.argv[1:])

    # Check for required arguments
    if not config['original_goal']:
        print("Error: --original-goal argument is required")
        print("\nUsage examples:")
        print("  /intent-drift --original-goal \"Reduce memory usage\" --current-plan \"Improve startup\"")
        print("  /intent-drift --original-goal \"Add feature\" --current-plan \"Change architecture\" --auto-context")
        sys.exit(1)

    if not config['current_plan']:
        print("Error: --current-plan argument is required")
        sys.exit(1)

    # Perform analysis
    try:
        report = parser.analyze(config)

        # Export result
        output = parser.export_report(report, config['format'])
        print(output)

        # Exit with error code if low alignment
        if report.overall_alignment < config['threshold']:
            sys.exit(1)

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    main()