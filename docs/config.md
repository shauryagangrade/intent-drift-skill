# Configuration

The skill reads `config/defaults.yaml`. All keys are optional and overridden by CLI flags.

```yaml
analysis:
  threshold: 75              # min alignment % to be "on track"
  confidence_threshold: 80   # min confidence % for a reliable read
  providers:
    enabled:                 # which providers run (subset supported)
      - goal_provider
      - constraint_provider
      # ...
  weights:                   # relative importance (normalized internally)
    goal_provider: 0.25
    constraint_provider: 0.20
    # ...

export:
  default_format: text       # text | markdown | json
  file: null                 # path or null → stdout
  include_metadata: true

context_collection:
  auto_enabled: false
  methods:
    git_diff: true
    recent_commits: true
    edited_files: true
    recent_commands: true
    file_changes: true
  lookback_hours: 24
```

## CLI overrides

| Flag | Overrides | Notes |
|------|-----------|-------|
| `--threshold N` | `analysis.threshold` | 0–100 |
| `--format F` | `export.default_format` | text/markdown/json |
| `--auto-context` | `context_collection.auto_enabled` | runs `ContextCollector` |
| `--context "..."` | `execution_context` | manual evidence string |

## Per-invocation config

Drop a `config/user.yaml` next to `defaults.yaml`; the analyzer merges it over the
defaults. `user.yaml` is git-ignored by convention.
