#!/usr/bin/env python3
"""Exercise MacWise apply/recovery/undo only against a disposable synthetic bundle.

This is product-side test tooling, not part of the independent evaluator.  It never
enumerates, moves, or changes installed Mac applications.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from macwise.execution import (
    FilesystemActionError,
    TrashFilesystemAdapter,
    application_identity_digest,
)
from macwise.models import (
    ActionObservation,
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    ExecutionAction,
    SoftwareRecord,
)
from macwise.persistence import ExecutionStore, PlanStore, execution_digest
from macwise.services import (
    ExecutionService,
    ExecutionServiceError,
    apply_approval_phrase,
    prepare_execution,
    undo_approval_phrase,
)
from macwise.services.planning import add_candidate

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
COMPLETE_COLLECTORS = tuple(
    CollectorStatus(
        collector=name, state=CollectorState.COMPLETE, collected_at=NOW, records_count=1
    )
    for name in ("applications", "homebrew", "usage", "startup", "backups", "overlap")
)


def _empty_output_directory(path: Path) -> None:
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise ValueError("--output-dir must be an empty, non-symlink directory")
    path.mkdir(parents=True, exist_ok=True)


def _probe(path: Path) -> ActionObservation:
    if not path.exists():
        return ActionObservation(exists=False)
    item = path.lstat()
    return ActionObservation(
        exists=True,
        device=item.st_dev,
        inode=item.st_ino,
        identity_digest=application_identity_digest(path) if path.is_dir() else None,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_temporary_root() -> Path:
    """Resolve the host temporary directory before product state-lock validation."""
    return Path(tempfile.gettempdir()).resolve(strict=True)


def _exercise() -> dict[str, object]:
    # /tmp is a symlink on macOS. The product deliberately rejects state paths
    # beneath symlink ancestors, so resolve it on every host before creating state.
    with tempfile.TemporaryDirectory(
        prefix="eval-action-lab-", dir=_canonical_temporary_root()
    ) as temporary:
        root = Path(temporary)
        applications = root / "Applications"
        trash = root / "TemporaryTrash"
        source = applications / "Synthetic.app"
        payload = source / "Contents" / "payload.txt"
        sentinel = root / "unrelated-sentinel.txt"
        payload.parent.mkdir(parents=True)
        trash.mkdir()
        payload.write_text("action-lab payload", encoding="utf-8")
        sentinel.write_text("must stay unchanged", encoding="utf-8")
        before_digest = _sha256(payload)
        sentinel_digest = _sha256(sentinel)
        record = SoftwareRecord(
            id="application:synthetic",
            entity_type=EntityType.APPLICATION,
            name="Synthetic",
            display_name="Synthetic App",
            install_path=str(source),
        )
        audit = AuditDocument(
            audit_id="audit:action-lab",
            collected_at=NOW,
            software=(record,),
            collectors=COMPLETE_COLLECTORS,
        )
        plan = add_candidate(
            None,
            audit,
            record.id,
            clock=lambda: NOW,
            plan_id_factory=lambda: "plan:action-lab",
            trash_root=trash,
        ).plan
        prepared = prepare_execution(plan, audit, trash_root=trash, filesystem_probe=_probe)
        state = root / "state"
        lock_path = state / "action-lab.lock"
        plan_store = PlanStore(state / "plans.db", lock_path=lock_path)
        execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
        plan_store.append(plan)
        adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)
        service = ExecutionService(
            plan_store=plan_store,
            execution_store=execution_store,
            state_lock_path=lock_path,
            trash_adapter=adapter,
            filesystem_probe=_probe,
            revalidator=lambda _: prepared,
            clock=lambda: NOW,
            run_id_factory=lambda: "run:action-lab",
        )
        applied = service.apply(prepared, approval=apply_approval_phrase(prepared.plan_digest))
        destination = Path(plan.actions[0].destination_path or "")
        after_apply = {"source_exists": source.exists(), "trash_exists": destination.exists()}

        class RestoreThenLoseEvidence:
            def apply(self, action: ExecutionAction) -> ActionObservation:
                return adapter.apply(action)

            def undo(self, action: ExecutionAction) -> ActionObservation:
                adapter.undo(action)
                raise FilesystemActionError("intentional action-lab evidence interruption")

        service.trash_adapter = RestoreThenLoseEvidence()
        with suppress(ExecutionServiceError):
            service.undo(approval=undo_approval_phrase(execution_digest(applied)))
        interrupted = execution_store.active()
        if interrupted is None:
            raise RuntimeError("action lab failed to retain an interrupted recovery journal")
        interrupted_recovery = {
            "state": interrupted.state.value,
            "source_exists": source.exists(),
        }
        service.trash_adapter = adapter
        undone = service.undo(approval=undo_approval_phrase(execution_digest(interrupted)))
        return {
            "schema_version": 1,
            "lab_kind": "temporary_synthetic_bundle",
            "source_before": {"exists": True, "payload_sha256": before_digest},
            "after_apply": after_apply,
            "interrupted_recovery": interrupted_recovery,
            "after_undo": {
                "source_exists": source.exists(),
                "trash_exists": destination.exists(),
                "payload_sha256": _sha256(payload),
            },
            "sentinel": {"unchanged": _sha256(sentinel) == sentinel_digest},
            "journal": {"apply_state": applied.state.value, "final_state": undone.state.value},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    _empty_output_directory(arguments.output_dir)
    (arguments.output_dir / "action-lab.json").write_text(
        json.dumps(_exercise(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("Saved temporary action-lab receipt.")


if __name__ == "__main__":
    main()
