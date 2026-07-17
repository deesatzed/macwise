"""Read-only collection of macOS application bundle metadata."""

import os
import plistlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    Reliability,
    SoftwareRecord,
    StorageLocation,
    stable_software_id,
)

StorageResolver = Callable[[Path], StorageLocation]


@dataclass(frozen=True, slots=True)
class ApplicationCollection:
    """Application records and the limitations that qualify them."""

    software: tuple[SoftwareRecord, ...]
    status: CollectorStatus


def _unknown_storage(_path: Path) -> StorageLocation:
    return StorageLocation.UNKNOWN


def _string_value(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _bundle_size(app_path: Path) -> int:
    """Return lstat size without traversing symlinked directories."""
    total = app_path.lstat().st_size
    for current_root, directories, files in os.walk(app_path, followlinks=False):
        root = Path(current_root)
        retained_directories: list[str] = []
        for directory in directories:
            child = root / directory
            total += child.lstat().st_size
            if not child.is_symlink():
                retained_directories.append(directory)
        directories[:] = retained_directories
        for filename in files:
            total += (root / filename).lstat().st_size
    return total


def _collect_application(
    app_path: Path,
    *,
    collected_at: datetime,
    storage_resolver: StorageResolver,
) -> tuple[SoftwareRecord, tuple[str, ...]]:
    limitations: list[str] = []
    metadata: dict[str, Any] = {}
    plist_path = app_path / "Contents" / "Info.plist"
    if not plist_path.is_file():
        limitations.append(f"The application bundle {app_path} does not contain Info.plist.")
    else:
        try:
            loaded = plistlib.loads(plist_path.read_bytes())
            if isinstance(loaded, dict):
                metadata = cast(dict[str, Any], loaded)
            else:
                limitations.append(f"The application bundle {app_path} metadata could not be read.")
        except (OSError, plistlib.InvalidFileException, ValueError):
            limitations.append(f"The application bundle {app_path} metadata could not be read.")

    bundle_name = app_path.stem
    display_name = _string_value(metadata, "CFBundleDisplayName", "CFBundleName") or bundle_name
    identifier = _string_value(metadata, "CFBundleIdentifier")
    version = _string_value(metadata, "CFBundleShortVersionString", "CFBundleVersion")

    try:
        size_bytes = _bundle_size(app_path)
    except OSError:
        size_bytes = None
        limitations.append(f"The application bundle {app_path} size could not be measured.")

    try:
        storage_location = storage_resolver(app_path)
    except OSError:
        storage_location = StorageLocation.UNKNOWN
        limitations.append(f"The application bundle {app_path} storage location is unavailable.")

    evidence: list[Evidence] = []
    if metadata:
        evidence.append(
            Evidence(
                kind="application_bundle_metadata",
                value={
                    "bundle_id": identifier,
                    "display_name": display_name,
                    "version": version,
                },
                source=str(plist_path),
                collected_at=collected_at,
                reliability=Reliability.HIGH,
            )
        )
    if size_bytes is not None:
        evidence.append(
            Evidence(
                kind="application_bundle_size",
                value=size_bytes,
                source="filesystem metadata",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
                limitations=("Includes the app bundle only, not related user data.",),
            )
        )

    canonical_key = identifier or str(app_path.resolve(strict=False))
    return (
        SoftwareRecord(
            id=stable_software_id(EntityType.APPLICATION, canonical_key),
            entity_type=EntityType.APPLICATION,
            name=bundle_name,
            display_name=display_name,
            identifier=identifier,
            version=version,
            install_path=str(app_path),
            size_bytes=size_bytes,
            storage_location=storage_location,
            evidence=tuple(evidence),
        ),
        tuple(limitations),
    )


def _find_application_bundles(root: Path, limitations: list[str]) -> tuple[Path, ...]:
    app_paths: list[Path] = []

    def record_walk_error(error: OSError) -> None:
        affected_path = error.filename or str(root)
        limitations.append(f"The application folder {affected_path} could not be read.")

    for current_root, directories, _files in os.walk(
        root,
        topdown=True,
        followlinks=False,
        onerror=record_walk_error,
    ):
        current_path = Path(current_root)
        retained_directories: list[str] = []
        for directory in sorted(directories, key=str.casefold):
            candidate = current_path / directory
            if candidate.is_symlink():
                continue
            if candidate.suffix.casefold() == ".app" and candidate.is_dir():
                app_paths.append(candidate)
                continue
            retained_directories.append(directory)
        directories[:] = retained_directories
    return tuple(app_paths)


def collect_applications(
    roots: Sequence[Path],
    *,
    collected_at: datetime,
    storage_resolver: StorageResolver = _unknown_storage,
) -> ApplicationCollection:
    """Collect `.app` bundles within approved roots without entering bundles."""
    records: list[SoftwareRecord] = []
    limitations: list[str] = []

    for root in sorted(roots, key=lambda path: str(path).casefold()):
        if root.is_symlink() or not root.is_dir():
            limitations.append(f"The configured application folder {root} is not available.")
            continue
        for app_path in _find_application_bundles(root, limitations):
            record, item_limitations = _collect_application(
                app_path,
                collected_at=collected_at,
                storage_resolver=storage_resolver,
            )
            records.append(record)
            limitations.extend(item_limitations)

    state = CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL
    return ApplicationCollection(
        software=tuple(records),
        status=CollectorStatus(
            collector="applications",
            state=state,
            collected_at=collected_at,
            records_count=len(records),
            limitations=tuple(limitations),
        ),
    )
