# Contributing to intent-drift

We welcome contributions to the intent-drift skill! This document describes how to
get started and how the contribution flow is gated so the project keeps moving in
the direction the maintainer has chosen (see [ROADMAP.md](ROADMAP.md)).

The rules below are mechanics, not value judgments: they apply the same way to
every contributor, whether the change comes from a human or an agent.

## Direction gates

- The project's direction of record is `ROADMAP.md`. Read it before starting.
- Every open issue carries one of these labels:
  - **core** — needed for the core promise; milestone work. PRs welcome, but
    non-trivial changes need approach sign-off first (below).
  - **planned** — on the roadmap but not scheduled yet; **not** accepting PRs.
  - **up for grabs** — direction is clear; PRs welcome. Best place to start.
  - **out-of-scope** — not wanted; PRs targeting these will be rejected.
- Work on an issue not covered by the labels? Open a discussion/issue first and
  get the maintainer to confirm the direction before writing code.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/intent-drift-skill
   cd intent-drift-skill
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Link to your Claude Code skills directory**:
   ```bash
   ln -s "$PWD" ~/.claude/skills/intent-drift
   ```

## Code Style

- Follow PEP 8 with a line length of 100 characters
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Use Black for formatting and isort for import sorting

## Testing

Run the test suite:
```bash
pytest tests/
```

For coverage:
```bash
pytest --cov=intent_drift tests/
```

All PRs must pass CI (tests across py3.10–3.12 on Linux/macOS/Windows, lint/format,
secret scanning).

## Adding a New Provider

1. Create a new file in `providers/` named `<provider_name>_provider.py`
2. Subclass `EvidenceProvider` from `providers/base.py`
3. Implement the `collect()` method returning `List[Evidence]`
4. Add your provider to `providers/__init__.py`
5. Register it in `src/intent_alignment/engine.py` (in `_register_default_providers()`)
6. Add tests in `tests/unit/test_providers.py`

New providers change the weighted score, so they are **core** work: discuss the
approach with the maintainer before implementing.

## Adding a New Exporter

1. Create a new exporter class in `exporters/`
2. Subclass `BaseExporter`
3. Implement the `export()` method
4. Add it to the exporter registry in `analyzer.py`

## Documentation

- Update `docs/` for any user-facing changes
- Update `README.md` for new features
- Update `metadata.json` if parameters change
- Add a `CHANGELOG.md` entry under the matching section (Required — see below)

## Pull Request Process

1. **Claim first.** Comment "claiming" on the issue you plan to fix (or ask to be
   assigned). This avoids parallel work on the same issue.
2. **Keep it small.** One issue per PR.
3. **Non-trivial change?** Get maintainer sign-off on the *approach* before writing
   code — post a one-paragraph plan in the issue (or an early draft PR) and wait
   for an OK.
4. Create a feature branch: `git checkout -b fix/your-fix`
5. Make your changes with tests.
6. Run the full test suite and Black/ruff locally.
7. Add a `CHANGELOG.md` entry in the matching section — this is a required checkbox
   in the PR template. No changelog entry, no merge.
8. Submit a PR with the completed template. Reference the claimed issue
   (`Closes #NN`) and link the claim comment.

## Limits (same for every contributor)

- **Max 3 concurrent open PRs per author.** If you already have 3 open, finish or
  close one before opening another.
- **No PRs on `planned` or `out-of-scope` issues** (they will be closed without
  review). Prefer the `up for grabs` backlog.
- Reviews are batched (weekly by default). A PR sitting a few days does not mean
  it's ignored — maintainer reviews happen on a cadence.

## Code of Conduct

Please be respectful and constructive in all interactions. See `CODE_OF_CONDUCT.md`
for details.
