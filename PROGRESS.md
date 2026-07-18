# PROGRESS.md

## Status Overview

Phase 5 is locally accepted: MacWise now has exact approval, fresh locked revalidation, allowlisted reversible actions, crash-visible journals, bounded recovery classification, post-action verification, and separately approved undo. MW-400 passed Python 3.12/3.13, independent-review, quality, build, privacy, skill, and clean-wheel synthetic/fake-mutator gates. This does not prove live installed-app, Homebrew, or launchctl behavior. MW-011 remains PARTIAL because no hosted/Linux runner or Git remote exists; Phases 6–7 and public release remain open.

## Current Assumptions

- This folder is the canonical MacWise implementation root.
- `GOAL.md` is approved product design and takes precedence over the two older planning artifacts.
- Python 3.12 is available for development or can be installed without changing product scope.
- Phase 1 may use sanitized command fixtures on non-macOS CI while macOS runners exercise bounded integration smoke tests.
- GitHub repository creation, package publication, Homebrew tap changes, and production release require explicit authority/credentials at the relevant phase; local preparation does not.
- The approved Phase 3 goal authorizes a versioned exact-match role catalog and guarded read-only recommendations; unknown relationships remain unknown, and removal authorization stays deferred to planning/execution phases.
- The active autonomous goal approves the Phase 4 assumption that one exact unsafe candidate may be persisted as blocked for review; ambiguous names still refuse, and no plan grants execution authority.

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
| Complete Phase 7 local RC | Done | Codex | `1.0.0rc1` artifacts/docs/workflow, real isolated pipx, locked formula candidate, security/privacy review, and local acceptance are complete; external publication remains blocked. |
| Prepare external distribution proof | Done | Codex | Hosted CI now includes ephemeral formula audit/install/test; a manual public smoke verifies pipx, Homebrew, checksums, PyPI, GitHub release, and tap identity after publication. No hosted run is claimed. |

## Decision Links

- D-001 through D-032 are in `DECISIONS.md`.

## Current Milestone

Local `1.0.0rc1` handoff complete; public publication, hosted CI/release, and public install proof remain explicitly blocked.

## Next Actions

1. Obtain explicit tag/push/PyPI/GitHub/tap authority and confirm repository ownership.
2. Upgrade/use a clean hosted Xcode 27 macOS runner for strict formula audit/install/test.
3. Run hosted CI and the exact RC release workflow, then verify public pipx/brew installs.
4. Update acceptance from external evidence; never infer those results from local structure.

## Blockers

Local Phase 7 work is complete. Public completion is truly blocked by authority and external infrastructure: no publication authorization, no hosted run, no configured publisher/tap ownership proof, and Xcode 26.4 cannot satisfy Homebrew's Xcode 27 audit prerequisite.

Live verification on 2026-07-18 found the intended GitHub repository, PyPI project, and
Homebrew tap endpoints all return 404. `gh` is authenticated as `deesatzed`, but no
remote exists and credentials alone do not authorize repository creation or publication.

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
