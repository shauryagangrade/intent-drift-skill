# intent-drift

[![CI](https://github.com/shauryagangrade/intent-drift-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/shauryagangrade/intent-drift-skill/actions/workflows/ci.yml)
[![Security](https://github.com/shauryagangrade/intent-drift-skill/actions/workflows/security.yml/badge.svg)](https://github.com/shauryagangrade/intent-drift-skill/actions/workflows/security.yml)
[![License](https://img.shields.io/github/license/shauryagangrade/intent-drift-skill)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](setup.py)
[![Stars](https://img.shields.io/github/stars/shauryagangrade/intent-drift-skill?style=social)](https://github.com/shauryagangrade/intent-drift-skill)
<p align="center">
  <a href="docs/media/intent-drift-demo.gif">
    <img src="docs/media/intent-drift-demo.gif" alt="intent-drift demo" width="80%">
  </a>
</p>


A skill that uses the Intent Alignment Engine to analyze intent drift in AI-assisted development.

## 🎯 Purpose

Detects when AI coding agents begin solving a different problem than originally requested by monitoring alignment between:
- Original goals
- Current execution plans  
- File changes and behavior

### What the skill is for (and is not)

- **Evidence over prose:** drift assessments are grounded in real repo state
  (git diff, edited files, file changes — and shell history only when you opt
  in with `--include-shell-history`), not just what a plan claims.
- **Explainable:** every score traces back to evidence lines a human can verify.
- **A maintainer tool, not a replacement:** it produces a pause-and-confirm call,
  never an autonomous decision.
- **Privacy-safe by default:** auto-collected context is scrubbed of secret-like
  content unless scrubbing is explicitly disabled.

The project's direction of record lives in [ROADMAP.md](ROADMAP.md); every merged
change is recorded in [CHANGELOG.md](CHANGELOG.md).

## 🛠️ Features

- Evidence-based drift detection using multiple providers
- Explainable assessments with detailed evidence tracking
- Timeline tracking across runs with history comparison
- Pluggable architecture for custom evidence providers
- Type-safe with comprehensive validation
- Exportable reports in multiple formats


> Like it? Leave a ⭐ — it helps others find the project.

## 🚀 Quick Start

```bash
# Run the CLI without installing anything (Python 3.10+ required)
npx intent-drift \
  --original-goal "Reduce application memory usage" \
  --current-plan "Optimize startup performance" \
  --auto-context

# Import into any Claude Code agent
cd ~/.claude/skills/intent-drift
./analyze-code
```

`npx intent-drift` is the packaged distribution: on first run it creates a
dedicated virtualenv (`~/.intent-drift-venv`) and installs the analysis engine.
Set `INTENT_DRIFT_PYTHON` to a specific Python 3.10+ binary if needed.

### Usage Examples

```bash
# Basic usage
/intent-drift
--original-goal "Reduce application memory usage"
--current-plan "Optimize startup performance"
--context "Edited: main.py, startup.py"

# With auto-collection of git context
/intent-drift
--original-goal "Improve response time"
--current-plan "Add database indexing"
--auto-context

# Print the score timeline recorded so far (no analysis run)
/intent-drift --history

# Compare this run against the run 3 analyses ago (trend + drift acceleration)
/intent-drift
--original-goal "Improve response time"
--current-plan "Add database indexing"
--compare 3
```

Every analysis appends its score to `~/.local/share/intent-drift/history.json`
and seeds the report's `timeline` with the running history, so the
`--history` / `--compare` views and the timeline sections of the exporters
reflect the full trend across sessions.

## 📊 Analysis Output

```
Intent Alignment Report

Overall Alignment: 68%
Status: Moderate Drift
Confidence: 89%

Evidence:
✓ Goal partially overlaps
✓ Constraints remain satisfied
⚠ Edited files primarily affect startup logic
⚠ Implementation no longer targets memory allocation

Risk: High - additional work unlikely to improve memory usage

Recommendation: Pause and confirm alignment before continuing
```

## 🏗️ Architecture

```
intent-drift/
├── __init__.py              # Skill entrypoint
├── analyzer.py              # Core analysis logic
├── config.py                # Config loading (defaults.yaml + user.yaml merge)
├── providers/               # Evidence providers
├── exporters/               # Report exporters (text, markdown, json)
├── config/                  # Configuration defaults
├── docs/                    # Usage documentation
└── examples/                # Usage examples
```

## 🔧 Configuration

### Required Configuration

```yaml
# config/defaults.yaml
analysis:
  threshold: 75              # Minimum alignment score (%)
  confidence: 80            # Minimum confidence (%)
  providers:
    enabled:               # Which providers to use
      - goal_provider
      - constraint_provider
      - execution_provider
      - scope_provider
  
  evidence_providers:
    goal_provider:
      weight: 0.25
      thresholds:
        match_score: 80
        drift_score: 60
    
    constraint_provider:
      weight: 0.20
      thresholds:
        violation_score: 90
        partial_compliance: 70
```

### Customization

```bash
# Edit config file
nano ~/.claude/skills/intent-drift/config/user.yaml

# Reset to defaults
./analyze-code --reset-config
```

## 📁 Integration

### With Git Repos

Automatically analyzes:
- Git diffs between commit points
- File modification patterns
- Commit message trends
- Branch divergence

### With Codebase Features

Analyzes:
- Type checking evidence
- Build system outputs
- Test coverage changes
- Performance metrics

## 🔌 Extending the Skill

### Adding New Evidence Providers

```python
# New providers go in providers/
class CustomEvidenceProvider:
    def __init__(self):
        self.name = "custom_provider"
        self.weight = 0.15
    
    def collect(self, context):
        # Implementation
        return [Evidence(...)]
```

### Custom Export Formats

```python
# New exporters go in exporters/
class CsvExporter:
    def export(self, report, output_path):
        # CSV implementation
        pass
```

## 📚 Documentation

See the `docs/` directory for:
- [Architecture Overview](docs/architecture.md)
- [Evidence Providers](docs/providers.md)
- [Configuration Reference](docs/config.md)
- [Customization Guide](docs/customizing.md)
- [API Reference](docs/api.md)

## 🤝 Contributing

See `CONTRIBUTING.md` for:
- Code style guidelines
- Testing requirements
- Documentation standards
- The contribution flow: claim-before-PR, a 3-PR-per-author cap, maintainer
  sign-off on approach for non-trivial changes, and a `CHANGELOG.md` entry on
  every merged PR

New to the project? Browse the issues tagged [good first issue](https://github.com/shauryagangrade/intent-drift-skill/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [up for grabs](https://github.com/shauryagangrade/intent-drift-skill/issues?q=is%3Aissue+is%3Aopen+label%3A%22up+for+grabs%22).

<a href="https://github.com/shauryagangrade/intent-drift-skill/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=shauryagangrade/intent-drift-skill"/>
</a>

## 📍 Roadmap

See [ROADMAP.md](ROADMAP.md) for the direction of record: goals, milestones,
the "up for grabs" backlog, and what is explicitly out of scope.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Based on the Intent Alignment Engine by Shaurya Gangrade.