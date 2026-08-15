# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Report them through
GitHub's private vulnerability reporting:

**https://github.com/shauryagangrade/intent-drift-skill/security/advisories**

A maintainer will be notified and will work with you privately on a fix and a
coordinated disclosure. You can expect an acknowledgement within a few days.

## Scope

- Secret handling: the skill scrubs auto-collected shell history and git
  context by default (see `CHANGELOG.md`); a report that scrubbing can be
  bypassed is treated as a security issue.
- Execution safety: the skill runs `git` with fixed argv and never uses
  `shell=True`; code paths that invoke subprocesses are in scope.
- Supply chain: any pinned dependency that ships a known vulnerability.

## Security checks

Every pull request runs `gitleaks` (secret scanning) and `pip-audit`
(dependency vulnerability audit) in CI. See `.github/workflows/security.yml`.
