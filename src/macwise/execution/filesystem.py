"""Exclusive descriptor-relative Trash moves for exact synthetic or approved bundles."""

import ctypes
import os
import stat
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    InverseKind,
    PlanActionKind,
    VerificationState,
)

RenameOperation = Callable[[int, str, int, str], None]
_RENAME_EXCL = 0x00000004
_RENAME_NOFOLLOW_ANY = 0x00000010
_RENAME_NOREPLACE_LINUX = 0x1


class FilesystemActionError(RuntimeError):
    """An exact filesystem action could not proceed or verify safely."""


def _exclusive_rename(
    source_fd: int,
    source_name: str,
    destination_fd: int,
    destination_name: str,
) -> None:
    """Rename without replacement through already opened trusted directories."""
    library = ctypes.CDLL(None, use_errno=True)
    function: Any
    flags: int
    if sys.platform == "darwin":
        function = library.renameatx_np
        flags = _RENAME_EXCL | _RENAME_NOFOLLOW_ANY
    elif sys.platform.startswith("linux"):
        function = library.renameat2
        flags = _RENAME_NOREPLACE_LINUX
    else:
        raise OSError("Exclusive descriptor-relative rename is unavailable on this platform")
    function.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    function.restype = ctypes.c_int
    result = function(
        source_fd,
        os.fsencode(source_name),
        destination_fd,
        os.fsencode(destination_name),
        flags,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), destination_name)


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise FilesystemActionError("The action path contains a symbolic link ancestor.")


class TrashFilesystemAdapter:
    """Apply and reverse one exact same-filesystem application rename."""

    def __init__(
        self,
        *,
        source_roots: Sequence[Path],
        trash_root: Path,
        rename_operation: RenameOperation = _exclusive_rename,
    ) -> None:
        self.source_roots = tuple(path.expanduser().absolute() for path in source_roots)
        self.trash_root = trash_root.expanduser().absolute()
        self._rename = rename_operation

    def _require_allowed_paths(self, source: Path, destination: Path, *, undo: bool) -> None:
        expected_source_parents = (self.trash_root,) if undo else self.source_roots
        expected_destination_parents = self.source_roots if undo else (self.trash_root,)
        if source.parent not in expected_source_parents or destination.parent not in (
            expected_destination_parents
        ):
            raise FilesystemActionError("The action paths are outside the approved roots.")
        original = destination if undo else source
        if original.suffix.casefold() != ".app" or original.name in {"", ".", ".."}:
            raise FilesystemActionError("The source is not an ordinary application directory.")
        _reject_symlink_ancestors(source.parent)
        _reject_symlink_ancestors(destination.parent)

    @staticmethod
    def _open_directory(path: Path) -> int:
        flags = os.O_RDONLY | os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            return os.open(path, flags)
        except OSError as error:
            raise FilesystemActionError(
                "An approved action directory is not safely openable."
            ) from error

    def _move(
        self,
        source: Path,
        destination: Path,
        expected: ActionObservation,
        *,
        undo: bool,
    ) -> ActionObservation:
        source = source.expanduser().absolute()
        destination = destination.expanduser().absolute()
        self._require_allowed_paths(source, destination, undo=undo)
        source_fd = self._open_directory(source.parent)
        destination_fd = self._open_directory(destination.parent)
        try:
            try:
                source_stat = os.stat(source.name, dir_fd=source_fd, follow_symlinks=False)
            except FileNotFoundError as error:
                raise FilesystemActionError("The exact application source is missing.") from error
            if not stat.S_ISDIR(source_stat.st_mode):
                raise FilesystemActionError("The source is not an ordinary application directory.")
            if (
                expected.exists is not True
                or expected.device != source_stat.st_dev
                or expected.inode != source_stat.st_ino
            ):
                raise FilesystemActionError("The exact application identity changed.")
            if os.fstat(destination_fd).st_dev != source_stat.st_dev:
                raise FilesystemActionError("The application and Trash are not on one filesystem.")
            try:
                os.stat(destination.name, dir_fd=destination_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FilesystemActionError("The exact action destination is already occupied.")

            try:
                self._rename(source_fd, source.name, destination_fd, destination.name)
            except FileExistsError as error:
                raise FilesystemActionError(
                    "The exact action destination became occupied."
                ) from error
            except OSError as error:
                raise FilesystemActionError("The exclusive application move failed.") from error

            destination_stat = os.stat(
                destination.name,
                dir_fd=destination_fd,
                follow_symlinks=False,
            )
            try:
                os.stat(source.name, dir_fd=source_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FilesystemActionError("The source still exists after the application move.")
            if (
                destination_stat.st_dev != source_stat.st_dev
                or destination_stat.st_ino != source_stat.st_ino
            ):
                raise FilesystemActionError("The moved application identity did not verify.")
            return ActionObservation(
                exists=True,
                device=destination_stat.st_dev,
                inode=destination_stat.st_ino,
                identity_digest=expected.identity_digest,
            )
        finally:
            os.close(destination_fd)
            os.close(source_fd)

    def apply(self, action: ExecutionAction) -> ActionObservation:
        """Move one freshly prepared manual app to its exact exclusive Trash path."""
        if (
            action.kind is not PlanActionKind.MOVE_APPLICATION_TO_TRASH
            or action.state is not ActionState.PENDING
            or action.inverse.kind is not InverseKind.RESTORE_FROM_TRASH
            or action.inverse.source_path is None
            or action.inverse.destination_path is None
        ):
            raise FilesystemActionError("The action is not a freshly prepared Trash move.")
        return self._move(
            Path(action.inverse.destination_path),
            Path(action.inverse.source_path),
            action.before,
            undo=False,
        )

    def undo(self, action: ExecutionAction) -> ActionObservation:
        """Restore one exactly verified Trash move without overwriting its origin."""
        if (
            action.kind is not PlanActionKind.MOVE_APPLICATION_TO_TRASH
            or action.state is not ActionState.VERIFIED
            or action.verification is not VerificationState.VERIFIED
            or action.after is None
            or action.inverse.kind is not InverseKind.RESTORE_FROM_TRASH
            or action.inverse.source_path is None
            or action.inverse.destination_path is None
        ):
            raise FilesystemActionError("The action is not an exactly verified Trash move.")
        return self._move(
            Path(action.inverse.source_path),
            Path(action.inverse.destination_path),
            action.after,
            undo=True,
        )
