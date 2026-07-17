"""Process-wide advisory lock for MacWise state-changing workflows."""

import errno
import fcntl
import os
from pathlib import Path
from types import TracebackType


class StateLockError(RuntimeError):
    """Bounded failure while acquiring the shared state lock."""


class StateLock:
    """Hold one non-blocking exclusive lock without following symbolic links."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().absolute()
        self._descriptor: int | None = None

    def _reject_symlink_ancestors(self) -> None:
        for ancestor in (self.path.parent, *self.path.parent.parents):
            if ancestor.is_symlink():
                raise StateLockError("The MacWise state lock path contains a symbolic link.")

    @property
    def is_held(self) -> bool:
        """Whether this exact lock instance currently owns its descriptor."""
        return self._descriptor is not None

    def __enter__(self) -> "StateLock":
        self._reject_symlink_ancestors()
        if self.path.is_symlink():
            raise StateLockError("The MacWise state lock cannot be a symbolic link.")
        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as error:
            raise StateLockError("MacWise could not create the state lock directory.") from error
        self._reject_symlink_ancestors()
        if not self.path.parent.is_dir():
            raise StateLockError("The MacWise state lock parent is not a directory.")

        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(self.path, flags, 0o600)
        except OSError as error:
            raise StateLockError("MacWise could not open the state lock safely.") from error
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            os.close(descriptor)
            if error.errno in {errno.EACCES, errno.EAGAIN}:
                raise StateLockError("another MacWise change is in progress") from error
            raise StateLockError("MacWise could not acquire the state lock safely.") from error
        self._descriptor = descriptor
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        if self._descriptor is None:
            return
        descriptor = self._descriptor
        self._descriptor = None
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
