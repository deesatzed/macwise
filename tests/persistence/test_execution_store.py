import hashlib
import sqlite3
from contextlib import closing
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


def observed_action(state: ActionState) -> ExecutionAction:
    return ExecutionAction(
        plan_action_id="action:example",
        sequence=1,
        subject_id="application:example",
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        state=state,
        verification=VerificationState.VERIFIED,
        before=ActionObservation(exists=True, device=42, inode=100),
        after=ActionObservation(exists=True, device=42, inode=100),
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


def observed_run(
    manifest_revision: int,
    *,
    run_id: str,
    state: ExecutionState,
    action_state: ActionState,
) -> ExecutionRun:
    return ExecutionRun(
        run_id=run_id,
        manifest_revision=manifest_revision,
        plan_id=f"plan:{run_id}",
        plan_revision=1,
        plan_digest=PLAN_DIGEST,
        approval_fingerprint="A" * 16,
        created_at=NOW,
        updated_at=NOW,
        state=state,
        actions=(observed_action(action_state),),
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
    with closing(sqlite3.connect(database)) as connection, connection:
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
    assert store.latest_undoable() == active


def test_execution_store_rejects_corruption_and_future_schema_without_mutation(
    tmp_path: Path,
) -> None:
    database = tmp_path / "executions.db"
    lock_path = tmp_path / "macwise.lock"
    store = ExecutionStore(database, lock_path=lock_path)
    with StateLock(lock_path) as held:
        store.append(run(), state_lock=held)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "UPDATE execution_revisions SET document_json = ?",
            ('{"tampered":true}',),
        )
    with pytest.raises(ExecutionStoreError, match="integrity"):
        store.active()

    future = tmp_path / "future.db"
    with closing(sqlite3.connect(future)) as connection, connection:
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


def test_latest_undoable_skips_newer_undone_run_and_can_resume_older_history(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "macwise.lock"
    store = ExecutionStore(tmp_path / "executions.db", lock_path=lock_path)
    with StateLock(lock_path) as held:
        store.append(
            observed_run(
                1, run_id="run:a", state=ExecutionState.PREPARED, action_state=ActionState.PENDING
            ),
            state_lock=held,
        )
        store.append(
            observed_run(
                2,
                run_id="run:a",
                state=ExecutionState.IN_PROGRESS,
                action_state=ActionState.IN_PROGRESS,
            ),
            state_lock=held,
        )
        run_a = observed_run(
            3, run_id="run:a", state=ExecutionState.SUCCEEDED, action_state=ActionState.VERIFIED
        )
        store.append(run_a, state_lock=held)
        store.append(
            observed_run(
                1, run_id="run:b", state=ExecutionState.PREPARED, action_state=ActionState.PENDING
            ),
            state_lock=held,
        )
        store.append(
            observed_run(
                2,
                run_id="run:b",
                state=ExecutionState.IN_PROGRESS,
                action_state=ActionState.IN_PROGRESS,
            ),
            state_lock=held,
        )
        run_b = observed_run(
            3, run_id="run:b", state=ExecutionState.SUCCEEDED, action_state=ActionState.VERIFIED
        )
        store.append(run_b, state_lock=held)
        store.append(
            observed_run(
                4,
                run_id="run:b",
                state=ExecutionState.UNDO_IN_PROGRESS,
                action_state=ActionState.UNDO_IN_PROGRESS,
            ),
            state_lock=held,
        )
        store.append(
            observed_run(
                5, run_id="run:b", state=ExecutionState.UNDONE, action_state=ActionState.UNDONE
            ),
            state_lock=held,
        )

        assert store.latest_undoable() == run_a
        resumed = observed_run(
            4,
            run_id="run:a",
            state=ExecutionState.UNDO_IN_PROGRESS,
            action_state=ActionState.UNDO_IN_PROGRESS,
        )
        store.append(resumed, state_lock=held)

    assert store.active() == resumed


def test_historical_resume_rechecks_prior_revision_integrity(tmp_path: Path) -> None:
    lock_path = tmp_path / "macwise.lock"
    database = tmp_path / "executions.db"
    store = ExecutionStore(database, lock_path=lock_path)
    with StateLock(lock_path) as held:
        store.append(
            observed_run(
                1, run_id="run:a", state=ExecutionState.PREPARED, action_state=ActionState.PENDING
            ),
            state_lock=held,
        )
        store.append(
            observed_run(
                2,
                run_id="run:a",
                state=ExecutionState.IN_PROGRESS,
                action_state=ActionState.IN_PROGRESS,
            ),
            state_lock=held,
        )
        store.append(
            observed_run(
                3,
                run_id="run:a",
                state=ExecutionState.SUCCEEDED,
                action_state=ActionState.VERIFIED,
            ),
            state_lock=held,
        )
        for revision, state, action_state in (
            (1, ExecutionState.PREPARED, ActionState.PENDING),
            (2, ExecutionState.IN_PROGRESS, ActionState.IN_PROGRESS),
            (3, ExecutionState.SUCCEEDED, ActionState.VERIFIED),
            (4, ExecutionState.UNDO_IN_PROGRESS, ActionState.UNDO_IN_PROGRESS),
            (5, ExecutionState.UNDONE, ActionState.UNDONE),
        ):
            store.append(
                observed_run(
                    revision,
                    run_id="run:b",
                    state=state,
                    action_state=action_state,
                ),
                state_lock=held,
            )

    with closing(sqlite3.connect(database)) as connection, connection:
        document = connection.execute(
            "SELECT document_json FROM execution_revisions WHERE run_id = ? AND manifest_revision = 3",
            ("run:a",),
        ).fetchone()[0]
        connection.execute(
            "UPDATE execution_revisions SET document_json = ? WHERE run_id = ? AND manifest_revision = 3",
            (str(document).replace('"inode":100', '"inode":101'), "run:a"),
        )

    resumed = observed_run(
        4,
        run_id="run:a",
        state=ExecutionState.UNDO_IN_PROGRESS,
        action_state=ActionState.UNDO_IN_PROGRESS,
    )
    with (
        StateLock(lock_path) as held,
        pytest.raises(ExecutionStoreError, match="integrity"),
    ):
        store.append(resumed, state_lock=held)
