"""Closed host-action adapters used only after approval and revalidation."""

from macwise.execution.filesystem import FilesystemActionError, TrashFilesystemAdapter

__all__ = ["FilesystemActionError", "TrashFilesystemAdapter"]
