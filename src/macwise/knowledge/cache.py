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

    def _validate_cache_directory(self, *, create: bool) -> None:
        self._reject_symlink_ancestors(self.state_root)
        if self.state_root.exists() and not self.state_root.is_dir():
            raise OSError("cache state root is not a directory")
        if create:
            self.state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._reject_symlink_ancestors(self.state_root)
            self.cache_dir.mkdir(mode=0o700, exist_ok=True)
        if self.cache_dir.is_symlink():
            raise OSError("cache directory is a symbolic link")
        if self.cache_dir.exists() and not self.cache_dir.is_dir():
            raise OSError("cache directory is not a directory")
        self._reject_symlink_ancestors(self.cache_dir.parent)

    @staticmethod
    def _read_regular_file(path: Path) -> bytes:
        if path.is_symlink():
            raise OSError("cache entry is a symbolic link")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
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
            self._validate_cache_directory(create=False)
            if not entry.exists() and not entry.is_symlink():
                return self._unresolved(identity)
            claim = PublicPurposeClaim.model_validate_json(self._read_regular_file(entry))
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
        return PublicLookupResult(
            identity=identity,
            status=LookupStatus.RESOLVED,
            claim=claim,
            reason="Found fresh public app information in the local cache.",
        )

    def store(self, claim: PublicPurposeClaim) -> PublicLookupResult:
        """Stage and atomically activate one complete claim without recording lookup history."""

        identity = claim.identity
        entry = self.path_for(identity)
        temporary: Path | None = None
        try:
            self._validate_cache_directory(create=True)
            payload = claim.model_dump_json().encode()
            if len(payload) > _MAX_RECORD_BYTES:
                raise OSError("claim exceeds cache entry size limit")
            temporary = self.cache_dir / f".{entry.name}.{secrets.token_hex(16)}.tmp"
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(temporary, flags, 0o600)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("cache staging path is not a regular file")
                _write_all(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temporary, entry)
            temporary = None
            self._prune()
        except (OSError, ValueError):
            return self._unavailable(
                identity,
                "Public app information could not be saved to the local cache.",
            )
        finally:
            if temporary is not None:
                with suppress(OSError):
                    temporary.unlink(missing_ok=True)
        return PublicLookupResult(
            identity=identity,
            status=LookupStatus.RESOLVED,
            claim=claim,
            reason="Saved verified public app information in the local cache.",
        )

    def _prune(self) -> None:
        entries = [
            path
            for path in self.cache_dir.glob("*.json")
            if not path.is_symlink() and path.is_file()
        ]
        entries.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for entry in entries[self.max_entries :]:
            entry.unlink()
