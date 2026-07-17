import hashlib
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    InverseIntent,
    InverseKind,
    PlanActionKind,
    VerificationState,
)
from macwise.persistence import (
    ExecutionStore,
    ExecutionStoreError,
    StateLock,
    canonical_execution_json,
    execution_digest,
)

NOW = datetime(2026, 7, 18, 2, 30, tzinfo=UTC)
PLAN_DIGEST = "a" * 64


def action(state: ActionState = ActionState.PENDING) -> ExecutionAction:
    return ExecutionAction(
        plan_action_id="action:example",
        sequence=1,
        subject_id="application:example",
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        state=state,
        verification=VerificationState.PENDING,
        before=ActionObservation(exists=True, device=42, inode=100),
        inverse=InverseIntent(
            kind=InverseKind.RESTORE_FROM_TRASH,
            source_path="/Users/example/.Trash/Example.app.macwise-test",
            destination_path="/Applications/Example.app",
        ),
    )


def run(
    manifest_revision: int = 1,
    *,
    run_id: str = "run:test",
    state: ExecutionState = ExecutionState.PREPARED,
    action_state: ActionState = ActionState.PENDING,
) -> ExecutionRun:
    return ExecutionRun(
        run_id=run_id,
        manifest_revision=manifest_revision,
        plan_id="plan:test",
        plan_revision=2,
        plan_digest=PLAN_DIGEST,
        approval_fingerprint="A" * 16,
        created_at=NOW,
        updated_at=NOW,
        state=state,
        actions=(action(action_state),),
    )


def test_execution_store_is_read_only_until_first_locked_append_and_round_trips(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state" / "executions.db"
    lock_path = tmp_path / "state" / "macwise.lock"
    store = ExecutionStore(database, lock_path=lock_path)

    assert store.active() is None
    assert not database.exists()
    with StateLock(lock_path) as held:
        store.append(run(), state_lock=held)

    assert store.active() == run()
    document_json = canonical_execution_json(run())
    assert execution_digest(run()) == hashlib.sha256(document_json.encode()).hexdigest()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        stored_json, stored_digest = connection.execute(
            "SELECT document_json, document_sha256 FROM execution_revisions"
        ).fetchone()
    assert stored_json == document_json
    assert stored_digest == execution_digest(run())


def test_execution_store_requires_exact_held_lock_and_monotonic_revisions(
    tmp_path: Path,
) -> None:
    database = tmp_path / "executions.db"
    lock_path = tmp_path / "macwise.lock"
    store = ExecutionStore(database, lock_path=lock_path)

    with pytest.raises(ExecutionStoreError, match="state lock"):
        store.append(run(), state_lock=StateLock(lock_path))

    with StateLock(lock_path) as held:
        store.append(run(), state_lock=held)
        with pytest.raises(ExecutionStoreError, match="active manifest"):
            store.append(run(3, state=ExecutionState.IN_PROGRESS), state_lock=held)
        store.append(run(2, state=ExecutionState.IN_PROGRESS), state_lock=held)

    assert store.active() == run(2, state=ExecutionState.IN_PROGRESS)


def test_interrupted_or_in_progress_run_blocks_competing_initial_run(tmp_path: Path) -> None:
    database = tmp_path / "executions.db"
    lock_path = tmp_path / "macwise.lock"
    store = ExecutionStore(database, lock_path=lock_path)
    with StateLock(lock_path) as held:
        store.append(run(), state_lock=held)
        store.append(
            run(
                2,
                state=ExecutionState.IN_PROGRESS,
                action_state=ActionState.IN_PROGRESS,
            ),
            state_lock=held,
        )
        with pytest.raises(ExecutionStoreError, match="unresolved"):
            store.append(run(run_id="run:competing"), state_lock=held)

    active = store.active()
    assert active is not None and active.run_id == "run:test"


def test_execution_store_rejects_corruption_and_future_schema_without_mutation(
    tmp_path: Path,
) -> None:
    database = tmp_path / "executions.db"
    lock_path = tmp_path / "macwise.lock"
    store = ExecutionStore(database, lock_path=lock_path)
    with StateLock(lock_path) as held:
        store.append(run(), state_lock=held)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE execution_revisions SET document_json = ?",
            ('{"tampered":true}',),
        )
    with pytest.raises(ExecutionStoreError, match="integrity"):
        store.active()

    future = tmp_path / "future.db"
    with sqlite3.connect(future) as connection:
        connection.execute("PRAGMA user_version = 2")
    before = future.read_bytes()
    with pytest.raises(ExecutionStoreError, match="newer MacWise schema"):
        ExecutionStore(future).active()
    assert future.read_bytes() == before


def test_execution_store_rejects_nested_symlink_ancestor(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(outside, target_is_directory=True)
    store = ExecutionStore(
        link / "nested" / "executions.db",
        lock_path=tmp_path / "macwise.lock",
    )

    with (
        StateLock(tmp_path / "macwise.lock") as held,
        pytest.raises(ExecutionStoreError, match="symbolic link"),
    ):
        store.append(run(), state_lock=held)

    assert not (outside / "nested").exists()
