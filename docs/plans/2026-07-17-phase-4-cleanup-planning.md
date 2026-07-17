# Phase 4 Cleanup Planning Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver persistent immutable cleanup-plan previews with dependency, ambiguity,
protection, usage, related-data, backup, and rollback preflight while proving that Phase 4
cannot change installed software or user data.

**Architecture:** Add a strict version-1 plan model, a pure audit-to-plan service, and an
append-only SQLite store. The Typer CLI performs a fresh read-only audit only for
`plan add`, persists typed non-executable intent, and renders the saved revision for
`plan`/`plan show`; `apply` and `undo` remain Phase 5 refusals.

**Tech Stack:** Python 3.12+, Pydantic v2, standard-library `sqlite3`/`hashlib`,
platformdirs, Typer, pytest, Ruff, Pyright, uv/hatchling.

---

Controlling design: `docs/plans/2026-07-17-phase-4-cleanup-planning-design.md` and
D-024/D-025 in `DECISIONS.md`.

### Task 1: Strict immutable plan schema

**Files:**

- Create: `src/macwise/models/plan.py`
- Modify: `src/macwise/models/__init__.py`
- Create: `tests/models/test_plan.py`

**Step 1: Write the failing model tests**

Test the public enums and frozen models:

```python
def test_plan_document_is_frozen_versioned_and_requires_consistent_eligibility() -> None:
    document = PlanDocument(
        plan_id="plan:test",
        revision=1,
        created_at=COLLECTED_AT,
        source_audit_id="audit:test",
        source_audit_collected_at=COLLECTED_AT,
        candidates=(candidate(),),
        actions=(trash_action(),),
        checks=(passing_check(),),
        rollback=(trash_rollback(),),
        eligibility=PlanEligibility.PREVIEW_READY,
    )
    assert document.schema_version == 1
    assert PlanDocument.model_validate_json(document.model_dump_json()) == document
    with pytest.raises(ValidationError):
        document.revision = 2
```

Also assert:

- stable plan/action/check/rollback IDs are deterministic and do not embed raw paths;
- a block check requires `eligibility=blocked`;
- action subject IDs and rollback action IDs must exist in the same document;
- typed action validators require only the fields appropriate to application Trash,
  Homebrew formula, or Homebrew cask intent;
- no model contains `command`, `shell`, or arbitrary executable fields;
- candidates/checks/actions are nonempty where required and unknown extras reject.

**Step 2: Verify RED**

Run: `uv run pytest -q tests/models/test_plan.py`

Expected: collection fails because `macwise.models.plan` does not exist.

**Step 3: Implement the minimal models**

Define:

- `PlanEligibility`: `blocked`, `preview_ready`;
- `PlanActionKind`: `move_application_to_trash`, `homebrew_uninstall_formula`,
  `homebrew_uninstall_cask`;
- `PreflightKind`: identity, protection, dependency, usage, overlap, related_data,
  backup, startup, rollback, staleness;
- `PreflightOutcome`: pass, warning, block;
- `RollbackFeasibility`: reversible, best_effort, unavailable;
- `PlanCandidate`, `PlannedAction`, `PreflightCheck`, `RollbackBlueprint`,
  `PlanDocument` as `extra="forbid", frozen=True` Pydantic models;
- SHA-256 stable ID helpers scoped by plan/subject/action/check/revision.

Use typed optional fields with model validators rather than a persisted argv. Ensure the
document validator checks referential integrity and derives/validates eligibility.

**Step 4: Verify GREEN**

Run: `uv run pytest -q tests/models/test_plan.py tests/models`

Expected: all plan and existing model tests pass.

**Step 5: Commit**

```bash
git add src/macwise/models/plan.py src/macwise/models/__init__.py tests/models/test_plan.py
git commit -m "feat: add immutable cleanup plan models"
```

### Task 2: Deterministic action previews and preflight engine

**Files:**

- Create: `src/macwise/services/planning.py`
- Modify: `src/macwise/services/__init__.py`
- Create: `tests/services/test_planning.py`

**Step 1: Write failing planner fixtures**

Build only synthetic `AuditDocument` fixtures. Test:

```python
def test_standalone_application_gets_exact_trash_preview_and_preserves_data() -> None:
    result = add_candidate(None, audit, app.id, clock=lambda: NOW)
    action = result.plan.actions[0]
    assert action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH
    assert action.source_path == "/Applications/Example.app"
    assert action.trash_path is not None
    assert result.plan.eligibility is PlanEligibility.PREVIEW_READY
    assert related_path.id not in {action.target_id for action in result.plan.actions}
```

Cover these boundaries:

- standalone application -> exact Trash intent and reversible restore blueprint;
- exactly cask-linked application -> one cask-uninstall intent, never a second Trash
  action;
- formula/cask -> exact token and best-effort reinstall blueprint;
- dependency install role, reverse dependencies, or approved project references -> block;
- protected application -> persisted candidate, no action, protection block;
- missing/ambiguous action identity -> persisted candidate, no action, identity block;
- active/recent/probable/indirect usage -> block; cautious/missing evidence -> warning;
- keep/keep-together recommendation -> block; review/no-recommendation -> warning;
- related paths/startup owners -> preserved warnings, never actions;
- backup coverage always remains unverified and warning-only for reversible/preserved-data
  actions;
- unavailable rollback -> block; best-effort Homebrew rollback -> warning;
- incomplete collector evidence -> explicit warning/block rather than a negative claim;
- duplicate subject add is idempotent and returns `changed=False`;
- adding a new subject appends revision + 1 and preserves the prior immutable document;
- ordering and stable IDs are deterministic.

**Step 2: Verify RED**

Run: `uv run pytest -q tests/services/test_planning.py`

Expected: collection fails because the planning service does not exist.

**Step 3: Implement pure planning functions**

Expose a result dataclass and function:

```python
@dataclass(frozen=True, slots=True)
class PlanningResult:
    plan: PlanDocument
    changed: bool

def add_candidate(
    current: PlanDocument | None,
    audit: AuditDocument,
    subject_id: str,
    *,
    clock: Callable[[], datetime],
    plan_id_factory: Callable[[], str],
) -> PlanningResult: ...
```

Split small pure helpers for snapshots, typed action selection, each preflight group,
rollback construction, and eligibility. A deterministic Trash destination uses the
original bundle basename plus action-ID suffix under `~/.Trash` as preview data only;
do not touch or create that path. Never import `sqlite3`, Typer, or subprocess adapters.

**Step 4: Verify GREEN**

Run: `uv run pytest -q tests/services/test_planning.py tests/services`

Expected: planner and service regressions pass.

**Step 5: Commit**

```bash
git add src/macwise/services/planning.py src/macwise/services/__init__.py tests/services/test_planning.py
git commit -m "feat: build cleanup plan previews"
```

### Task 3: Append-only SQLite plan store

**Files:**

- Create: `src/macwise/persistence/__init__.py`
- Create: `src/macwise/persistence/plans.py`
- Create: `tests/persistence/test_plan_store.py`

**Step 1: Write failing persistence tests**

Use only `tmp_path`. Assert:

- construction does not create a database; first append creates parent/database;
- schema migration creates version 1 tables and `PRAGMA user_version = 1`;
- append + read returns the identical `PlanDocument`;
- two revisions coexist and only the active pointer advances;
- duplicate `(plan_id, revision)` refuses instead of overwriting;
- canonical JSON digest verifies on read;
- tampered JSON/digest, malformed document, and future DB schema refuse closed;
- transaction failure preserves the previous active revision;
- a symlink database or unsafe non-directory parent refuses;
- no production state path appears in temporary-store tests.

**Step 2: Verify RED**

Run: `uv run pytest -q tests/persistence/test_plan_store.py`

Expected: collection fails because `macwise.persistence` does not exist.

**Step 3: Implement the store**

Create `PlanStore(path: Path | None = None)` with:

```python
def default_plan_database() -> Path:
    return user_data_path("macwise") / "macwise.db"

def active(self) -> PlanDocument | None: ...
def append(self, plan: PlanDocument) -> None: ...
```

Use explicit transactions, bound SQL parameters, canonical sorted compact JSON, SHA-256,
strict schema checks, short busy timeout, foreign keys, and no destructive migrations.
Wrap expected failures in a typed `PlanStoreError` whose public message contains no SQL
or private implementation detail.

**Step 4: Verify GREEN**

Run: `uv run pytest -q tests/persistence/test_plan_store.py`

Expected: all store/integrity tests pass.

**Step 5: Commit**

```bash
git add src/macwise/persistence tests/persistence/test_plan_store.py
git commit -m "feat: persist immutable plan revisions"
```

### Task 4: Real `plan add`, `plan`, and `plan show` CLI

**Files:**

- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Create: `tests/cli/test_phase_four_planning.py`
- Modify: `tests/cli/test_guided_menu.py`
- Modify: `tests/cli/test_help_contract.py`

**Step 1: Write failing CLI tests**

Inject a static audit and temporary `PlanStore`. Test:

- `plan`/`plan show` with no state explain `plan add NAME`, report no changes, and exit 0;
- `plan add app:Example` appends revision 1 and renders snapshot, eligibility, exact action
  preview, blockers/warnings/passes, preserved related data/startup, rollback, and
  “No changes were made”;
- a second distinct add renders revision 2; duplicate add remains revision 1 and explains
  idempotence;
- missing/ambiguous names exit 2 and leave SQLite unchanged;
- exact protected/dependency candidates persist as blocked;
- `plan show` reads the saved plan without invoking `_service_factory`;
- store errors exit 2 with bounded recovery text and preserve prior state;
- `apply` still exits 2 even for preview-ready state and names revalidation/approval,
  verification, and undo as unavailable;
- guided menu choice 8 routes to the real no-plan planning view;
- help describes read-only plan-state writes accurately, gives realistic examples, and
  points to `plan show`/`explain`.

**Step 2: Verify RED**

Run: `uv run pytest -q tests/cli/test_phase_four_planning.py`

Expected: tests fail on the Phase 3 refusal surfaces and absent store factory.

**Step 3: Implement CLI integration**

Add an injectable `_plan_store_factory`. Keep `_resolve_record` as the unique identity
boundary. Add a shared sanitized renderer for plan snapshots. `plan add` is the only
command that runs `_audit()` and writes planning state; `plan` and `plan show` only call
`store.active()`.

Update Phase 4 help to say planning writes local MacWise state but does not change
installed software. Do not add a hidden approval flag or action executor.

**Step 4: Verify GREEN**

Run:

```bash
uv run pytest -q tests/cli/test_phase_four_planning.py tests/cli/test_guided_menu.py tests/cli/test_help_contract.py
```

Expected: all Phase 4 CLI/help/guided tests pass.

**Step 5: Commit**

```bash
git add src/macwise/cli.py src/macwise/help_text.py tests/cli
git commit -m "feat: deliver persistent cleanup previews"
```

### Task 5: Hostile-data and zero-host-mutation proof

**Files:**

- Modify: `tests/security/test_hostile_metadata.py`
- Create: `tests/security/test_planning_safety.py`
- Modify: `docs/threat-model.md`

**Step 1: Write failing safety tests**

Assert hostile names/paths/tokens containing shell syntax, prompt text, newlines, Markdown,
control/bidi characters, and SQL-shaped strings:

- remain raw inert data in plan JSON/SQLite;
- cannot forge terminal sections or create marker files;
- are passed only as SQL parameters;
- never select an action executable or action kind;
- cannot escape an approved application bundle identity into arbitrary deletion intent.

Install spies/guards around `Path.rename`, `Path.unlink`, `shutil`, `subprocess`, and the
read-command adapter during pure planner/store/show tests. Permit creation/writes only
inside the injected temporary planning-state root. Assert no Trash, application,
Homebrew, startup, or related-data path changed.

**Step 2: Verify RED**

Run: `uv run pytest -q tests/security/test_planning_safety.py tests/security/test_hostile_metadata.py`

Expected: new assertions fail until the plan renderer/path validators and threat-model
contract exist.

**Step 3: Implement minimal hardening**

Tighten plan validators, persistence path checks, and terminal sanitization only where
the failing tests demonstrate a boundary. Document SQLite local-state threats,
persisted-data non-authority, exact target revalidation, and Phase 4 zero-action scope.

**Step 4: Verify GREEN**

Run:

```bash
uv run pytest -q tests/security tests/persistence tests/cli/test_phase_four_planning.py
```

Expected: safety, persistence, and planning CLI tests pass with no marker or host changes.

**Step 5: Commit**

```bash
git add tests/security docs/threat-model.md
git commit -m "test: prove planning cannot mutate the host"
```

### Task 6: Independent review and corrections

**Files:**

- Modify only files justified by accepted findings
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md` only for a material design change

**Step 1: Run a skeptical review**

Use @requesting-code-review for correctness, SQLite integrity, stale-state handling,
privacy, target/action confusion, TOCTOU, help quality, and any path from preview data to
execution. Ask specifically whether exact-but-blocked storage can be mistaken for
approval and whether every Phase 4 write is confined to injected/local state.

**Step 2: Adjudicate feedback**

Use @receiving-code-review. Classify every finding Accepted, Rejected, or Needs
Investigation with code/test evidence. Add a failing regression before each accepted
behavioral fix.

**Step 3: Verify corrections**

Run focused regressions, then:

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright
```

Expected: all tests and quality gates pass.

**Step 4: Record and commit**

Update `PROGRESS.md` with review disposition and evidence. Commit only accepted fixes and
their tests.

### Task 7: Phase 4 artifact and acceptance gates

**Files:**

- Create: `docs/phase-4-acceptance.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`

**Step 1: Run fresh verification**

Use @verification-before-completion and run:

```bash
uv run --python 3.12 pytest -q
uv run --python 3.13 pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright
uv build
uv run --with pyyaml python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/macwise
ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ci.yml")'
uv run pytest -q tests/repository
git diff --check
```

Repeat a fresh Python 3.12 wheel install. In a temporary state root, prove plan model and
SQLite round-trip plus plan help. Run one aggregate-only real read-only audit through the
planner without persisting names/paths; print counts/statuses only. Do not invoke apply,
Homebrew uninstall, Trash moves, or startup mutation.

**Step 2: Validate the claim**

Use @claim-validation. Check requirements, tests, scoped TODO/FIXME/HACK/
NotImplemented markers, skipped tests, dirty state, independent review, SQLite state
scope, and every open external/action gate.

**Step 3: Update durable truth**

Only mark MW-300 done if direct evidence passes. Advance MW-400 to `ready`. Keep hosted
CI/public publication, all action execution, approval, verification, undo, Codex
integration, and release explicitly open.

**Step 4: Commit**

```bash
git add docs/phase-4-acceptance.md README.md CHANGELOG.md PROGRESS.md TASK_QUEUE.md
git commit -m "docs: accept local Phase 4 planning"
```
