"""Claude Code Skill: Intent Drift Analyzer

A skill that analyzes intent drift in AI-assisted development using the
Intent Alignment Engine.

This package lives at ~/.claude/skills/intent-drift. It imports the
Intent Alignment Engine from ~/Projects/intent-drift/intent-alignment-engine.
"""

import sys
from pathlib import Path

# Add the engine to the import path so `intent_alignment` resolves.
ENGINE_PATH = Path.home() / "Projects" / "intent-drift" / "intent-alignment-engine"
for _p in (ENGINE_PATH / "src", ENGINE_PATH):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from intent_alignment.models import AlignmentContext, AlignmentReport
from intent_alignment.engine import IntentAlignmentEngine

__version__ = "1.0.0"
__author__ = "Intent Alignment Engine Team"


def analyze_code():
    """Return a ready-to-use IntentDriftAnalyzer."""
    from analyzer import IntentDriftAnalyzer

    return IntentDriftAnalyzer()
