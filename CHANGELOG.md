# Changelog

## Changelog policy

- **Every merged PR must add an entry here** under the right section (this is a
  hard requirement enforced by the PR template).
- New entries are added by the PR author at the top of the appropriate section.
- Sections follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):
  `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- The `[Unreleased]` section is where changes accumulate until the next release.
- This file is the project's permanent direction ledger: reading the diffs here
  over time should show the project moving along `ROADMAP.md`.

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- A read-only HOME (CI, container, mounted volume) no longer kills an
  otherwise good analysis: when the history file cannot be written, the CLI
  warns on stderr and continues without persisting the run (#65).

### Added
- Per-run score history: `--history` and `--compare N` CLI views backed by a
  per-user persisted timeline (`~/.local/share/intent-drift/history.json`,
  `$XDG_DATA_HOME`-aware) with atomic writes; every analysis seeds
  `report.timeline` so the exporters render the full trend (#20).
- Project governance: `ROADMAP.md` as the direction of record (goals, milestones,
  explicit out-of-scope list), a `CHANGELOG.md` every-PR-entry policy, and
  AI-neutral contribution gates (claim-before-PR, 3-PR-per-author cap, maintainer
  sign-off on approach for non-trivial work).
- PR and issue templates, a PR-governance CI check (scope, cap, claim), and a
  weekly-review workflow with `scripts/weekly_summary.py` that asks whether
  merged work still moves the roadmap forward.
- `npx intent-drift` distribution: npm package with a Node launcher that
  bootstraps a Python 3.10+ virtualenv, installs the engine, and runs the CLI
  (`package.json`, `bin/intent-drift.js`).
- `--version` and `--help` CLI output; version reads from `metadata.json` as the
  single source of truth (#17).
- Secret scrubbing of auto-collected context by default: tokens, `password=` /
  `api_key=` assignments, `Authorization:` headers, and long base64 blobs are
  masked before they reach the analyzer or report exporters (#31).
- gitleaks config allowing the test fixtures that deliberately contain fake
  secrets (#31).

### Changed
- Package metadata lives in a `[project]` table in `pyproject.toml`; `setup.py`
  is now a thin shim instead of the source of truth (#41).
- The skill now requires the `intent_alignment` engine as an installed package —
  the local-checkout fallback was removed, so no developer path can leak into
  shipped code (#41).
- `config/defaults.yaml` and `config/user.yaml` are now loaded and deep-merged
  (precedence: CLI > `user.yaml` > `defaults.yaml` > built-in) with validation;
  `export.file`, `export.include_metadata`, and `context_collection.lookback_hours`
  are honored instead of being dead configuration (#11).
- `parse_arguments` builds on the merged config instead of hardcoded defaults,
  so `--threshold` / `--format` override the files rather than constants (#11).
- Shell history is no longer collected by default: `--auto-context` gathers
  repo-only signals (git diff, commits, edited files, file changes) unless the
  new `--include-shell-history` flag is passed, and auto-context hands the
  providers the real structured context dict instead of a placeholder string
  (#13).
- Auto context collection now skips heavy/vendored directories and reads only the
  tail of shell-history files, keeping collection fast on large repos (#14, #34).
- Evidence values are canonicalized to the 0–100 scale used by the rest of the
  engine (#33).
- Edited-file resolution in `FileGraphProvider` is now repo-root relative (#36).

### Removed
- Unused `click` and `python-dateutil` dependencies (declared everywhere,
  imported nowhere) (#41).

### Fixed
- Packaging tests run on the full matrix: `tomllib` is Python 3.11+, so tests
  fall back to a regex parse on 3.10, and all reads are explicit UTF-8 to pass
  on Windows (#41).
- The installed wheel now packages `config.py` and `history.py` (they were
  missing from `setup.py`'s `py_modules`), fixing `ModuleNotFoundError` in the
  installed CLI.
- PR-governance and good-first-issue CI checks no longer require ripgrep, which
  is absent on GitHub-hosted runners (`rg` → `grep`).
- Clear errors for missing or invalid CLI values (`--format`, `--threshold`,
  unknown flags) instead of silent fallbacks (#37).
- `install.sh` now works on macOS and never deletes a real directory (#32).
- Cross-platform test failures on Windows (path separators, `USERPROFILE`) (#34, #35).

### Security
- Shell-history collection is opt-in: default runs never read `~/.bash_history` /
  `~/.zsh_history` / `~/.history`, and `config` defaults (`defaults.yaml`,
  built-in) set `recent_commands: false` to match (#13).
- Auto-collected shell history and git context are scrubbed by default before any
  export (#31).

## [1.0.0] - 2026-08-10

Initial release of the intent-drift skill.
