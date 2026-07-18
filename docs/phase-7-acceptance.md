# Phase 7 Acceptance Audit

Date: 2026-07-18

Verdict: **PASS for the local `1.0.0rc1` candidate; BLOCKED for public release.** The
repository contains tested RC artifacts, current documentation/demo, pinned least-
privilege release automation, a real isolated pipx proof, a lock-aligned Homebrew
candidate, an ephemeral hosted formula install job, and a manual post-publication smoke
workflow. External publication and hosted behavior are not complete.

## Novice acceptance map

| # | Outcome | Local evidence | Remaining boundary |
|---:|---|---|---|
| 1 | Install with one command | Real isolated pipx wheel install passes; formula candidate is complete | Public pipx/brew installs unverified. |
| 2 | Run without subcommands | Guided/noninteractive CLI tests and pipx smoke pass | None local. |
| 3 | Understand an unfamiliar app | Explain service/CLI fixtures pass | Host evidence can remain unknown. |
| 4 | Learn direct/indirect use | Usage finding and help/report tests pass | No complete usage-history claim. |
| 5 | See overlap | Exact catalog compare/review tests pass | Unknown identities are not fuzzily matched. |
| 6 | See which appears active | Evidence-basis activity comparison tests pass | Missing use stays unknown. |
| 7 | Internal/external storage | Volume/location/size tests pass | Missing size is `Unknown`. |
| 8 | Backup limitations | Backup configuration/coverage-separation tests pass | No complete recoverability claim. |
| 9 | Create a no-change plan | Immutable planning and zero-mutation tests pass | Local state is written only on explicit add. |
| 10 | Preview every change | Action/check/rollback integrity tests pass | Unsupported actions remain blocked. |
| 11 | Trash one approved manual app | Synthetic descriptor-relative apply test passes | No live user app was moved. |
| 12 | Undo that action | Synthetic exact restoration tests pass | Changed/occupied targets refuse. |
| 13 | Set up Codex | Isolated setup/rollback/recovery matrix passes | No live personal installation. |
| 14 | `$macwise` conversational review | Skill, workflow, eight-tool SDK and installed-wheel call proofs pass | No hosted model-quality evaluation. |
| 15 | Useful help/errors | Root/nested help, refusal, recovery, pipx help smokes pass | None local. |

## Release evidence

- Python 3.12.11 and Python 3.13.13: 377 tests passed on each.
- Full statement coverage: 88%; warnings exposed unclosed test SQLite connections, which
  were fixed and the persistence-focused suite then passed with ResourceWarnings fatal.
- Ruff, format, Pyright, build, plugin/skill validation, privacy, workflow, artifact,
  pipx, and Homebrew resource-lock tests pass locally.
- Installed-environment `pip-audit` reported no known dependency vulnerabilities; the
  local editable MacWise package itself is not on PyPI and was skipped.
- `brew style` passes. `brew audit --strict` is blocked before formula evaluation because
  Homebrew requires Xcode 27.0 and this host has 26.4. Installation was not attempted
  against the shared user prefix.
- CI now defines an ephemeral macOS job that builds the exact sdist, audits the public
  formula, substitutes only its source URL with the local artifact, installs/tests it,
  and removes the temporary formula. A manual workflow separately tests both published
  install commands and verifies PyPI/GitHub/checksum/tap identity. Neither hosted workflow
  has run, so these are verification surfaces rather than pass evidence.

## Claim validation

**PASS:** “The repository contains a locally verified MacWise `1.0.0rc1` candidate.”

**BLOCK:** “MacWise `1.0.0rc1` is publicly released or ready for public users.” That
claim requires authorization, hosted CI/release results, trusted-publisher/tap ownership,
strict formula audit/install, and clean public install proofs listed in
`RELEASE_CHECKLIST.md`.
