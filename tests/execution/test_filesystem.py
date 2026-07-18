import os
from pathlib import Path

import pytest

from macwise.execution.filesystem import (
    FilesystemActionError,
    TrashFilesystemAdapter,
    application_identity_digest,
)
from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    InverseIntent,
    InverseKind,
    PlanActionKind,
    VerificationState,
)


def prepared_action(source: Path, destination: Path) -> ExecutionAction:
    source_stat = source.lstat()
    return ExecutionAction(
        plan_action_id="action:synthetic-trash",
        sequence=1,
        subject_id="application:synthetic",
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        state=ActionState.PENDING,
        verification=VerificationState.PENDING,
        before=ActionObservation(
            exists=True,
            device=source_stat.st_dev,
            inode=source_stat.st_ino,
            identity_digest=application_identity_digest(source),
        ),
        inverse=InverseIntent(
            kind=InverseKind.RESTORE_FROM_TRASH,
            source_path=str(destination),
            destination_path=str(source),
        ),
    )


def synthetic_bundle(tmp_path: Path) -> tuple[Path, Path, Path]:
    applications = tmp_path / "Applications"
    trash = tmp_path / "Trash"
    source = applications / "Synthetic.app"
    source.mkdir(parents=True)
    trash.mkdir()
    destination = trash / "Synthetic.app.macwise-test"
    return applications, trash, destination


def test_trash_move_refuses_changed_bundle_metadata_with_same_inode(tmp_path: Path) -> None:
    applications, trash, destination = synthetic_bundle(tmp_path)
    source = applications / "Synthetic.app"
    contents = source / "Contents"
    contents.mkdir()
    plist = contents / "Info.plist"
    plist.write_text("original")
    action = prepared_action(source, destination)
    original_inode = source.stat().st_ino
    plist.write_text("changed")

    adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)
    with pytest.raises(FilesystemActionError, match="identity changed"):
        adapter.apply(action)

    assert source.stat().st_ino == original_inode
    assert not destination.exists()


def test_descriptor_relative_trash_move_and_reverse_preserve_exact_inode(
    tmp_path: Path,
) -> None:
    applications, trash, destination = synthetic_bundle(tmp_path)
    source = applications / "Synthetic.app"
    action = prepared_action(source, destination)
    adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)

    after = adapter.apply(action)

    assert not source.exists()
    assert destination.is_dir()
    assert after.device == action.before.device
    assert after.inode == action.before.inode

    applied = action.model_copy(
        update={
            "state": ActionState.VERIFIED,
            "verification": VerificationState.VERIFIED,
            "after": after,
        }
    )
    restored = adapter.undo(applied)

    assert source.is_dir()
    assert not destination.exists()
    assert restored.inode == action.before.inode


def test_trash_move_refuses_occupied_destination_and_changed_inode(tmp_path: Path) -> None:
    applications, trash, destination = synthetic_bundle(tmp_path)
    source = applications / "Synthetic.app"
    action = prepared_action(source, destination)
    adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)
    destination.mkdir()

    with pytest.raises(FilesystemActionError, match="destination"):
        adapter.apply(action)
    assert source.is_dir()

    destination.rmdir()
    assert action.before.inode is not None
    changed = action.model_copy(
        update={"before": action.before.model_copy(update={"inode": action.before.inode + 1})}
    )
    with pytest.raises(FilesystemActionError, match="identity changed"):
        adapter.apply(changed)
    assert source.is_dir()


def test_trash_move_refuses_symlink_source_and_exclusive_rename_race(tmp_path: Path) -> None:
    applications, trash, destination = synthetic_bundle(tmp_path)
    source = applications / "Synthetic.app"
    action = prepared_action(source, destination)
    real = applications / "Real.app"
    source.rename(real)
    source.symlink_to(real, target_is_directory=True)
    adapter = TrashFilesystemAdapter(source_roots=(applications,), trash_root=trash)

    with pytest.raises(FilesystemActionError, match="ordinary application directory"):
        adapter.apply(action)
    assert real.is_dir()

    source.unlink()
    real.rename(source)
    action = prepared_action(source, destination)
    calls = 0

    def losing_race(
        source_fd: int,
        source_name: str,
        destination_fd: int,
        destination_name: str,
    ) -> None:
        nonlocal calls
        calls += 1
        os.mkdir(destination_name, dir_fd=destination_fd)
        raise FileExistsError(destination_name)

    racing = TrashFilesystemAdapter(
        source_roots=(applications,),
        trash_root=trash,
        rename_operation=losing_race,
    )
    with pytest.raises(FilesystemActionError, match="destination"):
        racing.apply(action)

    assert calls == 1
    assert source.is_dir()
    assert destination.is_dir()
