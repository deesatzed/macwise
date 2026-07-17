# Phase 4 Acceptance Audit

Date: 2026-07-18

Verdict: **PASS for MW-300 local cleanup-planning scope**. Phase 4 now creates
immutable cleanup previews for exactly identified software, evaluates all ten required
preflight categories, records typed non-executable action and rollback intent, and
persists complete integrity-checked revisions in local SQLite state. This is not an
execution or production-readiness verdict: apply, approval, host-state revalidation,
post-action verification, undo, Codex integration, hosted CI, and public release remain
open under Phases 5–7.

## Acceptance evidence

| Requirement | Verdict | Direct evidence | Honest limitation |
|---|---|---|---|
| Immutable typed plan snapshots | PASS | Model tests enforce frozen schema-1 snapshots, unique candidates/actions/checks, one action per subject, and one-to-one action/rollback mappings. | Typed intent is not execution authority. |
| Exact identity and blocked review | PASS | CLI/service tests refuse missing or ambiguous names without state changes and preserve exactly resolved unsafe targets as visibly blocked candidates. | The user must resolve ambiguity outside the plan before adding an item. |
| Exact non-executable action previews | PASS | Application Trash and Homebrew formula/cask previews use kind-specific fields; hostile tests prove there is no command, shell, executable, or argv field. | No preview is approved or executable in Phase 4. |
| Complete preflight | PASS | Every planned candidate receives identity, protection, dependency, usage, overlap, related-data, backup, startup, rollback, and staleness checks with evidence and limitations. | Backup configuration never proves recoverability; every fact must be revalidated at action time. |
| Rollback blueprints | PASS | Trash moves receive reversible restore intent; Homebrew removals receive qualified best-effort reinstall intent; missing exact actions block rollback readiness. | Homebrew restoration is not guaranteed, and no undo operation exists yet. |
| Append-only local persistence | PASS | SQLite tests cover canonical JSON digests, immutable revisions, transactions, active pointers, corruption/future-schema refusal, read-only display, and optimistic writer conflicts. | Phase 4 stores local planning state only; it does not yet expose history browsing or migration beyond schema 1. |
| Path and hostile-input safety | PASS | Security tests cover control text, SQL-shaped values, terminal structure, path traversal, symlink database/ancestor redirection, system-path defense, and mutation spies. | The state root must have a non-symlink ancestor chain; macOS `/tmp` is intentionally refused in favor of canonical `/private/tmp` during tests. |
| CLI review and refusal boundaries | PASS | `plan`, `plan add`, `plan show`, guided choice 8, and help tests prove persistent previews and safe language; `apply` and `undo` still refuse. | Approval, execution, verification, and undo belong to Phase 5. |

## Independent review disposition

| Recommendation | Classification | Resolution |
|---|---|---|
| Make `plan show` read-only for an existing version-0 database | Accepted / Resolved | Split read-only schema validation from append-time initialization; empty stores remain byte-for-byte unchanged and unknown version-0 schemas refuse. |
| Reject every existing symlink ancestor before planning-state writes | Accepted / Resolved | Added full ancestor checks before and after parent creation plus a nested-redirection regression. |
| Prevent competing first revisions from replacing the active pointer | Accepted / Resolved | Added transactional optimistic concurrency checks for initial and subsequent revisions. |
| Enforce exactly one rollback blueprint per action | Accepted / Resolved | Added action-subject and rollback-action uniqueness invariants with regressions. |

No critical findings remained. A second fast review was stopped after the bounded primary
review produced actionable findings and those findings were resolved and reverified.

## Fresh verification

- Python 3.12.11: 186 tests passed in an isolated project environment.
- Python 3.13.13: 186 tests passed in an isolated project environment.
- Ruff lint and format checks passed; Pyright reported 0 errors.
- `uv build` produced the `macwise-0.1.0a0` wheel and source distribution.
- The repository privacy contract reported 5 passing tests.
- The bundled read-only skill validated with an ephemeral validator-only PyYAML
  dependency; the pinned workflow parsed as YAML.
- A fresh Python 3.12 environment installed only the wheel and passed plan-model import,
  blocked-plan construction, schema-1 SQLite round-trip, integrity readback, and safe
  `plan --help` checks.
- Scoped TODO/FIXME/HACK/XXX/NotImplemented and skipped/xfail scans returned no
  implementation or test matches.
- `git diff --check` passed.

## Real read-only and planning evidence

One aggregate-only real-Mac audit returned schema 4 with 325 software records and all
seven collector states: three complete, four partial, and none unavailable. One exactly
selected record was passed through the pure planner, producing one candidate, ten
preflight checks, one typed action, one rollback blueprint, and preview-ready eligibility
in 20.29 seconds. Only counts and states were printed. No name or path was emitted, no
plan was persisted, the proposed Trash root was not created, and no host mutation command
was invoked.

## Claim validation

| Completion requirement | Result | Evidence |
|---|---|---|
| Acceptance criteria defined and met | PASS | `IMPLEMENTATION_PACKET.md`, the Phase 4 design/plan, and the evidence table above. |
| Tests exist and pass | PASS | Focused model/planner/persistence/CLI/security regressions plus both 186-test interpreter runs. |
| No blocking scoped stubs | PASS | Scoped marker and skipped-test scans returned no implementation/test matches. |
| Independent review performed and adjudicated | PASS | Four important findings were accepted, resolved test-first, and reverified; no critical finding remained. |
| Persistence and mutation boundaries proved | PASS | Clean-wheel SQLite round-trip, symlink/concurrency/corruption tests, mutation spies, and the aggregate-only live planner smoke passed. |
| Dirty-state truth preserved | PASS | Phase 4 implementation and review-fix commits are recorded; only this acceptance documentation update is pending at audit time. |

**Claim verdict: PASS** for “MW-300 Phase 4 local cleanup-planning scope is complete.”

## Still open

1. MW-011 hosted Linux/macOS CI remains unverified because this checkout has no remote
   runner; local macOS version evidence does not substitute for hosted results.
2. Public PyPI/pipx and Homebrew tap installation remain unproven until publication.
3. Approval-gated apply, action-time revalidation, post-action verification, manifests,
   and undo belong to Phase 5 and remain disabled.
4. Typed Codex integration, setup, and release work remain owned by Phases 6–7.
