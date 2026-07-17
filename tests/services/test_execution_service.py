import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.execution import FilesystemActionError, TrashFilesystemAdapter
from macwise.models import (
    ActionObservation,
    AuditDocument,
    EntityType,
    ExecutionAction,
    ExecutionState,
    SoftwareRecord,
)
from macwise.persistence import (
    ExecutionStore,
    PlanStore,
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


def filesystem_probe(path: Path) -> ActionObservation:
    if not path.exists():
        return ActionObservation(exists=False)
    item = path.lstat()
    return ActionObservation(
        exists=True,
        device=item.st_dev,
        inode=item.st_ino,
        identity_digest="a" * 64 if path.suffix.casefold() == ".app" else None,
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
    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=TrashFilesystemAdapter(
            source_roots=(applications,),
            trash_root=trash,
        ),
        clock=lambda: NOW,
        run_id_factory=lambda: "run:synthetic",
    )

    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )

    assert applied.state is ExecutionState.SUCCEEDED
    destination = Path(plan.actions[0].destination_path or "")
    assert destination.is_dir()
    assert not source.exists()
    assert execution_store.active() == applied
    with sqlite3.connect(execution_store.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)

    with pytest.raises(ExecutionServiceError, match="already executed"):
        service.apply(
            prepared,
            approval=apply_approval_phrase(prepared.plan_digest),
        )
    with sqlite3.connect(execution_store.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)

    undone = service.undo(
        approval=undo_approval_phrase(execution_digest(applied)),
    )

    assert undone.state is ExecutionState.UNDONE
    assert source.is_dir()
    assert not destination.exists()
    with sqlite3.connect(execution_store.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (5,)


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
    audit = AuditDocument(audit_id="audit:test", collected_at=NOW, software=(record,))
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
    assert active.state is ExecutionState.FAILED
    assert active.actions[0].state.value == "failed"
    assert source.is_dir()
    with sqlite3.connect(execution_store.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM execution_revisions").fetchone() == (3,)
