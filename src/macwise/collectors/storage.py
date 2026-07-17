"""Read-only storage inventory from structured diskutil output."""

import os
import plistlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    Evidence,
    Reliability,
    StorageLocation,
    VolumeRecord,
    stable_volume_id,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command

DISK_IDENTIFIER = re.compile(r"^disk[0-9]+(?:s[0-9]+)*$")


class StorageRunner(Protocol):
    """The narrow command boundary needed by the storage collector."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class StorageCollection:
    """Volume records and the limitations that qualify them."""

    volumes: tuple[VolumeRecord, ...]
    status: CollectorStatus


def _mapping_from_plist(data: bytes | str) -> dict[str, Any]:
    loaded = plistlib.loads(data.encode() if isinstance(data, str) else data)
    if not isinstance(loaded, dict):
        raise ValueError("Property list root is not a dictionary")
    return cast(dict[str, Any], loaded)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _boolean(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _read_only(metadata: dict[str, Any]) -> bool | None:
    values = (
        _boolean(cast(object, metadata.get("ReadOnlyMedia"))),
        _boolean(cast(object, metadata.get("ReadOnlyVolume"))),
    )
    known = tuple(value for value in values if value is not None)
    return any(known) if known else None


def parse_volume_info(data: bytes | str, *, collected_at: datetime) -> VolumeRecord:
    """Normalize one `diskutil info -plist` document."""
    metadata = _mapping_from_plist(data)
    device_identifier = _text(cast(object, metadata.get("DeviceIdentifier")))
    if device_identifier is None or not DISK_IDENTIFIER.fullmatch(device_identifier):
        raise ValueError("Volume metadata does not contain a safe device identifier")

    internal = _boolean(cast(object, metadata.get("Internal")))
    location = (
        StorageLocation.INTERNAL
        if internal is True
        else StorageLocation.EXTERNAL
        if internal is False
        else StorageLocation.UNKNOWN
    )
    encrypted = _boolean(cast(object, metadata.get("Encrypted")))
    if encrypted is None:
        encrypted = _boolean(cast(object, metadata.get("FileVault")))

    name = _text(cast(object, metadata.get("VolumeName"))) or device_identifier
    mount_point = _text(cast(object, metadata.get("MountPoint")))
    filesystem = _text(cast(object, metadata.get("FilesystemName"))) or _text(
        cast(object, metadata.get("FilesystemType"))
    )
    capacity = _integer(cast(object, metadata.get("TotalSize")))
    free = _integer(cast(object, metadata.get("FreeSpace")))
    removable = _boolean(cast(object, metadata.get("RemovableMedia")))
    protocol = _text(cast(object, metadata.get("BusProtocol")))
    smart_status = _text(cast(object, metadata.get("SMARTStatus")))
    read_only = _read_only(metadata)

    return VolumeRecord(
        id=stable_volume_id(device_identifier),
        name=name,
        device_identifier=device_identifier,
        mount_point=mount_point,
        location=location,
        filesystem=filesystem,
        capacity_bytes=capacity,
        free_bytes=free,
        read_only=read_only,
        encrypted=encrypted,
        removable=removable,
        protocol=protocol,
        smart_status=smart_status,
        evidence=(
            Evidence(
                kind="diskutil_volume_metadata",
                value={
                    "capacity_bytes": capacity,
                    "device_identifier": device_identifier,
                    "encrypted": encrypted,
                    "free_bytes": free,
                    "internal": internal,
                    "mount_point": mount_point,
                    "read_only": read_only,
                    "removable": removable,
                },
                source=f"diskutil info -plist {device_identifier}",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
            ),
        ),
    )


def _listed_identifiers(data: str) -> tuple[str, ...]:
    metadata = _mapping_from_plist(data)
    raw_identifiers: object = metadata.get("AllDisks", [])
    if not isinstance(raw_identifiers, list):
        raise ValueError("diskutil list metadata does not contain AllDisks")
    identifiers: list[str] = []
    for raw_identifier in cast(list[object], raw_identifiers):
        identifier = _text(raw_identifier)
        if identifier is None or not DISK_IDENTIFIER.fullmatch(identifier):
            continue
        identifiers.append(identifier)
    return tuple(dict.fromkeys(identifiers))


def collect_storage(
    *,
    collected_at: datetime,
    runner: StorageRunner = run_read_command,
) -> StorageCollection:
    """Collect disk and volume metadata through read-only diskutil plist commands."""
    listed = runner(ReadCommand.DISKUTIL, ("list", "-plist"))
    if listed.state is not CommandState.COMPLETE:
        state = (
            CollectorState.UNAVAILABLE
            if listed.state is CommandState.UNAVAILABLE
            else CollectorState.PARTIAL
        )
        return StorageCollection(
            volumes=(),
            status=CollectorStatus(
                collector="storage",
                state=state,
                collected_at=collected_at,
                records_count=0,
                limitations=listed.limitations,
            ),
        )

    try:
        identifiers = _listed_identifiers(listed.stdout)
    except (plistlib.InvalidFileException, ValueError, UnicodeError):
        return StorageCollection(
            volumes=(),
            status=CollectorStatus(
                collector="storage",
                state=CollectorState.PARTIAL,
                collected_at=collected_at,
                records_count=0,
                limitations=("The disk list metadata could not be read.",),
            ),
        )

    volumes: list[VolumeRecord] = []
    limitations: list[str] = []
    for identifier in identifiers:
        info = runner(ReadCommand.DISKUTIL, ("info", "-plist", identifier))
        if info.state is not CommandState.COMPLETE:
            limitations.extend(info.limitations or (f"Metadata for {identifier} is unavailable.",))
            continue
        try:
            volumes.append(parse_volume_info(info.stdout, collected_at=collected_at))
        except (plistlib.InvalidFileException, ValueError, UnicodeError):
            limitations.append(f"Metadata for {identifier} could not be read.")

    volumes.sort(key=lambda volume: volume.device_identifier)
    return StorageCollection(
        volumes=tuple(volumes),
        status=CollectorStatus(
            collector="storage",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=len(volumes),
            limitations=tuple(limitations),
        ),
    )


def resolve_storage_location(
    path: Path,
    volumes: Sequence[VolumeRecord],
) -> StorageLocation:
    """Classify a path by its longest known mount-point prefix."""
    absolute_path = Path(os.path.abspath(path))
    matches: list[tuple[int, VolumeRecord]] = []
    for volume in volumes:
        if volume.mount_point is None:
            continue
        mount_point = Path(os.path.abspath(volume.mount_point))
        if absolute_path == mount_point or mount_point in absolute_path.parents:
            matches.append((len(mount_point.parts), volume))
    if not matches:
        return StorageLocation.UNKNOWN
    _, best_match = max(matches, key=lambda match: match[0])
    if best_match.mount_point == "/" and absolute_path.parts[1:2] in {("Volumes",), ("Network",)}:
        return StorageLocation.UNKNOWN
    return best_match.location
