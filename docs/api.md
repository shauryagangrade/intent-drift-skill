# API Reference

The skill exposes a small Python API and a CLI.

## `IntentDriftAnalyzer`
* `parse_arguments(args: list) -> dict` — convert CLI args to a config dict.
* `analyze(config: dict) -> AlignmentReport` — build context, run the engine, return a
  report. `config` needs at least `original_goal` and `current_plan`.
* `export_report(report, format) -> str` — `format` ∈ `{"text","markdown","json"}`.
* `_collect_auto_context() -> str` — thin wrapper over `ContextCollector`.

```python
from analyzer import IntentDriftAnalyzer
a = IntentDriftAnalyzer()
cfg = a.parse_arguments(["--original-goal", "X", "--current-plan", "Y"])
report = a.analyze(cfg)
print(a.export_report(report, "markdown"))
```

## `AlignmentReport` (from `intent_alignment.models`)
| Field | Type | Meaning |
|-------|------|---------|
| `overall_alignment` | float | 0–100 weighted alignment score |
| `confidence` | float | 0–100 consistency-based confidence |
| `status` | str | `Fully_Aligned` … `Critical_Drift` |
| `breakdown` | dict | per-provider score/weight |
| `summary` | str | prose summary |
| `evidence` | list[Evidence] | all evidence items |
| `risk` | str | risk statement |
| `recommendation` | str | recommended action |
| `timeline` | list | (empty in this build) |

## `Evidence` (from `intent_alignment.models`)
`source: str`, `value: float` (0–1), `confidence: float` (0–1), `details: str`.

## `ContextCollector`
`collect_all() -> dict` with `git_diff`, `recent_commits`, `edited_files`,
`recent_commands`, `file_changes`, `metadata`. Used by `--auto-context`.

## CLI
```bash
python3 ~/.claude/skills/intent-drift/analyzer.py \
  --original-goal "..." --current-plan "..." \
  [--context "..." | --auto-context] [--format text|markdown|json] [--threshold N]
```
Exit code is `1` when alignment < threshold (for use in CI / hooks).
