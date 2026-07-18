import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.execution import (
    FilesystemActionError,
    TrashFilesystemAdapter,
    application_identity_digest,
)
from macwise.models import (
    ActionObservation,
    ActionState,
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    PlanDocument,
    SoftwareRecord,
)
from macwise.persistence import (
    ExecutionStore,
    PlanStore,
    StateLock,
    StateLockError,
    execution_digest,
)
from macwise.services import (
    ExecutionService,
    ExecutionServiceError,
    apply_approval_phrase,
    prepare_execution,
    undo_approval_phrase,
)
from macwise.services.planning import add_candidate

NOW = datetime(2026, 7, 18, 4, 0, tzinfo=UTC)
COMPLETE_COLLECTORS = tuple(
    CollectorStatus(
        collector=name,
        state=CollectorState.COMPLETE,
        collected_at=NOW,
        records_count=1,
    )
    for name in ("applications", "homebrew", "usage", "startup", "backups", "overlap")
)


def filesystem_probe(path: Path) -> ActionObservation:
    if not path.exists():
        return ActionObservation(exists=False)
    item = path.lstat()
    return ActionObservation(
        exists=True,
        device=item.st_dev,
        inode=item.st_ino,
        identity_digest=application_identity_digest(path) if path.is_dir() else None,
    )


def test_execution_service_journals_before_move_verifies_and_undoes_synthetic_bundle(
    tmp_path: Path,
) -> None:
    applications = tmp_path / "Applications"
    trash = tmp_path / "Trash"
    source = applications / "Synthetic.app"
    source.mkdir(parents=True)
    trash.mkdir()
    record = SoftwareRecord(
        id="application:synthetic",
        entity_type=EntityType.APPLICATION,
        name="Synthetic",
        display_name="Synthetic App",
        install_path=str(source),
    )
    planned_audit = AuditDocument(
        audit_id="audit:planned",
        collected_at=NOW,
        software=(record,),
        collectors=COMPLETE_COLLECTORS,
    )
    plan = add_candidate(
        None,
        planned_audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:synthetic",
        trash_root=trash,
    ).plan
    fresh_audit = planned_audit.model_copy(update={"audit_id": "audit:fresh"})
    prepared = prepare_execution(
        plan,
        fresh_audit,
        trash_root=trash,
        filesystem_probe=filesystem_probe,
    )
    state = tmp_path / "state"
    lock_path = state / "macwise.lock"
    plan_store = PlanStore(state / "macwise.db", lock_path=lock_path)
    execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
    plan_store.append(plan)
    revalidations: list[str] = []

    def locked_revalidator(current_plan: PlanDocument):
        revalidations.append(current_plan.plan_id)
        with (
            pytest.raises(StateLockError, match="in progress"),
            StateLock(lock_path),
        ):
            pass
        return prepared

    base_adapter = TrashFilesystemAdapter(
        source_roots=(applications,),
        trash_root=trash,
    )
    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=base_adapter,
        filesystem_probe=filesystem_probe,
        revalidator=locked_revalidator,
        clock=lambda: NOW,
        run_id_factory=lambda: "run:synthetic",
    )

    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )

    assert applied.state is ExecutionState.SUCCEEDED
    assert revalidations == [plan.plan_id]
    destination = Path(plan.actions[0].destination_path or "")
    assert destination.is_dir()
    assert not source.exists()
    assert execution_store.active() == applied
    with closing(sqlite3.connect(execution_store.path)) as connection, connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)

    with pytest.raises(ExecutionServiceError, match="already executed"):
        service.apply(
            prepared,
            approval=apply_approval_phrase(prepared.plan_digest),
        )
    with closing(sqlite3.connect(execution_store.path)) as connection, connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)

    class RestoreThenLoseEvidence:
        def apply(self, action: ExecutionAction) -> ActionObservation:
            return base_adapter.apply(action)

        def undo(self, action: ExecutionAction) -> ActionObservation:
            base_adapter.undo(action)
            raise FilesystemActionError("synthetic lost post-restore evidence")

    service.trash_adapter = RestoreThenLoseEvidence()
    with pytest.raises(ExecutionServiceError, match="approved undo"):
        service.undo(approval=undo_approval_phrase(execution_digest(applied)))
    interrupted = execution_store.active()
    assert interrupted is not None
    assert interrupted.state is ExecutionState.INTERRUPTED
    assert interrupted.actions[0].state is ActionState.UNDO_IN_PROGRESS

    service.trash_adapter = base_adapter
    undone = service.undo(
        approval=undo_approval_phrase(execution_digest(interrupted)),
    )

    assert undone.state is ExecutionState.UNDONE
    assert source.is_dir()
    assert not destination.exists()
    with closing(sqlite3.connect(execution_store.path)) as connection, connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (6,)


def test_interrupted_trash_move_is_classified_then_restored(tmp_path: Path) -> None:
    applications = tmp_path / "Applications"
    trash = tmp_path / "Trash"
    source = applications / "Synthetic.app"
    source.mkdir(parents=True)
    trash.mkdir()
    record = SoftwareRecord(
        id="application:synthetic",
        entity_type=EntityType.APPLICATION,
        name="Synthetic",
        display_name="Synthetic App",
        install_path=str(source),
    )
    audit = AuditDocument(
        audit_id="audit:crash",
        collected_at=NOW,
        software=(record,),
        collectors=COMPLETE_COLLECTORS,
    )
    plan = add_candidate(
        None,
        audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:crash",
        trash_root=trash,
    ).plan
    prepared = prepare_execution(
        plan,
        audit,
        trash_root=trash,
        filesystem_probe=filesystem_probe,
    )
    state = tmp_path / "state"
    lock_path = state / "macwise.lock"
    plan_store = PlanStore(state / "macwise.db", lock_path=lock_path)
    execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
    plan_store.append(plan)
    created = ExecutionRun(
        run_id="run:crash",
        manifest_revision=1,
        plan_id=plan.plan_id,
        plan_revision=plan.revision,
        plan_digest=prepared.plan_digest,
        approval_fingerprint=prepared.plan_digest[:16].upper(),
        created_at=NOW,
        updated_at=NOW,
        state=ExecutionState.PREPARED,
        actions=prepared.actions,
    )
    in_progress = created.model_copy(
        update={
            "manifest_revision": 2,
            "state": ExecutionState.IN_PROGRESS,
            "actions": (prepared.actions[0].model_copy(update={"state": ActionState.IN_PROGRESS}),),
        }
    )
    adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)
    with StateLock(lock_path) as held:
        execution_store.append(created, state_lock=held)
        execution_store.append(in_progress, state_lock=held)
    adapter.apply(prepared.actions[0])
    destination = Path(plan.actions[0].destination_path or "")
    assert destination.is_dir() and not source.exists()
    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=adapter,
        filesystem_probe=filesystem_probe,
        clock=lambda: NOW,
        run_id_factory=lambda: "unused",
    )

    recovered = service.undo(
        approval=undo_approval_phrase(execution_digest(in_progress)),
    )

    assert recovered.state is ExecutionState.UNDONE
    assert source.is_dir()
    assert not destination.exists()


def test_execution_service_records_failure_after_in_progress_before_stopping(
    tmp_path: Path,
) -> None:
    applications = tmp_path / "Applications"
    trash = tmp_path / "Trash"
    source = applications / "Synthetic.app"
    source.mkdir(parents=True)
    trash.mkdir()
    record = SoftwareRecord(
        id="application:synthetic",
        entity_type=EntityType.APPLICATION,
        name="Synthetic",
        display_name="Synthetic App",
        install_path=str(source),
    )
    audit = AuditDocument(
        audit_id="audit:test",
        collected_at=NOW,
        software=(record,),
        collectors=COMPLETE_COLLECTORS,
    )
    plan = add_candidate(
        None,
        audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:synthetic",
        trash_root=trash,
    ).plan
    prepared = prepare_execution(
        plan,
        audit,
        trash_root=trash,
        filesystem_probe=filesystem_probe,
    )
    state = tmp_path / "state"
    lock_path = state / "macwise.lock"
    plan_store = PlanStore(state / "macwise.db", lock_path=lock_path)
    execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
    plan_store.append(plan)

    class FailingAdapter:
        def apply(self, action: ExecutionAction) -> ActionObservation:
            del action
            raise FilesystemActionError("synthetic adapter failure")

        def undo(self, action: ExecutionAction) -> ActionObservation:
            raise AssertionError(f"unexpected undo: {action}")

    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=FailingAdapter(),
        clock=lambda: NOW,
        run_id_factory=lambda: "run:failed",
    )

    with pytest.raises(ExecutionServiceError, match="approved action"):
        service.apply(prepared, approval=apply_approval_phrase(prepared.plan_digest))

    active = execution_store.active()
    assert active is not None
    assert active.state is ExecutionState.INTERRUPTED
    assert active.actions[0].state is ActionState.IN_PROGRESS
    assert active.actions[0].verification.value == "unknown"
    assert source.is_dir()
    with closing(sqlite3.connect(execution_store.path)) as connection, connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)
