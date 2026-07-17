# PROGRESS.md

## Status Overview

25% complete – The Phase 1 CLI surface is now implemented: guided interactive and non-interactive entry, the complete required root/nested hierarchy, real terminal/JSON/Markdown scans, explicit output-file safeguards, basic verified explain/review/storage/startup views, and contract-tested help for every command. Later-phase overlap, usage, backup, planning, apply/undo, and Codex commands exist only as honest read-only messages or safe refusals. Public documentation/CI and the Phase 1 acceptance audit remain before Phase 2.

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
| Complete Phases 2–7 | Pending | Codex | Governed by `IMPLEMENT.md` and acceptance audit. |

## Decision Links

- D-001 through D-008 are in `DECISIONS.md`.

## Current Milestone

Phase 1 read-only evidence foundation: versioned models and the bounded command adapter, followed by application/Homebrew/drive collectors.

## Next Actions

1. Commit the verified MW-008 CLI/help slice.
2. Add the Phase 1 public repository foundation, privacy/threat-model docs, and CI checks.
3. Run build, isolated install, real read-only scan, and Phase 1 requirement audit.
4. Continue into Phase 2 without collapsing later phases.

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
