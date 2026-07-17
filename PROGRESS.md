# PROGRESS.md

## Status Overview

30% complete – MacWise now has a locally verified public-repository foundation, valid initial read-only Codex skill, CI definition, isolated wheel install proof, and real read-only scan proof in addition to the guided CLI and core collectors. The requirement-level Phase 1 audit is intentionally PARTIAL: application, Homebrew, and drive collectors still lack named fields from `GOAL.md`; public pipx/Homebrew installation and hosted CI are also unproven. Those gaps remain open before Phase 1 can be accepted.

## Current Assumptions

- This folder is the canonical MacWise implementation root.
- `GOAL.md` is approved product design and takes precedence over the two older planning artifacts.
- Python 3.12 is available for development or can be installed without changing product scope.
- Phase 1 may use sanitized command fixtures on non-macOS CI while macOS runners exercise bounded integration smoke tests.
- GitHub repository creation, package publication, Homebrew tap changes, and production release require explicit authority/credentials at the relevant phase; local preparation does not.

## Task Tracker

| Task | Status | Owner | Notes |
|---|---|---|---|
| Reconcile active goal and prior artifacts | Done | Codex | D-001 records authority order. |
| Create project controls | Done | Codex | `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, and this file created. |
| Record repository map and risks | Done | Codex | `REPO_MAP.md` and `RISK_NOTES.md` record verified greenfield state. |
| Write approved Phase 1 design and implementation plan | Done | Codex | Saved under `docs/plans/`; modular ports/adapters approach selected. |
| Initialize Git repository | Done | Codex | Initialized `main` on 2026-07-17. |
| Build Phase 1 foundation and guided CLI slice | Done | Codex | MW-001 verified test-first, including isolated Python 3.12 wheel install. |
| Build versioned evidence and audit models | Done | Codex | MW-002 verified test-first; schema version 1 round-trips provenance. |
| Build bounded read-command adapter | Done | Codex | MW-003 verified test-first; fixed programs, no shell, time/output/environment bounds, typed failures. |
| Build application inventory | Done | Codex | MW-004 verified test-first with synthetic bundles, malformed metadata, nested roots, and no-execution/symlink tests. |
| Build Homebrew inventory | Done | Codex | MW-005 verified test-first with formula/cask/service fixtures and explicit/dependency safety classification. |
| Build storage inventory | Done | Codex | MW-006 verified test-first with plist fixtures, partial/unavailable states, and guarded longest-mount path resolution. |
| Build audit orchestration and reports | Done | Codex | MW-007 verified test-first; partial aggregation, stable ordering, JSON round trip, and honest Markdown unknowns. |
| Complete Phase 1 CLI hierarchy and help | Done | Codex | MW-008 verified test-first across 24 root/nested help surfaces, guided routing, formats, output safeguards, and refusal paths. |
| Build public repository foundation | Done | Codex | README/license/security/contribution/changelog/privacy/threat-model docs, valid initial skill, and commit-pinned CI added; local contract passes. |
| Audit Phase 1 against `GOAL.md` | Done | Codex | `docs/phase-1-acceptance.md` verdict is PARTIAL with direct evidence and explicit collector/release gaps. |
| Complete Phases 2–7 | Pending | Codex | Governed by `IMPLEMENT.md` and acceptance audit. |

## Decision Links

- D-001 through D-008 are in `DECISIONS.md`.

## Current Milestone

Phase 1 read-only evidence foundation: versioned models and the bounded command adapter, followed by application/Homebrew/drive collectors.

## Next Actions

1. Commit the verified public foundation and Phase 1 acceptance audit.
2. Close MW-009 application/Homebrew/storage field gaps test-first.
3. Add cross-parser malicious metadata and prompt-injection fixtures under MW-010.
4. Re-audit Phase 1, then continue into Phase 2 without collapsing later phases.

## Blockers

None for local implementation.

## Questions for User

None required. Tap ownership and publication credentials are deferred until they become necessary for release.

## Verification Log

- 2026-07-17: `git init -b main` succeeded; repository is on `main` with no prior commits.
- 2026-07-17: tracked-candidate file enumeration matched the intended public planning baseline.
- 2026-07-17: privacy/secret pattern scan over public candidates returned no matches. Historical `GOAL_old.md` and `docpre2.md` remain local and ignored.
- 2026-07-17 MW-001 RED: ephemeral `pytest` collection failed with `ModuleNotFoundError: No module named 'macwise'` before package code existed.
- 2026-07-17 MW-001 GREEN: `uv run pytest tests/cli/test_root.py -q` reported `2 passed`.
- 2026-07-17 MW-001 gates: Ruff reported all checks passed, Pyright reported 0 errors, and `uv build` produced the sdist and wheel.
- 2026-07-17 MW-001 install smoke: the wheel installed into a fresh Python 3.12 environment; both `macwise --help` and no-argument `macwise` exited successfully and displayed the expected read-only help/guided output.
- 2026-07-17 MW-002 RED: `uv run pytest tests/models -q` failed collection because `macwise.models` did not exist.
- 2026-07-17 MW-002 GREEN: the model suite reported 6 passed; the full suite reported 8 passed, Ruff passed, and Pyright reported 0 errors.
- 2026-07-17 MW-003 RED: `uv run pytest tests/system/test_commands.py -q` failed collection because `macwise.system` did not exist.
- 2026-07-17 MW-003 GREEN: 6 command-adapter tests passed; the full suite reported 14 passed, Ruff passed, and Pyright reported 0 errors.
- 2026-07-17 MW-004 RED: application collector tests failed collection because `macwise.collectors` did not exist.
- 2026-07-17 MW-004 scope RED: nested-subfolder regression failed with zero collected records before recursive, app-boundary-pruned traversal was added.
- 2026-07-17 MW-004 GREEN: 6 application tests passed; the full suite reported 20 passed, Ruff formatting/lint passed, and Pyright reported 0 errors.
- 2026-07-17 MW-005 RED: Homebrew tests failed collection because `macwise.collectors.homebrew` did not exist.
- 2026-07-17 Homebrew safety RED: the command-boundary environment test failed until fixed `HOMEBREW_NO_AUTO_UPDATE=1` and `HOMEBREW_NO_ANALYTICS=1` values were added.
- 2026-07-17 MW-005 GREEN: 5 Homebrew tests passed; the full suite reported 25 passed, Ruff formatting/lint passed, and Pyright reported 0 errors.
- 2026-07-17 MW-006 RED: storage tests failed collection because `macwise.collectors.storage` did not exist.
- 2026-07-17 real-smoke RED: installed Homebrew JSON reached the original 1 MB output cap, causing a zero-record partial result. Two regression tests failed before per-command output bounds and limitation propagation were implemented.
- 2026-07-17 MW-006 GREEN: 5 storage tests and both output-cap regressions passed; the full suite reported 32 passed, Ruff passed, and Pyright reported 0 errors.
- 2026-07-17 read-only host smoke: storage and Homebrew collectors completed against the current Mac without persisting inventory; the application collector returned records plus an explicit unavailable-root limitation rather than failing or guessing.
- 2026-07-17 MW-007 RED: service/report tests failed collection because `macwise.services` and `macwise.reporting` did not exist.
- 2026-07-17 MW-007 GREEN: 5 audit/report tests passed; the full suite reported 37 passed, Ruff passed, and Pyright reported 0 errors.
- 2026-07-17 MW-008 RED: the CLI suite reported 34 failures spanning missing commands, help clauses, scan formats, guided routing, output safeguards, and refusal paths.
- 2026-07-17 MW-008 GREEN: 36 CLI tests passed; the full suite reported 71 passed, Ruff passed, Pyright reported 0 errors, and wheel/sdist build succeeded.
- 2026-07-17 MW-008 manual help smoke: root, scan, and review help rendered the required plain-language, safety, examples, next-step, and command-list sections; `setup codex` refused with exit status 2 and stated that no changes were made.
- 2026-07-17 public-foundation RED: repository tests reported four failures for missing public files, README/package metadata, and CI; the privacy check already passed.
- 2026-07-17 public-foundation GREEN: 5 repository contract tests passed and the generated `skills/macwise` scaffold passed the skill-creator validator.
- 2026-07-17 complete local gate: 76 tests passed, Ruff format/lint passed, Pyright reported 0 errors, and sdist/wheel build succeeded.
- 2026-07-17 isolated install: the wheel installed under Python 3.12; version, root help, guided no-argument output, scan help, nested help, and exit-2 Codex setup refusal were verified.
- 2026-07-17 real scan smoke: JSON schema/collector structure and Markdown verified/limitations/unknown sections passed in memory; no inventory was persisted or added to Git.
- 2026-07-17 Phase 1 audit: PARTIAL due to explicit application, Homebrew, drive, malicious-fixture, public-install, and hosted-CI gaps recorded in `docs/phase-1-acceptance.md`.
