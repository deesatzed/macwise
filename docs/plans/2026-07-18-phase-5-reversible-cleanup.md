# Phase 5 Reversible Cleanup Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver fingerprint-approved, freshly revalidated, allowlisted apply/verify/undo for Trash-first manual applications, exact safe-scope Homebrew packages, and supported reversible startup items, with append-only crash-visible manifests.

**Architecture:** Evolve plans to schema 2 for explicit ordered action targets, then keep approval, revalidation, host adapters, execution coordination, and append-only execution persistence as separate typed modules. A shared state lock binds the active plan and execution journal across databases; each adapter reconstructs an allowlisted operation from current trusted roots, writes an in-progress manifest before mutation, verifies observed state afterward, and supplies a separately approved inverse.

**Tech Stack:** Python 3.12+, Pydantic v2, SQLite, Typer/Rich, standard-library `fcntl`/`os`/`sqlite3`/`hashlib`, pytest, Ruff, Pyright, uv.

---

The active feature branch is the canonical user-declared workspace. The normally required
`using-git-worktrees` skill is not available in this environment, so implementation stays
on this non-main branch. Never run a real uninstall, real startup mutation, or move from
the real Applications folders/Trash during implementation or acceptance.

### Task 1: Plan schema 2, canonical digests, ordered startup previews, and state lock

**Files:**

- Modify: `src/macwise/models/plan.py`
- Modify: `src/macwise/models/__init__.py`
- Modify: `src/macwise/services/planning.py`
- Modify: `src/macwise/services/__init__.py`
- Modify: `src/macwise/persistence/plans.py`
- Create: `src/macwise/persistence/locking.py`
- Modify: `src/macwise/persistence/__init__.py`
- Modify: `src/macwise/cli.py`
- Test: `tests/models/test_plan.py`
- Test: `tests/services/test_planning.py`
- Test: `tests/persistence/test_plan_store.py`
- Create: `tests/persistence/test_state_lock.py`
- Test: `tests/cli/test_phase_four_planning.py`

**Step 1: Write failing schema-2 and lock tests**

Add tests proving:

- schema-1 plan JSON remains readable and its digest is stable;
- new planning emits schema 2, ordered removal actions, and the same full digest across
  round-trips;
- `include_startup=True` previews only exact supported current-user LaunchAgents and
  Homebrew services, before the removal action;
- unsupported/ambiguous/system startup kinds create blockers rather than actions;
- action sequences are unique and contiguous, startup IDs are unique, and every action
  still has exactly one rollback blueprint;
- adding to a schema-1 active plan creates a freshly revalidated schema-2 revision rather
  than treating old candidate snapshots as execution-ready;
- the shared lock rejects a concurrent writer and neither plan state nor lock paths may
  traverse symlink ancestors.

Model the schema distinction explicitly:

```python
class PlanActionKind(StrEnum):
    MOVE_APPLICATION_TO_TRASH = "move_application_to_trash"
    HOMEBREW_UNINSTALL_FORMULA = "homebrew_uninstall_formula"
    HOMEBREW_UNINSTALL_CASK = "homebrew_uninstall_cask"
    DISABLE_LAUNCH_AGENT = "disable_launch_agent"
    STOP_HOMEBREW_SERVICE = "stop_homebrew_service"

class PlannedAction(BaseModel):
    sequence: int | None = Field(default=None, ge=1)
    startup_id: str | None = None
    startup_kind: StartupKind | None = None
    startup_label: str | None = None
    startup_source_path: str | None = None
```

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/models/test_plan.py tests/services/test_planning.py tests/persistence/test_plan_store.py tests/persistence/test_state_lock.py tests/cli/test_phase_four_planning.py
```

Expected: collection/import failures for `StateLock` and assertion failures for schema 2,
ordered startup actions, digest APIs, and refresh behavior.

**Step 3: Implement the minimum schema and lock**

- Accept plan schema versions 1 and 2 in the model, preserving schema-1 validation.
- Require schema-2 action sequence/order/target invariants and emit schema 2 for every new
  or refreshed plan.
- Expose one canonical JSON byte/digest function from plan persistence; never duplicate
  digest serialization in approval code.
- Extend planner input with opt-in startup intent, using only collected exact typed
  records and stable IDs. Do not hash/read plist contents during pure planning.
- Add `StateLock` using a non-symlink regular lock file and non-blocking `fcntl.flock`.
  Inject the path in tests. Plan append acquires the lock unless the caller supplies an
  already-held lock context for a later execution transaction.
- Keep schema-1 reads intact; the future executor, not PlanStore, will refuse schema 1.
- Update `plan show` to render every ordered action and inverse limitation. Update
  `plan add` with an explicit `--include-startup` option and truthful upgrade language.

**Step 4: Run focused and full green gates**

Run:

```bash
uv run pytest -q tests/models/test_plan.py tests/services/test_planning.py tests/persistence/test_plan_store.py tests/persistence/test_state_lock.py tests/cli/test_phase_four_planning.py
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Expected: all pass; existing schema-1 persistence and Phase 4 CLI regressions remain green.

**Step 5: Commit**

```bash
git add src/macwise/models src/macwise/services src/macwise/persistence src/macwise/cli.py tests/models/test_plan.py tests/services/test_planning.py tests/persistence tests/cli/test_phase_four_planning.py
git commit -m "feat: prepare execution-ready plan schema"
```

Rollback: revert this commit; append-only schema-1 plan rows remain readable by the prior
code. Do not delete local planning state.

### Task 2: Strict execution, observation, approval, and manifest models

**Files:**

- Create: `src/macwise/models/execution.py`
- Modify: `src/macwise/models/__init__.py`
- Create: `src/macwise/services/approval.py`
- Modify: `src/macwise/services/__init__.py`
- Create: `tests/models/test_execution.py`
- Create: `tests/services/test_approval.py`

**Step 1: Write failing model and fingerprint tests**

Test strict frozen models for run/action states, before/after observations, inverse
intent, complete manifest revisions, valid transition ordering, unique action mappings,
and schema/future-version refusal. Test a 16-character uppercase display fingerprint and
full-digest comparison:

```python
full_digest = plan_digest(plan)
assert approval_fingerprint(full_digest) == full_digest[:16].upper()
assert approval_phrase(full_digest) == f"APPLY {full_digest[:16].upper()}"
```

Reject approval with whitespace tricks, case changes, prefixes/suffixes, another plan
revision, or schema 1.

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/models/test_execution.py tests/services/test_approval.py
```

Expected: import failures because execution/approval modules do not exist.

**Step 3: Implement minimum strict models and pure approval helpers**

Define `ExecutionState`, `ActionState`, `VerificationState`, typed inert observations,
`ExecutionAction`, and `ExecutionRun`. Store only typed operation kinds and inert target
facts—never arbitrary executables or argv. Validators enforce:

- monotonic manifest revision;
- one execution action per plan action and exact order;
- no succeeded run with unverified actions;
- partial/failed/interrupted states truthfully reflect action states;
- undo uses reverse verified action order and never claims Homebrew exact restoration.

Approval helpers compare the exact phrase with `hmac.compare_digest`, even though the
fingerprint is not secret, to avoid normalization surprises.

**Step 4: Run focused and full gates**

Run the focused tests, full suite, Ruff, format check, and Pyright. Expected: all pass.

**Step 5: Commit**

```bash
git add src/macwise/models/execution.py src/macwise/models/__init__.py src/macwise/services/approval.py src/macwise/services/__init__.py tests/models/test_execution.py tests/services/test_approval.py
git commit -m "feat: model approved execution manifests"
```

Rollback: revert; no persistence or host adapter exists yet.

### Task 3: Append-only execution store and interrupted-run truth

**Files:**

- Create: `src/macwise/persistence/executions.py`
- Modify: `src/macwise/persistence/__init__.py`
- Create: `tests/persistence/test_execution_store.py`
- Modify: `tests/security/test_planning_safety.py`

**Step 1: Write failing persistence tests**

Cover absent-store read-only behavior, schema creation on first append only, canonical
JSON/digest round-trip, immutable manifest revisions, active pointer, one unresolved run,
stale writer conflict, transaction rollback, corruption, future/unknown schema,
non-regular/symlink/ancestor paths, lock sharing, and interrupted in-progress state.

Add a crash simulation:

```python
store.append(prepared)
store.append(in_progress)
assert store.active().state is ExecutionState.IN_PROGRESS
with pytest.raises(ExecutionStoreError, match="interrupted"):
    store.begin(another_run)
```

**Step 2: Run tests to verify RED**

Run `uv run pytest -q tests/persistence/test_execution_store.py tests/security/test_planning_safety.py`.
Expected: import failures for `ExecutionStore`.

**Step 3: Implement the minimum store**

Use separate `executions.db`, schema version 1, canonical JSON SHA-256, bound SQL,
`BEGIN IMMEDIATE`, exact expected active revision checks, and the accepted full ancestor
symlink policy. Reads never migrate. Store complete immutable run snapshots keyed by
`(run_id, manifest_revision)` and one active pointer. Require a caller-held `StateLock`
for append/begin APIs so plan and execution coordination can share one critical section.

**Step 4: Run focused/full/static gates**

Expected: focused tests and full suite pass; Ruff/Pyright clean.

**Step 5: Commit**

```bash
git add src/macwise/persistence tests/persistence/test_execution_store.py tests/security/test_planning_safety.py
git commit -m "feat: persist crash-visible execution manifests"
```

Rollback: revert; do not delete any generated execution database because it is the action
journal even if a later implementation is rolled back.

### Task 4: Fresh plan revalidation and reconstructed prepared operations

**Files:**

- Create: `src/macwise/services/revalidation.py`
- Modify: `src/macwise/services/__init__.py`
- Modify: `src/macwise/collectors/homebrew.py`
- Modify: `src/macwise/models/software.py`
- Modify: `src/macwise/models/audit.py`
- Create: `tests/services/test_revalidation.py`
- Modify: `tests/collectors/test_homebrew.py`
- Modify: `tests/models/test_audit.py`

**Step 1: Write failing revalidation tests**

Fixtures prove refusal for schema 1, blocked/empty plans, changed plan digest, missing or
ambiguous current identity, new dependency/project/usage/keep/protection blocker,
unavailable collector evidence, changed action kind/target, occupied Trash destination,
cross-device source/Trash, unsafe path topology, and unsupported cask artifacts.

Add safe passes for a current manual app, explicit leaf formula, simple app-only cask,
user LaunchAgent with exact owner/path/label, and Homebrew service. The result is a typed
`PreparedExecution` with reconstructed operations and full before observations; it does
not mutate.

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/services/test_revalidation.py tests/collectors/test_homebrew.py tests/models/test_audit.py
```

Expected: import/model failures and absent cask artifact safety metadata.

**Step 3: Implement minimum read-only revalidation**

- Preserve enough raw typed cask artifact categories from Homebrew JSON to distinguish
  simple app artifacts from uninstall/zap/pkg/privileged/unknown behavior. Migrate older
  audit schemas with an empty/unknown-safe value.
- Reuse pure preflight policy through a public revalidation API; do not duplicate weaker
  policy in the CLI.
- Reconstruct canonical Trash destinations from action IDs/current Trash root and compare
  them with inert preview fields.
- Produce typed prepared operations only for schema-2 ordered actions whose current
  evidence and exact host facts pass. Unknown means refusal.
- Hash supported LaunchAgent plist bytes but do not load/disable anything.

**Step 4: Run focused/full/static gates**

Expected: all pass. Confirm no mutating function or subprocess enum is imported by this
read-only module.

**Step 5: Commit**

```bash
git add src/macwise/services/revalidation.py src/macwise/services/__init__.py src/macwise/collectors/homebrew.py src/macwise/models tests/services/test_revalidation.py tests/collectors/test_homebrew.py tests/models/test_audit.py
git commit -m "feat: revalidate cleanup actions against current state"
```

Rollback: revert model/collector/service changes; old audit migrations remain covered by
tests and no host action exists.

### Task 5: Descriptor-relative Trash apply, verification, and undo coordinator

**Files:**

- Create: `src/macwise/execution/__init__.py`
- Create: `src/macwise/execution/filesystem.py`
- Create: `src/macwise/services/execution.py`
- Modify: `src/macwise/services/__init__.py`
- Create: `tests/execution/test_filesystem.py`
- Create: `tests/services/test_execution_service.py`
- Modify: `tests/security/test_planning_safety.py`

**Step 1: Write failing synthetic filesystem tests**

Create only synthetic `.app` directories beneath `/private`-canonical pytest temporary
roots with injected source and Trash roots. Prove:

- descriptor-relative same-device rename preserves inode and never copies/deletes;
- source/destination symlink, ancestor swap, inode replacement, identity replacement,
  occupied destination, path escape, cross-device signal, system path, or permission
  failure refuses;
- prepared and in-progress manifests are appended before rename;
- source absence + destination identity verifies success;
- process crash after in-progress is recovered read-only from exact source/destination;
- undo requires exact destination identity and free original path, renames in reverse,
  verifies, and refuses replay;
- a manifest append failure before rename prevents the adapter call.

Use spies so production Applications/Trash paths cause immediate test failure.

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/execution/test_filesystem.py tests/services/test_execution_service.py tests/security/test_planning_safety.py
```

Expected: import failures for execution modules.

**Step 3: Implement minimum filesystem adapter and coordinator**

- Adapter accepts only a typed prepared Trash operation and injected trusted roots.
- Open trusted parent directories with no-follow semantics, lstat exact basenames, compare
  device/inode/identity, and call descriptor-relative `os.rename` without overwrite or
  cross-device fallback.
- Coordinator holds `StateLock`, verifies plan digest, appends manifest revisions before
  and after adapter calls, stops on first failure, and verifies observed state rather than
  trusting return values.
- Undo reads the journal, displays/accepts no approval itself yet, applies reverse order,
  and manifests every state. CLI integration comes later.

**Step 4: Run focused/full/static gates**

Expected: all pass. Confirm the test mutation spy reports only synthetic rename calls.

**Step 5: Commit**

```bash
git add src/macwise/execution src/macwise/services/execution.py src/macwise/services/__init__.py tests/execution tests/services/test_execution_service.py tests/security/test_planning_safety.py
git commit -m "feat: apply and undo synthetic Trash actions"
```

Rollback: revert source/tests only. If a synthetic test journal remains, retain it until
the test root is naturally removed; never delete or edit a real execution journal.

### Task 6: Exact Homebrew and supported startup adapters

**Files:**

- Create: `src/macwise/execution/commands.py`
- Modify: `src/macwise/execution/__init__.py`
- Modify: `src/macwise/services/execution.py`
- Modify: `src/macwise/system/commands.py`
- Modify: `src/macwise/system/__init__.py`
- Create: `tests/execution/test_commands.py`
- Modify: `tests/services/test_execution_service.py`
- Modify: `tests/system/test_commands.py`
- Modify: `tests/security/test_planning_safety.py`

**Step 1: Write failing exact-runner tests**

With injected runners/resolvers only, prove exact argv/environment/timeout/output bounds
and `shell=False` for:

- `brew uninstall --formula TOKEN` and safe-scope `--cask TOKEN`;
- best-effort `brew install --formula/--cask TOKEN` undo with version limitation;
- `brew services stop TOKEN` and inverse start only when prior state was running;
- current-user `launchctl disable/bootout` and inverse `enable/bootstrap` only for exact
  safe label/domain/path and unchanged plist hash.

Reject null/control tokens, extra flags, discovered executables, system domains,
LaunchDaemons, changed plist content, unsupported cask artifacts, live runner use in tests,
and any force/zap/cleanup/autoremove argument. Simulate success exit with failed fresh
verification and require `verification-failed` plus stop.

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/execution/test_commands.py tests/services/test_execution_service.py tests/system/test_commands.py tests/security/test_planning_safety.py
```

Expected: missing mutating command adapter and coordinator support.

**Step 3: Implement minimum dedicated mutating adapter**

Define a closed `MutationOperation` enum and fixed argument builders; do not expose a
generic `run(arguments)` public API. Reuse safe environment/bounded output primitives
without adding mutation operations to `ReadCommand`. Fresh read callbacks determine
verification. Integrate action ordering, stop-on-first-failure, partial manifests, and
reverse-order separately approved undo preparation.

**Step 4: Run focused/full/static gates**

Expected: all pass; exact spies show no live Homebrew/launchctl mutation.

**Step 5: Commit**

```bash
git add src/macwise/execution src/macwise/services/execution.py src/macwise/system tests/execution/test_commands.py tests/services/test_execution_service.py tests/system/test_commands.py tests/security/test_planning_safety.py
git commit -m "feat: add allowlisted Homebrew and startup actions"
```

Rollback: revert. Never attempt to “clean up” a real external tool because tests must have
used fake runners only.

### Task 7: Approval-gated `apply` and `undo` CLI with recovery UX

**Files:**

- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Create: `tests/cli/test_phase_five_execution.py`
- Modify: `tests/cli/test_guided_menu.py`
- Modify: `tests/cli/test_help_contract.py`
- Modify: `tests/cli/test_scan.py`

**Step 1: Write failing CLI tests**

Inject audit, stores, lock, coordinator, adapters, clock, and interactivity. Cover:

- no plan, schema-1 plan, blocked plan, changed/stale plan, unsupported action, unresolved
  prior run, and failed revalidation refuse without manifest/action;
- interactive `apply` renders exact action/warning/inverse list and requires exact
  `APPLY <fingerprint>`;
- non-TTY apply refuses without `--approve` and succeeds only with the exact fingerprint;
- apply reports verified, partial, failed, verification-failed, and interrupted states
  with concrete recovery commands;
- undo renders reverse actions/limitations and requires exact `UNDO <run-fingerprint>`;
- already undone, changed destination/plist, ambiguous recovery, or unavailable inverse
  refuses;
- all hostile names/paths/errors are sanitized and never become terminal structure;
- help states mutation, approval, no elevation, preserved related data, best-effort
  Homebrew undo, examples, and next steps;
- guided menu routes to plan review before apply and exposes undo recovery without
  auto-confirming.

**Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/cli/test_phase_five_execution.py tests/cli/test_guided_menu.py tests/cli/test_help_contract.py tests/cli/test_scan.py
```

Expected: current Phase 4 refusal output fails all real execution expectations.

**Step 3: Implement minimum CLI integration**

Add explicit `--approve` options whose values are not normalized. TTY prompts use hidden
or ordinary input only as UX; fingerprints are not secrets. Always show plan/run details
before prompting. Catch only bounded public execution/store/lock errors; never print raw
stack traces or subprocess output. `apply` and `undo` exit nonzero unless every requested
operation and verification completes. Preserve read-only behavior of `plan show`.

**Step 4: Run focused/full/static/help gates**

Run focused tests, full suite, Ruff, format, Pyright, and manual help rendering for root,
plan, apply, and undo. Expected: all pass; no real adapter factories are invoked by tests.

**Step 5: Commit**

```bash
git add src/macwise/cli.py src/macwise/help_text.py tests/cli
git commit -m "feat: deliver approved apply and undo workflow"
```

Rollback: revert CLI/tests; execution journals remain immutable and inspectable even if
commands temporarily return to refusal.

### Task 8: Threat hardening, independent review, and Phase 5 acceptance

**Files:**

- Modify: `tests/security/test_planning_safety.py`
- Create: `tests/security/test_execution_safety.py`
- Modify: `docs/threat-model.md`
- Create: `docs/phase-5-acceptance.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`

**Step 1: Add adversarial safety regressions**

Test plan DB tampering, manifest tampering, digest collision-prefix mismatch, approval
replay, state-lock races, inode/symlink swaps, destination substitution, control/bidi/
newline targets, SQL-shaped metadata, Homebrew flag injection, malicious plist content,
changed LaunchAgent hash, crash at every journal boundary, partial multi-action runs,
and reverse-order undo. Mutation spies must enumerate only synthetic rename or fake runner
calls.

**Step 2: Run security RED/GREEN and full local gates**

Run focused security tests first and implement only demonstrated hardening. Then run:

```bash
uv run --python 3.12 --frozen pytest -q
uv run --python 3.13 --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen pyright
uv build
uv run --with pyyaml python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/macwise
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ci.yml")'
uv run --frozen pytest -q tests/repository
git diff --check
```

Use isolated `UV_PROJECT_ENVIRONMENT` paths for parallel Python-version runs. Install the
wheel into a fresh Python 3.12 environment and exercise schema-2 planning, execution
model/store, apply/undo help, a synthetic bundle move/verify/undo under canonical
`/private/tmp`, and fake Homebrew/startup runners only.

**Step 3: Request and adjudicate independent skeptical review**

Use @requesting-code-review. Require Critical/Important findings across approval,
revalidation, state locking, TOCTOU, command allowlists, crash semantics, manifest
integrity, partial failure, undo, UX, and test/live-boundary leakage. Use
@receiving-code-review; classify every recommendation Accepted / Rejected / Needs
Investigation in `PROGRESS.md`, fix accepted findings test-first, and rerun the full gate.

**Step 4: Run claim validation and update durable truth**

Use @claim-validation and @verification-before-completion. Scan scoped markers/skips,
inspect dirty state, render help, and save `docs/phase-5-acceptance.md` only if direct
evidence passes. Mark MW-400 done and MW-500 ready. State explicitly that local acceptance
used synthetic/fake mutators and does not prove real installed-app permissions, live
Homebrew behavior, live launchctl behavior, hosted CI, publication, or production safety.

**Step 5: Commit accepted hardening and acceptance separately**

```bash
git add src tests docs/threat-model.md PROGRESS.md DECISIONS.md
git commit -m "fix: close Phase 5 review gaps"
git add docs/phase-5-acceptance.md README.md CHANGELOG.md PROGRESS.md TASK_QUEUE.md
git commit -m "docs: accept local Phase 5 cleanup"
```

Rollback: do not delete or rewrite action journals. Revert source/docs commits only;
users with an interrupted or applied manifest must retain the version capable of reading
and recovering that manifest.

## Overall stop rules

Stop and request authority before any command could touch a real installed app, real
Trash, real Homebrew installation, real launchctl state, privileged path, published
package, remote repository, or production system. Stop on three repeated failures after
bounded mitigation, unresolved manifest corruption, an ambiguous interrupted action, or
any design change that would broaden mutation beyond D-026 through D-030.
