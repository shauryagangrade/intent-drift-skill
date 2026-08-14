# intent-drift Roadmap

> This is the direction of record for the project. PRs that are not aligned with
> the roadmap below (or an explicitly labeled "up for grabs" issue) will be
> reviewed against it before being accepted. This document is maintained by the
> maintainer — contributions that move the project toward the goals below are
> welcome; changes that push it away are out of scope.

## Purpose

intent-drift detects when an AI coding agent starts solving a *different* problem
than the one originally requested, by comparing the original goal against the
current plan and real execution evidence (edited files, git diff, shell history).

## Principles

1. **Evidence over prose.** Drift assessments must be grounded in real repo state,
   not just what the plan *claims*.
2. **Explainable, not mysterious.** Every score must trace back to evidence lines a
   human can verify.
3. **A tool for the maintainer, not a replacement.** The output is a pause-and-confirm
   call, never an autonomous decision.
4. **Privacy-safe by default.** Anything the skill reads (shell history, git diffs)
   must be scrubable and opt-in, with secrets masked unless explicitly disabled.

## Goals

- **G1 — The advertised feature set actually works.** Every feature documented in
  `README.md`/`SKILL.md` exists, is wired up, and is tested. No placeholders, no
  flags that do nothing. *(High priority — several open bugs violate this today.)*
- **G2 — Trustworthy drift output.** Correct 0–100 evidence scale everywhere
  (no ✅-for-everything exports), accurate confidence, and a report a reviewer can
  act on.
- **G3 — Easy to install and extend.** Working `pip`/`analyze-code` entrypoints,
  loaded config, and a documented path for adding providers and exporters.
- **G4 — Healthy project stewardship.** Clear direction (this roadmap), an
  "up for grabs" list, a changelog that records every merged change, and a
  contribution flow that protects the direction above.

## Milestones

### M1 — Make it real (next)
Close the gap between docs and code so the core promise works end-to-end:

- [ ] Fix CLI: real flag parsing with clear errors; drop undocumented flags
      (`--reset-config`, `./analyze-code`) or implement them (`#5`, `#6`, `#16`)
- [ ] Load `config/defaults.yaml` and honor `user.yaml` (`#11`)
- [ ] Wire `_collect_auto_context()` to `ContextCollector` (`#10`)
- [ ] Consistent import/entrypoint path across `__init__.py`, `analyzer.py`,
      `setup.py` (`#3`, `#12`)
- [ ] Fix evidence markers so ✅/⚠/❌ reflect actual values (`#1`)

*M1 done = README's own examples run correctly with `--auto-context` on a clean install.*

### M2 — Grow the surface (next-next)
- [ ] CSV and HTML exporters (`#19`)
- [ ] Write reports to a file via `--output` (`#18`)
- [ ] Timeline tracking that is actually populated across runs (`#20`)

### M3 — Harden and widen
- [ ] Cross-platform + privacy: document and harden shell-history handling (`#13`)
- [ ] Simplify provider/exporter plumbing (dedupe exporter logic, `#15`)
- [ ] Performance: keep auto-context fast on large repos

## Out of scope (not wanted)

- Moving to a different framework or language rewrite
- Tying drift detection to a proprietary model API or requiring network access
- Adding features unrelated to intent drift (generic code QA, style linting, etc.)
- Autonomous/self-approving behavior — the skill pauses and asks, always
- Non-drift "nice-to-have" auto-context providers (e.g. metrics dashboards)

## Contributing alignment

- PRs target "up for grabs" issues, or issues the maintainer has approved in
  discussion first.
- Every merged PR adds a `CHANGELOG.md` entry (checked in the PR template).
- Non-trivial PRs get maintainer sign-off on the *approach* before code is written.
- Max 3 concurrent open PRs per author; claim an issue before starting.
