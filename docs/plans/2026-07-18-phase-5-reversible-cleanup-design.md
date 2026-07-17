# Phase 5 Reversible Cleanup Design

Date: 2026-07-18

Status: Approved by the active autonomous goal and the existing Phase 5 product contract.
No installed software may be changed during implementation or acceptance; all mutating
tests use synthetic temporary bundles or injected command runners.

## Goal

Turn one accepted immutable cleanup preview into explicit, allowlisted, action-time
approved changes with fresh host-state validation, durable crash-visible manifests,
post-action verification, and separately approved undo. Deliver Trash-first manual app
removal, exact Homebrew uninstall, reversible supported startup disable, `macwise apply`,
and `macwise undo` without ever making discovered text or persisted command text
executable.

## Non-goals

- No arbitrary files, related user data, system components, launch daemons, privileged
  helpers, kernel/system extensions, or official vendor uninstallers are executed.
- No `sudo`, authorization prompt, shell, arbitrary command, recursive deletion, or
  permanent Trash emptying.
- No automatic rollback after a partial failure. MacWise stops, records truth, and asks
  for a separately reviewed undo.
- No real Homebrew uninstall, real startup mutation, or installed-app move during tests
  or local acceptance.
- No remote approval, background daemon, scheduled cleanup, multi-user execution, Codex
  mutation tool, or production release.

## Approaches considered

### 1. Execute persisted preview fields directly

Rejected. Even typed persisted intent can be stale or corrupted relative to current host
state. An executor must reconstruct an allowlisted operation after fresh identity,
dependency, protection, path, and destination checks.

### 2. Use a reusable approval token stored in SQLite

Rejected. A stored token can outlive the exact review and look like authentication. The
approval is instead an exact phrase derived from the current plan revision digest. It is
not secret and authorizes only that fingerprint after fresh revalidation.

### 3. Update one mutable execution row

Rejected. A crash between mutation and row update can erase the most important evidence.
Complete manifest revisions are appended before and after every attempted action so an
interrupted state remains visible and blocks further apply.

### 4. Automatically undo earlier actions if a later action fails

Rejected. Automatic rollback performs additional mutations without a fresh user choice
and may be only best effort for Homebrew. Execution stops on the first failure or failed
verification; the manifest exposes exactly what changed and `macwise undo` requires a
separate approval.

### 5. Recommended: fingerprint approval plus revalidated allowlisted adapters

Selected. It matches the public workflow, keeps CLI behavior inspectable, gives crashes
durable meaning, and permits each mutator to be isolated behind a small typed interface.

## User workflow

1. `macwise plan show` renders the exact active revision and its fingerprint.
2. `macwise apply` loads and integrity-checks that same revision, performs a fresh audit
   and action-specific host checks, and refuses any blocker, changed identity, missing
   source, occupied destination, unavailable evidence, or prior interrupted run.
3. Interactive use displays every action and warning, then requires the exact phrase
   `APPLY <16-character fingerprint>`. Non-interactive use refuses unless the same value
   is passed explicitly with `--approve`; the value is consent evidence, not a secret.
4. MacWise appends a prepared manifest revision, appends an in-progress revision before
   each action, invokes exactly one allowlisted adapter, verifies the result, and appends
   the observed outcome. It stops immediately on failure or verification mismatch.
5. `macwise undo` selects the latest run with applied reversible actions, renders its
   reverse-order operations, revalidates current state, and requires
   `UNDO <16-character run fingerprint>`. Each undo attempt is likewise manifested and
   verified.

Non-TTY calls without an exact fingerprint fail without mutation. Blocked plans, empty
plans, already-applied revisions, unresolved execution runs, and changed plan pointers
also fail without mutation.

## Plan evolution and startup intent

Phase 4 plan schema 1 remains readable but is never executable; `apply` requires a fresh
schema-2 preview so the user reviews the complete execution-era contract. New plans use
schema 2, including when they contain only Trash or Homebrew removal. Schema 2
preserves all schema-1 fields and adds typed action-target identity so one software
candidate may preview multiple ordered actions without weakening the one-rollback-per-
action invariant.

Startup mutation is opt-in during planning. A new plan-add option previews supported
startup disables alongside the software action; every startup action and inverse appears
in `plan show` before approval. Supported scope:

- exact user LaunchAgents under the current user's `~/Library/LaunchAgents`, with one
  unambiguous owner, a safe plist path, a safe label, and no symlink path component;
- exact Homebrew services with one owning formula and a valid Homebrew token.

LaunchDaemons, privileged helpers, login/background items without a stable reversible
interface, system extensions, Finder/Quick Look extensions, ambiguous ownership, and
system paths remain blocked. Startup disable does not delete a plist. The adapter uses
fixed `/bin/launchctl` argument vectors for the current user domain or exact
`brew services stop`; undo uses the recorded inverse only after current-state checks.

## Execution models

Strict frozen models define:

- `ExecutionRun`: run ID, plan ID/revision/digest, approval fingerprint, timestamps,
  ordered action records, state, limitations, and manifest revision;
- `ExecutionAction`: copied typed plan intent plus reconstructed operation kind, before
  observation, attempt state, verification state, inverse intent, and sanitized error;
- `ExecutionState`: prepared, in-progress, succeeded, partial, failed,
  verification-failed, undo-in-progress, undone, undo-partial, or interrupted;
- `ActionState`: pending, in-progress, applied, verified, failed, undo-in-progress,
  undone, or undo-failed;
- typed observations for Trash paths, Homebrew installation/service state, and supported
  LaunchAgent state.

Models never contain a shell program chosen from persisted data. A manifest may retain
the allowlisted operation kind and inert target values needed for verification and undo.
Every complete snapshot has canonical JSON and a SHA-256 integrity digest.

## Persistence and crash semantics

Execution history uses a separate versioned `executions.db` beneath the MacWise user data
directory or an injected test root. Separating it from `macwise.db` avoids coupling plan
schema migration to the higher-risk action journal.

The SQLite store is append-only by `(run_id, manifest_revision)`, maintains one active
execution pointer transactionally, validates every digest on read, rejects future or
unknown schemas, uses bound parameters, and applies the accepted plan-store symlink and
ancestor protections. A new run requires no unresolved active execution and the exact
active plan pointer/digest observed during preparation.

A shared advisory lock beneath the state root is acquired by plan append, apply, and undo.
Apply holds it for the complete critical section, reloads the full plan digest after lock
acquisition and before every action, and refuses concurrent writers. The displayed
fingerprint is the first 16 hexadecimal characters; internal comparisons always use the
full SHA-256 digest.

Before an adapter call, an in-progress revision is committed. If the process disappears,
the next command sees that revision as interrupted and refuses both new apply and blind
undo until bounded recovery inspection determines the actual state. No crash is silently
reported as success or failure.

## Revalidation

Revalidation is independent from the renderer and from execution adapters.

For every run:

- reload and digest-check the active plan;
- require preview-ready eligibility and at least one supported action;
- collect fresh audit evidence and require every target to resolve to the same exact
  identity;
- rerun dependency, usage, overlap, protection, backup, startup, rollback, and freshness
  policy; any new blocker refuses the whole run;
- require the plan pointer and digest to remain unchanged when the prepared manifest is
  appended.

For Trash actions:

- lstat the source without following symlinks;
- require an ordinary `.app` directory, the same bundle identity when available, a
  non-system path, and a non-symlink ancestor chain;
- reconstruct the destination from the typed plan/action identity and canonical current
  Trash root, require exact equality with the inert preview, and require it to be absent
  and on the same filesystem;
- refuse cross-device moves instead of copying recursively.

For Homebrew actions:

- resolve only a fixed Homebrew executable path;
- require the exact typed formula/cask token to remain installed with the same entity
  kind;
- rerun reverse-dependency, explicit-role, project-reference, service, and blocker checks;
- construct only `brew uninstall --formula TOKEN` or `brew uninstall --cask TOKEN` with
  no shell and Homebrew auto-update/analytics disabled;
- block casks whose fresh metadata contains uninstall, zap, pkg, privileged, or unknown
  removal artifacts; never use force, zap, cleanup, or autoremove.

For startup actions:

- require the same stable startup ID, kind, label/token, owner, user domain, and safe
  source path;
- capture whether the item was loaded/running/enabled before mutation and the exact
  plist SHA-256 for LaunchAgents;
- permit only the supported current-user LaunchAgent and Homebrew-service adapters.

## Allowlisted adapters and verification

### Manual applications

Use an injected filesystem adapter whose production implementation opens trusted source
and Trash parent directory descriptors, rechecks device/inode and bundle identity, and
performs one descriptor-relative same-filesystem atomic rename to the unique reconstructed
Trash name. It never follows symlinks, copies a directory tree, overwrites a destination,
or deletes content. Verification requires source absence, destination presence, and the
same captured inode/bundle identity. Undo requires the destination to remain the same
bundle and the original path to be free, then performs the reverse descriptor-relative
rename and verifies both paths.

### Homebrew

Use a dedicated mutating command adapter, separate from read collectors, with an enum of
allowed operations and fixed argument builders. Uninstall uses the exact formula/cask
form. Undo is explicitly best effort and uses the recorded type/token plus captured
version context; if the exact historical version cannot be restored, MacWise states that
limitation before approval. Verification uses fresh Homebrew read evidence rather than
exit status alone.

### Startup

Current-user LaunchAgent and Homebrew-service operations use dedicated fixed argument
builders. Verification queries fresh launch/service state; exit status alone is
insufficient. Undo restores only the recorded prior state and refuses if the plist hash,
owner, token, label, path, or domain changed.

## Failure behavior

- A preparation or approval failure writes no execution manifest and performs no action.
- An adapter failure records the bounded error, marks the run failed or partial, and
  stops before the next action.
- A verification mismatch records `verification-failed`, stops, and preserves undo
  eligibility when a reversible before/after observation exists.
- A manifest write failure before mutation prevents mutation. A manifest write failure
  after mutation is surfaced as an interrupted run and blocks further actions.
- Repeated apply of the same plan revision refuses. Repeated undo of an already-undone
  run is an idempotent refusal.
- Raw subprocess output, paths, labels, and metadata remain untrusted and sanitized only
  at human-output boundaries.

## Testing and acceptance

Implementation follows TDD in these slices:

1. execution/approval/manifest models and stable fingerprints;
2. append-only execution store, integrity, concurrency, and crash-state tests;
3. fresh revalidation and plan-digest compare-and-append;
4. synthetic same-filesystem Trash apply/verify/undo;
5. injected exact Homebrew uninstall/verify/best-effort undo;
6. plan-schema-2 startup previews and injected supported startup adapters;
7. `apply`/`undo` CLI, TTY/non-TTY approval, errors, help, and guided flow;
8. hostile target, symlink, race, stale plan, partial failure, replay, and mutation-spy
   tests;
9. independent skeptical review and full Python 3.12/3.13, quality, build, privacy,
   skill, clean-wheel, synthetic manual-app demo, and aggregate-only read gates.

Tests may atomically rename only synthetic bundles inside a canonical temporary root.
All Homebrew and launchctl mutation calls use injected runners and assert exact argv,
environment, timeouts, bounded output, and `shell=False`. Local acceptance does not
exercise installed software, the real Trash, real Homebrew state, or real startup state.

## Stop conditions

Implementation stops for user authority before any real installed-software demo,
privileged action, production deployment, package publication, or irreversible recovery
choice. Missing evidence, changed identity, unsafe path topology, an unavailable exact
inverse, or repeated verification failure causes a safe refusal rather than broader
mutation.
