"""Closed host-action adapters used only after approval and revalidation."""

from macwise.execution.commands import (
    CommandActionError,
    MutationCommandAdapter,
    MutationExecutable,
)
from macwise.execution.filesystem import FilesystemActionError, TrashFilesystemAdapter

__all__ = [
    "CommandActionError",
    "FilesystemActionError",
    "MutationCommandAdapter",
    "MutationExecutable",
    "TrashFilesystemAdapter",
]
