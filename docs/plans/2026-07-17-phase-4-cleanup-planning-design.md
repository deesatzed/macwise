# Phase 4 Cleanup Planning Design

Date: 2026-07-17

Status: Approved under the active autonomous goal, `GOAL.md`, and the standing rule to
continue with safe documented assumptions. The selected behavior retains an exact but
unsafe candidate as visibly blocked; a name with no unique identity still refuses.

## Goal and boundary

Phase 4 turns reviewed audit evidence into a persistent, immutable cleanup preview. It
implements `macwise plan`, `macwise plan add NAME`, and `macwise plan show`, including
dependency, ambiguity, protection, data, backup, and rollback preflight. It may write
only MacWise planning state. It must not uninstall, move, disable, unload, delete, or
otherwise change installed software, startup state, or user data.

`macwise apply` and `macwise undo` remain honest Phase 5 refusals. A Phase 4 plan is not
approval and does not grant execution authority.

## Approaches considered

### 1. Append-only SQLite revisions with typed immutable snapshots — selected

Each plan change creates a complete immutable revision in SQLite. The revision captures
the source audit identity/time, exact subject snapshots, typed proposed actions,
preflight results, and rollback blueprints. A digest detects corruption, and one active
pointer identifies the latest revision.

This matches the required SQLite source of truth, preserves exactly what the user
reviewed, supports future approval/revalidation, and keeps persistence local.

### 2. Mutable normalized SQLite rows

This is smaller initially, but an add/remove or refreshed preflight silently changes the
same plan. It cannot prove which preview was reviewed and complicates later approval and
undo integrity. Rejected.

### 3. Atomic JSON plan files

JSON is directly inspectable and easy to implement, but `GOAL.md` explicitly selects
SQLite for audit history and decisions. File replacement also provides weaker revision
and concurrent-write semantics. Rejected.

## Architecture

Phase 4 adds four narrow components:

1. `models/plan.py` defines strict frozen version-1 plan documents, candidate snapshots,
   typed action intent, preflight results, rollback blueprints, and stable IDs.
2. `services/planning.py` is a pure deterministic planner. It consumes one current
   `AuditDocument` plus exact selected subject IDs and produces the next immutable plan
   revision. It does not access SQLite, the filesystem, subprocesses, or Typer.
3. `persistence/plans.py` owns SQLite location, migration, append/read transactions,
   integrity digests, and the active-plan pointer. It has no host-action capability.
4. The CLI resolves a unique record through the existing exact/qualified matching,
   invokes the planner, persists one revision, and renders a novice-readable preview.

The store uses `platformdirs.user_data_path("macwise") / "macwise.db"` in production and
an injected path in tests. SQLite uses the built-in `sqlite3` module; no new runtime
dependency is needed. Migration is explicit through `PRAGMA user_version`.

## Plan model

The plan schema is independent from the audit schema and package version.

`PlanDocument` contains:

- `schema_version = 1`;
- stable `plan_id`, monotonic `revision`, and aware `created_at`;
- source `audit_id` and `audit_collected_at`;
- immutable ordered candidates, proposed actions, preflight checks, and rollback
  blueprints;
- a derived eligibility of `blocked` or `preview_ready`;
- explicit limitations, including snapshot staleness and no-execution authority.

Each `PlanCandidate` snapshots only action-relevant facts: stable subject ID, entity
type, safe display label, exact install identity/path or Homebrew token, installed
version, source, explicit/dependency role, protection state, reverse dependencies,
approved project references, usage label, related path IDs, and owned startup IDs. It
does not copy arbitrary file contents.

Each `PlannedAction` is typed rather than an executable command string:

- `move_application_to_trash` records the exact source bundle and a deterministic future
  Trash destination derived from the plan/action ID;
- `homebrew_uninstall_formula` records the exact formula token;
- `homebrew_uninstall_cask` records the exact cask token.

Human output renders an exact preview such as an argument vector, but Phase 5 must
reconstruct and validate an allowlisted operation from typed fields. Persisted metadata
can never become executable authority by itself.

Each `RollbackBlueprint` records the original identity/location, intended recovery
strategy, feasibility (`reversible`, `best_effort`, or `unavailable`), prerequisites,
and limitations. Homebrew reinstall is best-effort because a captured version may no
longer be available; the plan must not promise guaranteed restoration.

## Identity and candidate behavior

`plan add` performs a fresh read-only audit and uses the existing CLI resolver:

- no match refuses without changing plan state;
- multiple matches refuse and suggest `app:`, `cask:`, or `formula:` qualification;
- one exact record may be persisted even when unsafe, but its plan remains blocked;
- adding the same stable subject to the active plan is idempotent and creates no new
  revision;
- a later add creates a full new revision rather than mutating the prior document.

An application linked exactly to a Homebrew cask plans the typed cask uninstall rather
than both a Trash move and a cask uninstall. A standalone application with an exact
install path plans a Trash move. A formula/cask plans its exact Homebrew token. Missing
or contradictory action identity produces no action and a blocking preflight.

## Preflight policy

Every candidate receives deterministic checks. Outcomes are `pass`, `warning`, or
`block`; each has a short statement, evidence references, and limitations.

Blocking checks:

- identity is no longer unique or action identity/path/token is missing;
- Apple/system protection is true or unknown for a system-like target;
- a Homebrew dependency is not explicitly selected by the user;
- reverse dependencies or approved project references exist;
- active, recent, probable, or indirect-use evidence contradicts cleanup intent;
- a keep/keep-together recommendation conflicts with removal;
- no meaningful rollback blueprint can be constructed.

Warnings that remain visible but do not claim safety:

- backup configuration or path coverage is unknown or unverified;
- related-data paths exist and will be preserved;
- startup components are owned and will not be changed in Phase 4;
- usage evidence is missing, stale, or only cautiously suggests non-use;
- Homebrew restoration is best-effort;
- the saved audit is a point-in-time snapshot requiring action-time revalidation.

Passing a check means only that its bounded condition was observed. It never means the
target is globally “safe to remove.” A plan is `preview_ready` only when no blocking
check exists; warnings and limitations still render. Phase 5 must rerun every check and
require explicit action-time approval.

Related data is never included in a removal action. Backup configuration, a timestamp,
and “not excluded” evidence never become a coverage claim.

## Persistence and integrity

SQLite schema version 1 contains:

- `plan_revisions(plan_id, revision, created_at, document_json, document_sha256)` with a
  composite primary key;
- `active_plan(singleton_id, plan_id, revision)` with exactly one optional pointer.

Appending a revision and moving the pointer occurs in one transaction. Documents use
canonical deterministic JSON, and reads verify the stored SHA-256 before Pydantic
validation. Existing revisions are never updated or deleted by public Phase 4 commands.
Unknown database versions refuse with recovery guidance; malformed/corrupt documents do
not fall back to guessed state.

SQLite writes are the sole Phase 4 mutation and occur only after the explicit
`plan add` command. `plan show` is a database read. Tests use isolated temporary paths;
public fixtures contain no host details.

## CLI and novice experience

`macwise plan` and `macwise plan show` render the active revision. With no plan, they
explain how to review and add one item. Output includes:

- plan ID, revision, snapshot time, and eligibility;
- each candidate and why it is being considered;
- exact typed action preview or “no action can be planned”;
- checks grouped as blockers, warnings, and observed passes;
- related data and startup components that remain untouched;
- rollback feasibility and limitations;
- a prominent “No changes were made” statement;
- the next safe command.

`plan add NAME` reports whether a revision was appended and immediately renders the
result. Hostile names/paths are sanitized for terminal output and remain inert data.

`apply` continues to exit nonzero and states that Phase 5 execution, current-state
revalidation, approval, verification, and undo are unavailable. It must not interpret a
`preview_ready` plan as authorization.

## Error handling

- Unavailable/partial audit evidence becomes warning or blocking preflight, not a crash
  or confident negative claim.
- Missing state directory is created only for explicit plan persistence.
- Directory/symlink/permission failures produce a bounded CLI recovery message and no
  partial revision.
- SQLite busy/corrupt/future-schema errors fail closed without overwriting data.
- A transaction failure leaves the prior active revision intact.
- Plan rendering never invokes collectors, actions, or external commands.

## Testing and acceptance

Tests proceed red-to-green and prove:

- strict frozen plan models, stable IDs, deterministic JSON, and validator invariants;
- every required preflight boundary using synthetic audit fixtures;
- exact cask/formula/standalone-app previews and no arbitrary executable string;
- ambiguous refusal, blocked exact candidates, duplicate idempotence, and append-only
  revisions;
- SQLite migration, hash validation, transaction rollback, injected paths, and refusal
  of future/corrupt state;
- CLI no-plan/add/show output, excellent help, hostile text sanitization, and Phase 5
  apply/undo refusal;
- filesystem/subprocess spies proving no installed-software, startup, or related-data
  mutation;
- full Python 3.12/3.13, Ruff, Pyright, build, privacy, skill, clean-wheel, and real
  read-only preview gates.

Phase 4 acceptance is local and independently reviewed. Hosted CI, public publication,
all action execution, action-time approval, verification, and undo remain open.

## Non-goals

- Applying, approving, verifying, or undoing actions.
- Removing related data, changing startup state, or invoking uninstallers.
- Plan item removal/reordering, multiple named plans, interactive questionnaires, or
  cross-device synchronization.
- Treating backup configuration as coverage or a preview as removal authorization.
- Live AI/research, Codex setup, public release, or hosted CI execution.
