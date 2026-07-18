"""Exclusive descriptor-relative Trash moves for exact synthetic or approved bundles."""

import ctypes
import hashlib
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


def _identity_digest_from_directory(descriptor: int, item: os.stat_result) -> str:
    digest = hashlib.sha256()
    digest.update(f"macwise-bundle-v1\0{item.st_dev}\0{item.st_ino}\0".encode())
    flags = os.O_RDONLY
    directory_flags = flags | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
        directory_flags |= os.O_NOFOLLOW
    contents_descriptor: int | None = None
    plist_descriptor: int | None = None
    try:
        try:
            contents_descriptor = os.open("Contents", directory_flags, dir_fd=descriptor)
            plist_descriptor = os.open(
                "Info.plist",
                flags,
                dir_fd=contents_descriptor,
            )
        except FileNotFoundError:
            digest.update(b"no-info-plist")
        else:
            plist_stat = os.fstat(plist_descriptor)
            if not stat.S_ISREG(plist_stat.st_mode):
                raise FilesystemActionError("The application metadata is not a regular file.")
            plist_digest = hashlib.sha256()
            while chunk := os.read(plist_descriptor, 64 * 1024):
                plist_digest.update(chunk)
            digest.update(b"info-plist\0")
            digest.update(plist_digest.digest())
    except OSError as error:
        raise FilesystemActionError("The application metadata is not safely readable.") from error
    finally:
        if plist_descriptor is not None:
            os.close(plist_descriptor)
        if contents_descriptor is not None:
            os.close(contents_descriptor)
    return digest.hexdigest()


def application_identity_digest(path: Path) -> str:
    """Bind an application identity to its inode and descriptor-read metadata."""
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path.expanduser().absolute(), flags)
    except OSError as error:
        raise FilesystemActionError("The application identity is not safely readable.") from error
    try:
        item = os.fstat(descriptor)
        if not stat.S_ISDIR(item.st_mode):
            raise FilesystemActionError("The application identity is not a directory.")
        return _identity_digest_from_directory(descriptor, item)
    finally:
        os.close(descriptor)


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

    @staticmethod
    def _open_child_directory(parent_descriptor: int, name: str) -> int:
        flags = os.O_RDONLY | os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            return os.open(name, flags, dir_fd=parent_descriptor)
        except OSError as error:
            raise FilesystemActionError(
                "The approved application is not safely openable."
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
        source_bundle_fd: int | None = None
        try:
            try:
                source_stat = os.stat(source.name, dir_fd=source_fd, follow_symlinks=False)
            except FileNotFoundError as error:
                raise FilesystemActionError("The exact application source is missing.") from error
            if not stat.S_ISDIR(source_stat.st_mode):
                raise FilesystemActionError("The source is not an ordinary application directory.")
            source_bundle_fd = self._open_child_directory(source_fd, source.name)
            current_identity = _identity_digest_from_directory(source_bundle_fd, source_stat)
            if (
                expected.exists is not True
                or expected.device != source_stat.st_dev
                or expected.inode != source_stat.st_ino
                or expected.identity_digest != current_identity
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
            destination_identity = _identity_digest_from_directory(
                source_bundle_fd,
                destination_stat,
            )
            if destination_identity != current_identity:
                raise FilesystemActionError("The moved application metadata did not verify.")
            return ActionObservation(
                exists=True,
                device=destination_stat.st_dev,
                inode=destination_stat.st_ino,
                identity_digest=destination_identity,
            )
        finally:
            if source_bundle_fd is not None:
                os.close(source_bundle_fd)
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
