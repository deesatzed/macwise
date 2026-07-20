# PROGRESS.md

## Status Overview

Phases 1-6 and the simple first-run UX are locally accepted. Public release execution remains
open. Phase 8 independent-evaluation design is accepted in `GOAL_EVAL.md`; implementation has not
started, no evaluator result exists yet, and the paid human pilot remains separately gated.

## Current Assumptions

- This folder is the canonical MacWise implementation root.
- `GOAL.md` is approved product design and takes precedence over the two older planning artifacts.
- Python 3.12 is available for development or can be installed without changing product scope.
- Phase 1 may use sanitized command fixtures on non-macOS CI while macOS runners exercise bounded integration smoke tests.
- Package publication and production release require explicit authority/credentials; Homebrew tap work is outside the first-release milestone.
- The approved Phase 3 goal authorizes a versioned exact-match role catalog and guarded read-only recommendations; unknown relationships remain unknown, and removal authorization stays deferred to planning/execution phases.
- The active autonomous goal approves the Phase 4 assumption that one exact unsafe candidate may be persisted as blocked for review; ambiguous names still refuse, and no plan grants execution authority.
- `GOAL_EVAL.md` supplements rather than supersedes `GOAL.md`; the evaluator begins as an isolated
  subproject, may consume only serialized product output, and must retain private real-Mac evidence
  outside Git.

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
| Run MW-011 clean-platform acceptance | Done | Codex | Hosted Linux/macOS 15/macOS 26 and Python 3.12-3.14 passed in run `29641643615`; local macOS 27 and isolated install evidence also pass. |
| Build MW-100 evidence and analysis core | Done | Codex | Schema 3, v1/v2 migration, usage/startup collectors, evidence-basis findings, bounded related paths, and backup facts pass the 112-test gate. |
| Build MW-100 explain/review views | Done | Codex | Explain, review unused, startup, backups, help, and four-basis Markdown views pass focused, hostile-render, and 118-test full gates. |
| Run MW-100 acceptance | Done | Codex | `docs/phase-2-acceptance.md` records a local PASS from 118 tests on Python 3.12/3.13, quality/build/privacy/skill/clean-wheel gates, and aggregate-only real scans. |
| Design and plan MW-200 overlap intelligence | Done | Codex | Exact-match catalog and guarded-recommendation design plus seven-task TDD plan are saved under `docs/plans/`; D-022/D-023 record the boundaries. |
| Build MW-200 role-aware overlap intelligence | Done | Codex | Schema 4, catalog, analyzer, compare/review/explain/report views, ambiguity propagation, and guarded guidance pass the 142-test gate. |
| Adjudicate independent MW-200 review | Done | Codex | Three recommendations were Accepted and Resolved: ambiguity visibility, explicit actual-use comparison, and neutral-pair learning guidance. No critical finding remained. |
| Run MW-200 acceptance | Done | Codex | `docs/phase-3-acceptance.md` records a local PASS from 142 tests on Python 3.12/3.13, quality/build/privacy/skill/clean-wheel gates, independent review, and aggregate-only real scans. |
| Design MW-300 cleanup planning | Done | Codex | Append-only SQLite revisions, typed non-executable intent, blocked-candidate review, preflight, and rollback-blueprint boundaries are saved under `docs/plans/`; D-024/D-025 record the choices. |
| Build MW-300 cleanup planning | Done | Codex | Immutable plan models, pure preview construction, append-only SQLite revisions, persistent CLI review, hostile-input defenses, and zero-host-mutation tests pass the 186-test gate. |
| Adjudicate independent MW-300 review | Done | Codex | Four recommendations were Accepted and Resolved test-first: read-only zero-version display, ancestor-symlink rejection, optimistic active-plan concurrency, and one-to-one action/rollback integrity. No critical finding remained. |
| Run MW-300 acceptance | Done | Codex | `docs/phase-4-acceptance.md` records a local PASS from 186 tests on Python 3.12/3.13, quality/build/privacy/skill/clean-wheel gates, independent review, and an aggregate-only real planner smoke. |
| Design MW-400 reversible cleanup | Done | Codex | Fingerprint approval, fresh revalidation, append-only crash-visible manifests, allowlisted Trash/Homebrew/startup adapters, stop-on-failure, and separately approved undo are saved under `docs/plans/`; D-026 through D-030 record the boundaries. |
| Plan MW-400 reversible cleanup | Done | Codex | Ranked options and loophole review tightened the design; the eight-task TDD plan and current implementation packet define exact files, proof gates, commits, rollback, and no-live-mutation stop rules. |
| Build MW-400 execution-ready plans | Done | Codex | Plan schema 2 adds deterministic action order and opt-in supported startup previews; schema-1 duplicate adds refresh from current evidence, canonical full digests are public, and plan writes share a symlink-safe advisory lock. |
| Build MW-400 execution manifest models | Done | Codex | Strict frozen run/action/observation/inverse models enforce ordered references, approval fingerprint integrity, and truthful verified/undone states; pure approval helpers reject every non-exact phrase. |
| Build MW-400 execution journal | Done | Codex | Separate append-only SQLite manifest revisions require the exact shared lock, canonical integrity, monotonic identity/state transitions, and safe refusal for stale, corrupt, future, symlinked, or unresolved state. |
| Build MW-400 fresh revalidation | Done | Codex | Read-only preparation rebuilds schema-2 policy from current audit evidence, reconstructs canonical operations, captures Trash inode/device identity and startup plist hashes/prior state, and blocks changed targets, new blockers, cross-device moves, occupied destinations, and risky/unknown cask behavior. |
| Build MW-400 Trash execution slice | Done | Codex | A closed descriptor-relative adapter uses exclusive no-replace same-filesystem renames for approved roots, verifies device/inode identity, and reverses exactly; the coordinator locks, journals before mutation, verifies, records failure, rejects replay, and separately approves undo. |
| Build MW-400 command execution slice | Done | Codex | Closed fixed-path Homebrew and current-user launchctl adapters accept only structured safe identities, use bounded shell-free fake-runner-tested invocations, require fresh before/after observations, preserve startup/removal and reverse undo ordering, and journal verification or undo failure before stopping. |
| Build MW-400 approval and recovery CLI | Done | Codex | `apply` and `undo` render review surfaces, require exact interactive or explicit fingerprints, collect fresh evidence, expose durable failure states and recovery guidance, and use injected fake execution services in tests; default assembly uses the shared journal lock and closed adapters without elevation. |
| Harden and accept MW-400 reversible cleanup | Done | Codex | Independent review findings were adjudicated and resolved except the explicitly rejected full-digest display change; 292 tests and all local artifact gates pass. `docs/phase-5-acceptance.md` records proof and limitations. |
| Design MW-500 Codex integration | Done | Codex | Approved native plugin plus strictly read-only STDIO MCP design is saved under `docs/plans/`; D-031 pins the protocol and preserves the standalone mutation boundary. |
| Build MW-500 Codex integration | Done | Codex | Eight typed read-only tools, native plugin/skill payload, one-command setup, bounded STDIO server, clean-wheel call proof, and review hardening pass 361 tests on Python 3.12/3.13. |
| Complete Phase 7 local RC | Done | Codex | `1.0.0rc1` artifacts, UV/pipx packaging, release workflow, security/privacy review, clean-clone UV install, and real read-only run-through are complete; external publication remains gated. |
| Prepare external distribution proof | Done | Codex | The manual public smoke now verifies isolated UV-tool installation plus PyPI/GitHub checksum identity; Homebrew distribution is deferred. |
| Design MW-604 independent evaluation lab | Done | Codex | The design selects an isolated, separately packaged evaluator with independent receipts, predeclared oracles, frozen hard gates, exact macOS tuples, development/acceptance/fresh-holdout roles, mutation adequacy, and no misleading master score. |
| Build MW-604 independent evaluation lab | In progress | Codex | Isolated evaluator boundary, immutable capsules, disclosure gate, frozen safety contract, serialized claim parser, report CLI, corpus/mutation gates, and private bounded reference capture are verified; action lab, version matrix, and live-Mac evaluation remain. |

## Decision Links

- D-001 through D-040 are in `DECISIONS.md`.

## Current Milestone

UV-first `1.0.0rc1` candidate UX correction and autonomous clean-clone verification are complete.
MW-604 is the next local evidence milestone; public publication remains separately gated.

## Next Actions

1. Execute `GOAL_EVAL.md` from Task 1, preserving the evaluator/product independence boundary.
2. Freeze the evaluator contract before judging the final MacWise build.
3. Run fixture, mutation, hosted-macOS, disposable-action, and private current-Mac evidence gates.
4. Separately configure PyPI trusted publishing and run the RC release only when authorized.

## Blockers

The GitHub repository and hosted CI now exist. Public completion remains blocked only by
PyPI trusted-publisher configuration, the authorized RC tag/release workflow, and clean
public UV-tool proof. The absent Homebrew tap is intentional deferred scope, not a blocker.

## Questions for User

None required for local implementation. PyPI account configuration is required immediately before publication.

The later paid evaluation pilot requires explicit recruitment, consent, compensation-budget, and
aggregate-data-return approval; it does not block the local evaluator build.

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
- 2026-07-17 MW-100 schema/collector/analysis TDD: schema-3 migration, bounded usage and related-path evidence, launch/Homebrew startup ownership, and evidence-basis usage labels each failed for their intended missing behavior before passing focused tests.
- 2026-07-17 MW-100 backup RED/GREEN: service tests first rejected the missing backup collector boundary, and a failure-path regression proved that unavailable `tmutil isexcluded` output must preserve an existing path fact rather than replace it with unknown.
- 2026-07-17 MW-100 evidence-core gate: 112 tests passed; Ruff lint/format passed; Pyright reported 0 errors. Backup facts include configuration, available destinations, last-verifiable timestamp, and path exclusion state but deliberately no coverage field.
- 2026-07-17 MW-100 UX RED/GREEN: five command/report tests failed on the Phase 1 refusal surfaces and missing Markdown sections before deterministic explain, cautious unused review, startup ownership/state, backup facts, and four-basis report rendering were added.
- 2026-07-17 MW-100 UX gate: 118 tests passed; Ruff lint/format passed; Pyright reported 0 errors; the hostile renderer now asserts the exact seven allowed level-2 headings and rejects forged structure.
- 2026-07-17 MW-100 acceptance: 118 tests passed on Python 3.12.11 and 3.13.13; Ruff/Pyright/build/privacy/skill/workflow/clean-wheel gates passed; the installed wheel rendered Phase 2 evidence correctly.
- 2026-07-17 MW-100 real smokes: an in-memory audit produced 325 findings for 325 software records, 28 startup records, 97 bounded related paths, six usage-label kinds, schema round-trip, and exact safe headings in 25.54 seconds. A 19.2-second aggregate rerun showed 3 complete and 3 explicitly partial collectors; no inventory was saved.
- 2026-07-17 MW-100 claim validation: PASS for the local read-only Phase 2 scope; overall product, hosted CI, publication, and Phase 3+ claims remain open in `docs/phase-2-acceptance.md`.
- 2026-07-17 MW-200 TDD: schema-4 migration, immutable overlap models, exact catalog matching, role-aware relations, guarded recommendations, audit integration, compare/review/explain views, and Markdown reporting each failed for their intended missing behavior before passing focused tests.
- 2026-07-17 MW-200 identity RED/GREEN: two application paths sharing a bundle identifier initially collapsed to one stable ID; the regression failed before path-scoped application identity preserved distinct installations.
- 2026-07-17 MW-200 independent review: three important findings were Accepted and Resolved test-first—typed ambiguity propagation to partial state, order-independent actual-use comparison with explicit unresolved cases, and non-conflicting learning guidance after neutral pair guidance. No critical finding remained.
- 2026-07-17 MW-200 acceptance: 142 tests passed on Python 3.12.11 and 3.13.13; Ruff/Pyright/build/privacy/skill/workflow/clean-wheel gates passed; scoped stub and skipped-test scans were clean.
- 2026-07-17 MW-200 real smoke: an aggregate-only schema-4 audit produced 325 distinct software records, 25 catalog assessments, 6 relations, 21 guarded recommendations, exact safe headings, JSON round-trip, and 3 complete/4 partial collector states in 19.18 seconds. No names, paths, or inventory were saved.
- 2026-07-17 MW-200 claim validation: PASS for the local read-only Phase 3 scope; overall product, hosted CI, publication, and Phases 4–7 remain open in `docs/phase-3-acceptance.md`.
- 2026-07-18 MW-300 TDD: immutable plan invariants, deterministic preview construction, integrity-checked append-only storage, persistent CLI review, hostile input handling, and zero-mutation boundaries each failed for their intended missing behavior before focused and full suites passed.
- 2026-07-18 MW-300 independent review: four important findings were Accepted and Resolved test-first—read-only display no longer initializes version-0 stores, every existing path ancestor is checked for symlinks, stale competing writers cannot replace the active pointer, and action/rollback mappings are one-to-one. No critical finding remained.
- 2026-07-18 MW-300 review-fix gate: 186 tests passed; focused model/planner/persistence tests reported 28 passed and the final persistence suite reported 11 passed; Ruff format/lint, Pyright, and `git diff --check` passed repository-wide.
- 2026-07-18 MW-300 acceptance: 186 tests passed on Python 3.12.11 and 3.13.13; Ruff/Pyright/build/privacy/skill/workflow/clean-wheel gates passed; scoped stub and skipped-test scans were clean.
- 2026-07-18 MW-300 clean-wheel smoke: a fresh Python 3.12 wheel install passed blocked-plan construction, schema-1 SQLite integrity round-trip, and safe plan-help checks under a canonical non-symlink state root.
- 2026-07-18 MW-300 real smoke: an aggregate-only schema-4 audit produced 325 software records and 3 complete/4 partial collector states; pure planning produced 1 candidate, 1 action, 10 checks, and 1 rollback blueprint in 20.29 seconds without printing names/paths, persisting state, or mutating the host.
- 2026-07-18 MW-300 claim validation: PASS for local Phase 4 cleanup-planning scope; hosted CI, publication, all action execution/approval/verification/undo, Codex integration, and Phases 5–7 remain open in `docs/phase-4-acceptance.md`.
- 2026-07-18 MW-400 Task 1 RED/GREEN: shared-lock imports, canonical digest exports, schema-2 ordered actions, supported LaunchAgent/Homebrew-service previews, unsupported-startup blocking, schema-1 refresh, and CLI multi-action rendering each failed for the intended missing behavior before passing focused tests.
- 2026-07-18 MW-400 Task 1 gate: 197 tests passed; Ruff format/lint, Pyright, and `git diff --check` passed repository-wide. No host action executor exists and no installed software was changed.
- 2026-07-18 MW-400 Task 2 RED/GREEN: execution/approval imports failed before strict run/action/observation/inverse models and exact 16-character approval phrases were implemented; 10 focused tests then passed.
- 2026-07-18 MW-400 Task 2 gate: 207 tests passed; Ruff format/lint, Pyright, and `git diff --check` passed repository-wide. Models contain no generic command, executable, shell, or argv field.
- 2026-07-18 MW-400 Task 3 RED/GREEN: the execution-store import failed before read-only absent state, caller-held locking, canonical digests, monotonic revisions, unresolved-run exclusion, corruption/future-schema refusal, and nested-symlink tests passed.
- 2026-07-18 MW-400 Task 3 gate: 212 tests passed; Ruff format/lint, Pyright, and `git diff --check` passed repository-wide. The execution journal remains inert; no adapter or host mutation exists.
- 2026-07-18 MW-400 Task 4 RED/GREEN: cask artifact preservation, missing revalidation imports, schema-1/changed-identity/new-blocker refusal, canonical Trash observations, occupied/cross-device refusal, risky cask blocking, LaunchAgent plist hashing, Homebrew-service prior state, and exact cask entity matching each failed before the read-only implementation passed.
- 2026-07-18 MW-400 Task 4 gate: 222 tests passed; 21 focused collector/model/revalidation tests passed; Ruff format/lint, Pyright, and `git diff --check` passed. Preparation performed no mutation.
- 2026-07-18 MW-400 Task 5 RED/GREEN: missing filesystem/coordinator imports, synthetic exclusive rename/undo, occupied destination, inode replacement, symlink source, destination race, journal-before-move, verified undo, adapter failure journaling, and same-plan replay each failed before passing.
- 2026-07-18 MW-400 Task 5 gate: 227 tests passed; Ruff format/lint, Pyright, and `git diff --check` passed. The only real mutation was an exclusive rename and reverse rename of a synthetic `.app` inside pytest's canonical temporary root; no installed app or real Trash was touched.
- 2026-07-18 MW-400 Task 6 RED/GREEN: the mutating-command import and coordinator constructor first failed; exact fake runners then proved allowlisted formula/cask install and uninstall, Homebrew service stop/start, current-user LaunchAgent disable/bootout and enable/bootstrap, safe environment, fixed executables, structured-token rejection, output bounds, prepared-action substitution refusal, fresh before/after verification, stop-on-failure, startup-before-removal ordering, reverse-order undo, and durable undo-failure state.
- 2026-07-18 MW-400 Task 6 gate: 248 tests passed; Ruff format/lint, Pyright, and `git diff --check` passed repository-wide. Every Homebrew and launchctl mutation used an injected recording fake; no real Homebrew package, service, LaunchAgent, installed app, or user Trash was touched.
- 2026-07-18 MW-400 Task 7 RED/GREEN: approval CLI tests first failed on missing injection seams and the Phase 4 refusal commands; exact non-TTY and interactive apply approval, separate undo approval, no-plan and stale-plan refusal, durable failure-state rendering, guided undo recovery, launchctl read-state probing, and updated help then passed with fake execution services only.
- 2026-07-18 MW-400 Task 7 gate: 256 tests passed; Ruff format/lint, Pyright, build, `git diff --check`, and manual `apply --help` / `undo --help` rendering passed. No real mutating adapter was invoked and no installed software, startup state, real Trash, or Homebrew state changed.
- 2026-07-18 MW-400 independent review adjudication: Accepted and Resolved—partial/interrupted recovery, collector-complete Homebrew absence, action-specific collector completeness, locked revalidation plus per-action active-digest reload, canonical-only launchctl not-found handling, doctor recovery visibility, bounded streaming command capture, bundle metadata identity, regular-file lock validation, post-command partial observation, and historical undo selection. Rejected—the request to display the complete digest in approval phrases, because D-026 intentionally defines a 16-character consent fingerprint while the full active digest is separately checked internally; its theoretical 64-bit prefix collision limit is documented rather than misrepresented.
- 2026-07-18 MW-400 hardening RED/GREEN: regressions first exposed unavailable evidence, post-hoc output bounds, same-inode bundle changes, FIFO locks, stranded older runs, partial command state, and interrupted apply/undo recovery. Focused fixes now preserve unknowns, cap retained subprocess output during drain, bind Trash identity to descriptor-read Info.plist metadata, reject non-regular locks, query recoverable history, observe command failures, and classify interrupted command/Trash state before approved undo.
- 2026-07-18 MW-400 second review adjudication: Accepted and Resolved—unobserved post-mutation failures remain interrupted and later classifiable; never-attempted tail actions are explicit `NOT_APPLIED`; LaunchAgent and Homebrew-service prior state must be authoritative; LaunchAgent inverse commands use fresh-state deltas; absent collector status refuses; lock contention is bounded; doctor exposes historical undo; unreadable application identity becomes unknown. Accepted and Resolved from final re-review—typed unknown decisive fields never become recoverable after-state, undo independently rejects non-authoritative after-state, `NOT_APPLIED` has strict truth invariants, and ambiguous inverse failures remain interrupted. The final re-review reported no remaining Critical or Important findings.
- 2026-07-18 MW-400 local gate: 292 tests passed on Python 3.12.11 and 3.13.13; repository-wide Ruff format/lint, Pyright, build, privacy, skill, workflow YAML, scoped marker/skip, and `git diff --check` gates passed. Coverage measured 89% across the full suite.
- 2026-07-18 MW-400 clean-wheel smoke: a fresh Python 3.12 wheel environment rendered root/apply/undo help, then 43 installed-wheel tests passed synthetic Trash move/restore, fixed fake mutation runners, execution coordination, partial recovery, and interrupted apply/undo recovery. No real application, real Trash, Homebrew state, or launchctl state was changed.
- 2026-07-18 MW-400 claim validation: PASS for local Phase 5 reversible-cleanup scope only. Live permissions/behavior, hosted CI, public artifacts, Codex integration, and production safety remain unproven.
- 2026-07-18 first public hosted CI: Python 3.12/3.13 quality jobs passed, but the Homebrew candidate job failed because current Homebrew rejects `brew audit` by filesystem path and the temporary tap did not yet exist. Publication remained stopped.
- 2026-07-18 hosted-CI repair RED/GREEN: repository workflow tests failed on the stale macOS/Python matrix and path-based audit ordering, then passed after covering Python 3.12-3.14, macOS 15/current hosted macOS 26, and creating/copying the ephemeral formula before auditing `macwise-local/tap/macwise`.

## Rescue Ladder - step `hosted-homebrew-candidate` - attempt 2

### Rung 1: alternate pattern
- Searched: `Homebrew brew audit strict named formula in ephemeral tap GitHub Actions audit failure`
- Considered: `7126fe8b-bc35-4d1b-a686-7a33d7a18662`, `3efab124-fa86-41e8-96da-9073bb94bc88`, `52e7729b-ee6c-4a20-ab42-cc2eb08e2b2d`
- Selected / Rejected: Rejected all three stale immutable-audit-trail results as unrelated; selected the exact current Homebrew diagnostics from hosted job `88072721159`.

### Rung 2: bisect
- Diff hunks tried: 2
- Smallest failing hunk: `packaging/homebrew/Formula/macwise.rb:7`; the explicit RC version duplicated the version inferred from the URL, and the generated local tap also required explicit trust before formula loading.

### Rung 3: escalate
- BLOCKER.md updated: no
- User question: none; the hosted log provided an exact bounded repair and no expanded authority was required.

- 2026-07-18 hosted-CI repair accepted by run `29641643615`: all nine Linux/macOS 15/macOS 26 jobs passed on Python 3.12, 3.13, and 3.14; the current Homebrew candidate audit, exact local-source install, installed-version test, and cleanup passed on macOS 26 in 8m34s.
- 2026-07-18 D-035 scope decision: `uv tool install macwise` became the primary first-release UX, pipx remained an alternative, and Homebrew distribution moved to a later separately accepted milestone to reduce cross-repository drift.
- 2026-07-18 deferred-formula drift check: the candidate formula checksum changed when packaged README content changed, directly demonstrating cross-channel drift. With user approval, only `packaging/homebrew/` and its repository-level formula tests were removed; all Homebrew inventory, analysis, service, planning, apply/undo, and safety code/tests remain in scope.
- 2026-07-18 UV-first local gate: 374 tests passed in 37.54s; Ruff format/lint, Pyright, wheel/sdist build, repository contracts, and `git diff --check` passed. Four removed tests belonged only to the deferred Homebrew formula distribution surface.
- 2026-07-18 clean-clone proof: `/tmp/macwise-cleanclone.pv260p/repo` cloned commit `632eb587c34265cf2adb5543fa401ecbdd9cb72a`, matched `origin/main`, and was clean. `uv build` produced `1.0.0rc1` wheel/sdist; isolated `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` installation under Python 3.12 installed 38 packages and the `macwise` executable without touching global UV tool state.
- 2026-07-18 novice command proof from the clean clone: installed `macwise --version`, root help, no-argument guided menu, scan help, Codex setup help, and Homebrew review help all exited 0. A real read-only schema-4 scan completed with 325 software records (69 applications, 27 casks, 229 formulae), 28 startup records, 28 volumes, 325 findings, 6 overlaps, and 21 guarded recommendations; no inventory was committed.
- 2026-07-18 real Homebrew proof from the clean clone: the Homebrew collector completed with 256 records and zero limitations, and `macwise review brew` exited 0 with a 745-line local report redirected to temporary private output. `macwise doctor` also exited 0. Names, paths, and inventory remain only under the temporary clone root.
- 2026-07-18 corrected-UX TDD: regressions reproduced APFS `FreeSpace=0` despite positive `APFSContainerFree`, unbounded Homebrew/startup/unknown/largest/backup output, raw byte sizes, missing direct overlap command, false Python-version duplicate classification, catalog-purpose contradictions, same-name overlap ambiguity, and Homebrew records leaking into the application-largest view. Each regression failed before its minimal correction passed.
- 2026-07-18 corrected-UX local gate: 389 tests passed in 34.18s before the final same-name/largest refinements; the affected CLI/overlap/catalog suites then passed 27 and 21 focused tests respectively. Ruff format/lint, Pyright, repository contracts, wheel/sdist build, and `git diff --check` passed after the final corrections.
- 2026-07-18 autonomous final-clone proof: three successive GitHub clones were used because the walkthrough itself exposed and corrected two additional presentation defects. The final isolated UV-tool clone matched code commit `274343b`, installed 38 packages under Python 3.12.11, and reported MacWise `1.0.0rc1`. A real read-only schema-4 audit contained 325 software records, 28 startup records, 28 volumes, 325 findings, 6 overlap relations, and 26 guarded recommendations. Homebrew, backups, and storage collectors were complete; application, overlap, startup, and usage collectors remained explicitly partial with recorded limitations.
- 2026-07-18 corrected real-Mac results: `macwise storage` showed only the three user-relevant mounted volumes by default and agreed with `df` at collection precision (about 156 GiB, 1.5 TiB, and 77 GiB free). Backups foregrounded the independently verified 18-day-old timestamp and stale warning; Homebrew and startup defaults showed 20 of 256 and 20 of 28 with exact `--all` recovery; unknown-purpose output fell to 53 and excluded explicitly cataloged common apps; overlap removed the false Python pair and disambiguated two ChatGPT paths; largest showed readable sizes and 20 of 69 applications. No cleanup/apply/undo command ran.
- 2026-07-18 launch-doc RED/GREEN: repository contracts failed on the absent landing-page assets,
  stale hosted-CI wording, and unchecked links before passing with a rewritten novice README,
  expanded sanitized walkthrough, explicit knowledge-source limits, and a framework-free static
  site with no scripts, remote assets, trackers, or real inventory.
- 2026-07-18 launch-page visual check: headless Chrome rendered the page at 1440x1200 and 390x844.
  The first mobile render exposed horizontal clipping from intrinsic terminal/header width; a CSS
  correction constrained grid children and hid narrow navigation, and the second render passed
  visual inspection without clipping. Production GitHub Pages publication was not enabled.
- 2026-07-18 launch-doc local gate: 392 tests passed in 39.60s; Ruff format/lint, Pyright,
  wheel/sdist build, workflow YAML parsing, documentation links, repository privacy contracts,
  and `git diff --check` passed. Scoped TODO/FIXME/HACK/XXX/NotImplemented and skipped/xfail
  scans found no launch-blocking implementation gap. Public PyPI/GitHub release proof remains open.
- 2026-07-18 launch-doc publish proof: commit `991a608` pushed to `main`; a new GitHub clone was
  clean at that exact commit, locked UV sync installed `1.0.0rc1`, doctor reported Darwin 27 and
  read-only collectors, and all 10 launch contracts passed. Hosted run `29652271086` then passed
  all nine Linux/macOS 15/macOS 26 and Python 3.12-3.14 jobs. No tag, PyPI package, GitHub Release,
  GitHub Pages deployment, Homebrew tap, or shared online database was published.
- 2026-07-18 scorecard RED/GREEN: missing score-model, scoring-service, command, help, guided-menu,
  and public-doc contracts failed before immutable models, capped pure scoring, aggregate-only
  terminal/JSON/Markdown output, explicit file safeguards, and the guided score route passed.
  Regression tests prove unknown usage earns no non-use points and complementary pairs earn no
  consolidation opportunity.
- 2026-07-18 private scorecard evaluation: one real read-only audit completed and scored in 25.94
  seconds at Opportunity 70/100 and Usefulness 86/100. Aggregate focused-command cross-checks
  confirmed 28 startup records, 4 comparison-worthy of 6 overlap relations, 22 applications at
  least 500 MiB of 69 measured, 53 unknown-purpose records, zero supported non-use findings, and a
  stale-backup warning. Only counts, scores, reasons, and limitations entered repository docs.
- 2026-07-18 scorecard local gate: 405 tests passed in 35.10 seconds; all 109 files passed Ruff
  formatting, Ruff lint passed, Pyright reported zero errors, workflow YAML parsed, wheel and sdist
  built, repository privacy/link contracts passed, and `git diff --check` was clean.
- 2026-07-18 scorecard clean-clone/hosted proof: public GitHub clone `3953348` was clean, locked UV
  sync installed `1.0.0rc1`, score help rendered, and 21 score/model/privacy contracts passed.
  Hosted run `29653569296` passed all nine Linux/macOS 15/macOS 26 and Python 3.12-3.14 jobs.
- 2026-07-19 MW-603 design: accepted `GOAL_SIMPLE_UX.md` is implemented through a distinct
  `macwise checkup` entry point so scan/export, detailed scoring, and diagnostics keep their
  established responsibilities. D-039 records one fresh in-memory audit per guided session.
- 2026-07-19 MW-603 RED/GREEN: missing checkup models/service/command, recommended menu route,
  bounded evidence cards, report-confidence language, unknown-item choices, session-only user
  context, and plan-preview handoff each failed focused tests before implementation. The current
  focused gates pass 20 checkup/guided/planning tests, 11 scoring tests, and 112 CLI/repository
  tests; full and artifact-level verification remain pending.
- 2026-07-19 MW-603 local gate: 415 tests passed in 36.28 seconds; all 115 files passed
  formatting, Ruff lint passed, Pyright reported zero errors, wheel/sdist build passed, and
  `git diff --check` was clean. The adversarial review caught and resolved single-priority session
  exit and over-wide focused output; one audit now supports repeated choices and terminal lines
  are capped at 96 characters.
- 2026-07-19 MW-603 installed-wheel/real-Mac proof: an isolated Python 3.12 UV tool install of the
  final wheel reported `1.0.0rc1`; its real read-only checkup showed five aggregate priorities,
  86/100 report confidence, explicit fresh/not-saved language, a largest-evidence-gap explanation,
  a 95-character maximum line, and an explicit no-change statement. No item names, paths, or
  inventory were retained in repository files.
- 2026-07-19 MW-603 landing-page acceptance: the user opened the current local page successfully,
  described it as looking very good, and supplied a one-page macOS PDF export. Poppler rendered
  the 1445-by-6175-point export to a 2208-by-9435 PNG; visual inspection found the current
  recommended-checkup wording, updated score labels, complete sections, consistent hierarchy,
  and no clipping or overlap. The user explicitly waived a separate mobile export as unimportant.
  Hosted run `29690088780` passed all nine Linux/macOS and Python 3.12-3.14 jobs on commit
  `a2fe775`.
- 2026-07-20 MW-604 methodology design: selected a separately packaged evaluator subproject over
  product-internal assertions or an immediate remote-repository split. `GOAL_EVAL.md` and the
  design/implementation plans require independent receipts, predeclared oracles, frozen policy,
  multi-axis reporting, hard critical gates, mutation adequacy, exact macOS environment tuples,
  anti-overfitting corpus roles, disposable action verification, private real-Mac evidence, and a
  separately authorized later human pilot. No evaluator code, paid test, upload, or real host
  mutation has occurred.
- 2026-07-20 MW-604 Task 1 RED/GREEN: the initial evaluator test failed because
  `macwise_eval` did not exist. A standalone nested project now exposes `macwise-eval` without
  importing or executing product code; AST/text boundary tests pass. `uv lock --directory
  evaluator --check`, evaluator tests, version smoke, Ruff format/lint, and Pyright all pass.
  Exact evaluator commands now use `--directory evaluator` so paths resolve against the isolated
  project rather than the product checkout.
- 2026-07-20 MW-604 Tasks 2-3 RED/GREEN: missing evaluator models/I-O and privacy scanner caused
  the intended collection failures. Strict frozen capsule, receipt, oracle, verdict, metric, and
  report models now validate provenance, disclosure, exact environment tuples, unique identifiers,
  contained paths, SHA-256 receipts, and explicit denominators. The disclosure gate detects
  private-path, hostname, serial-shaped, secret-shaped, control, prompt-shaped, and inventory
  markers without rewriting evidence. A repository-wide privacy test caught a secret-shaped test
  fixture; the fixture now exercises parsed JSON detection without resembling a public credential.
  Evaluator tests, format/lint, Pyright, and repository privacy checks pass.
- 2026-07-20 MW-604 Task 4 RED/GREEN: missing oracle/policy modules and freeze script produced
  the expected test failures. The evaluator now loads eight closed versioned policy invariants,
  rejects unknown or severity-weakened expectations, records traceable policy mismatches, and
  content-locks policy input through an atomic digest script. Policy tests prove a modified input
  fails `--check`; evaluator format/lint, Pyright, and frozen-contract verification pass.
- 2026-07-20 MW-604 Tasks 5-6 RED/GREEN: missing serialized-product parser, metric, evaluator,
  report renderer, and CLI command each failed focused tests before implementation. The evaluator
  now parses audit schema 4, checkup, plan schema 2, and execution schema 1 without importing or
  launching product code; future/malformed output remains inconclusive. A separate product-side
  driver emits sanitized JSON fixtures. Exact fact comparison, transparent precision/recall,
  non-averageable critical policy failure, deterministic JSON/Markdown reports, and the explicit
  empty-output `macwise-eval evaluate` command pass. Evaluator tests, product-driver tests,
  formatting, linting, and Pyright pass.
- 2026-07-20 MW-604 Task 7 RED/GREEN: missing scenario and mutation modules caused the expected
  collection failures. The corpus now has twelve explicitly role-labeled domains, with holdouts
  retiring to development when inspected. Eight policy-linked seeded mutants are all caught by the
  hard-gate adequacy run; a deliberately supplied passing outcome exposes a surviving mutant by
  ID. D-041 elevates overlap-removal authority and unsupported-environment validation to critical
  safety violations, and the frozen contract digest was regenerated and verified.
- 2026-07-20 MW-604 Task 8 RED/GREEN: missing fixed command and reference-capture modules caused
  the intended test failures. The evaluator now uses shell-free allowlisted `df`, `tmutil`,
  Homebrew, and launch configuration observations plus approved-root application traversal,
  explicitly marking shared-source checks as correlated. `macwise-eval capture --private-output`
  writes only to an explicit empty local directory and reports aggregate category count without
  printing inventory. Fake-runner, CLI, format/lint, and Pyright gates pass; the real-Mac protocol
  records the later fresh-holdout procedure.
- 2026-07-20 MW-604 Task 9 RED/GREEN: the new disposable action-lab driver initially failed because
  macOS `/tmp` has a symlink ancestor rejected by the product's state-lock safety check, then exposed
  that receipt values were being read after undo instead of at apply time. The repaired driver uses
  a canonical temporary root, records each lifecycle checkpoint at its occurrence, creates only a
  synthetic bundle and sentinel, exercises apply, intentional recovery interruption, and approved
  undo, and emits a path-free receipt. The evaluator independently rejects any missing recovery,
  changed sentinel/payload, wrong journal state, or surviving temporary Trash copy. Focused product
  and evaluator tests, Ruff format/lint, and `git diff --check` pass.
- 2026-07-20 MW-604 policy-evidence correction: the earlier mutation harness accepted a supplied
  policy-outcome mapping, which could only prove that the mapping was compared, not that unsafe
  product output was detected. D-042 removes that flag from the evaluator API and CLI. Each of the
  eight seeded mutants is now a serialized audit, plan, or execution artifact parsed through the
  evaluator's normal parser and independently recognized by a frozen evaluator-owned signature.
  Mutation adequacy names any survivor explicitly. Focused evaluator tests pass nine cases;
  evaluator Ruff and Pyright are clean.
- 2026-07-20 MW-604 environment correction: private reference capture now records the exact
  macOS product and build versions through a shell-free, allowlisted `sw_vers` query rather than
  leaving the build as `unknown`. A failed query remains visibly `unknown`; it does not inherit a
  validated status. The fixed-command test and the complete evaluator suite pass.
- 2026-07-20 MW-604 private live holdout: a fresh ignored local capsule collected five independent
  reference categories, followed by a close-in-time read-only product audit. The tracked aggregate
  records only schema/counts and the exact macOS 27.0 build 26A5378n/Darwin 27.0.0/arm64/Python
  3.13.13 tuple. It is explicitly INCONCLUSIVE because no predeclared private oracle exists; this
  is a capture proof, not an accuracy, safety, or population claim. An initial relative output path
  was resolved under the evaluator working directory; its ignored location is now covered and the
  accepted capture used an absolute ignored path.
- 2026-07-20 MW-604 hosted/pilot readiness: CI now has an isolated evaluator job on both available
  hosted macOS 15 and 26 images, recording `sw_vers` and Darwin output before locked evaluator
  tests, formatting, lint, and type checks. The separate pilot protocol is dry-run only and
  prohibits recruitment, compensation, uploads, real actions, and release claims pending explicit
  later approval. Local `uv sync --directory evaluator --locked`, evaluator version smoke, and
  workflow YAML parsing pass; hosted evidence requires a pushed branch and completed run.
- 2026-07-20 MW-604 hosted correction: evaluator jobs passed on hosted macOS 15 and 26. The broader
  first CI run exposed the action lab's macOS-specific `/private/tmp` assumption on Linux. The
  driver now resolves the host temporary root before creating its disposable state, preserving the
  no-symlink safety property on macOS and portability elsewhere. The focused regression passes
  locally; the follow-up hosted run is queued at the time of this record.
- 2026-07-20 MW-604 threshold gate RED/GREEN: acceptance evidence was initially missing. The new
  evaluator-owned synthesis records all eight predeclared thresholds separately—zero critical
  violations, zero destructive-unknown guidance, protected refusal, undo restoration, precision,
  recall, top-three retrieval, and critical abstention. A zero denominator is INCONCLUSIVE and a
  single critical violation is FAIL; no master score exists. Focused tests, Ruff, and Pyright pass.
- 2026-07-20 MW-604 clean evaluator install: a fresh disposable UV tool environment built the
  isolated evaluator and ran `--version`, `capture --help`, and `evaluate --help` successfully.
  The proof is local only; publication remains explicitly out of scope.
- 2026-07-20 MW-604 canonical execution: the standalone evaluator replayed the frozen synthetic
  storage capsule against a serialized audit and returned PASS with factual precision/recall 1/1,
  no policy mismatch, and contract digest `f892c3b15e13b82f5864e850028f58815b8203fadf2859a044b941053185d5f7`.
  The temporary action driver and independent receipt judge also returned PASS. This is explicitly
  one canonical replay, not a substitute for the remaining scenario-family evidence.
