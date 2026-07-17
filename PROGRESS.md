# PROGRESS.md

## Status Overview

47% complete – MacWise now has a locally verified public-repository foundation, schema-v2 audit migration, enriched read-only application/Homebrew/storage evidence, hostile cross-parser/display fixtures, a valid read-only Codex skill, CI definition, Python 3.12/3.13 and actual isolated pipx/wheel proof, and real read-only scan proof. MW-009 and MW-010 are closed; MW-011 is PARTIAL because no hosted/Linux runner or Git remote exists. Several later evidence fields and public Homebrew/release proof also remain open.

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
| Close MW-009 inventory field gaps | Done | Codex | Schema v2 plus application signing/architecture/process/components/source, Homebrew size/executable/state/reference/location/correlation, and storage topology/ownership/Time Machine facts are fixture-tested and real-smoked. |
| Complete MW-010 hostile metadata coverage | Done | Codex | Synthetic plist/Homebrew/disk/prompt fixtures prove path containment, raw JSON provenance, Markdown/terminal neutralization, inert CLI matching, and the skill's prompt boundary. |
| Run MW-011 clean-platform acceptance | Partial | Codex | Python 3.12 and 3.13 pass on macOS; clean wheel and isolated pipx installs pass. Hosted Linux/macOS CI cannot run without a remote runner; Docker/Podman engines are not running. |
| Complete Phases 2–7 | Pending | Codex | Governed by `IMPLEMENT.md` and acceptance audit. |

## Decision Links

- D-001 through D-008 are in `DECISIONS.md`.

## Current Milestone

Phase 2 explain/review evidence while the external hosted-CI/public-release gates remain explicitly open.

## Next Actions

1. Begin MW-100 with stable item matching, direct/indirect usage evidence, startup ownership, related-data estimates, and backup limitations.
2. Re-run hosted Linux/macOS CI once a Git remote/runner is authorized and available; do not treat the workflow definition as a run result.
3. Keep public Homebrew/release proof deferred until tap/artifact authority exists.

## Blockers

No blocker for local implementation. MW-011 hosted Linux/macOS CI is externally blocked by the absence of a Git remote/runner; local container CLIs have no running engine or VM.

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
- 2026-07-17 MW-009 TDD: schema-v2 migration, fixed metadata commands, application enrichment, Homebrew enrichment/correlation, storage topology/Time Machine parsing, and Markdown exposure each failed for the intended missing behavior before their minimal implementations passed.
- 2026-07-17 MW-009 complete local gate: 94 tests passed; Ruff format/lint passed; Pyright reported 0 errors; sdist/wheel build, skill validation, workflow YAML parsing, and `git diff --check` passed.
- 2026-07-17 MW-009 isolated install: the built wheel installed under Python 3.12; version, root/guided/scan help, explicit-root options, and exit-2 Codex setup refusal were verified.
- 2026-07-17 MW-009 real read-only smokes: application signing/architecture/process evidence, Homebrew size/executable/state evidence, storage topology/ownership/Time Machine facts, schema-v2 JSON, and enriched Markdown were validated in memory without persisting host inventory.
- 2026-07-17 MW-010 RED: hostile security tests exposed raw ESC/newline/bidi structure injection in Markdown/CLI output and missing explicit prompt-shaped evidence language; parser/path containment already passed.
- 2026-07-17 MW-010 GREEN: 4 focused security tests and 46 security/reporting/CLI regressions passed after shared human-display sanitization and the strengthened skill boundary.
- 2026-07-17 MW-010 complete local gate: 98 tests passed; Ruff format/lint, Pyright, build, skill validation, workflow parse, privacy contract, and diff checks passed.
- 2026-07-17 MW-010 isolated/real smokes: the Python 3.12 wheel neutralized hostile control/bidi/newline text; a real in-memory Markdown scan contained only the three genuine level-2 sections and was discarded.
- 2026-07-17 MW-011 Python matrix: all 98 tests passed under Python 3.12.11 and Python 3.13.13 on macOS; the full Ruff/Pyright/build/skill/workflow gate passed under 3.13.
- 2026-07-17 MW-011 pipx RED/GREEN: the first ephemeral install refused an incompatible default uv backend; a fresh isolated `pipx --backend pip` install succeeded and version/root/scan help smokes passed without changing the user's PATH.
- 2026-07-17 MW-011 external audit: no Git remote, hosted runner, running Docker daemon, or Podman VM exists, so Linux/hosted CI remains unverified rather than inferred from workflow YAML.
