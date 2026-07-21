"""Atomic, bounded local storage for cited public application claims."""

import hashlib
import json
import os
import secrets
import stat
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_data_path
from pydantic import ValidationError

from macwise.models.knowledge import (
    LookupIdentity,
    LookupStatus,
    PublicLookupResult,
    PublicPurposeClaim,
)

_CACHE_DIRECTORY_NAME = "public-claims"
_MAX_RECORD_BYTES = 16_384
_DEFAULT_MAX_ENTRIES = 256


def default_claim_cache_root() -> Path:
    """Return MacWise's platform-appropriate local state root."""

    return user_data_path("macwise")


def _write_all(descriptor: int, payload: bytes) -> None:
    """Write a complete cache record before its atomic activation."""

    remaining = memoryview(payload)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("could not write the complete cache record")
        remaining = remaining[written:]


class PublicClaimCache:
    """Store one expiring public claim per exact sanitized application identity."""

    def __init__(self, state_root: Path | None = None, *, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least one")
        selected_root = state_root if state_root is not None else default_claim_cache_root()
        self.state_root = selected_root.expanduser().absolute()
        self.cache_dir = self.state_root / _CACHE_DIRECTORY_NAME
        self.max_entries = max_entries

    @staticmethod
    def _reject_symlink_ancestors(path: Path) -> None:
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink():
                raise OSError("cache path contains a symbolic link")

    @staticmethod
    def _identity_key(identity: LookupIdentity) -> str:
        encoded = json.dumps(
            identity.model_dump(mode="json"),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def path_for(self, identity: LookupIdentity) -> Path:
        """Return the deterministic dedicated-cache path for an exact identity."""

        return self.cache_dir / f"{self._identity_key(identity)}.json"

    @staticmethod
    def _unavailable(identity: LookupIdentity, reason: str) -> PublicLookupResult:
        return PublicLookupResult(
            identity=identity,
            status=LookupStatus.UNAVAILABLE,
            reason=reason,
        )

    @staticmethod
    def _unresolved(identity: LookupIdentity) -> PublicLookupResult:
        return PublicLookupResult(
            identity=identity,
            status=LookupStatus.UNRESOLVED,
            reason="No fresh public app information is stored in the local cache.",
        )

    @staticmethod
    def _require_owner_only(directory_stat: os.stat_result) -> None:
        if not stat.S_ISDIR(directory_stat.st_mode):
            raise OSError("cache path is not a directory")
        if directory_stat.st_uid != os.getuid() or stat.S_IMODE(directory_stat.st_mode) & 0o077:
            raise OSError("cache directory is not owner-only")

    def _open_cache_directory(self, *, create: bool) -> int:
        self._reject_symlink_ancestors(self.state_root)
        if self.state_root.exists() and not self.state_root.is_dir():
            raise OSError("cache state root is not a directory")
        if create:
            self.state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._reject_symlink_ancestors(self.state_root)
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        root_descriptor = os.open(self.state_root, flags)
        descriptor: int | None = None
        try:
            self._require_owner_only(os.fstat(root_descriptor))
            if create:
                with suppress(FileExistsError):
                    os.mkdir(_CACHE_DIRECTORY_NAME, mode=0o700, dir_fd=root_descriptor)
            descriptor = os.open(_CACHE_DIRECTORY_NAME, flags, dir_fd=root_descriptor)
            self._require_owner_only(os.fstat(descriptor))
        except BaseException:
            if descriptor is not None:
                os.close(descriptor)
            raise
        finally:
            os.close(root_descriptor)
        return descriptor

    @staticmethod
    def _read_regular_file(directory_descriptor: int, name: str) -> bytes:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(name, flags, dir_fd=directory_descriptor)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("cache entry is not a regular file")
            data = os.read(descriptor, _MAX_RECORD_BYTES + 1)
            if len(data) > _MAX_RECORD_BYTES:
                raise OSError("cache entry exceeds the size limit")
            return data
        finally:
            os.close(descriptor)

    def lookup(self, identity: LookupIdentity, *, now: datetime | None = None) -> PublicLookupResult:
        """Return a fresh exact cache match, or a typed nonfatal cache outcome."""

        checked_at = datetime.now(UTC) if now is None else now
        if checked_at.tzinfo is None or checked_at.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        entry = self.path_for(identity)
        try:
            directory_descriptor = self._open_cache_directory(create=False)
            try:
                claim = PublicPurposeClaim.model_validate_json(
                    self._read_regular_file(directory_descriptor, entry.name)
                )
            finally:
                os.close(directory_descriptor)
        except FileNotFoundError:
            return self._unresolved(identity)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError):
            return self._unavailable(
                identity,
                "Stored public app information is unavailable or could not be verified.",
            )
        if claim.identity != identity or not claim.is_fresh(checked_at):
            return self._unavailable(
                identity,
                "Stored public app information did not match or is no longer current.",
            )
        return self._resolved(
            identity,
            claim,
            "Found fresh public app information in the local cache.",
        )

    def store(self, claim: PublicPurposeClaim) -> PublicLookupResult:
        """Stage and atomically activate one complete claim without recording lookup history."""

        identity = claim.identity
        entry = self.path_for(identity)
        temporary_name: str | None = None
        directory_descriptor: int | None = None
        try:
            if not claim.is_fresh(datetime.now(UTC)):
                raise ValueError("claim is already expired")
            directory_descriptor = self._open_cache_directory(create=True)
            payload = claim.model_dump_json().encode()
            if len(payload) > _MAX_RECORD_BYTES:
                raise OSError("claim exceeds cache entry size limit")
            temporary_name = f".{entry.name}.{secrets.token_hex(16)}.tmp"
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(temporary_name, flags, 0o600, dir_fd=directory_descriptor)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("cache staging path is not a regular file")
                _write_all(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(
                temporary_name,
                entry.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
            )
            temporary_name = None
            with suppress(OSError):
                self._prune(directory_descriptor)
        except (OSError, ValueError):
            return self._unavailable(
                identity,
                "Public app information could not be saved to the local cache.",
            )
        finally:
            if temporary_name is not None and directory_descriptor is not None:
                with suppress(OSError):
                    os.unlink(temporary_name, dir_fd=directory_descriptor)
            if directory_descriptor is not None:
                os.close(directory_descriptor)
        return self._resolved(
            identity=identity,
            claim=claim,
            reason="Saved verified public app information in the local cache.",
        )

    def _resolved(
        self, identity: LookupIdentity, claim: PublicPurposeClaim, reason: str
    ) -> PublicLookupResult:
        try:
            return PublicLookupResult(
                identity=identity,
                status=LookupStatus.RESOLVED,
                claim=claim,
                reason=reason,
            )
        except ValidationError:
            return self._unavailable(
                identity,
                "Stored public app information is no longer current.",
            )

    def _prune(self, directory_descriptor: int) -> None:
        entries: list[tuple[str, int]] = []
        for name in os.listdir(directory_descriptor):
            if not name.endswith(".json"):
                continue
            entry_stat = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            if stat.S_ISREG(entry_stat.st_mode):
                entries.append((name, entry_stat.st_mtime_ns))
        entries.sort(key=lambda entry: entry[1], reverse=True)
        for name, _ in entries[self.max_entries :]:
            os.unlink(name, dir_fd=directory_descriptor)
